# -*- coding: utf-8 -*-
"""
MSA_FULL_MINITAB_ENGINE_INTEGRATED_FINAL_ALL.py

Minitab 재현용 MSA 엔진
- Variable Gage R&R (ANOVA, Type I Sequential)
- Full / Reduced 모델 자동 선택
- Variance Components / %Contribution / SD / Study Variation / %Study Variation / %Tolerance / ndc
- Gage Run Chart PNG 생성
- 한글 폰트 NanumGothic 자동 적용

GPTs 지식 업로드용 단일 파이썬 파일입니다.

필수 패키지
pip install pandas numpy statsmodels matplotlib openpyxl

기본 사용
python MSA_FULL_MINITAB_ENGINE.py data.xlsx --chart

CSV/XLSX 파일은 long 형식 또는 Minitab형 wide 형식을 지원합니다.
long 형식 컬럼명 예:
Part/시료, Operator/측정자, Measurement/측정값, Trial/반복

차트 기본 저장 위치:
/mnt/data/gage_run_chart.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import math
import re
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


PART_ALIASES = ["시료", "part", "Part", "Sample", "sample", "품번", "부품"]
OP_ALIASES = ["측정자", "operator", "Operator", "Appraiser", "appraiser", "검사자"]
MEAS_ALIASES = ["측정값", "measurement", "Measurement", "Response", "response", "Value", "value", "Y", "y"]
TRIAL_ALIASES = ["Trial", "trial", "반복", "반복수", "회차"]


class MSAResult:
    """
    GPT 실행 환경 안정화 버전.
    dataclass를 사용하지 않는다.
    - 일부 GPT/Notebook/importlib 실행 환경에서 dataclass가
      sys.modules 등록 전 __module__ 참조 문제로 실패할 수 있기 때문.
    """

    def __init__(
        self,
        selected_model: str,
        interaction_p_value: float,
        anova_full: pd.DataFrame,
        anova_selected: pd.DataFrame,
        variance_components: pd.DataFrame,
        gage_evaluation: pd.DataFrame,
        ndc: int,
        raw: Dict[str, Any],
        chart_path: Optional[str] = None,
    ):
        self.selected_model = selected_model
        self.interaction_p_value = interaction_p_value
        self.anova_full = anova_full
        self.anova_selected = anova_selected
        self.variance_components = variance_components
        self.gage_evaluation = gage_evaluation
        self.ndc = ndc
        self.raw = raw
        self.chart_path = chart_path

    def to_minitab_text(self) -> str:
        return format_minitab_text(self)


def _find_col(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    lowmap = {str(c).strip().lower(): c for c in df.columns}
    for a in aliases:
        if a.lower() in lowmap:
            return lowmap[a.lower()]
    return None


def _auto_trial(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    trial = _find_col(df, TRIAL_ALIASES)
    if trial is None:
        df["_Trial"] = df.groupby(["Part", "Operator"], sort=False).cumcount() + 1
    else:
        df["_Trial"] = df[trial]
    return df


def wide_minitab_table_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minitab형 wide table 변환.
    예:
    시료 | 측정자 A 1 2 3 | 측정자 B 1 2 3 | 측정자 C 1 2 3
    """
    if isinstance(df.columns, pd.MultiIndex):
        part_col = df.columns[0]
        rows = []
        current_operator = None
        for col in df.columns[1:]:
            top = str(col[0]).strip()
            bottom = str(col[1]).strip()
            if top and not top.startswith("Unnamed"):
                current_operator = top
            op = current_operator or top
            tr = bottom
            for _, r in df.iterrows():
                rows.append({"Part": r[part_col], "Operator": op, "Trial": tr, "Measurement": r[col]})
        return pd.DataFrame(rows).dropna(subset=["Measurement"])

    part_col = _find_col(df, PART_ALIASES) or df.columns[0]
    rows = []
    for col in df.columns:
        if col == part_col:
            continue
        name = str(col).strip()
        m = re.search(r"(측정자\s*[A-Za-z가-힣0-9]+|[ABC])[^0-9]*(\d+)$", name)
        if m:
            op, tr = m.group(1), m.group(2)
        else:
            op, tr = name, None
        for _, r in df.iterrows():
            rows.append({"Part": r[part_col], "Operator": op, "Trial": tr, "Measurement": r[col]})
    out = pd.DataFrame(rows).dropna(subset=["Measurement"])
    if out["Trial"].isna().any():
        out["Trial"] = out.groupby(["Part", "Operator"], sort=False).cumcount() + 1
    return out


