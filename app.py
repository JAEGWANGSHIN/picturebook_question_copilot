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
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Nanum+Gothic:wght@400;700;800&display=swap');

/* ── 전역 배경 & 폰트 ── */
html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #fff9f0 0%, #fff0fb 40%, #f0f8ff 100%) !important;
    font-family: 'Nanum Gothic', sans-serif !important;
}

/* 배경 도트 패턴 */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image: radial-gradient(circle, #ffb3d966 1.5px, transparent 1.5px);
    background-size: 32px 32px;
    pointer-events: none;
    z-index: 0;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ff6b9d 0%, #c44ddb 50%, #7c4dff 100%) !important;
    border-right: none !important;
}
[data-testid="stSidebar"] * {
    color: #fff !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li {
    color: rgba(255,255,255,0.92) !important;
    font-size: 0.88rem;
}
[data-testid="stSidebar"] h1 {
    font-family: 'Jua', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 900 !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.3), 0 0 20px rgba(255,255,255,0.2) !important;
    letter-spacing: -0.3px;
}
[data-testid="stSidebar"] h3 {
    font-family: 'Jua', sans-serif !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    border-bottom: 2px solid rgba(255,255,255,0.4);
    padding-bottom: 6px;
    margin-top: 20px !important;
    text-shadow: 0 1px 4px rgba(0,0,0,0.2);
}
[data-testid="stSidebar"] [data-testid="stInfo"] {
    background: rgba(255,255,255,0.15) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 12px !important;
    color: #fff !important;
}

/* ── 탭 스타일 ── */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(255,255,255,0.7);
    border-radius: 16px;
    padding: 3px 4px;
    gap: 2px;
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 12px rgba(255,107,157,0.15);
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    scrollbar-width: none;
}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {
    display: none;
}
[data-testid="stTabs"] [role="tab"] {
    border-radius: 12px !important;
    font-family: 'Nanum Gothic', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    padding: 5px 9px !important;
    transition: all 0.2s !important;
    color: #666 !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #ff6b9d, #c44ddb) !important;
    color: #fff !important;
    box-shadow: 0 3px 10px rgba(255,107,157,0.4) !important;
}

