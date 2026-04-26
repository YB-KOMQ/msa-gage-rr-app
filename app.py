import sys
import base64
import importlib.util
from pathlib import Path
from io import StringIO

import pandas as pd
import streamlit as st

# ------------------------
# 경로 설정
# ------------------------
BASE_DIR = Path(__file__).parent
ENGINE_PATH = BASE_DIR / "MSA_FULL_MINITAB_ENGINE_STABLE_FINAL.py"
LOGO_PATH = BASE_DIR / "komq_logo.jpg"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ------------------------
# 엔진 로딩
# ------------------------
spec = importlib.util.spec_from_file_location("msa_engine", ENGINE_PATH)
msa = importlib.util.module_from_spec(spec)
sys.modules["msa_engine"] = msa
spec.loader.exec_module(msa)

# ------------------------
# 유틸
# ------------------------
def image_base64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")

logo_b64 = image_base64(LOGO_PATH)

# ------------------------
# 기본 설정
# ------------------------
st.set_page_config(layout="wide")

# ------------------------
# 사이드바 메뉴
# ------------------------
if logo_b64:
    st.sidebar.image(LOGO_PATH, use_container_width=True)

page = st.sidebar.radio(
    "메뉴",
    ["홈", "분석 결과", "사용 가이드", "도움말"],
    label_visibility="collapsed"
)

# ------------------------
# 상태 저장 초기화
# ------------------------
if "result_text" not in st.session_state:
    st.session_state["result_text"] = None
if "chart_path" not in st.session_state:
    st.session_state["chart_path"] = None

# =========================================================
# 🏠 홈
# =========================================================
if page == "홈":

    st.title("KOMQ MSA Gage R&R 분석 시스템")
    st.caption("엑셀 업로드 또는 붙여넣기로 ANOVA 기반 Gage R&R 분석 수행")

    input_mode = st.radio(
        "입력 방식",
        ["엑셀/CSV 업로드", "데이터 붙여넣기"],
        horizontal=True
    )

    tolerance_text = st.text_input("공차 (선택)")

    df = None

    # 파일 업로드
    if input_mode == "엑셀/CSV 업로드":
        uploaded_file = st.file_uploader("파일 업로드", type=["csv", "xlsx", "xls"])

        if uploaded_file:
            file_path = OUTPUT_DIR / uploaded_file.name
            file_path.write_bytes(uploaded_file.getvalue())

            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

    # 붙여넣기
    else:
        pasted = st.text_area("데이터 붙여넣기")

        if pasted.strip():
            df = pd.read_csv(StringIO(pasted), sep=None, engine="python")

    # 미리보기
    if df is not None:
        st.dataframe(df, use_container_width=True)

    # 실행 버튼
    if st.button("🚀 분석 실행"):

        if df is None:
            st.error("데이터 없음")
            st.stop()

        try:
            tolerance = float(tolerance_text) if tolerance_text else None

            chart_path = OUTPUT_DIR / "gage_run_chart.png"

            result = msa.analyze_gage_rr_with_chart(
                df,
                tolerance=tolerance,
                chart_path=chart_path
            )

            result_text = result.to_minitab_text()

            # 🔥 상태 저장
            st.session_state["result_text"] = result_text
            st.session_state["chart_path"] = result.chart_path

            st.success("분석 완료")
            st.markdown(result_text)

            if result.chart_path:
                st.image(result.chart_path)

        except Exception as e:
            st.error("분석 실패")
            st.code(str(e))


# =========================================================
# 📊 분석 결과
# =========================================================
elif page == "분석 결과":

    st.title("📊 분석 결과")

    if st.session_state["result_text"]:

        st.markdown(st.session_state["result_text"])

        if st.session_state["chart_path"]:
            st.image(st.session_state["chart_path"])

    else:
        st.info("먼저 홈에서 분석을 실행하세요.")


# =========================================================
# 📋 사용 가이드
# =========================================================
elif page == "사용 가이드":

    st.title("📋 사용 가이드")

    st.markdown("""
### ✔ 데이터 형식

| 항목 | 컬럼명 예시 |
|---|---|
| 시료 | Part / 시료 |
| 측정자 | Operator |
| 측정값 | Measurement |
| 반복 | Trial |

### ✔ 규칙
- Long format 사용
- 균형 데이터만 가능
- 공차는 숫자로 입력

### ✔ 파일 지원
- CSV
- XLSX
- XLS
""")


# =========================================================
# ℹ️ 도움말
# =========================================================
elif page == "도움말":

    st.title("ℹ️ 도움말")

    st.markdown("""
### ❗ 자주 발생 오류

- 컬럼명이 인식 안됨
- 데이터 불균형
- 공차 문자 입력

### ✔ 해결 방법

- 컬럼명을 Part / Operator / Measurement로 맞추기
- 각 시료 동일 반복수 유지
- 공차 숫자 입력

### 📞 문의
KOMQ MSA 시스템 관리자
""")
