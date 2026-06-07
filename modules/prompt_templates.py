"""Prompt templates for picturebook question-centered lessons."""

from __future__ import annotations

import json
from typing import Any


SAFETY_BLOCK = """
[정서 안전 원칙]
- 학생의 글이나 질문을 보고 심리 진단을 하지 않는다.
- “이 학생은 불안장애가 있다”, “자존감이 낮다”처럼 단정하지 않는다.
- “걱정, 외로움, 망설임 같은 감정 표현이 보입니다”처럼 관찰 중심으로 말한다.
- 개인사, 가족사, 트라우마를 직접 묻는 질문을 피한다.
- 학생에게 사적인 경험을 강제로 공개하게 하지 않는다.
- 개인 경험 질문은 선택형 또는 간접형으로 제시한다.
- 인물 중심 질문 → 나와 연결 질문 → 공동체 실천 질문 순서로 안전하게 확장한다.

[저작권 안전 원칙]
- 업로드된 그림책 원문을 길게 재출력하지 않는다.
- 결과물은 원문 복제가 아니라 요약, 질문, 지도안, 활동지 형태로 변환한다.
- 확실하지 않은 책 정보는 지어내지 말고 “확인 필요”라고 쓴다.
""".strip()


def _json_dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def recommendation_prompt(
    grade: str,
    subject: str,
    achievement: str,
    topic: str,
    class_context: str,
    lesson_minutes: int,
    activity_style: str,
    candidates: list[dict[str, Any]],
) -> str:
    return f"""
TASK:RECOMMENDATION
너는 초등 그림책 질문 중심수업 코파일럿이다. 아래 교사 입력과 점수 기반 1차 후보를 바탕으로 추천 이유를 보완하라.

{SAFETY_BLOCK}

[교사 입력]
- 학년: {grade}
- 교과: {subject}
- 성취기준: {achievement}
- 수업 주제: {topic}
- 학급 상황: {class_context}
- 수업 시간: {lesson_minutes}분
- 원하는 활동 방식: {activity_style}

[점수 기반 1차 후보]
{_json_dump(candidates)}

[출력 형식]
JSON 배열로만 출력한다. 각 원소는 다음 필드를 포함한다.
그림책 제목, 추천 이유, 적합 학년, 핵심 주제, 정서 키워드, 질문 중심수업 가능성, 핵심 질문 1개, 수업 활동 아이디어, 유의점, 추천 근거
""".strip()


def scan_material_prompt(title: str, ocr_text: str) -> str:
    return f"""
TASK:SCAN_MATERIAL
교사가 vFlat SCAN으로 추출한 OCR 텍스트를 바탕으로 그림책 수업 설계 자료를 만들어라.

{SAFETY_BLOCK}

[그림책 제목]
{title or "확인 필요"}

[OCR 텍스트]
{ocr_text}

[출력 형식]
아래 필드를 가진 JSON 객체로만 출력한다.
그림책 내용 요약, 주요 인물, 핵심 사건, 핵심 갈등, 인물의 감정 흐름, 수업 주제 후보, 질문을 만들기 좋은 장면, 수업 활동 아이디어, 정서적 유의점
""".strip()


def question_cards_prompt(title: str, summary: str, grade: str, topic: str) -> str:
    return f"""
TASK:QUESTION_CARDS
그림책 흐름에 따른 질문 10개를 만들어라. 질문은 초등학생에게 적합하고 정서적으로 안전해야 한다.

{SAFETY_BLOCK}

[그림책 제목]
{title}

[그림책 요약 또는 수업 구상]
{summary}

[학년]
{grade}

[수업 주제]
{topic}

[질문 흐름]
1. 표지 또는 제목 질문
2. 그림 관찰 질문
3. 이야기 이해 질문
4. 인물 감정 질문
5. 행동 이유 질문
6. 관점 전환 질문
7. 가치 판단 질문
8. 삶 연결 질문
9. 공동체 실천 질문
10. 생각 쓰기 질문

[출력 형식]
JSON 배열로만 출력한다. 각 원소는 질문 유형, 질문, 질문 의도, 예상 학생 반응, 후속 질문, 정서 안전성 점검 필드를 포함한다.
""".strip()


def lesson_plan_prompt(
    title: str,
    grade: str,
    subject: str,
    minutes: int,
    lesson_idea: str,
    questions_text: str,
) -> str:
    return f"""
TASK:LESSON_PLAN
질문 10개 또는 교사의 수업 구상을 바탕으로 {minutes}분 질문 중심수업 지도안을 작성하라.

{SAFETY_BLOCK}

[그림책 제목]
{title}

[학년]
{grade}

[교과]
{subject}

[수업 구상]
{lesson_idea}

[질문 목록]
{questions_text}

[지도안 구조]
수업 제목, 대상 학년, 관련 교과, 수업 주제, 핵심 질문, 수업 목표, 준비물, 도입, 전개 1: 그림책 읽기와 멈춤 질문, 전개 2: 질문 만들기, 전개 3: 짝 토론 또는 모둠 토론, 정리: 나만의 생각 쓰기, 평가 관점, 교사 유의점, 정서 안전 유의점

[출력 형식]
JSON 객체로만 출력한다. metadata와 steps를 포함한다. steps는 시간, 단계, 교사 발문, 학생 활동, 예상 반응, 판서 또는 활동지, 교사 유의점 필드를 가진 배열이다.
""".strip()


def student_question_prompt(question_text: str) -> str:
    return f"""
TASK:STUDENT_QUESTION_ANALYSIS
학생 질문 목록을 유형별로 분류하고 수업화하라.

{SAFETY_BLOCK}

[학생 질문 목록]
{question_text}

[분류 유형]
사실 확인 질문, 해석 질문, 감정 질문, 관점 전환 질문, 가치 판단 질문, 삶 연결 질문, 공동체 실천 질문, 위험하거나 사생활 노출 가능성이 있는 질문

[출력 형식]
JSON 객체로만 출력한다. classified, recommended, safe_rewrites 필드를 포함한다.
""".strip()