def standardize_long(df: pd.DataFrame) -> pd.DataFrame:
    part = _find_col(df, PART_ALIASES)
    op = _find_col(df, OP_ALIASES)
    meas = _find_col(df, MEAS_ALIASES)

    if part is None or op is None or meas is None:
        df = wide_minitab_table_to_long(df)
        part, op, meas = "Part", "Operator", "Measurement"

    out = pd.DataFrame({
        "Part": df[part],
        "Operator": df[op],
        "Measurement": pd.to_numeric(df[meas], errors="coerce"),
    }).dropna(subset=["Measurement"])

    trial = _find_col(df, TRIAL_ALIASES)
    if trial is not None:
        out["Trial"] = df.loc[out.index, trial].values

    out = _auto_trial(out)

    # 입력 순서 유지. Minitab 범주 순서 재현에 중요.
    out["Part"] = pd.Categorical(out["Part"], categories=pd.unique(out["Part"]), ordered=True)
    out["Operator"] = pd.Categorical(out["Operator"], categories=pd.unique(out["Operator"]), ordered=True)
    out["_Trial"] = pd.Categorical(out["_Trial"], categories=pd.unique(out["_Trial"]), ordered=True)

    return out.reset_index(drop=True)


def _anova_type1(model) -> pd.DataFrame:
    a = sm.stats.anova_lm(model, typ=1)
    a = a.rename(columns={"df": "DF", "sum_sq": "SS", "mean_sq": "MS", "F": "F", "PR(>F)": "P"})
    return a


def _clean_anova_full(a: pd.DataFrame) -> pd.DataFrame:
    idxmap = {
        "C(Part)": "Part",
        "C(Operator)": "Operator",
        "C(Part):C(Operator)": "Part*Operator",
        "Residual": "Repeatability",
    }
    out = a.copy()
    out.index = [idxmap.get(str(i), str(i)) for i in out.index]
    return out[["DF", "SS", "MS", "F", "P"]]


def _clean_anova_reduced(a: pd.DataFrame) -> pd.DataFrame:
    idxmap = {
        "C(Part)": "Part",
        "C(Operator)": "Operator",
        "Residual": "Repeatability",
    }
    out = a.copy()
    out.index = [idxmap.get(str(i), str(i)) for i in out.index]
    return out[["DF", "SS", "MS", "F", "P"]]


