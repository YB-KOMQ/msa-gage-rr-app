import sys
import base64
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


def image_base64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


logo_b64 = image_base64(LOGO_PATH)

st.set_page_config(
    page_title="KOMQ MSA Gage R&R 분석 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 80% 10%, rgba(0, 180, 255, 0.18), transparent 30%),
        linear-gradient(135deg, #06111f 0%, #071a31 48%, #030914 100%);
    color: #f8fafc;
}

.block-container {
    max-width: 1320px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07182d 0%, #03101f 100%);
    border-right: 1px solid rgba(96, 165, 250, 0.18);
}

.logo-side {
    background: white;
    border-radius: 16px;
    padding: 12px;
    margin: 16px 8px 28px 8px;
    box-shadow: 0 16px 35px rgba(0,0,0,.22);
}

.logo-side img {
    width: 100%;
    display: block;
}

.menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #dbeafe;
    font-size: 16px;
    font-weight: 800;
    padding: 14px 16px;
    border-radius: 14px;
    margin: 8px 6px;
}

.menu-active {
    background: linear-gradient(135deg, #1d4ed8, #0ea5e9);
    box-shadow: 0 16px 36px rgba(37, 99, 235, .32);
}

.feature-box {
    margin: 34px 6px 0 6px;
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(147, 197, 253, .25);
    background: rgba(15, 38, 70, .68);
    color: #dbeafe;
    line-height: 1.9;
    font-size: 14px;
}

.sidebar-footer {
    margin: 44px 8px 12px 8px;
    color: #93a4bb;
    font-size: 12px;
    line-height: 1.7;
}

.topbar {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 18px;
}

.top-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: #22d3ee;
    border: 1px solid rgba(34, 211, 238, .45);
    border-radius: 999px;
    padding: 10px 16px;
    font-weight: 900;
    font-size: 13px;
    background: rgba(5, 20, 42, .78);
}

.hero {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 34px;
    align-items: center;
    padding: 38px;
    border-radius: 28px;
    border: 1px solid rgba(147, 197, 253, .28);
    background:
        linear-gradient(135deg, rgba(15, 40, 74, .96), rgba(8, 25, 48, .94));
    box-shadow: 0 28px 90px rgba(0,0,0,.34);
    margin-bottom: 26px;
}

.hero-logo {
    background: white;
    border-radius: 22px;
    padding: 24px;
    box-shadow: inset 0 0 0 1px rgba(15,23,42,.06), 0 18px 45px rgba(0,0,0,.25);
}

.hero-logo img {
    width: 100%;
    display: block;
}

.hero-title {
    color: white;
    font-size: 46px;
    line-height: 1.16;
    letter-spacing: -1.4px;
    font-weight: 900;
    margin-bottom: 18px;
}

.hero-sub {
    color: #b7c7dc;
    font-size: 18px;
    line-height: 1.75;
    font-weight: 600;
}

.hero-meta {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 26px;
}

.meta-chip {
    border: 1px solid rgba(147, 197, 253, .22);
    background: rgba(15, 23, 42, .45);
    color: #bfdbfe;
    border-radius: 999px;
    padding: 8px 13px;
    font-weight: 800;
    font-size: 13px;
}

.input-card {
    padding: 28px 30px;
    border-radius: 24px;
    border: 1px solid rgba(147, 197, 253, .24);
    background: linear-gradient(135deg, rgba(13, 38, 70, .92), rgba(6, 23, 43, .91));
    margin-bottom: 22px;
}

.input-head {
    display: flex;
    align-items: center;
    gap: 18px;
}

.icon-circle {
    width: 60px;
    height: 60px;
    border-radius: 18px;
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    box-shadow: 0 16px 36px rgba(14,165,233,.28);
}

.card-title {
    color: white;
    font-size: 26px;
    font-weight: 900;
    margin-bottom: 6px;
}

.card-desc {
    color: #b7c7dc;
    font-size: 16px;
    font-weight: 600;
}

.form-panel {
    padding: 24px 28px 28px 28px;
    border-radius: 24px;
    border: 1px solid rgba(147, 197, 253, .18);
    background: rgba(3, 14, 28, .32);
}

