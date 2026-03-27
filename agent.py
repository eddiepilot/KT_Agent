"""
Telecom Sales BI Agent
통신사 휴대폰 판매 추이·재고 관리·매출 증대 전략 제안 Agent
실행: streamlit run agent.py
"""

import os
import io
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 1. 데이터 로더
# ─────────────────────────────────────────────

SHEET_SALES = "세일즈_원장 (Sales_Transactions)"
SHEET_INV   = "일일_재고흐름 (Inventory_Log)"
SHEET_MKT   = "채널별_마케팅 (Marketing_Spend)"
SHEET_MODEL = "단말_마스터 (Master_Model)"
SHEET_AGENCY= "유통망_마스터 (Master_Agency)"

COL_MAP_SALES = {
    "거래일시": "거래일시", "거래ID": "거래ID", "대리점코드": "대리점코드",
    "모델코드": "모델코드", "가입유형": "가입유형", "요금제": "요금제",
    "고객세그먼트": "고객세그먼트", "단말매출(원)": "단말매출",
    "리베이트(원)": "리베이트", "상태": "상태",
}
COL_MAP_INV = {
    "기준일": "기준일", "대리점코드": "대리점코드", "모델코드": "모델코드",
    "기초물량": "기초물량", "본사입고": "본사입고", "타점포이관": "타점포이관",
    "판매출고": "판매출고", "기말보유량": "기말보유량",
}
COL_MAP_MKT = {
    "집행일자": "집행일자", "유입채널": "유입채널", "캠페인명": "캠페인명",
    "타겟팅": "타겟팅", "소진예산(원)": "소진예산",
    "노출수": "노출수", "클릭수": "클릭수", "유효리드(명)": "유효리드",
}
COL_MAP_MODEL = {
    "모델코드": "모델코드", "펫네임(기기명)": "기기명", "제조사": "제조사",
    "세그먼트": "세그먼트", "네트워크": "네트워크", "출고가(원)": "출고가",
}
COL_MAP_AGENCY = {
    "대리점코드": "대리점코드", "상호명": "상호명", "권역": "권역",
    "상권유형": "상권유형", "점포등급": "점포등급", "월목표건수": "월목표건수",
}


@st.cache_data(show_spinner=False)
def load_excel(file_bytes: bytes) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(io.BytesIO(file_bytes))

    def read(sheet, col_map):
        df = xls.parse(sheet)
        df.columns = [c.strip() for c in df.columns]
        # 원본 컬럼명 → 내부 컬럼명
        rename = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=rename)
        return df

    sales  = read(SHEET_SALES,  COL_MAP_SALES)
    inv    = read(SHEET_INV,    COL_MAP_INV)
    mkt    = read(SHEET_MKT,    COL_MAP_MKT)
    models = read(SHEET_MODEL,  COL_MAP_MODEL)
    agency = read(SHEET_AGENCY, COL_MAP_AGENCY)

    # 숫자형 정제
    for col in ["단말매출", "리베이트"]:
        if col in sales.columns:
            sales[col] = pd.to_numeric(sales[col], errors="coerce").fillna(0)
    for col in ["기초물량", "본사입고", "타점포이관", "판매출고", "기말보유량"]:
        if col in inv.columns:
            inv[col] = pd.to_numeric(inv[col], errors="coerce").fillna(0)
    for col in ["소진예산", "유효리드"]:
        if col in mkt.columns:
            mkt[col] = pd.to_numeric(mkt[col], errors="coerce").fillna(0)
    for col in ["노출수", "클릭수"]:
        if col in mkt.columns:
            mkt[col] = pd.to_numeric(mkt[col], errors="coerce")  # NaN 허용 (오프라인)
    if "출고가" in models.columns:
        models["출고가"] = pd.to_numeric(models["출고가"], errors="coerce").fillna(0)
    if "월목표건수" in agency.columns:
        agency["월목표건수"] = pd.to_numeric(agency["월목표건수"], errors="coerce").fillna(0)

    return {"sales": sales, "inv": inv, "mkt": mkt, "models": models, "agency": agency}


# ─────────────────────────────────────────────
# 2. 비즈니스 로직
# ─────────────────────────────────────────────

def compute_kpis(sales: pd.DataFrame, inv: pd.DataFrame) -> dict:
    total = len(sales)
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    n_completed = len(completed)
    rate = n_completed / total * 100 if total > 0 else 0

    total_rev  = completed["단말매출"].sum() if "단말매출" in completed.columns else 0
    total_reb  = completed["리베이트"].sum() if "리베이트" in completed.columns else 0
    rebate_rate = total_reb / total_rev * 100 if total_rev > 0 else 0

    type_counts = {}
    if "가입유형" in completed.columns:
        type_counts = completed["가입유형"].value_counts().to_dict()

    return {
        "total_tx": total,
        "n_completed": n_completed,
        "completion_rate": rate,
        "total_revenue": total_rev,
        "total_rebate": total_reb,
        "rebate_rate": rebate_rate,
        "type_counts": type_counts,
    }


