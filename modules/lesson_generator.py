"""Lesson, scan, question-card generation helpers."""

from __future__ import annotations

import json
import re
from typing import Any

from .llm_client import generate_text, is_mock_mode
from .pdf_utils import trim_text_for_prompt
from .prompt_templates import lesson_plan_prompt, question_cards_prompt, scan_material_prompt

QUESTION_TYPES = [
    "표지 또는 제목 질문",
    "그림 관찰 질문",
    "이야기 이해 질문",
    "인물 감정 질문",
    "행동 이유 질문",
    "관점 전환 질문",
    "가치 판단 질문",
    "삶 연결 질문",
    "공동체 실천 질문",
    "생각 쓰기 질문",
]


def _safe_json_loads(text: str) -> Any | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.S)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                return None
    return None


def _infer_characters(text: str) -> list[str]:
    candidates = re.findall(r"[가-힣]{2,6}", text or "")
    stopwords = {"그림책", "그리고", "하지만", "어느날", "이야기", "친구들", "선생님", "학생들", "아이들"}
    names: list[str] = []
    for c in candidates:
        if c not in stopwords and c not in names:
            names.append(c)
        if len(names) >= 5:
            break
    return names or ["주인공", "주변 인물"]


def generate_scan_material(title: str, raw_text: str) -> dict[str, Any]:
    text = trim_text_for_prompt(raw_text, 5000)
    if not is_mock_mode() and len(text) >= 30:
        response = generate_text(scan_material_prompt(title, text))
        parsed = _safe_json_loads(response)
        if isinstance(parsed, dict):
            return parsed

    clean = re.sub(r"\s+", " ", text).strip()
    short = clean[:500] + ("..." if len(clean) > 500 else "")
    characters = _infer_characters(clean)
    return {
        "그림책 내용 요약": short or "OCR 텍스트가 부족합니다. 제목과 주요 장면을 추가로 입력해 주세요.",
        "주요 인물": characters,
        "핵심 사건": [
            "인물이 낯선 상황 또는 갈등을 만납니다.",
            "인물의 마음이 흔들리거나 선택이 필요해집니다.",
            "관계, 자기수용, 용기와 관련된 변화 가능성이 드러납니다.",
        ],
        "핵심 갈등": "인물의 속마음과 외부 상황 사이의 긴장, 또는 나와 타인의 차이를 받아들이는 문제로 수업화할 수 있습니다.",
        "인물의 감정 흐름": ["궁금함", "망설임", "불안 또는 속상함", "이해", "안도 또는 용기"],
        "수업 주제 후보": ["인물의 마음 읽기", "다름과 자기수용", "속마음 표현하기", "친구와 공동체"],
        "질문을 만들기 좋은 장면": [
            "표지 또는 제목에서 인물의 마음을 상상할 수 있는 장면",
            "인물이 갈등을 마주하는 장면",
            "인물이 말하지 못한 마음이 드러나는 장면",
            "관계나 선택이 달라지는 장면",
        ],
        "수업 활동 아이디어": ["질문 카드 만들기", "짝 토론", "인물에게 말 걸기", "마음성장노트 쓰기"],
        "정서적 유의점": [
            "학생 개인의 가족사나 상처 경험을 직접 묻지 않습니다.",
            "인물의 마음을 먼저 다룬 뒤 선택적으로 나와 연결합니다.",
            "감정 표현은 진단이 아니라 관찰과 공감의 언어로 다룹니다.",
        ],
    }