label, .stRadio label {
    color: #f8fafc !important;
    font-weight: 800 !important;
}

div[data-testid="stFileUploader"] {
    background: rgba(15, 23, 42, .78);
    border: 1px dashed rgba(147, 197, 253, .42);
    border-radius: 18px;
    padding: 18px;
}

input, textarea {
    background-color: rgba(30, 41, 59, .9) !important;
    color: white !important;
    border-radius: 14px !important;
    border: 1px solid rgba(148, 163, 184, .22) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    border: none;
    border-radius: 16px;
    padding: .85rem 1.55rem;
    font-size: 18px;
    font-weight: 900;
    box-shadow: 0 18px 45px rgba(14, 165, 233, .28);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #0891b2);
    color: white;
}

.result-card {
    background: rgba(7, 23, 43, .88);
    border: 1px solid rgba(147, 197, 253, .22);
    border-radius: 22px;
    padding: 24px;
    margin-top: 24px;
}

.footer {
    border-top: 1px solid rgba(147, 197, 253, .2);
    text-align: center;
    color: #9fb0c6;
    margin-top: 34px;
    padding-top: 22px;
    font-weight: 700;
}

@media (max-width: 900px) {
    .hero {
        grid-template-columns: 1fr;
    }
    .hero-logo {
        max-width: 320px;
    }
    .hero-title {
        font-size: 34px;
    }
}
</style>
""", unsafe_allow_html=True)


# Sidebar
if logo_b64:
    st.sidebar.markdown(
        f'<div class="logo-side"><img src="data:image/jpeg;base64,{logo_b64}"></div>',
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown("## KOMQ")

st.sidebar.markdown("""
<div class="menu-item menu-active">🏠 홈</div>
<div class="menu-item">📈 분석 결과</div>
<div class="menu-item">📋 사용 가이드</div>
<div class="menu-item">ℹ️ 도움말</div>

<div class="feature-box">
    ⭐ <b>MSA 전문가가 만든<br>Gage R&R 분석 솔루션</b><br><br>
    ✅ ANOVA 기반 정확한 분석<br>
    ✅ Full / Reduced 모델 자동 선택<br>
    ✅ Run Chart 자동 생성<br>
    ✅ Minitab 형식 결과 제공
</div>

<div class="sidebar-footer">
    © 2026 한국경영품질연구원(KOMQ)<br>
    MSA Analysis System v1.0<br>
    All rights reserved.
</div>
""", unsafe_allow_html=True)


# Top
st.markdown("""
<div class="topbar">
    <div class="top-badge">🛡️ Made by KOMQ · Quality · Data · Innovation</div>
</div>
""", unsafe_allow_html=True)


# Hero
if logo_b64:
    logo_html = f'<div class="hero-logo"><img src="data:image/jpeg;base64,{logo_b64}"></div>'
else:
    logo_html = '<div class="hero-logo"><b>KOMQ</b></div>'

st.markdown(f"""
<div class="hero">
    {logo_html}
    <div>
        <div class="hero-title">KOMQ MSA Gage R&R<br>분석 시스템</div>
        <div class="hero-sub">
            엑셀 업로드 또는 데이터 붙여넣기만으로 ANOVA 기반 Gage R&R 분석,<br>
            Full / Reduced 모델 선택, 분산 성분 분석, Run Chart 생성을 자동 수행합니다.
        </div>
        <div class="hero-meta">
            <div class="meta-chip">ANOVA Gage R&R</div>
            <div class="meta-chip">Minitab Style Output</div>
            <div class="meta-chip">Run Chart Auto</div>
            <div class="meta-chip">KOMQ Quality System</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# Input card
st.markdown("""
<div class="input-card">
    <div class="input-head">
        <div class="icon-circle">⇧</div>
        <div>
            <div class="card-title">데이터 입력</div>
            <div class="card-desc">CSV, XLSX, XLS 파일을 업로드하거나 엑셀 데이터를 그대로 붙여넣으세요.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="form-panel">', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)


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
    MSA Analysis System v1.0 &nbsp;&nbsp; | &nbsp;&nbsp;
    © 2026 All rights reserved.
</div>
""", unsafe_allow_html=True)