def analyze_inventory(inv: pd.DataFrame, models: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    """대리점×모델 재고 긴급도 분류"""
    if inv.empty:
        return pd.DataFrame()

    # 일평균 판매 = 판매출고 평균 (대리점·모델 기준)
    grp = inv.groupby(["대리점코드", "모델코드"]).agg(
        기말보유량=("기말보유량", "last"),
        일평균판매=("판매출고", "mean"),
        총판매출고=("판매출고", "sum"),
    ).reset_index()

    # 잔여일수
    grp["잔여일수"] = grp.apply(
        lambda r: round(r["기말보유량"] / r["일평균판매"], 1) if r["일평균판매"] > 0 else 999,
        axis=1,
    )

    # 긴급도 분류
    def urgency(d):
        if d <= 2:   return 3, "긴급"
        if d <= 5:   return 2, "주의"
        if d <= 7:   return 1, "관심"
        return 0, "정상"

    grp[["urgency", "재고상태"]] = grp["잔여일수"].apply(
        lambda d: pd.Series(urgency(d))
    )

    # 권장발주량 (긴급/주의: 14일치 목표 기준)
    grp["권장발주"] = grp.apply(
        lambda r: max(0, round(r["일평균판매"] * 14 - r["기말보유량"]))
        if r["urgency"] >= 2 else 0,
        axis=1,
    )

    # 부족예상일
    today = datetime.now()
    grp["부족예상일"] = grp["잔여일수"].apply(
        lambda d: (today + timedelta(days=d)).strftime("%m/%d") if d < 999 else "-"
    )

    # 모델명·대리점명 조인
    if not models.empty and "모델코드" in models.columns:
        grp = grp.merge(
            models[["모델코드", "기기명", "제조사", "세그먼트"]],
            on="모델코드", how="left",
        )
    if not agency.empty and "대리점코드" in agency.columns:
        grp = grp.merge(
            agency[["대리점코드", "상호명", "권역", "점포등급", "월목표건수"]],
            on="대리점코드", how="left",
        )

    return grp.sort_values(["urgency", "잔여일수"], ascending=[False, True])


def compute_regional(sales: pd.DataFrame, inv: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    if agency.empty:
        return pd.DataFrame()

    merged_sales = sales.merge(agency[["대리점코드", "권역", "상호명", "점포등급", "월목표건수"]], on="대리점코드", how="left")
    completed = merged_sales[merged_sales["상태"] == "개통완료"] if "상태" in merged_sales.columns else merged_sales

    agg = completed.groupby("권역").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()

    # 재고
    if not inv.empty:
        inv_agency = inv.merge(agency[["대리점코드", "권역"]], on="대리점코드", how="left")
        inv_agg = inv_agency.groupby("권역")["기말보유량"].sum().reset_index()
        inv_agg.columns = ["권역", "현재재고합계"]
        agg = agg.merge(inv_agg, on="권역", how="left")

    # 대리점 수
    n_agency = agency.groupby("권역").size().reset_index(name="대리점수")
    agg = agg.merge(n_agency, on="권역", how="left")

    return agg.sort_values("매출합계", ascending=False)


def compute_dealer_ranking(sales: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    if sales.empty or agency.empty:
        return pd.DataFrame()

    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    agg = completed.groupby("대리점코드").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()

    agg = agg.merge(agency, on="대리점코드", how="left")
    agg["목표달성률(%)"] = agg.apply(
        lambda r: round(r["판매건수"] / r["월목표건수"] * 100, 1) if r["월목표건수"] > 0 else 0,
        axis=1,
    )
    return agg.sort_values("매출합계", ascending=False).reset_index(drop=True)


def compute_marketing_roi(mkt: pd.DataFrame) -> pd.DataFrame:
    if mkt.empty:
        return pd.DataFrame()

    df = mkt.copy()
    df["CPL"] = df.apply(
        lambda r: round(r["소진예산"] / r["유효리드"]) if r["유효리드"] > 0 else None,
        axis=1,
    )
    df["CTR(%)"] = df.apply(
        lambda r: round(r["클릭수"] / r["노출수"] * 100, 2)
        if pd.notna(r.get("노출수")) and r.get("노출수", 0) > 0 else None,
        axis=1,
    )
    return df


# ─────────────────────────────────────────────
# 3. AI Agent (Claude)
# ─────────────────────────────────────────────

def build_context(kpis: dict, inv_df: pd.DataFrame, regional: pd.DataFrame, mkt_df: pd.DataFrame) -> str:
    type_str = " / ".join(f"{k} {v}건" for k, v in kpis["type_counts"].items())

    model_lines = ""
    if not inv_df.empty and "기기명" in inv_df.columns:
        top_models = inv_df.groupby("기기명")["기말보유량"].sum().nlargest(5)
        model_lines = "\n".join(f"  - {n}: 재고 {v}대" for n, v in top_models.items())

    regional_lines = ""
    if not regional.empty:
        for _, row in regional.head(5).iterrows():
            regional_lines += f"  - {row.get('권역','')}: 판매 {int(row.get('판매건수',0))}건, 매출 {int(row.get('매출합계',0)):,}원\n"

    mkt_lines = ""
    if not mkt_df.empty:
        for _, row in mkt_df.iterrows():
            cpl = f"CPL {int(row['CPL']):,}원" if pd.notna(row.get("CPL")) else "CPL 미집계"
            mkt_lines += f"  - {row.get('유입채널','')}/{row.get('캠페인명','')}: 예산 {int(row.get('소진예산',0)):,}원, 리드 {int(row.get('유효리드',0))}명, {cpl}\n"

    urgent = len(inv_df[inv_df["urgency"] >= 3]) if not inv_df.empty and "urgency" in inv_df.columns else 0
    warning = len(inv_df[inv_df["urgency"] == 2]) if not inv_df.empty and "urgency" in inv_df.columns else 0

    return f"""당신은 한국 이동통신사의 수석 마케팅 전략 컨설턴트입니다.

## 판매 데이터 현황
- 총 거래건수: {kpis['total_tx']}건 (개통완료: {kpis['n_completed']}건, 완료율: {kpis['completion_rate']:.1f}%)
- 총 매출: {int(kpis['total_revenue']):,}원 / 리베이트율: {kpis['rebate_rate']:.1f}%
- 가입유형: {type_str}

## 단말 재고 현황 (상위 5개 모델)
{model_lines or '  데이터 없음'}

## 재고 경보 현황
- 긴급(2일 이내): {urgent}건 / 주의(5일 이내): {warning}건

## 권역별 성과 (상위 5개)
{regional_lines or '  데이터 없음'}

## 마케팅 채널 성과
{mkt_lines or '  데이터 없음'}

답변 원칙:
- 위 수치 데이터를 반드시 인용하여 근거 제시
- 실행 전략 3~5개를 우선순위 순서로 제시
- 각 전략에 예상 효과 및 실행 방법 포함
- 한국어, 600자 이내로 간결하게 작성"""


def ask_claude(system_prompt: str, messages: list[dict]) -> str:
    import anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. `.env` 파일에 키를 추가해 주세요."

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ AI 응답 오류: {e}"


# ─────────────────────────────────────────────
# 4. Plotly 차트 헬퍼
# ─────────────────────────────────────────────

DARK_BG   = "#0D1117"
DARK_PLOT = "#161B22"
DARK_GRID = "#21262D"
DARK_TEXT = "#E6EDF3"
DARK_DIM  = "#8B949E"
ACCENT    = "#58A6FF"
GREEN     = "#3FB950"
RED       = "#F85149"
ORANGE    = "#D29922"
PURPLE    = "#BC8CFF"
CHART_COLORS = [ACCENT, GREEN, ORANGE, RED, PURPLE, "#F778BA", "#79C0FF", "#56D364"]

DARK_LAYOUT = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=DARK_PLOT,
    font=dict(color=DARK_TEXT, family="Noto Sans KR, sans-serif", size=12),
    xaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
    yaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
    margin=dict(t=40, b=40, l=40, r=20),
)


def apply_dark(fig):
    fig.update_layout(**DARK_LAYOUT)
    return fig


def bar_chart(df, x, y, title, color=ACCENT, orientation="v", **kwargs):
    if orientation == "h":
        fig = go.Figure(go.Bar(x=df[y], y=df[x], orientation="h",
                               marker_color=color, **kwargs))
        fig.update_layout(xaxis_title=y, yaxis_title=x)
    else:
        fig = go.Figure(go.Bar(x=df[x], y=df[y], marker_color=color, **kwargs))
        fig.update_layout(xaxis_title=x, yaxis_title=y)
    fig.update_layout(title=title)
    return apply_dark(fig)


def pie_chart(labels, values, title):
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.4,
        marker=dict(colors=CHART_COLORS),
        textfont=dict(color=DARK_TEXT),
    ))
    fig.update_layout(title=title, showlegend=True,
                      legend=dict(font=dict(color=DARK_TEXT)))
    return apply_dark(fig)