def generate_question_cards(title: str, summary: str, grade: str, topic: str) -> list[dict[str, str]]:
    if not is_mock_mode():
        response = generate_text(question_cards_prompt(title, summary, grade, topic))
        parsed = _safe_json_loads(response)
        if isinstance(parsed, list) and len(parsed) >= 5:
            return parsed[:10]

    book = title or "이 그림책"
    theme = topic or "인물의 마음"
    questions = [
        f"'{book}'이라는 제목과 표지를 보면 어떤 마음이나 사건이 떠오르나요?",
        "그림 속 인물의 표정, 몸짓, 색깔에서 가장 먼저 보이는 것은 무엇인가요?",
        "이야기에서 인물에게 가장 중요하게 일어난 일은 무엇인가요?",
        "그 장면에서 인물은 어떤 감정을 느꼈을까요? 그렇게 생각한 까닭은 무엇인가요?",
        "인물은 왜 그런 행동을 했을까요? 말하지 못한 마음이 있었을까요?",
        "다른 인물의 입장에서 같은 장면을 본다면 어떻게 다르게 보일까요?",
        f"인물의 선택이나 행동은 {theme}이라는 주제에서 어떻게 생각해 볼 수 있을까요?",
        "이 이야기가 우리 생활이나 교실 모습과 연결된다면 어떤 장면이 떠오르나요?",
        "우리 반에서 비슷한 마음을 가진 친구가 있다면 우리는 어떤 말을 해줄 수 있을까요?",
        f"이 책을 읽고 난 뒤 나의 생각을 한 문장으로 쓴다면 어떻게 쓸 수 있을까요?",
    ]
    intents = [
        "읽기 전 예측과 관심을 열기",
        "그림 근거로 생각 말하기",
        "이야기 구조 확인하기",
        "인물의 감정을 안전하게 추론하기",
        "행동 뒤의 마음과 맥락 탐색하기",
        "관점 전환으로 공감 확장하기",
        "정답 없는 가치 판단 토론 열기",
        "책과 삶을 선택적으로 연결하기",
        "공동체 실천 언어 만들기",
        "개별 성찰과 글쓰기 마무리하기",
    ]
    responses = [
        "제목이 궁금해요 / 무슨 일이 생길 것 같아요",
        "표정이 슬퍼 보여요 / 색이 어두워요 / 손이 움츠러들었어요",
        "주인공이 문제를 만났어요 / 친구와 일이 생겼어요",
        "속상했을 것 같아요 / 무서웠을 것 같아요 / 용기를 냈을 것 같아요",
        "도움을 받고 싶었을 것 같아요 / 혼자 해결하려 했을 것 같아요",
        "친구는 장난이라고 생각했을 수도 있어요 / 어른은 걱정했을 것 같아요",
        "고쳐야 하는 게 아니라 이해해야 해요 / 선택에는 책임이 필요해요",
        "우리 반에서도 말 걸기 어려운 때가 있어요 / 친구 평가가 신경 쓰일 때가 있어요",
        "괜찮다고 말해줘요 / 같이 하자고 해요 / 놀리지 않기로 약속해요",
        "나는 다름을 존중하겠습니다 / 나는 내 마음을 말해보겠습니다",
    ]
    followups = [
        "그렇게 생각하게 만든 표지의 단서는 무엇인가요?",
        "그림에서 보이는 것과 보이지 않는 마음은 어떻게 다를까요?",
        "그 사건 전과 후에 무엇이 달라졌나요?",
        "그 감정을 색깔이나 날씨로 표현하면 무엇일까요?",
        "인물이 다른 선택을 했다면 이야기는 어떻게 달라졌을까요?",
        "그 인물도 말하지 못한 마음이 있었을까요?",
        "우리 모두에게 좋은 선택이 되려면 무엇을 함께 생각해야 할까요?",
        "개인 경험을 말하지 않고도 인물에게 해줄 말로 표현할 수 있을까요?",
        "그 말을 교실 약속으로 바꾼다면 어떻게 쓸 수 있을까요?",
        "그 문장을 실천하기 위해 오늘 할 수 있는 작은 행동은 무엇인가요?",
    ]

    cards: list[dict[str, str]] = []
    for i, qtype in enumerate(QUESTION_TYPES):
        cards.append(
            {
                "번호": str(i + 1),
                "질문 유형": qtype,
                "질문": questions[i],
                "질문 의도": intents[i],
                "예상 학생 반응": responses[i],
                "후속 질문": followups[i],
                "정서 안전성 점검": "인물 중심으로 시작하고, 개인 경험 공유는 선택형으로 둡니다.",
            }
        )
    return cards