def analyze_gage_rr(
    data: pd.DataFrame,
    tolerance: Optional[float] = None,
    alpha_interaction: float = 0.05,
) -> MSAResult:
    """
    Minitab 방식 ANOVA Gage R&R.
    balanced design 전용.
    """
    d = standardize_long(data)

    n_part = d["Part"].nunique()
    n_operator = d["Operator"].nunique()
    trial_counts = d.groupby(["Part", "Operator"], observed=False)["Measurement"].count()
    if trial_counts.nunique() != 1:
        raise ValueError("Minitab ANOVA Gage R&R 1:1 모드는 balanced data만 지원합니다.")
    n_trial = int(trial_counts.iloc[0])

    full_model = ols("Measurement ~ C(Part) + C(Operator) + C(Part):C(Operator)", data=d).fit()
    reduced_model = ols("Measurement ~ C(Part) + C(Operator)", data=d).fit()

    af = _clean_anova_full(_anova_type1(full_model))
    ar = _clean_anova_reduced(_anova_type1(reduced_model))

    p_int = float(af.loc["Part*Operator", "P"])
    use_full = p_int < alpha_interaction
    selected_model = "Full" if use_full else "Reduced"
    anova_selected = af if use_full else ar

    if use_full:
        ms_e = float(af.loc["Repeatability", "MS"])
        ms_int = float(af.loc["Part*Operator", "MS"])
        ms_op = float(af.loc["Operator", "MS"])
        ms_part = float(af.loc["Part", "MS"])

        ev = ms_e
        inter = max((ms_int - ms_e) / n_trial, 0.0)
        op = max((ms_op - ms_int) / (n_part * n_trial), 0.0)
        reproducibility = op + inter
        part = max((ms_part - ms_int) / (n_operator * n_trial), 0.0)
    else:
        ms_e = float(ar.loc["Repeatability", "MS"])
        ms_op = float(ar.loc["Operator", "MS"])
        ms_part = float(ar.loc["Part", "MS"])

        ev = ms_e
        inter = 0.0
        op = max((ms_op - ms_e) / (n_part * n_trial), 0.0)
        reproducibility = op
        part = max((ms_part - ms_e) / (n_operator * n_trial), 0.0)

    total_gage = ev + reproducibility
    total = total_gage + part

    rows_vc = [
        ("총 Gage R&R", total_gage),
        ("  반복성", ev),
        ("  재현성", reproducibility),
        ("    측정자", op),
    ]
    if use_full:
        rows_vc.append(("    측정자*부품", inter))
    rows_vc.extend([
        ("부품-대-부품", part),
        ("총 변동", total),
    ])

    vc = pd.DataFrame(rows_vc, columns=["출처", "분산 성분"])
    vc["%기여(분산 성분)"] = np.where(total > 0, vc["분산 성분"] / total * 100.0, np.nan)

    ge = vc.copy()
    ge["표준 편차(SD)"] = np.sqrt(ge["분산 성분"])
    ge["연구 변동(6 × SD)"] = ge["표준 편차(SD)"] * 6.0
    total_sv = float(ge.loc[ge["출처"] == "총 변동", "연구 변동(6 × SD)"].iloc[0])
    ge["%연구 변동(%SV)"] = np.where(total_sv > 0, ge["연구 변동(6 × SD)"] / total_sv * 100.0, np.nan)
    if tolerance is not None:
        ge["%공차"] = ge["연구 변동(6 × SD)"] / tolerance * 100.0

    grr_sd = math.sqrt(total_gage)
    part_sd = math.sqrt(part)
    ndc = int(math.floor(1.41 * part_sd / grr_sd)) if grr_sd > 0 else 0
    ndc = max(ndc, 1) if part_sd > 0 and grr_sd > 0 else ndc

    return MSAResult(
        selected_model=selected_model,
        interaction_p_value=p_int,
        anova_full=af,
        anova_selected=anova_selected,
        variance_components=vc,
        gage_evaluation=ge,
        ndc=ndc,
        raw={
            "n_part": n_part,
            "n_operator": n_operator,
            "n_trial": n_trial,
            "data": d,
            "total_gage_var": total_gage,
            "total_var": total,
            "part_var": part,
        },
    )


def setup_korean_font(font_path: Optional[str | Path] = None) -> str:
    """
    NanumGothic 우선 적용.
    GPTs 환경 기본 경로: /mnt/data/NanumGothic.ttf
    """
    candidates = []
    if font_path:
        candidates.append(Path(font_path))
    candidates += [
        Path("/mnt/data/NanumGothic.ttf"),
        Path("/mnt/data/NanumGothicBold.ttf"),
        Path("/mnt/data/NanumGothicLight.ttf"),
        Path("./NanumGothic.ttf"),
        Path("./NanumGothicBold.ttf"),
    ]
    for p in candidates:
        if p.exists():
            font_manager.fontManager.addfont(str(p))
            name = font_manager.FontProperties(fname=str(p)).get_name()
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name

    warnings.warn("NanumGothic.ttf를 찾지 못했습니다. 한글이 깨질 수 있습니다.")
    plt.rcParams["axes.unicode_minus"] = False
    return plt.rcParams.get("font.family", ["sans-serif"])[0]