# ─────────────────────────────────────────────
# 5. 긴급도 배지 렌더링 헬퍼
# ─────────────────────────────────────────────

STATUS_EMOJI = {3: "🔴 긴급", 2: "🟠 주의", 1: "🔵 관심", 0: "🟢 정상"}


def format_inv_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = []
    for c in ["상호명", "권역", "점포등급", "기기명", "제조사", "세그먼트",
              "기말보유량", "일평균판매", "잔여일수", "재고상태", "권장발주", "부족예상일"]:
        if c in df.columns:
            cols.append(c)

    display = df[cols].copy() if cols else df.copy()
    display["일평균판매"] = display["일평균판매"].round(1) if "일평균판매" in display.columns else display.get("일평균판매", 0)
    return display


# ─────────────────────────────────────────────
# 6. Streamlit 앱 메인
# ─────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Telecom Sales BI Agent",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── 전역 스타일
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .main { background-color: #06080F; }
    .block-container { padding-top: 1.5rem; }
    div[data-testid="metric-container"] {
        background: #0D1117; border: 1px solid #21262D; border-radius: 10px; padding: 14px 18px;
    }
    div[data-testid="metric-container"] label { color: #8B949E !important; font-size: 11px; }
    div[data-testid="metric-container"] div[data-testid="metric-value"] { color: #E6EDF3 !important; }
    .status-critical { color: #F85149; font-weight: 700; }
    .status-warning  { color: #D29922; font-weight: 700; }
    .status-caution  { color: #58A6FF; font-weight: 600; }
    .status-normal   { color: #3FB950; }
    .stChatMessage { background: #0D1117; border: 1px solid #21262D; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

    # ── 사이드바: 파일 업로드
    with st.sidebar:
        st.markdown("## 📱 Telecom Sales BI Agent")
        st.markdown("통신사 휴대폰 판매 전략 · 재고 관리 · 마케팅 의사결정")
        st.divider()

        st.markdown("### 📂 데이터 업로드")
        uploaded = st.file_uploader("Excel 파일 (.xlsx)", type=["xlsx"])

        # 기본 파일 자동 로드
        file_bytes = None
        if uploaded is not None:
            file_bytes = uploaded.read()
            st.success(f"✅ {uploaded.name} 업로드 완료")
        else:
            default_path = os.path.join(os.path.dirname(__file__), "sample_data.xlsx")
            if os.path.exists(default_path):
                with open(default_path, "rb") as f:
                    file_bytes = f.read()
                st.info("📌 sample_data.xlsx 자동 로드 중")
            else:
                st.warning("Excel 파일을 업로드해 주세요.")

        st.divider()
        st.markdown("### ⚙️ 설정")
        api_key_input = st.text_input(
            "Anthropic API Key", type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="AI 전략 Agent 탭 사용 시 필요합니다.",
        )
        if api_key_input:
            os.environ["ANTHROPIC_API_KEY"] = api_key_input

        st.divider()
        st.markdown("<small style='color:#484F58'>© 2026 Telecom BI Agent</small>", unsafe_allow_html=True)

    if file_bytes is None:
        st.title("📱 Telecom Sales BI Agent")
        st.warning("좌측 사이드바에서 Excel 파일을 업로드하거나 sample_data.xlsx를 준비해 주세요.")
        return

    # ── 데이터 로드
    with st.spinner("데이터 분석 중..."):
        data = load_excel(file_bytes)

    sales   = data["sales"]
    inv     = data["inv"]
    mkt     = data["mkt"]
    models  = data["models"]
    agency  = data["agency"]

    # ── 비즈니스 로직
    kpis      = compute_kpis(sales, inv)
    inv_df    = analyze_inventory(inv, models, agency)
    regional  = compute_regional(sales, inv, agency)
    dealer_rk = compute_dealer_ranking(sales, agency)
    mkt_roi   = compute_marketing_roi(mkt)

    # ── 재고 경보 집계
    inv_critical = len(inv_df[inv_df["urgency"] >= 3]) if not inv_df.empty and "urgency" in inv_df.columns else 0
    inv_warning  = len(inv_df[inv_df["urgency"] == 2]) if not inv_df.empty and "urgency" in inv_df.columns else 0
    inv_caution  = len(inv_df[inv_df["urgency"] == 1]) if not inv_df.empty and "urgency" in inv_df.columns else 0
    inv_normal   = len(inv_df[inv_df["urgency"] == 0]) if not inv_df.empty and "urgency" in inv_df.columns else 0

    # ── 헤더
    st.markdown("""
    <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
        <div style="width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#58A6FF,#BC8CFF);
                    display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;color:#06080F;">T</div>
        <div>
            <div style="font-size:18px;font-weight:700;color:#E6EDF3;">Telecom Sales BI Agent</div>
            <div style="font-size:11px;color:#8B949E;">통신사 휴대폰 판매 전략 · 재고 관리 · 마케팅 의사결정</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "◉ 종합 현황",
        "◆ 단말 분석",
        "◈ 재고 현황",
        "◇ 지역·대리점",
        "⚡ AI 전략 Agent",
    ])

    # ════════════════════════════════════════════
    # Tab 1: 종합 현황
    # ════════════════════════════════════════════
    with tab1:
        st.markdown("### 핵심 KPI")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📱 총 거래건수",  f"{kpis['total_tx']}건")
        c2.metric("✅ 개통완료율",   f"{kpis['completion_rate']:.1f}%",
                  f"{kpis['n_completed']}건 완료")
        c3.metric("💰 총 매출",
                  f"{kpis['total_revenue']/1_000_000:.1f}백만원" if kpis['total_revenue'] >= 1_000_000
                  else f"{int(kpis['total_revenue']):,}원")
        c4.metric("📊 리베이트율",   f"{kpis['rebate_rate']:.1f}%",
                  f"{int(kpis['total_rebate']):,}원")
        c5.metric("🚨 재고 경보",    f"긴급 {inv_critical}건",
                  f"주의 {inv_warning}건")

        st.divider()
        col_a, col_b = st.columns(2)

        with col_a:
            # 가입유형 분포
            if kpis["type_counts"]:
                fig = pie_chart(
                    list(kpis["type_counts"].keys()),
                    list(kpis["type_counts"].values()),
                    "가입유형별 분포",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("가입유형 데이터가 없습니다.")

        with col_b:
            # 고객세그먼트별 판매
            if "고객세그먼트" in sales.columns:
                seg_data = sales[sales["상태"] == "개통완료"]["고객세그먼트"].value_counts().reset_index()
                seg_data.columns = ["세그먼트", "건수"]
                fig = bar_chart(seg_data, "세그먼트", "건수",
                                "고객세그먼트별 판매건수", color=ACCENT)
                fig.update_xaxes(tickangle=-20)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("고객세그먼트 데이터가 없습니다.")

        # 요금제별 매출
        if "요금제" in sales.columns and "단말매출" in sales.columns:
            plan_data = (
                sales[sales["상태"] == "개통완료"]
                .groupby("요금제")["단말매출"].sum()
                .reset_index()
                .sort_values("단말매출", ascending=False)
            )
            plan_data.columns = ["요금제", "매출합계"]
            fig = bar_chart(plan_data, "요금제", "매출합계",
                            "요금제별 매출 현황", color=PURPLE)
            st.plotly_chart(fig, use_container_width=True)

        # 대리점별 목표 달성 현황
        if not dealer_rk.empty:
            st.markdown("#### 대리점별 목표 달성 현황")
            display_cols = [c for c in ["상호명", "권역", "점포등급", "판매건수", "월목표건수", "목표달성률(%)", "매출합계"] if c in dealer_rk.columns]
            st.dataframe(
                dealer_rk[display_cols].style.format({
                    "매출합계": "{:,.0f}",
                    "목표달성률(%)": "{:.1f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )

    # ════════════════════════════════════════════
    # Tab 2: 단말 분석
    # ════════════════════════════════════════════
    with tab2:
        st.markdown("### 단말 라인업 성과 분석")

        # 필터
        filter_col1, filter_col2 = st.columns(2)
        maker_options = ["전체"] + sorted(models["제조사"].dropna().unique().tolist()) if not models.empty and "제조사" in models.columns else ["전체"]
        seg_options   = ["전체"] + sorted(models["세그먼트"].dropna().unique().tolist()) if not models.empty and "세그먼트" in models.columns else ["전체"]
        sel_maker = filter_col1.selectbox("제조사", maker_options)
        sel_seg   = filter_col2.selectbox("세그먼트", seg_options)

        # 단말별 판매 집계
        if not sales.empty and "모델코드" in sales.columns:
            completed_sales = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
            model_agg = completed_sales.groupby("모델코드").agg(
                판매건수=("거래ID", "count"),
                매출합계=("단말매출", "sum"),
                리베이트합계=("리베이트", "sum"),
            ).reset_index()

            model_detail = models.merge(model_agg, on="모델코드", how="left").fillna(0)
            model_detail["순이익"] = model_detail["매출합계"] - model_detail["리베이트합계"]

            # 필터 적용
            if sel_maker != "전체" and "제조사" in model_detail.columns:
                model_detail = model_detail[model_detail["제조사"] == sel_maker]
            if sel_seg != "전체" and "세그먼트" in model_detail.columns:
                model_detail = model_detail[model_detail["세그먼트"] == sel_seg]

            if not model_detail.empty:
                col_a, col_b = st.columns(2)

                with col_a:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=model_detail["기기명"],
                        y=model_detail["판매건수"],
                        name="판매건수",
                        marker_color=ACCENT,
                        yaxis="y",
                    ))
                    fig.add_trace(go.Scatter(
                        x=model_detail["기기명"],
                        y=model_detail["출고가"] / 10000,
                        name="출고가(만원)",
                        mode="lines+markers",
                        marker=dict(color=ORANGE, size=8),
                        line=dict(color=ORANGE, width=2),
                        yaxis="y2",
                    ))
                    fig.update_layout(
                        title="단말별 판매건수 & 출고가",
                        yaxis=dict(title="판매건수", gridcolor=DARK_GRID, color=DARK_DIM),
                        yaxis2=dict(title="출고가(만원)", overlaying="y", side="right",
                                    gridcolor=DARK_GRID, color=ORANGE),
                        legend=dict(font=dict(color=DARK_TEXT)),
                        xaxis=dict(tickangle=-20),
                        **{k: v for k, v in DARK_LAYOUT.items() if k not in ["yaxis", "xaxis"]},
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_b:
                    seg_rev = model_detail.groupby("세그먼트")["매출합계"].sum().reset_index()
                    if not seg_rev.empty and seg_rev["매출합계"].sum() > 0:
                        fig = pie_chart(seg_rev["세그먼트"], seg_rev["매출합계"], "세그먼트별 매출 비중")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("매출 데이터가 없습니다.")

                # 단말 상세 테이블
                st.markdown("#### 단말별 상세 현황")
                display_cols = [c for c in ["기기명", "제조사", "세그먼트", "네트워크", "출고가", "판매건수", "매출합계", "리베이트합계", "순이익"] if c in model_detail.columns]
                st.dataframe(
                    model_detail[display_cols].sort_values("판매건수", ascending=False).style.format({
                        "출고가": "{:,.0f}",
                        "매출합계": "{:,.0f}",
                        "리베이트합계": "{:,.0f}",
                        "순이익": "{:,.0f}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("선택한 조건에 해당하는 단말이 없습니다.")
        else:
            st.warning("판매 데이터가 없습니다.")

    # ════════════════════════════════════════════
    # Tab 3: 재고 현황
    # ════════════════════════════════════════════
    with tab3:
        st.markdown("### 재고 현황 및 경보")

        # KPI 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 전국 총 재고",
                  f"{int(inv['기말보유량'].sum()):,}대" if not inv.empty and "기말보유량" in inv.columns else "N/A")
        c2.metric("🔴 긴급 경보", f"{inv_critical}건", "2일 이내 소진")
        c3.metric("🟠 주의 경보", f"{inv_warning}건", "5일 이내 소진")
        c4.metric("🟢 정상",      f"{inv_normal}건")

        st.divider()

        if not inv_df.empty:
            # 필터
            fc1, fc2, fc3 = st.columns(3)
            region_options = ["전체"] + sorted(inv_df["권역"].dropna().unique().tolist()) if "권역" in inv_df.columns else ["전체"]
            grade_options  = ["전체"] + sorted(inv_df["점포등급"].dropna().unique().tolist()) if "점포등급" in inv_df.columns else ["전체"]
            status_options = ["전체", "🔴 긴급", "🟠 주의", "🔵 관심", "🟢 정상"]

            sel_region = fc1.selectbox("권역", region_options, key="inv_region")
            sel_grade  = fc2.selectbox("점포등급", grade_options, key="inv_grade")
            sel_status = fc3.selectbox("재고상태", status_options, key="inv_status")

            filtered_inv = inv_df.copy()
            if sel_region != "전체" and "권역" in filtered_inv.columns:
                filtered_inv = filtered_inv[filtered_inv["권역"] == sel_region]
            if sel_grade != "전체" and "점포등급" in filtered_inv.columns:
                filtered_inv = filtered_inv[filtered_inv["점포등급"] == sel_grade]
            if sel_status != "전체":
                status_map = {"🔴 긴급": "긴급", "🟠 주의": "주의", "🔵 관심": "관심", "🟢 정상": "정상"}
                target = status_map.get(sel_status, "")
                if "재고상태" in filtered_inv.columns:
                    filtered_inv = filtered_inv[filtered_inv["재고상태"] == target]

            st.markdown(f"#### 재고 현황 테이블 ({len(filtered_inv)}건)")
            display = format_inv_table(filtered_inv)
            st.dataframe(
                display.style.apply(
                    lambda col: [
                        "color: #F85149" if str(v) == "긴급" else
                        "color: #D29922" if str(v) == "주의" else
                        "color: #58A6FF" if str(v) == "관심" else
                        "color: #3FB950" if str(v) == "정상" else ""
                        for v in col
                    ] if col.name == "재고상태" else [""] * len(col),
                    axis=0,
                ).format({"일평균판매": "{:.1f}", "잔여일수": "{:.1f}", "권장발주": "{:.0f}"}),
                use_container_width=True,
                hide_index=True,
            )

            # 발주 계획 섹션
            st.divider()
            st.markdown("#### 📦 긴급 발주 계획")
            urgent_orders = inv_df[inv_df["urgency"] >= 2][["상호명", "기기명", "기말보유량", "일평균판매", "잔여일수", "권장발주", "재고상태"]]
            if not urgent_orders.empty:
                st.warning(f"총 {len(urgent_orders)}건의 긴급/주의 발주가 필요합니다.")
                st.dataframe(
                    urgent_orders.style.format({
                        "일평균판매": "{:.1f}",
                        "잔여일수":   "{:.1f}",
                        "권장발주":   "{:.0f}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
                total_order = int(urgent_orders["권장발주"].sum())
                st.info(f"총 권장 발주 수량: **{total_order:,}대**")
            else:
                st.success("긴급·주의 재고 경보가 없습니다.")
        else:
            st.warning("재고 데이터가 없습니다.")

    # ════════════════════════════════════════════
    # Tab 4: 지역·대리점
    # ════════════════════════════════════════════
    with tab4:
        st.markdown("### 지역·대리점 분석")

        if not regional.empty:
            col_a, col_b = st.columns(2)

            with col_a:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=regional["권역"], x=regional["판매건수"],
                    name="판매건수", orientation="h",
                    marker_color=ACCENT,
                ))
                if "현재재고합계" in regional.columns:
                    fig.add_trace(go.Bar(
                        y=regional["권역"], x=regional["현재재고합계"],
                        name="현재재고", orientation="h",
                        marker_color=ORANGE,
                    ))
                fig.update_layout(
                    title="권역별 판매건수 & 재고",
                    barmode="group",
                    **{k: v for k, v in DARK_LAYOUT.items()},
                    xaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                    yaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                    legend=dict(font=dict(color=DARK_TEXT)),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                fig = go.Figure(go.Bar(
                    y=regional["권역"],
                    x=regional["매출합계"],
                    orientation="h",
                    marker=dict(
                        color=regional["매출합계"],
                        colorscale=[[0, DARK_GRID], [1, ACCENT]],
                    ),
                ))
                fig.update_layout(title="권역별 매출 현황", **DARK_LAYOUT,
                                  xaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                                  yaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                                  )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("지역 데이터가 없습니다.")

        # 마케팅 채널 ROI
        if not mkt_roi.empty:
            st.markdown("#### 마케팅 채널 성과")
            cpl_data = mkt_roi.dropna(subset=["CPL"])
            if not cpl_data.empty:
                fig = go.Figure(go.Bar(
                    x=cpl_data["유입채널"],
                    y=cpl_data["CPL"],
                    marker_color=[GREEN if v == cpl_data["CPL"].min() else RED for v in cpl_data["CPL"]],
                    text=[f"CPL: {int(v):,}원" for v in cpl_data["CPL"]],
                    textposition="outside",
                ))
                fig.update_layout(
                    title="채널별 CPL (낮을수록 효율적)",
                    yaxis_title="CPL (원)",
                    **DARK_LAYOUT,
                    xaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                    yaxis=dict(gridcolor=DARK_GRID, linecolor=DARK_GRID, tickfont=dict(color=DARK_DIM)),
                )
                st.plotly_chart(fig, use_container_width=True)

            display_mkt = mkt_roi[["유입채널", "캠페인명", "타겟팅", "소진예산", "유효리드", "CPL", "CTR(%)"]].copy()
            st.dataframe(
                display_mkt.style.format({
                    "소진예산": "{:,.0f}",
                    "CPL": lambda v: f"{int(v):,}" if pd.notna(v) else "-",
                    "CTR(%)": lambda v: f"{v:.2f}%" if pd.notna(v) else "-",
                }),
                use_container_width=True,
                hide_index=True,
            )

        # 대리점 랭킹
        if not dealer_rk.empty:
            st.markdown("#### 대리점 성과 랭킹")
            display_cols = [c for c in ["상호명", "권역", "점포등급", "판매건수", "매출합계", "리베이트합계", "목표달성률(%)"] if c in dealer_rk.columns]
            ranked = dealer_rk[display_cols].reset_index(drop=True)
            ranked.index += 1
            st.dataframe(
                ranked.style.format({
                    "매출합계": "{:,.0f}",
                    "리베이트합계": "{:,.0f}",
                    "목표달성률(%)": "{:.1f}%",
                }),
                use_container_width=True,
            )

    # ════════════════════════════════════════════
    # Tab 5: AI 전략 Agent
    # ════════════════════════════════════════════
    with tab5:
        system_ctx = build_context(kpis, inv_df, regional, mkt_roi)

        col_chat, col_info = st.columns([2, 1])

        with col_info:
            st.markdown("### 📊 핵심 지표 요약")
            st.metric("총 거래건수",   f"{kpis['total_tx']}건")
            st.metric("개통완료율",    f"{kpis['completion_rate']:.1f}%")
            st.metric("총 매출",
                      f"{kpis['total_revenue']/1_000_000:.1f}백만원" if kpis['total_revenue'] >= 1_000_000
                      else f"{int(kpis['total_revenue']):,}원")
            st.metric("재고 긴급 경보", f"{inv_critical}건")

            st.divider()
            st.markdown("### 💡 추천 질문")
            suggested = [
                "번호이동 점유율 확대 전략은?",
                "긴급 재고 대리점 발주 우선순위 어떻게 정해야 하나요?",
                "마케팅 채널별 ROI 개선 방안을 알려주세요.",
                "플래그십 단말 판촉 전략을 제안해 주세요.",
                "리베이트 비율 최적화 방안은?",
                "신규가입 고객 유입을 늘리려면 어떻게 해야 하나요?",
                "지역별 매출 편차를 줄이기 위한 전략은?",
                "기기변경 고객 리텐션 전략을 알려주세요.",
            ]
            for q in suggested:
                if st.button(q, key=f"sq_{q}", use_container_width=True):
                    st.session_state["ai_input"] = q

        with col_chat:
            st.markdown("### ⚡ AI 전략 분석 Agent")
            st.caption("통신사 판매 데이터 기반 전략 질의 & 추천 — Claude Sonnet 구동")

            # 채팅 기록 초기화
            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []

            # 채팅 표시
            chat_container = st.container(height=420)
            with chat_container:
                if not st.session_state["chat_history"]:
                    st.markdown("""
                    <div style="text-align:center;padding:60px 20px;color:#8B949E;">
                        <div style="font-size:48px;margin-bottom:12px;">🤖</div>
                        <div style="font-size:14px;">통신사 판매 전략 AI Agent</div>
                        <div style="font-size:11px;margin-top:8px;line-height:1.8;">
                            판매 데이터 기반 전략적 질문을 해보세요.<br>
                            우측 추천 질문 버튼을 클릭하거나 직접 입력하세요.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                for msg in st.session_state["chat_history"]:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

            # 입력창
            preset = st.session_state.pop("ai_input", "")
            user_input = st.chat_input("전략 질문을 입력하세요...", key="chat_input")

            # 추천 질문 버튼으로 입력된 경우 처리
            query = user_input or preset
            if query:
                st.session_state["chat_history"].append({"role": "user", "content": query})

                api_key = os.getenv("ANTHROPIC_API_KEY", "")
                if not api_key:
                    answer = "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다. 좌측 사이드바에서 API 키를 입력해 주세요."
                else:
                    with st.spinner("전략 분석 중..."):
                        # system_ctx를 제외한 순수 메시지 히스토리
                        messages = [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state["chat_history"]
                        ]
                        answer = ask_claude(system_ctx, messages)

                st.session_state["chat_history"].append({"role": "assistant", "content": answer})
                st.rerun()

            # 대화 초기화 버튼
            if st.session_state["chat_history"]:
                if st.button("🗑️ 대화 초기화", use_container_width=True):
                    st.session_state["chat_history"] = []
                    st.rerun()

            # 비즈니스 로직 규칙 표시
            st.divider()
            st.markdown("#### 📐 재고 판단 규칙")
            rules = [
                ("R1", RED,    "잔여일수 ≤ 2일 → 긴급 발주 (14일치)"),
                ("R2", ORANGE, "잔여일수 ≤ 5일 → 주의 (발주 검토)"),
                ("R3", ACCENT, "잔여일수 ≤ 7일 → 관심 (모니터링)"),
                ("R4", GREEN,  "판매 추세 급증 → 일평균 상향 재계산"),
                ("R5", PURPLE, "S등급 대리점 → 발주 우선순위 부여"),
            ]
            for code, color, text in rules:
                st.markdown(
                    f'<span style="color:{color};font-weight:700;">{code}</span> '
                    f'<span style="color:#8B949E;font-size:13px;">{text}</span>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
