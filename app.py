import sys
import importlib.util
from pathlib import Path
from io import StringIO

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).parent
ENGINE_PATH = BASE_DIR / "MSA_FULL_MINITAB_ENGINE_STABLE_FINAL.py"
LOGO_PATH = BASE_DIR / "komq_logo.jpg"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

spec = importlib.util.spec_from_file_location("msa_engine", ENGINE_PATH)
msa = importlib.util.module_from_spec(spec)
sys.modules["msa_engine"] = msa
spec.loader.exec_module(msa)

st.set_page_config(
    page_title="MSA Gage R&R 분석 에이전트",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(0, 155, 255, 0.16), transparent 28%),
        linear-gradient(135deg, #06101f 0%, #07182c 48%, #020812 100%);
    color: #f8fafc;
}

.block-container {
    padding-top: 0.8rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06182d 0%, #03101f 100%);
    border-right: 1px solid rgba(94, 139, 190, 0.25);
}

[data-testid="stSidebar"] img {
    margin-top: 18px;
    margin-bottom: 28px;
}

.sidebar-menu {
    padding: 8px 4px;
}

.menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #e5edf8;
    font-size: 17px;
    font-weight: 700;
    padding: 14px 16px;
    border-radius: 14px;
    margin-bottom: 10px;
}