def create_gage_run_chart(
    data: pd.DataFrame,
    output_path: str | Path = "/mnt/data/gage_run_chart.png",
    title: str = "Part의 수준별 Response의 Gage 런 차트 - Operator",
    subtitle: Optional[str] = None,
    font_path: Optional[str | Path] = None,
    figsize: Tuple[float, float] = (16, 10),
    dpi: int = 150,
) -> str:
    """
    Minitab 스타일 Gage Run Chart 생성.
    - 기본 2행 × 5열 패널
    - 각 패널은 Part 1개
    - x축은 Operator 위치 분리
    - 각 Operator 위치 안에서 Trial 반복점 연결
    - Operator별 선/마커 스타일:
      1 = 파랑 원 실선
      2 = 빨강 사각 파선
      3 = 초록 마름모 파선
    - 전체 평균선 포함
    - 우측 Operator 범례
    - 한글 폰트 NanumGothic 적용
    - 기본 저장 위치: /mnt/data/gage_run_chart.png
    """
    setup_korean_font(font_path)
    d = standardize_long(data)

    parts = list(d["Part"].cat.categories)
    operators = list(d["Operator"].cat.categories)

    n_parts = len(parts)
    ncols = 5
    nrows = int(math.ceil(n_parts / ncols))
    if n_parts == 10:
        nrows, ncols = 2, 5

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, dpi=dpi, sharey=True)
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])
    axes = axes.ravel()

    color_map = ["#0057B8", "#A30F0F", "#008A2E", "#9467bd", "#8c564b", "#e377c2"]
    marker_map = ["o", "s", "D", "^", "v", "P"]
    linestyle_map = ["-", "--", "--", "-.", ":", "--"]

    y = d["Measurement"].astype(float)
    ymin, ymax = float(y.min()), float(y.max())
    yrng = ymax - ymin if ymax > ymin else 1.0
    pad = yrng * 0.10
    ylow = ymin - pad
    yhigh = ymax + pad
    overall_mean = float(y.mean())

    handles = []
    labels = []

    for i, part in enumerate(parts):
        ax = axes[i]
        subp = d[d["Part"] == part]

        for oi, op in enumerate(operators):
            cell = subp[subp["Operator"] == op].sort_values("_Trial")
            if len(cell) == 0:
                continue

            x_center = oi + 1
            if len(cell) == 1:
                xs = np.array([x_center])
            else:
                xs = x_center + np.linspace(-0.075, 0.075, len(cell))

            line, = ax.plot(
                xs,
                cell["Measurement"].astype(float).values,
                marker=marker_map[oi % len(marker_map)],
                color=color_map[oi % len(color_map)],
                linestyle=linestyle_map[oi % len(linestyle_map)],
                linewidth=0.75,
                markersize=5.5,
                markeredgewidth=0.5,
                label=str(op),
            )
            if i == 0:
                handles.append(line)
                labels.append(str(op))

        ax.axhline(overall_mean, color="#8a8a8a", linestyle="--", linewidth=0.8, zorder=0)

        ax.set_title(
            f"{part}",
            fontsize=10,
            pad=1.5,
            bbox=dict(facecolor="white", edgecolor="#777777", linewidth=0.6, boxstyle="square,pad=0.2"),
        )
        ax.set_xlim(0.6, len(operators) + 0.4)
        ax.set_ylim(ylow, yhigh)
        ax.set_xticks(range(1, len(operators) + 1))
        ax.set_xticklabels([])

        major_ticks = np.arange(math.floor(ylow * 5) / 5, math.ceil(yhigh * 5) / 5 + 0.001, 0.2)
        minor_ticks = np.arange(math.floor(ylow * 10) / 10, math.ceil(yhigh * 10) / 10 + 0.001, 0.1)
        ax.set_yticks(major_ticks)
        ax.set_yticks(minor_ticks, minor=True)

        ax.grid(True, which="major", axis="both", color="#e4e4e4", linewidth=0.6)
        ax.grid(True, which="minor", axis="y", color="#ececec", linewidth=0.5)

        for spine in ax.spines.values():
            spine.set_color("#777777")
            spine.set_linewidth(0.6)

        ax.tick_params(axis="both", labelsize=9, colors="#333333", width=0.5)

        if i == 0:
            ax.text(-0.08, overall_mean, "평균", transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=9, color="#333333")
        if i == n_parts - 1:
            ax.text(1.06, overall_mean, "평균", transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=9, color="#333333")

    for j in range(n_parts, len(axes)):
        axes[j].axis("off")

    # Minitab 스타일 헤더
    fig.text(0.025, 0.965, title, ha="left", va="top", fontsize=22, color="#333333")

    if subtitle:
        fig.text(0.02, 0.885, subtitle, ha="left", va="top", fontsize=11,
                 color="#333333", linespacing=1.05)
    else:
        fig.text(0.02, 0.885, "Gage 이름:\n연구 날짜:", ha="left", va="top",
                 fontsize=11, color="#333333", linespacing=1.05)
        fig.text(0.50, 0.905, "보고자:\n공차:\n기타:", ha="left", va="top",
                 fontsize=11, color="#333333", linespacing=1.05)

    fig.text(0.055, 0.50, "Response", rotation=90, ha="center", va="center",
             fontsize=14, color="#333333")
    fig.text(0.45, 0.09, "Operator", ha="center", va="center",
             fontsize=14, color="#333333")
    fig.text(0.035, 0.045, "패널 변수: Part", ha="left", va="center",
             fontsize=12, style="italic", color="#333333")

    if handles:
        fig.legend(
            handles,
            labels,
            title="Operator",
            loc="center right",
            bbox_to_anchor=(0.965, 0.68),
            frameon=False,
            fontsize=10,
            title_fontsize=11,
            handlelength=2.5,
        )

    plt.subplots_adjust(left=0.095, right=0.82, bottom=0.115, top=0.72, wspace=0.0, hspace=0.0)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches=False)
    plt.close(fig)
    return str(output_path)


