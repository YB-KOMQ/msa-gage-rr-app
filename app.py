import sys
import importlib.util
from pathlib import Path
from io import StringIO

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).parent
ENGINE_PATH = BASE_DIR / "MSA_FULL_MINITAB_ENGINE_STABLE_FINAL.py"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

spec = importlib.util.spec_from_file_location("msa_engine", ENGINE_PATH)
msa = importlib.util.module_from_spec(spec)
sys.modules["msa_engine"] = msa
spec.loader.exec_module(msa)

st.set_page_config(
    page_title="MSA Gage R&R 분석 에이전트",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1220, #111827);
}
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border: 1px solid #334155;
    border-radius: 24px;
    padding: 36px;
    margin-bottom: 24px;
}
.hero-title {
    color: white;
    font-size: 44px;
    font-weight: 800;
}
.hero-sub {
    color: #94a3b8;
    font-size: 17px;
    margin-top: 10px;
}
.card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
}
.card-title {
    color: white;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 8px;
}
.card-desc {
    color: #94a3b8;
    margin-bottom: 16px;
}
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: white;
    border-radius: 12px;
    font-weight: 800;
    border: none;
    padding: 0.7rem 1.2rem;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #0891b2);
    color: white;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="hero-title">MSA Gage R&R 분석 에이전트</div>
    <div class="hero-sub">
        엑셀 업로드 또는 데이터 붙여넣기만으로 ANOVA 기반 Gage R&R 분석과 Run Chart를 생성합니다.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="card-title">데이터 입력</div>
    <div class="card-desc">CSV, XLSX, XLS 파일을 업로드하거나 엑셀 데이터를 그대로 붙여넣으세요.</div>
</div>
""", unsafe_allow_html=True)

input_mode = st.radio(
    "입력 방식 선택",
    ["엑셀/CSV 업로드", "데이터 붙여넣기"],
    horizontal=True
)

tolerance_text = st.text_input("공차 Tolerance 입력 - 선택사항", "")

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
        height=280,
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

        st.markdown("## 📊 분석 결과")
        st.markdown(result_text)

        if result.chart_path:
            st.markdown("## 📈 Gage Run Chart")
            st.image(result.chart_path)

            with open(result.chart_path, "rb") as f:
                st.download_button(
                    "Run Chart PNG 다운로드",
                    data=f,
                    file_name="gage_run_chart.png",
                    mime="image/png"
                )

        st.download_button(
            "분석 결과 Markdown 다운로드",
            data=result_text,
            file_name="msa_result.md",
            mime="text/markdown"
        )

    except Exception as e:
        st.error("분석 실패")
        st.code(str(e))