def _split_minutes(total: int) -> list[int]:
    total = max(20, int(total or 40))
    ratios = [0.12, 0.33, 0.20, 0.20, 0.15]
    minutes = [max(3, round(total * r)) for r in ratios]
    diff = total - sum(minutes)
    minutes[-1] += diff
    return minutes


def generate_lesson_plan(
    title: str,
    grade: str,
    subject: str,
    minutes: int,
    lesson_idea: str,
    questions_text: str,
) -> dict[str, Any]:
    if not is_mock_mode():
        response = generate_text(lesson_plan_prompt(title, grade, subject, minutes, lesson_idea, questions_text))
        parsed = _safe_json_loads(response)
        if isinstance(parsed, dict) and "steps" in parsed:
            return parsed

    m1, m2, m3, m4, m5 = _split_minutes(minutes)
    core_question = _first_question(questions_text) or "그림책 속 인물의 마음은 우리 삶과 어떻게 연결될까?"
    metadata = {
        "수업 제목": f"'{title}'로 여는 질문 중심 그림책 수업",
        "대상 학년": grade,
        "관련 교과": subject or "국어, 도덕, 창의적 체험활동",
        "수업 주제": lesson_idea or "그림책을 통해 인물의 마음을 읽고 나와 공동체의 실천으로 연결하기",
        "핵심 질문": core_question,
        "수업 목표": [
            "그림책 장면을 근거로 인물의 마음을 말할 수 있다.",
            "정답 없는 질문을 만들고 짝과 생각을 나눌 수 있다.",
            "책에서 얻은 생각을 나의 언어로 쓸 수 있다.",
        ],
        "준비물": ["그림책", "질문 카드", "활동지", "마음성장노트", "포스트잇"],
        "평가 관점": [
            "장면 근거를 들어 질문과 의견을 말하는가",
            "친구의 의견을 존중하며 토론하는가",
            "개인 경험을 강요하지 않고 안전하게 성찰하는가",
        ],
        "교사 유의점": "정답 찾기보다 생각의 이유를 묻고, 학생 질문을 칭찬하며 확장한다.",
        "정서 안전 유의점": "개인사 공개를 강요하지 않고 인물 중심 질문에서 선택형 삶 연결 질문으로 이동한다.",
    }
    steps = [
        {
            "단계": "도입",
            "시간": f"{m1}분",
            "교사 발문": f"'{title}'의 제목과 표지를 보면 어떤 마음이 떠오르나요?",
            "학생 활동": "표지와 제목을 보고 떠오르는 단어를 말하거나 포스트잇에 쓴다.",
            "예상 반응": "궁금해요, 외로워 보여요, 친구 이야기가 나올 것 같아요.",
            "판서 또는 활동지": "오늘의 핵심 질문 / 떠오르는 감정 단어",
            "교사 유의점": "학생 반응을 좋고 나쁨으로 평가하지 않고 근거를 묻는다.",
        },
        {
            "단계": "전개 1: 그림책 읽기와 멈춤 질문",
            "시간": f"{m2}분",
            "교사 발문": "이 장면에서 인물의 표정과 행동은 어떤 마음을 보여주나요?",
            "학생 활동": "낭독을 들으며 멈춤 질문에 짧게 답하고 장면 근거를 찾는다.",
            "예상 반응": "속상했을 것 같아요, 망설였을 것 같아요, 도와주고 싶어요.",
            "판서 또는 활동지": "장면 / 보이는 것 / 짐작한 마음 / 근거",
            "교사 유의점": "학생의 개인 경험보다 인물의 마음을 먼저 다룬다.",
        },
        {
            "단계": "전개 2: 질문 만들기",
            "시간": f"{m3}분",
            "교사 발문": "책 안에 바로 정답이 없는 질문을 만들어 볼까요?",
            "학생 활동": "개인 질문 1개를 쓰고 짝과 비교하여 토론하기 좋은 질문을 고른다.",
            "예상 반응": "왜 그랬을까? 내가 그 상황이라면? 우리 반에서는?",
            "판서 또는 활동지": "좋은 질문 조건: 정답 없음 / 삶 연결 / 토론 가능 / 안전함",
            "교사 유의점": "위험하거나 사생활 노출 가능성이 있는 질문은 인물·공동체 중심으로 바꾼다.",
        },
        {
            "단계": "전개 3: 짝 토론 또는 모둠 토론",
            "시간": f"{m4}분",
            "교사 발문": "내 생각의 이유를 말하고, 친구 생각에서 새롭게 알게 된 점을 찾아봅시다.",
            "학생 활동": "짝과 질문을 고르고 생각-이유-장면 근거 순서로 말한다.",
            "예상 반응": "나는 다르게 생각해요, 그 장면을 보면 이해돼요, 이런 방법도 있어요.",
            "판서 또는 활동지": "내 생각 / 친구 생각 / 새롭게 알게 된 점",
            "교사 유의점": "논쟁보다 경청과 이유 말하기를 강조한다.",
        },
        {
            "단계": "정리: 나만의 생각 쓰기",
            "시간": f"{m5}분",
            "교사 발문": "오늘의 질문에 대한 나만의 생각을 한 문단으로 써 봅시다.",
            "학생 활동": "마음성장노트 또는 활동지에 선택형 성찰 문장을 쓴다.",
            "예상 반응": "인물에게 해주고 싶은 말, 우리 반 실천, 나에게 해주고 싶은 말.",
            "판서 또는 활동지": "나는 ○○○다 / 인물에게 해주고 싶은 말 / 우리 반에서 할 수 있는 일",
            "교사 유의점": "공유는 자원자 중심으로 운영하고 민감한 내용은 교사가 개별적으로 살핀다.",
        },
    ]
    return {"metadata": metadata, "steps": steps}