def analyze_gage_rr_with_chart(
    data: pd.DataFrame,
    tolerance: Optional[float] = None,
    chart_path: str | Path = "/mnt/data/gage_run_chart.png",
    font_path: Optional[str | Path] = None,
) -> MSAResult:
    result = analyze_gage_rr(data, tolerance=tolerance)
    result.chart_path = create_gage_run_chart(data, output_path=chart_path, font_path=font_path)
    return result


def _fmt(x: Any, digits: int) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def _markdown_table(headers: List[str], rows: List[List[Any]], right_align_from: int = 1) -> str:
    lines = []
    lines.append("| " + " | ".join(str(h) for h in headers) + " |")
    aligns = []
    for i in range(len(headers)):
        aligns.append("---:" if i >= right_align_from else "---")
    lines.append("| " + " | ".join(aligns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def _table_text(df: pd.DataFrame, cols: List[Tuple[str, int]]) -> str:
    headers = ["출처"] + [c for c, _ in cols]
    rows = []
    for _, r in df.iterrows():
        source = str(r["출처"]).strip()
        source = source.replace("측정자", "└ 측정자") if source == "측정자" else source
        source = source.replace("측정자*부품", "└ 측정자*부품") if source == "측정자*부품" else source
        rows.append([source] + [_fmt(r[c], d) for c, d in cols])
    return _markdown_table(headers, rows, right_align_from=1)


def _anova_text(df: pd.DataFrame) -> str:
    temp = df.reset_index().rename(columns={"index": "출처"})
    temp["DF"] = temp["DF"].astype(int)
    headers = ["출처", "DF", "SS", "MS", "F", "P"]
    rows = []
    for _, r in temp.iterrows():
        rows.append([
            r["출처"],
            str(int(r["DF"])),
            _fmt(r["SS"], 6),
            _fmt(r["MS"], 6),
            _fmt(r["F"], 6),
            _fmt(r["P"], 6),
        ])
    return _markdown_table(headers, rows, right_align_from=1)


def format_minitab_text(res: MSAResult) -> str:
    """
    Minitab 출력 순서를 유지하되 Markdown 표 형식으로 출력한다.
    """
    out = []
    out.append("Gage R&R")
    out.append("")
    out.append("| 항목 | 값 |")
    out.append("|---|---:|")
    out.append(f"| selected_model | {res.selected_model} |")
    out.append(f"| interaction_p_value | {res.interaction_p_value:.6f} |")
    out.append("")
    out.append("ANOVA Full")
    out.append(_anova_text(res.anova_full))
    out.append("")
    out.append(f"ANOVA Selected ({res.selected_model})")
    out.append(_anova_text(res.anova_selected))
    out.append("")
    out.append("분산 성분")
    out.append(_table_text(res.variance_components, [("분산 성분", 5), ("%기여(분산 성분)", 2)]))
    out.append("")
    out.append("Gage 평가")
    eval_cols = [("표준 편차(SD)", 5), ("연구 변동(6 × SD)", 5), ("%연구 변동(%SV)", 2)]
    if "%공차" in res.gage_evaluation.columns:
        eval_cols.append(("%공차", 2))
    out.append(_table_text(res.gage_evaluation, eval_cols))
    out.append("")
    out.append("구별 범주의 수")
    out.append("| 항목 | 값 |")
    out.append("|---|---:|")
    out.append(f"| ndc | {res.ndc} |")
    if res.chart_path:
        out.append("")
        out.append("Gage Run Chart")
        out.append("| 항목 | 경로 |")
        out.append("|---|---|")
        out.append(f"| gage_run_chart | {res.chart_path} |")
    return "\n".join(out)


def read_msa_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in [".xlsx", ".xls"]:
        # Minitab형 multi-header 우선
        try:
            df_multi = pd.read_excel(path, header=[0, 1])
            # 첫 열 외에 유효한 MultiIndex가 있으면 사용
            if isinstance(df_multi.columns, pd.MultiIndex) and len(df_multi.columns) > 2:
                return df_multi
        except Exception:
            pass
        return pd.read_excel(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise ValueError("지원 파일 형식: .xlsx, .xls, .csv")


def analyze_file(
    path: str | Path,
    tolerance: Optional[float] = None,
    chart: bool = True,
    chart_path: str | Path = "/mnt/data/gage_run_chart.png",
    font_path: Optional[str | Path] = None,
) -> MSAResult:
    df = read_msa_file(path)
    if chart:
        return analyze_gage_rr_with_chart(df, tolerance=tolerance, chart_path=chart_path, font_path=font_path)
    return analyze_gage_rr(df, tolerance=tolerance)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Minitab 재현용 MSA Gage R&R 엔진")
    parser.add_argument("file", help="CSV/XLSX data file")
    parser.add_argument("--tolerance", type=float, default=None)
    parser.add_argument("--chart", action="store_true", default=True, help="Gage Run Chart 생성")
    parser.add_argument("--chart-path", default="/mnt/data/gage_run_chart.png")
    parser.add_argument("--font-path", default=None)
    args = parser.parse_args()

    result = analyze_file(
        args.file,
        tolerance=args.tolerance,
        chart=args.chart,
        chart_path=args.chart_path,
        font_path=args.font_path,
    )
    print(result.to_minitab_text())
