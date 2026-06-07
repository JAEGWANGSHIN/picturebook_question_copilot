```python
from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from modules.catalog import catalog_to_dataframe_records, find_book, list_titles, load_catalog, load_methodology
from modules.export_utils import dated_filename, markdown_to_docx_bytes, result_to_markdown
from modules.lesson_generator import generate_lesson_plan, generate_question_cards, generate_scan_material, generate_worksheets
from modules.pdf_utils import extract_text_from_upload
from modules.question_analyzer import analyze_student_questions
from modules.recommendation import recommend_picturebooks

st.set_page_config(
    page_title="그림책 질문수업 코파일럿",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

SAFETY_NOTICE = """
- 개인정보: 학생 이름, 학교명, 반, 전화번호, 가족 정보 등은 입력하지 마세요.
- 저작권: 스캔 원문을 장문으로 복제하지 않고, 요약·질문·활동으로 변환합니다.
- 정서 안전: 학생의 마음을 진단하지 않고 관찰 가능한 표현과 안전한 질문으로 다룹니다.
""".strip()

CARD_CSS = """
<style>
.card {
    border: 1px solid #e6e6e6;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 12px;
    background: #ffffff;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.card h4 { margin-top: 0; }
.small { color: #666; font-size: 0.92rem; }
.warning-box {
    border-left: 5px solid #d9a441;
    padding: 12px 16px;
    background: #fffaf0;
    border-radius: 8px;
}
</style>
"""

st.markdown(CARD_CSS, unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = {}
if "last_title" not in st.session_state:
    st.session_state.last_title = "그림책 질문수업"


@st.cache_data(show_spinner=False)
def cached_catalog() -> list[dict[str, Any]]:
    return load_catalog()


@st.cache_data(show_spinner=False)
def cached_titles() -> list[str]:
    return list_titles()


def save_result(key: str, label: str, title: str, result: Any) -> None:
    st.session_state.results[key] = {
        "label": label,
        "title": title or "그림책 질문수업",
        "result": result,
    }
    st.session_state.last_title = title or "그림책 질문수업"


def show_json_like(result: Any) -> None:
    if isinstance(result, dict):
        for k, v in result.items():
            st.subheader(k)
            if isinstance(v, list):
                if v and all(isinstance(x, dict) for x in v):
                    st.dataframe(pd.DataFrame(v), use_container_width=True)
                else:
                    for item in v:
                        st.markdown(f"- {item}")
            elif isinstance(v, dict):
                st.json(v)
            else:
                st.write(v)
    elif isinstance(result, list):
        st.dataframe(pd.DataFrame(result), use_container_width=True)
    else:
        st.markdown(str(result))


def question_cards_view(cards: list[dict[str, str]]) -> None:
    for card in cards:
        st.markdown(
            f"""
<div class="card">
<h4>{card.get('번호', '')}. {card.get('질문 유형', '')}</h4>
<p><b>질문</b> | {card.get('질문', '')}</p>
<p class="small"><b>의도</b> | {card.get('질문 의도', '')}</p>
<p class="small"><b>예상 반응</b> | {card.get('예상 학생 반응', '')}</p>
<p class="small"><b>후속 질문</b> | {card.get('후속 질문', '')}</p>
<p class="small"><b>정서 안전성</b> | {card.get('정서 안전성 점검', '')}</p>
</div>
""",
            unsafe_allow_html=True,
        )


with st.sidebar:
    st.title("📚 질문수업 코파일럿")
    st.caption("교사의 그림책 수업 설계를 돕는 Streamlit MVP")
    st.markdown("### 안전 안내")
    st.info(SAFETY_NOTICE)
    st.markdown("### 현재 저장된 결과물")
    if st.session_state.results:
        for v in st.session_state.results.values():
            st.write("-", v["label"])
    else:
        st.write("아직 생성된 결과물이 없습니다.")


tabs = st.tabs(
    [
        "1. 홈",
        "2. 상황 기반 그림책 추천",
        "3. vFlat SCAN 자료화",
        "4. 질문 10개 만들기",
        "5. 질문 중심 지도안 만들기",
        "6. 학생 질문 수업화",
        "7. 내보내기",
    ]
)

with tabs[0]:
    st.title("그림책 질문수업 코파일럿")
    st.markdown(
        "교사가 수업 상황 또는 vFlat SCAN OCR 텍스트를 입력하면 그림책 추천, 질문 10개, 질문 중심 지도안, "
        "학생 활동지와 마음성장노트형 성찰 질문지를 만드는 웹앱 MVP입니다."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="card"><h4>① 그림책을 수업 매개로</h4>
<p>그림책을 독서 자료에만 머물게 하지 않고 자존감, 다름, 친구 관계, 가족, 환경, 인권 등 삶의 주제로 연결합니다.</p></div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="card"><h4>② 질문 중심 하브루타</h4>
<p>책 낭독 → 감상 나누기 → 질문 만들기 → 짝 토론하기 → 나만의 생각 쓰기 흐름을 기본으로 삼습니다.</p></div>
""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="card"><h4>③ 마음성장노트</h4>
<p>학생을 진단하지 않고, 인물의 마음에서 출발해 나와 공동체의 실천으로 안전하게 확장합니다.</p></div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("### 사용 흐름")
    st.write("상황 입력 → 그림책 추천 → OCR 자료화 → 질문 10개 → 지도안 → 학생 질문 수업화 → Markdown/DOCX 내보내기")

    st.markdown("### 내장 그림책 DB 미리보기")
    st.dataframe(pd.DataFrame(catalog_to_dataframe_records()), use_container_width=True)

    methodology = load_methodology()
    with st.expander("수업 원리 요약 보기"):
        st.json(methodology)

with tabs[1]:
    st.header("상황 기반 그림책 추천")
    st.markdown("교사의 수업 상황을 입력하면 내부 DB를 먼저 점수화하고, API가 있으면 추천 설명을 보완합니다.")

    col1, col2 = st.columns(2)
    with col1:
        grade = st.selectbox(
            "학년 선택",
            ["초등학교 1학년", "초등학교 2학년", "초등학교 3학년", "초등학교 4학년", "초등학교 5학년", "초등학교 6학년"],
            index=2,
            key="recommend_grade",
        )
        subject = st.text_input("교과 입력", value="국어, 도덕, 창의적 체험활동", key="recommend_subject")
        achievement = st.text_area(
            "성취기준 입력",
            value="인물의 마음을 짐작하고 자신의 생각을 친구와 나눈다.",
            key="recommend_achievement",
        )
    with col2:
        topic = st.text_input("수업 주제 입력", value="다름을 존중하기", key="recommend_topic")
        class_context = st.text_area(
            "학급 상황 입력",
            value="친구의 외모나 말투를 놀리는 일이 있다.",
            key="recommend_class_context",
        )
        lesson_minutes = st.slider("수업 시간 선택", 20, 80, 40, 5, key="recommend_lesson_minutes")
        activity_style = st.multiselect(
            "원하는 활동 방식 선택",
            ["짝 토론", "모둠 토론", "생각 쓰기", "마음성장노트", "역할극", "활동지", "카드 만들기"],
            default=["짝 토론", "생각 쓰기"],
            key="recommend_activity_style",
        )

    if st.button("그림책 추천하기", type="primary", key="recommend_button"):
        results = recommend_picturebooks(
            cached_catalog(),
            grade=grade,
            subject=subject,
            achievement=achievement,
            topic=topic,
            class_context=class_context,
            lesson_minutes=lesson_minutes,
            activity_style=", ".join(activity_style),
            top_n=5,
        )
        save_result("recommendations", "그림책 추천표", topic, results)
        st.success("추천 결과를 생성했습니다.")
        st.dataframe(pd.DataFrame(results).drop(columns=["점수 세부", "LLM 보완 메모"], errors="ignore"), use_container_width=True)

        with st.expander("점수 세부 보기"):
            for r in results:
                st.write(r["그림책 제목"], r["점수 세부"])

with tabs[2]:
    st.header("vFlat SCAN 자료화")
    st.markdown("PDF/TXT는 텍스트를 추출하고, 이미지 파일은 vFlat OCR 텍스트 붙여넣기를 기본으로 사용합니다.")
    st.markdown(f"<div class='warning-box'>{SAFETY_NOTICE}</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "PDF/JPG/PNG/TXT 업로드",
        type=["pdf", "jpg", "jpeg", "png", "txt", "md"],
        key="scan_file_uploader",
    )
    scan_title = st.text_input("그림책 제목 입력", value="", key="scan_title_input")
    pasted_ocr = st.text_area(
        "OCR 텍스트 붙여넣기",
        height=220,
        placeholder="vFlat SCAN에서 추출한 OCR 텍스트를 여기에 붙여넣으세요.",
        key="scan_ocr_text",
    )

    if st.button("자료화하기", type="primary", key="scan_material_button"):
        file_text = extract_text_from_upload(uploaded)
        combined_text = "\n".join([file_text, pasted_ocr]).strip()
        material = generate_scan_material(scan_title, combined_text)
        save_result("scan_material", "vFlat SCAN 자료화 결과", scan_title or "스캔 자료", material)
        st.success("수업 자료화 결과를 생성했습니다.")
        show_json_like(material)

with tabs[3]:
    st.header("그림책 흐름에 따른 질문 10개 만들기")
    titles = ["직접 입력"] + cached_titles()
    selected = st.selectbox("그림책 선택 또는 직접 입력", titles, key="question_book_selector")

    if selected == "직접 입력":
        q_title = st.text_input("그림책 제목", value="내 귀는 짝짝이", key="question_book_title_input")
        default_summary = "다름을 이유로 놀림받던 인물이 자신의 모습을 받아들이고 당당해지는 이야기"
    else:
        book = find_book(selected)
        q_title = selected
        default_summary = book.get("story_summary", "") if book else ""
        st.info(f"내부 DB 요약: {default_summary}")

    q_summary = st.text_area(
        "그림책 요약 또는 교사의 수업 구상",
        value=default_summary,
        height=140,
        key="question_summary",
    )
    q_grade = st.selectbox(
        "학년 선택",
        ["초등학교 1학년", "초등학교 2학년", "초등학교 3학년", "초등학교 4학년", "초등학교 5학년", "초등학교 6학년"],
        index=2,
        key="question_grade",
    )
    q_topic = st.text_input("수업 주제", value="다름과 자기수용", key="question_topic")

    if st.button("질문 10개 생성", type="primary", key="question_generate_button"):
        cards = generate_question_cards(q_title, q_summary, q_grade, q_topic)
        save_result("question_cards", "질문 10개 카드", q_title, cards)
        st.success("질문 10개를 생성했습니다.")
        st.dataframe(pd.DataFrame(cards), use_container_width=True)
        st.markdown("### 질문카드 보기")
        question_cards_view(cards)

with tabs[4]:
    st.header("질문 중심수업 지도안 만들기")
    col1, col2 = st.columns(2)

    with col1:
        lp_title = st.text_input(
            "그림책 제목",
            value=st.session_state.last_title if st.session_state.last_title != "그림책 질문수업" else "내 귀는 짝짝이",
            key="lesson_book_title_input",
        )
        lp_grade = st.text_input("학년", value="초등학교 3학년", key="lesson_grade_input")
        lp_subject = st.text_input("교과", value="국어, 도덕", key="lesson_subject_input")
        lp_minutes = st.slider("수업 시간", 20, 80, 40, 5, key="lesson_minutes_slider")

    with col2:
        lp_idea = st.text_area(
            "수업 구상",
            value="다르다는 것은 고쳐야 할 문제가 아니라 존중하고 이해할 수 있는 특징임을 질문과 토론으로 나눈다.",
            height=120,
            key="lesson_idea_text",
        )
        existing_questions = ""
        if "question_cards" in st.session_state.results:
            existing_questions = "\n".join(
                [x.get("질문", "") for x in st.session_state.results["question_cards"]["result"]]
            )
        lp_questions = st.text_area("질문 목록", value=existing_questions, height=180, key="lesson_questions_text")

    if st.button("지도안 생성", type="primary", key="lesson_generate_button"):
        plan = generate_lesson_plan(lp_title, lp_grade, lp_subject, lp_minutes, lp_idea, lp_questions)
        save_result("lesson_plan", "질문 중심수업 지도안", lp_title, plan)

        st.success("지도안을 생성했습니다.")
        st.subheader("수업 개요")
        for k, v in plan.get("metadata", {}).items():
            st.write(f"**{k}**: {', '.join(v) if isinstance(v, list) else v}")

        st.subheader("도입-전개-정리 지도안")
        st.dataframe(pd.DataFrame(plan.get("steps", [])), use_container_width=True)

        worksheet = generate_worksheets(lp_title)
        save_result("worksheets", "학생 활동지·짝 토론지·마음성장노트", lp_title, worksheet)

        with st.expander("함께 생성된 활동지 보기"):
            st.markdown(worksheet)

with tabs[5]:
    st.header("학생 질문 수업화")
    st.markdown("학생 이름과 개인 정보를 지운 뒤 붙여넣어 주세요. 예시는 학생 A, 학생 B처럼 익명화합니다.")

    sample_questions = """주인공은 왜 혼자 있었을까?
친구들이 놀리지 않았다면 어떻게 되었을까?
다르다는 것은 고쳐야 하는 걸까?
나도 친구에게 상처받은 적 있니?
우리 반에서 서로 다름을 인정하려면 무엇을 해야 할까?"""

    student_qs = st.text_area(
        "학생 질문 목록 붙여넣기",
        value=sample_questions,
        height=220,
        key="student_question_text",
    )

    if st.button("질문 분류 및 수업화", type="primary", key="student_question_analyze_button"):
        analysis = analyze_student_questions(student_qs)
        save_result("student_question_analysis", "학생 질문 수업화 결과", "학생 질문", analysis)

        st.success("학생 질문을 분류하고 수업화했습니다.")

        st.subheader("유형별 분류 결과")
        st.dataframe(pd.DataFrame(analysis["classified"]), use_container_width=True)

        st.subheader("수업화하기 좋은 질문 3개")
        st.dataframe(pd.DataFrame(analysis["recommended"]), use_container_width=True)

        st.subheader("토론·글쓰기·활동지 질문으로 변환")
        st.dataframe(pd.DataFrame(analysis["teaching_variants"]), use_container_width=True)

        if analysis["safe_rewrites"]:
            st.subheader("정서적으로 조심할 질문과 안전한 변환")
            st.dataframe(pd.DataFrame(analysis["safe_rewrites"]), use_container_width=True)

with tabs[6]:
    st.header("내보내기")

    if not st.session_state.results:
        st.info("먼저 다른 탭에서 결과물을 생성해 주세요.")
    else:
        labels = {key: val["label"] for key, val in st.session_state.results.items()}

        selected_key = st.selectbox(
            "현재 생성 결과 선택",
            list(labels.keys()),
            format_func=lambda k: labels[k],
            key="export_result_selector",
        )

        selected_result = st.session_state.results[selected_key]
        md_text = result_to_markdown(
            selected_result["title"],
            selected_result["label"],
            selected_result["result"],
        )

        st.text_area("복사하기용 텍스트", value=md_text, height=420, key="export_copy_text")

        md_filename = dated_filename(selected_result["title"], selected_key, "md")
        docx_filename = dated_filename(selected_result["title"], selected_key, "docx")

        st.download_button(
            "Markdown 다운로드",
            data=md_text.encode("utf-8"),
            file_name=md_filename,
            mime="text/markdown",
            key="export_markdown_button",
        )

        try:
            docx_bytes = markdown_to_docx_bytes(md_text)
            st.download_button(
                "DOCX 다운로드",
                data=docx_bytes,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="export_docx_button",
            )
        except Exception as exc:
            st.warning(f"DOCX 생성 중 오류가 발생했습니다. Markdown 다운로드를 사용해 주세요. 오류: {exc}")
```