def _first_question(text: str) -> str:
    for line in (text or "").splitlines():
        stripped = line.strip(" -*•\t")
        if "?" in stripped:
            return stripped
    return ""


def generate_worksheets(title: str, question_cards: list[dict[str, str]] | None = None) -> str:
    q = question_cards or generate_question_cards(title, "", "", "")
    life_q = next((x["질문"] for x in q if "삶 연결" in x.get("질문 유형", "")), "이 이야기가 우리 생활과 연결되는 부분은 무엇인가요?")
    community_q = next((x["질문"] for x in q if "공동체" in x.get("질문 유형", "")), "우리 반에서 실천할 수 있는 일은 무엇인가요?")
    writing_q = next((x["질문"] for x in q if "생각 쓰기" in x.get("질문 유형", "")), "오늘 읽은 뒤 나의 생각을 써 봅시다.")
    return f"""# '{title}' 학생 활동지

## 1. 장면을 보고 생각하기
- 기억에 남는 장면:
- 그 장면에서 보이는 것:
- 인물의 마음을 짐작한 근거:

## 2. 나의 질문 만들기
- 책 안에 바로 정답이 있는 질문:
- 정답은 없지만 토론하고 싶은 질문:

## 3. 짝 토론지
- 함께 고른 질문: {life_q}
- 내 생각:
- 친구 생각:
- 친구의 말을 듣고 새롭게 알게 된 점:

## 4. 마음성장노트형 성찰 질문지
- 인물에게 해주고 싶은 말:
- 내가 선택해서 연결해 보고 싶은 질문: {writing_q}
- 나에게 해주고 싶은 말:

## 5. 우리 반 실천
- 공동체 질문: {community_q}
- 오늘부터 할 수 있는 작은 실천 한 가지:
""".strip()