/* ── 페이지 타이틀 (메인 영역만) ── */
[data-testid="stMainBlockContainer"] h1 {
    font-family: 'Jua', sans-serif !important;
    background: linear-gradient(135deg, #ff6b9d, #7c4dff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.2rem !important;
}
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 {
    font-family: 'Jua', sans-serif !important;
    color: #5c3d8f !important;
}

/* ── 기본 카드 ── */
.card {
    border: none;
    border-radius: 20px;
    padding: 22px 24px;
    margin-bottom: 14px;
    background: #fff;
    box-shadow: 0 4px 20px rgba(196,77,219,0.10), 0 1px 4px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}
.card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #ff6b9d, #c44ddb, #7c4dff);
}
.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(196,77,219,0.18);
}
.card h4 {
    margin-top: 0;
    font-family: 'Jua', sans-serif;
    font-size: 1.05rem;
    color: #5c3d8f;
}
.card p { color: #444; line-height: 1.7; }
.small { color: #888; font-size: 0.88rem; }

/* 홈 특화 카드 3종 */
.card-pink::before  { background: linear-gradient(90deg, #ff6b9d, #ffb3d9); }
.card-purple::before { background: linear-gradient(90deg, #c44ddb, #7c4dff); }
.card-blue::before  { background: linear-gradient(90deg, #4db8ff, #7c4dff); }

/* ── 히어로 배너 ── */
.hero-banner {
    background: linear-gradient(135deg, #ff6b9d 0%, #c44ddb 50%, #7c4dff 100%);
    border-radius: 24px;
    padding: 36px 40px;
    margin-bottom: 28px;
    color: #fff;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(196,77,219,0.3);
}
.hero-banner::after {
    content: "📚";
    position: absolute;
    right: 40px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.25;
}
.hero-banner h1 {
    font-family: 'Jua', sans-serif !important;
    font-size: 2.2rem !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
    margin: 0 0 8px !important;
    text-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.hero-banner p {
    color: rgba(255,255,255,0.9);
    font-size: 1rem;
    line-height: 1.6;
    max-width: 680px;
    margin: 0;
}

/* ── 흐름 배지 ── */
.flow-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
    margin: 12px 0 20px;
}
.flow-badge {
    background: linear-gradient(135deg, #ff6b9d22, #7c4dff22);
    border: 1.5px solid #c44ddb44;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.82rem;
    font-weight: 700;
    color: #7c4dff;
}
.flow-arrow {
    color: #c44ddb;
    font-weight: 900;
    font-size: 1rem;
}

/* ── 섹션 헤더 ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    background: linear-gradient(135deg, #fff0fb, #f0f0ff);
    border-radius: 14px;
    padding: 12px 18px;
    margin: 20px 0 14px;
    border-left: 5px solid #c44ddb;
}
.section-header span {
    font-family: 'Jua', sans-serif;
    font-size: 1.1rem;
    color: #5c3d8f;
}

/* ── 경고 박스 ── */
.warning-box {
    border: none;
    border-left: 5px solid #ffb347;
    padding: 14px 18px;
    background: linear-gradient(135deg, #fffaf0, #fff5e0);
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(255,179,71,0.15);
}
.warning-box ul { margin: 6px 0 0; padding-left: 18px; }
.warning-box li { color: #7a5c00; font-size: 0.9rem; margin-bottom: 4px; }

/* ── 버튼 ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #ff6b9d, #c44ddb) !important;
    border: none !important;
    border-radius: 14px !important;
    font-family: 'Jua', sans-serif !important;
    font-size: 1rem !important;
    padding: 10px 28px !important;
    color: #fff !important;
    box-shadow: 0 4px 15px rgba(255,107,157,0.4) !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(196,77,219,0.5) !important;
}

/* ── 다운로드 버튼 ── */
[data-testid="stDownloadButton"] > button {
    border-radius: 12px !important;
    font-family: 'Nanum Gothic', sans-serif !important;
    font-weight: 700 !important;
}

/* ── 입력 필드 ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border-radius: 12px !important;
    border: 1.5px solid #e0c8f0 !important;
    background: #fdf8ff !important;
    font-family: 'Nanum Gothic', sans-serif !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #c44ddb !important;
    box-shadow: 0 0 0 3px rgba(196,77,219,0.12) !important;
}
[data-testid="stSelectbox"] > div > div {
    border-radius: 12px !important;
    border: 1.5px solid #e0c8f0 !important;
    background: #fdf8ff !important;
}

/* ── 성공/정보 알림 ── */
[data-testid="stSuccess"] {
    background: linear-gradient(135deg, #f0fff4, #e8ffee) !important;
    border-left: 5px solid #52c41a !important;
    border-radius: 12px !important;
}
[data-testid="stInfo"] {
    background: linear-gradient(135deg, #f0f8ff, #e8f4ff) !important;
    border-left: 5px solid #4db8ff !important;
    border-radius: 12px !important;
}

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
}

/* ── Streamlit 상단 툴바 숨김 & 레이아웃 보정 ── */
[data-testid="stHeader"] {
    display: none !important;
}
#MainMenu { display: none !important; }
footer { display: none !important; }

/* 메인 컨테이너 여백 */
[data-testid="stMainBlockContainer"] {
    padding-top: 16px !important;
    padding-bottom: 32px !important;
}

/* 탭 바 위 잘림 방지 */
[data-testid="stTabs"] {
    margin-top: 0 !important;
}
[data-testid="stTabs"] > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
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
    st.markdown("# 📚 질문수업 코파일럿")
    st.caption("교사의 그림책 수업 설계를 돕는 Streamlit MVP")
    st.markdown("### 🔒 안전 안내")
    st.info(SAFETY_NOTICE)
    st.markdown("### 🗂️ 현재 저장된 결과물")
    if st.session_state.results:
        icons = {
            "recommendations": "📖",
            "scan_material": "🔍",
            "question_cards": "❓",
            "lesson_plan": "📋",
            "worksheets": "📝",
            "student_question_analysis": "🙋",
        }
        for k, v in st.session_state.results.items():
            icon = icons.get(k, "✅")
            st.markdown(f"{icon} {v['label']}")
    else:
        st.markdown("_아직 생성된 결과물이 없습니다._")


tabs = st.tabs(
    [
        "🏠 홈",
        "📖 그림책 추천",
        "🔍 SCAN 자료화",
        "❓ 질문 10개",
        "📋 지도안 만들기",
        "🙋 학생 질문 수업화",
        "💾 내보내기",
    ]
)

with tabs[0]:
    st.markdown(
        """
<div class="hero-banner">
  <h1>📚 그림책 질문수업 코파일럿</h1>
  <p>교사가 수업 상황 또는 vFlat SCAN OCR 텍스트를 입력하면<br>
  그림책 추천 · 질문 10개 · 질문 중심 지도안 · 학생 활동지 · 마음성장노트를 바로 만들어 드려요!</p>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="card card-pink">
  <h4>🌱 그림책을 수업 매개로</h4>
  <p>그림책을 독서 자료에만 머물게 하지 않고 자존감, 다름, 친구 관계, 가족, 환경, 인권 등 <b>삶의 주제</b>로 연결합니다.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="card card-purple">
  <h4>💬 질문 중심 하브루타</h4>
  <p>책 낭독 → 감상 나누기 → 질문 만들기 → 짝 토론하기 → 나만의 생각 쓰기 흐름을 기본으로 삼습니다.</p>
</div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
<div class="card card-blue">
  <h4>💛 마음성장노트</h4>
  <p>학생을 진단하지 않고, 인물의 마음에서 출발해 나와 공동체의 실천으로 <b>안전하게 확장</b>합니다.</p>
</div>""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="section-header"><span>🗺️ 사용 흐름</span></div>
<div class="flow-row">
  <span class="flow-badge">📝 상황 입력</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">📖 그림책 추천</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">🔍 OCR 자료화</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">❓ 질문 10개</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">📋 지도안</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">🙋 학생 질문 수업화</span>
  <span class="flow-arrow">→</span>
  <span class="flow-badge">💾 내보내기</span>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-header"><span>📚 내장 그림책 DB 미리보기</span></div>', unsafe_allow_html=True)

    catalog_all = cached_catalog()
    grade_options = ["전체 학년"] + [
        "1-2학년", "3-4학년", "5-6학년"
    ]
    filter_col1, filter_col2 = st.columns([2, 3])
    with filter_col1:
        selected_grade_filter = st.selectbox(
            "학년으로 필터",
            grade_options,
            key="db_grade_filter",
        )
    with filter_col2:
        search_keyword = st.text_input(
            "주제·키워드 검색",
            placeholder="예: 자존감, 두려움, 친구 관계 …",
            key="db_keyword_search",
        )

    def grade_matches(band: str, sel: str) -> bool:
        if sel == "전체 학년":
            return True
        nums = [int(x) for x in __import__("re").findall(r"[1-6]", band)]
        if not nums:
            return True
        low, high = min(nums), max(nums)
        if sel == "1-2학년":
            return low <= 2
        if sel == "3-4학년":
            return low <= 4 and high >= 3
        if sel == "5-6학년":
            return high >= 5
        return True

    def keyword_matches(book: dict, kw: str) -> bool:
        if not kw.strip():
            return True
        kw_lower = kw.strip().lower()
        searchable = (
            " ".join(book.get("main_themes", []))
            + " ".join(book.get("emotion_keywords", []))
            + book.get("story_summary", "")
            + book.get("title", "")
        ).lower()
        return kw_lower in searchable

    filtered = [
        b for b in catalog_all
        if grade_matches(b.get("recommended_grade_band", ""), selected_grade_filter)
        and keyword_matches(b, search_keyword)
    ]

    st.markdown(
        f"<p style='color:#888;font-size:0.88rem;margin:4px 0 12px;'>"
        f"총 <b style='color:#c44ddb'>{len(catalog_all)}권</b> 중 "
        f"<b style='color:#ff6b9d'>{len(filtered)}권</b> 표시 중</p>",
        unsafe_allow_html=True,
    )

    GRADE_COLOR = {
        "1": "#4db8ff", "2": "#4db8ff",
        "3": "#ff9f43", "4": "#ff9f43",
        "5": "#c44ddb", "6": "#c44ddb",
    }

    for book in filtered:
        band = book.get("recommended_grade_band", "")
        first_grade = __import__("re").search(r"[1-6]", band)
        badge_color = GRADE_COLOR.get(first_grade.group() if first_grade else "1", "#888")
        themes = " · ".join(book.get("main_themes", [])[:4])
        emotions = " · ".join(book.get("emotion_keywords", [])[:4])
        hooks = book.get("question_hooks", [])
        activities = book.get("lesson_activity_ideas", [])
        cautions = book.get("cautions", [])

        label = f"📗 {book.get('title', '')}  |  {band}  |  {themes}"
        with st.expander(label):
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown(
                    f"<span style='background:{badge_color};color:#fff;"
                    f"border-radius:8px;padding:2px 10px;font-size:0.8rem;"
                    f"font-weight:700;'>{band}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**✍️ 저자** {book.get('author','확인 필요')} / **출판사** {book.get('publisher','확인 필요')}")
                st.markdown(f"**📌 핵심 주제** {themes}")
                st.markdown(f"**💛 정서 키워드** {emotions}")
                st.markdown(f"**📖 줄거리** {book.get('story_summary','')}")
                if book.get("curriculum_links"):
                    st.markdown("**🔗 교과 연계** " + " / ".join(book["curriculum_links"]))
            with c_right:
                if hooks:
                    st.markdown("**❓ 핵심 질문**")
                    for q in hooks:
                        st.markdown(f"- {q}")
                if activities:
                    st.markdown("**🎨 수업 활동 아이디어**")
                    for a in activities:
                        st.markdown(f"- {a}")
                if cautions:
                    st.markdown("**⚠️ 유의점**")
                    for cau in cautions:
                        st.markdown(
                            f"<div class='warning-box' style='padding:8px 12px;margin:4px 0;'>"
                            f"{cau}</div>",
                            unsafe_allow_html=True,
                        )

    methodology = load_methodology()
    with st.expander("📖 수업 원리 요약 보기"):
        st.json(methodology)

with tabs[1]:
    st.markdown('<div class="section-header"><span>📖 상황 기반 그림책 추천</span></div>', unsafe_allow_html=True)
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

    if st.button("📖 그림책 추천하기", type="primary", key="recommend_button"):
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
    st.markdown('<div class="section-header"><span>🔍 vFlat SCAN 자료화</span></div>', unsafe_allow_html=True)
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

    if st.button("🔍 자료화하기", type="primary", key="scan_material_button"):
        file_text = extract_text_from_upload(uploaded)
        combined_text = "\n".join([file_text, pasted_ocr]).strip()
        material = generate_scan_material(scan_title, combined_text)
        save_result("scan_material", "vFlat SCAN 자료화 결과", scan_title or "스캔 자료", material)
        st.success("수업 자료화 결과를 생성했습니다.")
        show_json_like(material)

with tabs[3]:
    st.markdown('<div class="section-header"><span>❓ 그림책 흐름에 따른 질문 10개 만들기</span></div>', unsafe_allow_html=True)
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

    if st.button("❓ 질문 10개 생성", type="primary", key="question_generate_button"):
        cards = generate_question_cards(q_title, q_summary, q_grade, q_topic)
        save_result("question_cards", "질문 10개 카드", q_title, cards)
        st.success("질문 10개를 생성했습니다.")
        st.dataframe(pd.DataFrame(cards), use_container_width=True)
        st.markdown("### 질문카드 보기")
        question_cards_view(cards)

with tabs[4]:
    st.markdown('<div class="section-header"><span>📋 질문 중심수업 지도안 만들기</span></div>', unsafe_allow_html=True)
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

    if st.button("📋 지도안 생성", type="primary", key="lesson_generate_button"):
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
    st.markdown('<div class="section-header"><span>🙋 학생 질문 수업화</span></div>', unsafe_allow_html=True)
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

    if st.button("🙋 질문 분류 및 수업화", type="primary", key="student_question_analyze_button"):
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
    st.markdown('<div class="section-header"><span>💾 내보내기</span></div>', unsafe_allow_html=True)

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
            "📄 Markdown 다운로드",
            data=md_text.encode("utf-8"),
            file_name=md_filename,
            mime="text/markdown",
            key="export_markdown_button",
        )

        try:
            docx_bytes = markdown_to_docx_bytes(md_text)
            st.download_button(
                "📝 DOCX 다운로드",
                data=docx_bytes,
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="export_docx_button",
            )
        except Exception as exc:
            st.warning(f"DOCX 생성 중 오류가 발생했습니다. Markdown 다운로드를 사용해 주세요. 오류: {exc}")
