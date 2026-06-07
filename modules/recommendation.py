"""Score-based recommendation logic."""

from __future__ import annotations

import re
from typing import Any

from .llm_client import generate_text, is_mock_mode
from .prompt_templates import recommendation_prompt


def _tokens(text: str) -> set[str]:
    raw = re.split(r"[\s,./|·:;!?()\[\]{}<>\"'`~]+", (text or "").lower())
    return {t.strip() for t in raw if len(t.strip()) >= 2}


def _extract_grade(grade_text: str) -> int | None:
    m = re.search(r"([1-6])", grade_text or "")
    return int(m.group(1)) if m else None


def _grade_in_band(grade: int | None, band: str) -> bool:
    if grade is None:
        return False
    nums = [int(x) for x in re.findall(r"[1-6]", band or "")]
    if not nums:
        return True
    if len(nums) == 1:
        return grade == nums[0]
    return min(nums) <= grade <= max(nums)


def _match_count(keywords: list[str], user_text: str) -> int:
    lowered = (user_text or "").lower()
    count = 0
    for kw in keywords:
        if kw.lower() in lowered:
            count += 1
    return count


def score_book(book: dict[str, Any], grade: str, topic: str, class_context: str) -> dict[str, Any]:
    grade_num = _extract_grade(grade)
    themes = book.get("main_themes", [])
    emotions = book.get("emotion_keywords", [])

    theme_matches = _match_count(themes, topic + " " + class_context)
    emotion_matches = _match_count(emotions, class_context + " " + topic)

    theme_score = 40 if theme_matches else 0
    if theme_matches > 1:
        theme_score = min(40, 20 + theme_matches * 10)

    grade_score = 20 if _grade_in_band(grade_num, book.get("recommended_grade_band", "")) else 0
    emotion_score = 20 if emotion_matches else 0
    if emotion_matches > 1:
        emotion_score = min(20, 10 + emotion_matches * 5)

    question_score = 10 if book.get("question_hooks") else 0
    activity_score = 10 if book.get("lesson_activity_ideas") else 0
    total = theme_score + grade_score + emotion_score + question_score + activity_score

    return {
        "score": total,
        "score_detail": {
            "주제 일치": theme_score,
            "학년 적합성": grade_score,
            "정서 키워드 일치": emotion_score,
            "질문 생성 가능성": question_score,
            "활동 확장성": activity_score,
        },
    }


def _fallback_reason(book: dict[str, Any], topic: str, class_context: str, activity_style: str) -> str:
    themes = ", ".join(book.get("main_themes", [])[:3])
    emotions = ", ".join(book.get("emotion_keywords", [])[:3])
    return (
        f"'{topic}' 주제와 {themes} 주제가 연결되고, 학급 상황에서 보이는 "
        f"{emotions} 같은 감정을 인물 중심으로 안전하게 다룰 수 있습니다. "
        f"{activity_style} 활동으로 확장하기 좋습니다."
    )


def recommend_picturebooks(
    catalog: list[dict[str, Any]],
    grade: str,
    subject: str,
    achievement: str,
    topic: str,
    class_context: str,
    lesson_minutes: int,
    activity_style: str,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for book in catalog:
        score_info = score_book(book, grade, topic, class_context)
        item = dict(book)
        item.update(score_info)
        scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    candidates = scored[:top_n]

    # In API mode, the LLM can rewrite reasons. The app still works without it.
    llm_note = ""
    if not is_mock_mode():
        prompt = recommendation_prompt(
            grade=grade,
            subject=subject,
            achievement=achievement,
            topic=topic,
            class_context=class_context,
            lesson_minutes=lesson_minutes,
            activity_style=activity_style,
            candidates=candidates,
        )
        llm_note = generate_text(prompt)

    results: list[dict[str, Any]] = []
    for book in candidates:
        hooks = book.get("question_hooks", [])
        activities = book.get("lesson_activity_ideas", [])
        cautions = book.get("cautions", [])
        results.append(
            {
                "그림책 제목": book.get("title", ""),
                "추천 점수": book.get("score", 0),
                "추천 이유": _fallback_reason(book, topic, class_context, activity_style),
                "적합 학년": book.get("recommended_grade_band", "확인 필요"),
                "핵심 주제": ", ".join(book.get("main_themes", [])),
                "정서 키워드": ", ".join(book.get("emotion_keywords", [])),
                "질문 중심수업 가능성": "높음" if book.get("score", 0) >= 70 else "보통",
                "핵심 질문 1개": hooks[0] if hooks else "확인 필요",
                "수업 활동 아이디어": activities[0] if activities else "확인 필요",
                "유의점": cautions[0] if cautions else "개인 경험 공개를 강요하지 않습니다.",
                "추천 근거": "내부 DB",
                "점수 세부": book.get("score_detail", {}),
                "LLM 보완 메모": llm_note[:500] if llm_note else "",
            }
        )
    return results
