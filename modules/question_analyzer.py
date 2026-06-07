"""Student question classification and safety rewriting."""

from __future__ import annotations

import re
from typing import Any

RISK_KEYWORDS = [
    "너도",
    "네가",
    "부모님",
    "엄마",
    "아빠",
    "가족",
    "상처받은 적",
    "맞은 적",
    "학대",
    "자살",
    "죽고",
    "죽어",
    "트라우마",
    "비밀",
    "괴롭힘 당한",
    "왕따당한",
]

CATEGORY_ORDER = [
    "사실 확인 질문",
    "해석 질문",
    "감정 질문",
    "관점 전환 질문",
    "가치 판단 질문",
    "삶 연결 질문",
    "공동체 실천 질문",
    "위험하거나 사생활 노출 가능성이 있는 질문",
]


def split_questions(text: str) -> list[str]:
    lines = [re.sub(r"^[\-*•\d.)\s]+", "", line.strip()) for line in (text or "").splitlines()]
    questions = [line for line in lines if line]
    if len(questions) <= 1 and "?" in (text or ""):
        parts = re.split(r"(?<=\?)\s+", text.strip())
        questions = [p.strip() for p in parts if p.strip()]
    return questions


def is_risky(question: str) -> bool:
    q = question.replace(" ", "")
    return any(k.replace(" ", "") in q for k in RISK_KEYWORDS)


def classify_question(question: str) -> str:
    q = question.strip()
    compact = q.replace(" ", "")
    if is_risky(q):
        return "위험하거나 사생활 노출 가능성이 있는 질문"
    if any(k in compact for k in ["우리반", "우리는", "서로", "공동체", "무엇을해야", "실천"]):
        return "공동체 실천 질문"
    if any(k in compact for k in ["나도", "내가", "우리생활", "경험", "삶", "생활"]):
        return "삶 연결 질문"
    if any(k in compact for k in ["옳", "좋", "나쁘", "고쳐야", "인정", "존중", "선택"]):
        return "가치 판단 질문"
    if any(k in compact for k in ["입장", "관점", "친구들이", "부모", "다른사람", "상대"]):
        return "관점 전환 질문"
    if any(k in compact for k in ["마음", "기분", "감정", "슬", "화", "두려", "외로", "무서"]):
        return "감정 질문"
    if any(k in compact for k in ["왜", "어떻게", "무슨뜻", "의미"]):
        return "해석 질문"
    return "사실 확인 질문"


def safe_rewrite(question: str) -> str:
    if not is_risky(question):
        return question
    compact = question.replace(" ", "")
    if "부모" in compact or "엄마" in compact or "아빠" in compact or "가족" in compact:
        return "주인공처럼 마음이 힘든 친구에게 우리는 어떤 말을 해줄 수 있을까?"
    if "상처" in compact or "괴롭힘" in compact or "왕따" in compact:
        return "책 속 인물이 속상했을 때 주변 사람들은 어떻게 도와줄 수 있었을까?"
    if "죽" in compact or "자살" in compact:
        return "상실이나 슬픔을 겪는 인물에게 필요한 위로와 도움은 무엇일까?"
    return "인물의 마음을 안전하게 살피고, 우리 반에서 도울 수 있는 방법은 무엇일까?"


def make_teaching_variants(question: str) -> dict[str, str]:
    base = safe_rewrite(question)
    return {
        "짝 토론 질문": base,
        "모둠 토론 질문": f"{base} 여러 생각을 모아 우리 반에서 할 수 있는 방법을 찾아봅시다.",
        "글쓰기 질문": f"'{base}'에 대한 내 생각과 그 까닭을 한 문단으로 써 봅시다.",
        "활동지 질문": f"장면 근거 1가지와 내 생각 1가지를 써 봅시다: {base}",
    }


def analyze_student_questions(text: str) -> dict[str, Any]:
    questions = split_questions(text)
    classified: list[dict[str, str]] = []
    for q in questions:
        category = classify_question(q)
        classified.append(
            {
                "학생 질문": q,
                "분류 유형": category,
                "정서 안전 점검": "수정 필요" if category == "위험하거나 사생활 노출 가능성이 있는 질문" else "대체로 안전",
                "안전한 질문 제안": safe_rewrite(q) if category == "위험하거나 사생활 노출 가능성이 있는 질문" else "",
            }
        )

    def rank(row: dict[str, str]) -> int:
        order_score = {
            "공동체 실천 질문": 8,
            "삶 연결 질문": 7,
            "가치 판단 질문": 6,
            "관점 전환 질문": 5,
            "감정 질문": 4,
            "해석 질문": 3,
            "사실 확인 질문": 2,
            "위험하거나 사생활 노출 가능성이 있는 질문": 1,
        }
        return order_score.get(row["분류 유형"], 0)

    safe_rows = [r for r in classified if r["분류 유형"] != "위험하거나 사생활 노출 가능성이 있는 질문"]
    recommended_rows = sorted(safe_rows, key=rank, reverse=True)[:3]
    if len(recommended_rows) < 3:
        recommended_rows += [r for r in classified if r not in recommended_rows][: 3 - len(recommended_rows)]

    teaching = []
    for r in recommended_rows:
        variants = make_teaching_variants(r["학생 질문"])
        teaching.append({"원 질문": r["학생 질문"], "분류 유형": r["분류 유형"], **variants})

    risky = [r for r in classified if r["분류 유형"] == "위험하거나 사생활 노출 가능성이 있는 질문"]

    return {
        "classified": classified,
        "recommended": recommended_rows,
        "teaching_variants": teaching,
        "safe_rewrites": risky,
        "summary": {
            "전체 질문 수": len(classified),
            "수업화 추천 질문 수": len(recommended_rows),
            "안전 수정 필요 질문 수": len(risky),
        },
    }