.menu-active {
    background: linear-gradient(135deg, #1e56d8, #11428f);
    box-shadow: 0 12px 30px rgba(25, 96, 220, 0.25);
}

.feature-box {
    border: 1px solid rgba(116, 159, 215, 0.35);
    border-radius: 18px;
    padding: 18px;
    margin-top: 36px;
    color: #e5edf8;
    background: rgba(9, 28, 52, 0.7);
    line-height: 1.8;
    font-size: 14px;
}

.sidebar-footer {
    color: #9fb0c6;
    font-size: 13px;
    margin-top: 48px;
    line-height: 1.7;
}

.top-badge {
    float: right;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #18d7ff;
    border: 1px solid rgba(65, 154, 255, 0.65);
    border-radius: 14px;
    padding: 12px 18px;
    font-weight: 800;
    background: rgba(5, 20, 42, 0.75);
    box-shadow: 0 0 24px rgba(0, 180, 255, 0.14);
}

.hero {
    margin-top: 58px;
    background:
        linear-gradient(135deg, rgba(17, 39, 70, 0.96), rgba(8, 25, 48, 0.92));
    border: 1px solid rgba(94, 139, 190, 0.48);
    border-radius: 24px;
    padding: 38px 44px;
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
}

.hero-title {
    color: white;
    font-size: 44px;
    font-weight: 900;
    letter-spacing: -1px;
    margin-bottom: 14px;
}

.hero-sub {
    color: #b8c7da;
    font-size: 18px;
    line-height: 1.75;
    font-weight: 500;
}

.hero-logo {
    display: flex;
    justify-content: flex-end;
    align-items: center;
}

.input-card {
    margin-top: 24px;
    background:
        linear-gradient(135deg, rgba(13, 38, 70, 0.92), rgba(6, 23, 43, 0.9));
    border: 1px solid rgba(94, 139, 190, 0.42);
    border-radius: 22px;
    padding: 26px 30px;
}

.input-card-title {
    color: white;
    font-size: 25px;
    font-weight: 900;
    margin-bottom: 8px;
}

.input-card-desc {
    color: #b8c7da;
    font-size: 16px;
}

.icon-circle {
    width: 64px;
    height: 64px;
    border-radius: 999px;
    background: linear-gradient(135deg, #154fd4, #09285f);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 30px;
    box-shadow: 0 16px 38px rgba(38, 109, 255, 0.25);
}

label, .stRadio label {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

div[data-testid="stFileUploader"] {
    background: rgba(11, 30, 55, 0.7);
    border: 1px dashed rgba(119, 163, 220, 0.58);
    border-radius: 18px;
    padding: 18px;
}

input, textarea {
    background-color: rgba(25, 39, 62, 0.95) !important;
    color: white !important;
    border-radius: 12px !important;
    border: 1px solid rgba(122, 151, 190, 0.28) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #1f74ff, #05c9de);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.85rem 1.5rem;
    font-size: 19px;
    font-weight: 900;
    box-shadow: 0 18px 44px rgba(0, 161, 255, 0.28);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #155ce0, #04abc0);
    color: white;
}

.footer {
    border-top: 1px solid rgba(116, 159, 215, 0.28);
    text-align: center;
    color: #aab8cb;
    margin-top: 34px;
    padding-top: 22px;
    font-weight: 600;
}

.result-card {
    background: rgba(7, 23, 43, 0.88);
    border: 1px solid rgba(94, 139, 190, 0.38);
    border-radius: 20px;
    padding: 24px;
    margin-top: 24px;
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


# Sidebar
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)
else:
    st.sidebar.markdown("## KOMQ")

st.sidebar.markdown("""
<div class="sidebar-menu">
    <div class="menu-item menu-active">🏠 홈</div>
    <div class="menu-item">📈 분석 결과</div>
    <div class="menu-item">📋 사용 가이드</div>
    <div class="menu-item">ℹ️ 도움말</div>
</div>

<div class="feature-box">
    ⭐ <b>MSA 전문가가 만든<br>Gage R&R 분석 솔루션</b><br><br>
    ✅ ANOVA 기반 정확한 분석<br>
    ✅ Full / Reduced 모델 자동 선택<br>
    ✅ Run Chart 자동 생성<br>
    ✅ Minitab 형식 결과 제공
</div>

<div class="sidebar-footer">
    © 2024 한국경영품질연구원(KOMQ)<br>
    All rights reserved.
</div>
""", unsafe_allow_html=True)


# Top badge
st.markdown("""
<div class="top-badge">
    🛡️ Made by KOMQ<br>
    Quality · Data · Innovation
</div>
""", unsafe_allow_html=True)


# Hero
hero_left, hero_right = st.columns([1.7, 1])

with hero_left:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">MSA Gage R&R 분석 에이전트</div>
        <div class="hero-sub">
            엑셀 업로드 또는 데이터 붙여넣기만으로 ANOVA 기반<br>
            Gage R&R 분석과 Run Chart를 생성합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

with hero_right:
    st.markdown('<div class="hero hero-logo">', unsafe_allow_html=True)
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown("### KOMQ")
    st.markdown("</div>", unsafe_allow_html=True)


# Input card
st.markdown("""
<div class="input-card">
    <div style="display:flex; gap:20px; align-items:center;">
        <div class="icon-circle">⇧</div>
        <div>
            <div class="input-card-title">데이터 입력</div>
            <div class="input-card-desc">
                CSV, XLSX, XLS 파일을 업로드하거나 엑셀 데이터를 그대로 붙여넣으세요.
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

input_mode = st.radio(
    "입력 방식 선택",
    ["엑셀/CSV 업로드", "데이터 붙여넣기"],
    horizontal=True
)

tolerance_text = st.text_input(
    "공차 Tolerance 입력 - 선택사항",
    placeholder="예) 10 또는 0.1"
)

df = None

if input_mode == "엑셀/CSV 업로드":
    uploaded_file = st.file_uploader(
        "파일 업로드",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:
        file_path = OUTPUT_DIR / uploaded_file.name
        file_path.write_bytes(uploaded_file.getvalue())

        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

else:
    pasted = st.text_area(
        "엑셀에서 복사한 데이터를 그대로 붙여넣으세요",
        height=260,
        placeholder="시료\t측정자\t측정값\n1\t1\t0.29\n2\t1\t0.41\n3\t1\t0.64"
    )

    if pasted.strip():
        df = pd.read_csv(StringIO(pasted), sep=None, engine="python")

if df is not None:
    st.markdown("### 입력 데이터 미리보기")
    st.dataframe(df, use_container_width=True)

run = st.button("🚀 Gage R&R 분석 실행")

if run:
    if df is None:
        st.error("먼저 데이터를 업로드하거나 붙여넣으세요.")
        st.stop()

    try:
        tolerance = None
        if tolerance_text.strip():
            tolerance = float(tolerance_text)

        chart_path = OUTPUT_DIR / "gage_run_chart.png"

        result = msa.analyze_gage_rr_with_chart(
            df,
            tolerance=tolerance,
            chart_path=chart_path
        )

        result_text = result.to_minitab_text()

        st.success("분석 완료")

        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown("## 📊 분석 결과")
        st.markdown(result_text)
        st.markdown("</div>", unsafe_allow_html=True)

        if result.chart_path:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown("## 📈 Gage Run Chart")
            st.image(result.chart_path)

            with open(result.chart_path, "rb") as f:
                st.download_button(
                    "Run Chart PNG 다운로드",
                    data=f,
                    file_name="gage_run_chart.png",
                    mime="image/png"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            "분석 결과 Markdown 다운로드",
            data=result_text,
            file_name="msa_result.md",
            mime="text/markdown"
        )

    except Exception as e:
        st.error("분석 실패")
        st.code(str(e))

st.markdown("""
<div class="footer">
    🏢 한국경영품질연구원(KOMQ) &nbsp;&nbsp; | &nbsp;&nbsp;
    Quality · Data · Innovation
</div>
""", unsafe_allow_html=True)
