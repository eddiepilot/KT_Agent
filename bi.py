"""
Telecom Sales BI Agent — bi.py
통신사 판매전략 수립 에이전트 | generated_data.xlsx 기반
실행: streamlit run bi.py
"""

import os
import io
import copy
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════
# 0. 디자인 토큰 (라이트 파스텔 테마)
# ═══════════════════════════════════════════════════
BG      = "#F0F4F8"          # 연한 블루-그레이 배경
CARD    = "#FFFFFF"          # 카드: 흰색
CARD2   = "#F8FAFC"          # 보조 카드: 극연한 회색
BORDER  = "#CBD5E1"          # 테두리: 소프트 그레이
ACCENT  = "#4F7EF7"          # 포인트: 코발트 블루
GREEN   = "#16A34A"          # 성공: 에메랄드
RED     = "#DC2626"          # 경고: 소프트 레드
ORANGE  = "#D97706"          # 주의: 앰버
PURPLE  = "#7C3AED"          # 보조: 바이올렛
CYAN    = "#0891B2"          # 정보: 틸
TEXT    = "#1E293B"          # 본문: 다크 슬레이트 (가독성 최대)
DIM     = "#475569"          # 보조 텍스트: 미디엄 슬레이트
MUTED   = "#94A3B8"          # 흐린 텍스트: 라이트 슬레이트
COLORS  = [ACCENT, GREEN, ORANGE, RED, PURPLE, CYAN,
           "#EC4899", "#0EA5E9", "#84CC16", "#F97316"]

# ── Altair 공통 테마 설정
_ALT_FONT  = "Noto Sans KR, sans-serif"
_ALT_SCALE = alt.Scale(range=COLORS)

def _alt_theme() -> dict:
    """Altair 공통 설정 딕셔너리"""
    return dict(
        config=alt.Config(
            background=CARD,
            view=alt.ViewConfig(stroke="transparent"),
            axis=alt.AxisConfig(
                labelFont=_ALT_FONT, labelColor=DIM, labelFontSize=11,
                titleFont=_ALT_FONT, titleColor=DIM, titleFontSize=11,
                gridColor=BORDER, gridOpacity=0.6, domainColor=BORDER,
                tickColor=BORDER,
            ),
            legend=alt.LegendConfig(
                labelFont=_ALT_FONT, labelColor=DIM, labelFontSize=11,
                titleFont=_ALT_FONT, titleColor=DIM, titleFontSize=11,
            ),
            title=alt.TitleConfig(
                font=_ALT_FONT, color=TEXT, fontSize=13, fontWeight="bold", anchor="start",
            ),
        )
    )


def _tooltip_fmt(fields: list[dict]) -> list:
    return [alt.Tooltip(**f) for f in fields]


def ac(chart, height: int = 300):
    """st.altair_chart 래퍼 — 테마 적용"""
    st.altair_chart(chart.properties(height=height), use_container_width=True)


# ═══════════════════════════════════════════════════
# 1. 데이터 로더
# ═══════════════════════════════════════════════════
SHEET_SALES = "세일즈_원장 (Sales_Transactions)"
SHEET_INV   = "일일_재고흐름 (Inventory_Log)"
SHEET_MODEL = "단말_마스터 (Master_Model)"
SHEET_AGN   = "유통망_마스터 (Master_Agency)"
SHEET_WH    = "물류창고_재고현황 (Warehouse_Stock)"


@st.cache_data(show_spinner=False)
def load_excel(raw: bytes) -> dict:
    xls = pd.ExcelFile(io.BytesIO(raw))

    def parse(sheet):
        df = xls.parse(sheet)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    sales  = parse(SHEET_SALES)
    inv    = parse(SHEET_INV)
    model  = parse(SHEET_MODEL)
    agency = parse(SHEET_AGN)
    wh     = parse(SHEET_WH) if SHEET_WH in xls.sheet_names else pd.DataFrame()

    # ── 컬럼 정규화
    sales  = sales.rename(columns={"단말매출(원)": "단말매출", "리베이트(원)": "리베이트"})
    model  = model.rename(columns={"펫네임(기기명)": "기기명", "출고가(원)": "출고가"})
    if not wh.empty:
        wh = wh.rename(columns={
            "현재재고(대)": "현재재고", "가용재고(대)": "가용재고",
            "재고금액(원)": "재고금액", "금일입고(대)": "금일입고",
            "금일출고(대)": "금일출고", "재주문기준(대)": "재주문기준",
            "펫네임(기기명)": "기기명",
        })

    # ── 숫자형 변환
    for c in ["단말매출", "리베이트"]:
        if c in sales.columns:
            sales[c] = pd.to_numeric(sales[c], errors="coerce").fillna(0)
    for c in ["판매출고", "재고현황"]:
        if c in inv.columns:
            inv[c] = pd.to_numeric(inv[c], errors="coerce").fillna(0)
    if "출고가" in model.columns:
        model["출고가"] = pd.to_numeric(model["출고가"], errors="coerce").fillna(0)
    if "월목표건수" in agency.columns:
        agency["월목표건수"] = pd.to_numeric(agency["월목표건수"], errors="coerce").fillna(0)
    if not wh.empty:
        for c in ["현재재고", "가용재고", "재고금액", "금일입고", "금일출고", "재주문기준"]:
            if c in wh.columns:
                wh[c] = pd.to_numeric(wh[c], errors="coerce").fillna(0)

    # ── datetime 변환
    sales["거래일시"] = pd.to_datetime(sales["거래일시"], errors="coerce")
    inv["기준일"]    = pd.to_datetime(inv["기준일"], errors="coerce")

    return {"sales": sales, "inv": inv, "model": model, "agency": agency, "wh": wh}


# ═══════════════════════════════════════════════════
# 2. 비즈니스 로직
# ═══════════════════════════════════════════════════

def compute_kpis(sales: pd.DataFrame) -> dict:
    """일간 및 누적 KPI"""
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    latest_date = sales["거래일시"].dt.date.max() if not sales.empty else None

    day_df    = completed[completed["거래일시"].dt.date == latest_date] if latest_date else pd.DataFrame()
    day_count = len(day_df)
    day_rev   = int(day_df["단말매출"].sum()) if not day_df.empty else 0
    total_rev = int(completed["단말매출"].sum())
    total_cnt = len(completed)
    arpu      = round(total_rev / total_cnt) if total_cnt > 0 else 0
    cancelled = len(sales[sales["상태"].isin(["정지", "14일철회"])]) if "상태" in sales.columns else 0
    net_add   = total_cnt - cancelled

    return {
        "day_count": day_count, "day_rev": day_rev,
        "arpu": arpu, "net_add": net_add,
        "total_rev": total_rev, "total_cnt": total_cnt,
        "latest_date": str(latest_date) if latest_date else "N/A",
    }


def compute_monthly_trend(sales: pd.DataFrame) -> pd.DataFrame:
    if sales.empty:
        return pd.DataFrame()
    df = sales.copy()
    df["월"] = df["거래일시"].dt.to_period("M").astype(str)
    completed = df[df["상태"] == "개통완료"] if "상태" in df.columns else df
    agg = completed.groupby("월").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
    ).reset_index()
    if "가입유형" in completed.columns:
        for t in ["신규가입", "번호이동", "기기변경"]:
            sub = completed[completed["가입유형"] == t].groupby("월")["거래ID"].count()
            agg[t] = agg["월"].map(sub).fillna(0).astype(int)
    return agg.sort_values("월")


def compute_brand_share(sales: pd.DataFrame, model: pd.DataFrame) -> pd.DataFrame:
    if sales.empty or model.empty:
        return pd.DataFrame()
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    merged = completed.merge(model[["모델코드", "제조사"]], on="모델코드", how="left")
    return merged.groupby("제조사")["거래ID"].count().reset_index(name="판매건수")


def compute_regional(sales: pd.DataFrame, inv: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    if sales.empty or agency.empty:
        return pd.DataFrame()
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    merged = completed.merge(
        agency[["대리점코드", "권역", "상호명", "점포등급", "월목표건수"]],
        on="대리점코드", how="left",
    )
    agg = merged.groupby("권역").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()
    if not inv.empty:
        inv_m = inv.merge(agency[["대리점코드", "권역"]], on="대리점코드", how="left")
        inv_a = inv_m.groupby("권역")["재고현황"].sum().reset_index(name="재고합계")
        agg = agg.merge(inv_a, on="권역", how="left").fillna(0)
    n_agn = agency.groupby("권역").size().reset_index(name="대리점수")
    agg = agg.merge(n_agn, on="권역", how="left")
    return agg.sort_values("매출합계", ascending=False)


def analyze_inventory(inv: pd.DataFrame, model: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    """대리점×모델 잔여일수·긴급도 계산"""
    if inv.empty:
        return pd.DataFrame()
    grp = inv.groupby(["대리점코드", "모델코드"]).agg(
        재고현황=("재고현황", "last"),
        일평균판매=("판매출고", "mean"),
        총판매=("판매출고", "sum"),
    ).reset_index()
    grp["잔여일수"] = grp.apply(
        lambda r: round(r["재고현황"] / r["일평균판매"], 1) if r["일평균판매"] > 0 else 999.0,
        axis=1,
    )

    def _urg(d):
        if d <= 2: return 3, "긴급"
        if d <= 5: return 2, "주의"
        if d <= 7: return 1, "관심"
        return 0, "정상"

    grp[["urgency", "재고상태"]] = grp["잔여일수"].apply(lambda d: pd.Series(_urg(d)))
    grp["권장발주"] = grp.apply(
        lambda r: max(0, round(r["일평균판매"] * 14 - r["재고현황"])) if r["urgency"] >= 2 else 0,
        axis=1,
    )
    today = datetime.now()
    grp["부족예상일"] = grp["잔여일수"].apply(
        lambda d: (today + timedelta(days=float(d))).strftime("%m/%d") if d < 999 else "충분"
    )
    if not model.empty:
        grp = grp.merge(model[["모델코드", "기기명", "제조사", "세그먼트"]], on="모델코드", how="left")
    if not agency.empty:
        grp = grp.merge(
            agency[["대리점코드", "상호명", "권역", "점포등급", "월목표건수"]],
            on="대리점코드", how="left",
        )
    return grp


def apply_priority(inv_df: pd.DataFrame, rules: list) -> pd.DataFrame:
    """비즈니스 규칙 → 우선순위 점수 계산 후 정렬"""
    if inv_df.empty:
        return inv_df
    df = inv_df.copy()
    df["우선순위점수"] = 0.0
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        ctype = rule["condition"]
        try:
            if ctype == "days_lte":
                mask = df["잔여일수"] <= float(rule["threshold"])
                df.loc[mask, "우선순위점수"] += float(rule["score"])
            elif ctype == "grade_eq" and "점포등급" in df.columns:
                mask = df["점포등급"] == str(rule["threshold"])
                df.loc[mask, "우선순위점수"] += float(rule["score"])
            elif ctype == "segment_eq" and "세그먼트" in df.columns:
                mask = df["세그먼트"] == str(rule["threshold"])
                df.loc[mask, "우선순위점수"] += float(rule["score"])
            elif ctype == "perf_grade_eq" and "성과등급" in df.columns:
                mask = df["성과등급"] == str(rule["threshold"])
                df.loc[mask, "우선순위점수"] += float(rule["score"])
        except Exception:
            pass
    return df.sort_values(
        ["우선순위점수", "urgency", "잔여일수"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def compute_device_perf(
    sales: pd.DataFrame, inv: pd.DataFrame, model: pd.DataFrame,
    date_from=None, date_to=None,
) -> pd.DataFrame:
    if sales.empty or model.empty:
        return pd.DataFrame()
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    if date_from:
        completed = completed[completed["거래일시"].dt.date >= date_from]
    if date_to:
        completed = completed[completed["거래일시"].dt.date <= date_to]
    agg = completed.groupby("모델코드").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()
    detail = model.merge(agg, on="모델코드", how="left").fillna(0)
    detail["순이익"]   = detail["매출합계"] - detail["리베이트합계"]
    detail["마진율(%)"] = detail.apply(
        lambda r: round(r["순이익"] / r["매출합계"] * 100, 1) if r["매출합계"] > 0 else 0.0,
        axis=1,
    )
    if not inv.empty:
        stock = inv.groupby("모델코드")["재고현황"].sum().reset_index(name="전국재고")
        detail = detail.merge(stock, on="모델코드", how="left").fillna(0)
    days = (date_to - date_from).days + 1 if date_from and date_to else 30
    detail["일평균"]    = (detail["판매건수"] / max(days, 1)).round(1)
    detail["월매출추정"] = (detail["매출합계"] / max(days, 1) * 30).astype(int)
    return detail.sort_values("판매건수", ascending=False)


def compute_dealer_ranking(sales: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    if sales.empty or agency.empty:
        return pd.DataFrame()
    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    agg = completed.groupby("대리점코드").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()
    merged = agg.merge(agency, on="대리점코드", how="left")
    merged["목표달성률(%)"] = merged.apply(
        lambda r: round(r["판매건수"] / r["월목표건수"] * 100, 1) if r.get("월목표건수", 0) > 0 else 0.0,
        axis=1,
    )
    return merged.sort_values("매출합계", ascending=False).reset_index(drop=True)


def compute_dealer_score(sales: pd.DataFrame, agency: pd.DataFrame) -> pd.DataFrame:
    """통계 분석: Z-score 복합지표로 대리점 성과 점수 및 S/A/B 등급 산출

    지표 (가중치):
      - 판매건수    35%  · 매출합계      35%
      - 목표달성률  20%  · 리베이트효율  10%
    등급 기준:
      - S: 상위 20% (성과점수 ≥ 80백분위)
      - A: 상위 50% (성과점수 ≥ 50백분위)
      - B: 나머지
    """
    if sales.empty or agency.empty:
        return pd.DataFrame()

    completed = sales[sales["상태"] == "개통완료"] if "상태" in sales.columns else sales
    agg = completed.groupby("대리점코드").agg(
        판매건수=("거래ID", "count"),
        매출합계=("단말매출", "sum"),
        리베이트합계=("리베이트", "sum"),
    ).reset_index()

    merged = agg.merge(
        agency[["대리점코드", "상호명", "권역", "점포등급", "월목표건수"]],
        on="대리점코드", how="left",
    )
    merged["목표달성률"] = merged.apply(
        lambda r: r["판매건수"] / r["월목표건수"] if r.get("월목표건수", 0) > 0 else 0.0,
        axis=1,
    )
    merged["리베이트효율"] = merged.apply(
        lambda r: 1.0 - (r["리베이트합계"] / r["매출합계"]) if r["매출합계"] > 0 else 0.0,
        axis=1,
    )

    metrics = ["판매건수", "매출합계", "목표달성률", "리베이트효율"]
    weights = [0.35,      0.35,      0.20,       0.10]

    df = merged.copy()
    df["복합점수"] = 0.0
    for col, w in zip(metrics, weights):
        vals = df[col].values.astype(float)
        std  = vals.std()
        z    = (vals - vals.mean()) / std if std > 0 else np.zeros_like(vals)
        df["복합점수"] += z * w

    mn, mx = df["복합점수"].min(), df["복합점수"].max()
    df["성과점수"] = ((df["복합점수"] - mn) / (mx - mn) * 100).round(1) if mx > mn else 50.0

    p80 = df["성과점수"].quantile(0.80)
    p50 = df["성과점수"].quantile(0.50)
    df["성과등급"] = df["성과점수"].apply(
        lambda s: "S" if s >= p80 else ("A" if s >= p50 else "B")
    )

    return df.sort_values("성과점수", ascending=False).reset_index(drop=True)


# ═══════════════════════════════════════════════════
# 3. 기본 비즈니스 규칙
# ═══════════════════════════════════════════════════
DEFAULT_RULES = [
    {"id": "R1", "name": "잔여일수 2일 이하 → 긴급 발주",    "condition": "days_lte",  "threshold": "2",      "score": 100, "enabled": True},
    {"id": "R2", "name": "잔여일수 5일 이하 → 발주 검토",    "condition": "days_lte",  "threshold": "5",      "score": 50,  "enabled": True},
    {"id": "R3", "name": "S등급 대리점 → 발주 우선순위",     "condition": "grade_eq",  "threshold": "S",      "score": 30,  "enabled": True},
    {"id": "R4", "name": "플래그십 재고 부족 → 최우선 배정", "condition": "segment_eq","threshold": "플래그십", "score": 40,  "enabled": True},
]

CONDITION_LABELS = {
    "days_lte":      "잔여일수 ≤ N일",
    "grade_eq":      "점포등급 = 값",
    "segment_eq":    "세그먼트 = 값",
    "perf_grade_eq": "통계성과등급 = 값",
}


# ═══════════════════════════════════════════════════
# 4. AI Agent (Gemini)
# ═══════════════════════════════════════════════════

def build_context(kpis: dict, inv_df: pd.DataFrame, regional: pd.DataFrame, rules: list) -> str:
    inv_critical = int(len(inv_df[inv_df["urgency"] >= 3])) if not inv_df.empty and "urgency" in inv_df.columns else 0
    inv_warning  = int(len(inv_df[inv_df["urgency"] == 2])) if not inv_df.empty and "urgency" in inv_df.columns else 0

    regional_lines = ""
    if not regional.empty:
        for _, r in regional.head(5).iterrows():
            regional_lines += f"  - {r.get('권역','')}: 판매 {int(r.get('판매건수',0))}건, 매출 {int(r.get('매출합계',0)):,}원\n"

    rules_lines = "\n".join(
        f"  [{r['id']}] {r['name']} (점수:{r['score']}, {'활성' if r['enabled'] else '비활성'})"
        for r in rules
    )

    return f"""당신은 한국 이동통신사의 수석 마케팅 전략 컨설턴트입니다.

## 판매 현황 ({kpis['latest_date']} 기준)
- 일 판매량: {kpis['day_count']}건 / 일 매출: {kpis['day_rev']:,}원
- ARPU: {kpis['arpu']:,}원 / 순증 가입자: {kpis['net_add']}명
- 누적 총 매출: {kpis['total_rev']:,}원 ({kpis['total_cnt']}건 개통완료)

## 재고 경보
- 긴급(2일 이내): {inv_critical}건 / 주의(5일 이내): {inv_warning}건

## 권역별 성과 (상위 5개)
{regional_lines or '  데이터 없음'}

## 활성 비즈니스 규칙
{rules_lines or '  규칙 없음'}

답변 원칙:
- 수치 근거를 반드시 인용하여 전략 제시
- 실행 전략 3~5개를 우선순위 순서로 제시
- 각 전략에 예상 효과와 실행 방법 포함
- 한국어, 600자 이내로 간결하게 작성"""


def stream_gemini(system_prompt: str, messages: list):
    """Gemini 스트리밍 제너레이터 (st.write_stream 호환)"""
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        yield "⚠️ GEMINI_API_KEY가 설정되지 않았습니다. 좌측 사이드바에서 API 키를 입력해 주세요."
        return
    genai.configure(api_key=api_key)
    gmodel = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt,
    )
    history = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
        for m in messages[:-1]
    ]
    last_msg = messages[-1]["content"] if messages else ""
    try:
        chat = gmodel.start_chat(history=history)
        for chunk in chat.send_message(last_msg, stream=True):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"❌ AI 응답 오류: {e}"


# ═══════════════════════════════════════════════════
# 5. 차트 헬퍼
# ═══════════════════════════════════════════════════
STATUS_COLOR = {"긴급": RED, "주의": ORANGE, "관심": ACCENT, "정상": GREEN}
STATUS_ICON  = {"긴급": "🔴", "주의": "🟠", "관심": "🔵", "정상": "🟢"}


def alt_donut(labels: list, values: list, title: str = "", height: int = 280):
    """Altair 도넛 차트"""
    df = pd.DataFrame({"항목": [str(l) for l in labels], "값": [int(v) for v in values]})
    base = (
        alt.Chart(df, title=title)
        .mark_arc(innerRadius=55, outerRadius=100, stroke="#fff", strokeWidth=2, cornerRadius=5)
        .encode(
            theta=alt.Theta("값:Q"),
            color=alt.Color("항목:N", scale=_ALT_SCALE, legend=alt.Legend(orient="right")),
            tooltip=[alt.Tooltip("항목:N", title="항목"),
                     alt.Tooltip("값:Q", title="건수", format=",")],
        )
    )
    ac(base, height=height)


def alt_bar_v(df: pd.DataFrame, x: str, y: str, title: str = "",
              color: str = ACCENT, height: int = 300):
    """Altair 단일 수직 바 (라운드 코너 + 레이블)"""
    bars = (
        alt.Chart(df, title=title)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=color)
        .encode(
            x=alt.X(f"{x}:N", sort=None, axis=alt.Axis(labelAngle=-18)),
            y=alt.Y(f"{y}:Q"),
            tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{y}:Q", format=",")],
        )
    )
    labels = bars.mark_text(dy=-6, fontSize=10, color=DIM).encode(text=alt.Text(f"{y}:Q", format=","))
    ac(bars + labels, height=height)


def alt_bar_grouped(df: pd.DataFrame, x: str, series: list[str],
                    title: str = "", height: int = 300):
    """Altair 그룹 바 (멀티 시리즈)"""
    df_m = df.melt(id_vars=[x], value_vars=series, var_name="구분", value_name="값")
    chart = (
        alt.Chart(df_m, title=title)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{x}:N", sort=None, axis=alt.Axis(labelAngle=-18)),
            y=alt.Y("값:Q"),
            color=alt.Color("구분:N", scale=_ALT_SCALE),
            xOffset="구분:N",
            tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip("구분:N"), alt.Tooltip("값:Q", format=",")],
        )
    )
    ac(chart, height=height)


def alt_bar_h(df: pd.DataFrame, y: str, x: str, title: str = "", height: int = 300):
    """Altair 수평 바 (그라데이션 효과 → 색상 인코딩)"""
    chart = (
        alt.Chart(df, title=title)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
        .encode(
            y=alt.Y(f"{y}:N", sort="-x", axis=alt.Axis(labelLimit=120)),
            x=alt.X(f"{x}:Q"),
            color=alt.Color(f"{x}:Q", scale=alt.Scale(scheme="blues"), legend=None),
            tooltip=[alt.Tooltip(f"{y}:N"), alt.Tooltip(f"{x}:Q", format=",")],
        )
    )
    labels = chart.mark_text(align="left", dx=4, fontSize=10, color=DIM).encode(
        text=alt.Text(f"{x}:Q", format=",")
    )
    ac(chart + labels, height=height)


def alt_mixed(df: pd.DataFrame, x: str, bar_col: str, line_cols: list[tuple],
              title: str = "", height: int = 320):
    """Altair Mixed: 바(판매) + 스무스 라인(추이)"""
    bars = (
        alt.Chart(df, title=title)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, color=ACCENT, opacity=0.82)
        .encode(
            x=alt.X(f"{x}:N", sort=None, axis=alt.Axis(labelAngle=-18), title=None),
            y=alt.Y(f"{bar_col}:Q", title=bar_col),
            tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{bar_col}:Q", format=",")],
        )
    )
    lines = []
    for col, clr in line_cols:
        if col in df.columns:
            line = (
                alt.Chart(df)
                .mark_line(color=clr, strokeWidth=2.5, interpolate="monotone")
                .encode(
                    x=alt.X(f"{x}:N", sort=None),
                    y=alt.Y(f"{col}:Q", title=""),
                    tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{col}:Q", format=",", title=col)],
                )
            )
            pts = (
                alt.Chart(df)
                .mark_point(color=clr, size=50, filled=True)
                .encode(x=alt.X(f"{x}:N", sort=None), y=alt.Y(f"{col}:Q"))
            )
            lines += [line, pts]

    combined = alt.layer(bars, *lines).resolve_scale(y="independent")
    ac(combined, height=height)


def _inv_style(col):
    cmap = {"긴급": f"color:{RED};font-weight:700", "주의": f"color:{ORANGE};font-weight:700",
            "관심": f"color:{ACCENT}", "정상": f"color:{GREEN}"}
    return [cmap.get(str(v), "") for v in col]


# ═══════════════════════════════════════════════════
# 6. 비즈니스 규칙 편집기 UI
# ═══════════════════════════════════════════════════
def rules_editor(rules: list) -> list:
    st.markdown("#### ⚙️ 비즈니스 규칙 관리")
    for i, r in enumerate(rules):
        c0, c1, c2, c3, c4, c5, c6 = st.columns([0.06, 0.36, 0.17, 0.17, 0.09, 0.09, 0.06])
        c0.markdown(f"<span style='color:{ACCENT};font-weight:700;font-size:12px'>{r['id']}</span>", unsafe_allow_html=True)
        c1.markdown(f"<span style='color:{TEXT if r['enabled'] else MUTED};font-size:12px'>{r['name']}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span style='color:{DIM};font-size:11px'>{CONDITION_LABELS.get(r['condition'], r['condition'])}</span>", unsafe_allow_html=True)
        c3.markdown(f"<span style='color:{DIM};font-size:11px'>임계값: <b style='color:{TEXT}'>{r['threshold']}</b></span>", unsafe_allow_html=True)
        c4.markdown(f"<span style='color:{ORANGE};font-size:11px;font-weight:600'>+{r['score']}점</span>", unsafe_allow_html=True)
        enabled = c5.checkbox("활성", value=r["enabled"], key=f"ren_{i}_{r['id']}", label_visibility="collapsed")
        rules[i]["enabled"] = enabled
        if c6.button("✕", key=f"rdel_{i}_{r['id']}", help="규칙 삭제"):
            rules.pop(i)
            st.rerun()

    st.markdown("---")
    st.markdown("##### ➕ 새 규칙 추가")
    with st.form("add_rule_form", clear_on_submit=True):
        f1, f2, f3, f4, f5 = st.columns([0.28, 0.22, 0.18, 0.14, 0.18])
        new_name  = f1.text_input("규칙 이름", placeholder="예: 7일 이하 관심")
        new_cond  = f2.selectbox("조건 유형", list(CONDITION_LABELS.keys()),
                                 format_func=lambda k: CONDITION_LABELS[k])
        new_thr   = f3.text_input("임계값", placeholder="예: 7 또는 S")
        new_score = f4.number_input("점수", min_value=1, max_value=999, value=20)
        submitted = f5.form_submit_button("추가", use_container_width=True)
        if submitted and new_name.strip() and new_thr.strip():
            new_id = f"R{len(rules)+1}"
            rules.append({"id": new_id, "name": new_name.strip(),
                           "condition": new_cond, "threshold": new_thr.strip(),
                           "score": int(new_score), "enabled": True})
            st.success(f"규칙 {new_id} 추가됨")
            st.rerun()
    return rules


# ═══════════════════════════════════════════════════
# 7. 전역 CSS
# ═══════════════════════════════════════════════════
GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
html, body, [class*="css"] {{
    font-family: 'Noto Sans KR', sans-serif;
    background: {BG}; color: {TEXT};
}}
.main {{ background: {BG}; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; }}

/* 사이드바 */
section[data-testid="stSidebar"] {{
    background: {CARD};
    border-right: 1px solid {BORDER};
    box-shadow: 2px 0 8px rgba(0,0,0,0.06);
}}

/* KPI 메트릭 카드 */
div[data-testid="metric-container"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
div[data-testid="metric-container"]::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {ACCENT}, {PURPLE});
}}
div[data-testid="metric-container"] label {{
    color: {MUTED} !important;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
}}
div[data-testid="metric-container"] [data-testid="metric-value"] {{
    color: {TEXT} !important;
    font-size: 22px;
    font-weight: 700;
}}
div[data-testid="metric-container"] [data-testid="metric-delta"] {{
    font-size: 11px;
}}

/* 탭 */
.stTabs [data-baseweb="tab-list"] {{
    background: {CARD};
    border-radius: 10px;
    gap: 2px;
    padding: 4px;
    border: 1px solid {BORDER};
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {DIM};
    border-radius: 7px;
    font-size: 12px;
    font-weight: 500;
    padding: 7px 18px;
    transition: all 0.15s;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: {BG};
    color: {TEXT};
}}
.stTabs [aria-selected="true"] {{
    background: {ACCENT} !important;
    color: #FFFFFF !important;
    font-weight: 700;
    box-shadow: 0 2px 6px rgba(79,126,247,0.35);
}}

/* 채팅 */
.stChatMessage {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

/* 데이터프레임 */
div[data-testid="stDataFrame"] {{
    background: {CARD};
    border-radius: 10px;
    border: 1px solid {BORDER};
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}}

/* 섹션 구분선 */
hr {{ border-color: {BORDER}; opacity: 0.6; }}

/* 버튼 */
.stButton > button {{
    background: {CARD};
    border: 1px solid {BORDER};
    color: {TEXT};
    border-radius: 7px;
    font-size: 11px;
    transition: all 0.15s;
    white-space: pre-wrap !important;
    line-height: 1.45 !important;
    min-height: 46px;
}}
.stButton > button:hover {{
    border-color: {ACCENT};
    color: {ACCENT};
    background: #EEF2FF;
}}

/* 입력 위젯 */
.stTextInput > div > input,
.stSelectbox > div,
.stDateInput > div {{
    background: {CARD} !important;
    border-color: {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 7px !important;
}}
</style>
"""


# ═══════════════════════════════════════════════════
# 8. 메인 앱
# ═══════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title="Telecom Sales BI Agent",
        page_icon="📡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    if "biz_rules" not in st.session_state:
        st.session_state["biz_rules"] = copy.deepcopy(DEFAULT_RULES)
    if "dealer_scores" not in st.session_state:
        st.session_state["dealer_scores"] = None
    if "orders" not in st.session_state:
        st.session_state["orders"] = {}      # key: (대리점코드, 모델코드) → True
    if "stat_rule_applied" not in st.session_state:
        st.session_state["stat_rule_applied"] = False
    if "agent_step" not in st.session_state:
        st.session_state["agent_step"] = 1   # 1, 2, 3
    if "agent_chat" not in st.session_state:
        st.session_state["agent_chat"] = []

    # ────────────── 사이드바 ──────────────
    with st.sidebar:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
            f"<div style='width:36px;height:36px;border-radius:9px;"
            f"background:linear-gradient(135deg,{ACCENT},{PURPLE});"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:18px;font-weight:700;color:#FFFFFF;'>T</div>"
            f"<div><div style='font-size:14px;font-weight:700;color:{TEXT};'>Telecom BI Agent</div>"
            f"<div style='font-size:10px;color:{MUTED};'>판매전략 수립 에이전트</div></div></div>",
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown("### 📂 데이터 업로드")
        uploaded = st.file_uploader("Excel 파일 (.xlsx)", type=["xlsx"])
        file_bytes = None
        if uploaded:
            file_bytes = uploaded.read()
            st.success(f"✅ {uploaded.name}")
        else:
            for fname in ["generated_data.xlsx", "sample_data.xlsx"]:
                fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
                if os.path.exists(fpath):
                    with open(fpath, "rb") as f:
                        file_bytes = f.read()
                    st.info(f"📌 {fname} 자동 로드")
                    break
            if file_bytes is None:
                st.warning("Excel 파일을 업로드해 주세요.")

        st.divider()
        st.markdown("### ⚙️ 설정")
        api_key_input = st.text_input(
            "Gemini API Key", type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="AI 전략 Agent 탭 사용 시 필요합니다.",
        )
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input

        st.divider()
        st.markdown(f"<small style='color:{MUTED}'>© 2026 Telecom BI Agent</small>",
                    unsafe_allow_html=True)

    if file_bytes is None:
        st.markdown(
            f"<div style='text-align:center;padding:80px 20px;'>"
            f"<div style='font-size:52px;margin-bottom:16px;'>📡</div>"
            f"<div style='font-size:22px;font-weight:700;color:{TEXT};'>Telecom Sales BI Agent</div>"
            f"<div style='font-size:14px;color:{DIM};margin-top:8px;'>좌측 사이드바에서 Excel 파일을 업로드해 주세요.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    with st.spinner("데이터 분석 중..."):
        data = load_excel(file_bytes)

    sales  = data["sales"]
    inv    = data["inv"]
    model  = data["model"]
    agency = data["agency"]
    wh     = data["wh"]

    # ── 사전 계산
    kpis         = compute_kpis(sales)
    monthly      = compute_monthly_trend(sales)
    brand_sh     = compute_brand_share(sales, model)
    regional     = compute_regional(sales, inv, agency)
    inv_raw      = analyze_inventory(inv, model, agency)
    dealer_rk    = compute_dealer_ranking(sales, agency)
    dealer_scores = compute_dealer_score(sales, agency)
    st.session_state["dealer_scores"] = dealer_scores

    # 통계 성과등급을 inv_raw에 병합
    if not dealer_scores.empty and not inv_raw.empty:
        inv_raw = inv_raw.merge(
            dealer_scores[["대리점코드", "성과점수", "성과등급"]],
            on="대리점코드", how="left",
        )

    inv_df = apply_priority(inv_raw, st.session_state["biz_rules"])

    inv_critical = int(len(inv_df[inv_df["urgency"] >= 3])) if not inv_df.empty else 0
    inv_warning  = int(len(inv_df[inv_df["urgency"] == 2])) if not inv_df.empty else 0
    inv_normal   = int(len(inv_df[inv_df["urgency"] == 0])) if not inv_df.empty else 0
    total_stock  = int(inv_df["재고현황"].sum()) if not inv_df.empty else 0

    # ── 헤더
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>"
        f"<div style='width:44px;height:44px;border-radius:11px;"
        f"background:linear-gradient(135deg,{ACCENT},{PURPLE});"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:22px;font-weight:700;color:#FFFFFF;'>T</div>"
        f"<div><div style='font-size:20px;font-weight:700;color:{TEXT};'>Telecom Sales BI Agent</div>"
        f"<div style='font-size:11px;color:{MUTED};'>통신사 판매전략 수립 에이전트 · {kpis['latest_date']} 기준</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "◉  종합현황", "◆  단말분석", "◈  단말재고현황", "◇  지역·대리점", "⚡  AI 전략 Agent",
    ])

    # ════════════════════════════════════════════════
    # Tab 1 — 종합현황
    # ════════════════════════════════════════════════
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📱 일 판매량",   f"{kpis['day_count']}건",  f"{kpis['latest_date']}")
        c2.metric(
            "💰 일 매출",
            f"{kpis['day_rev']/1_000_000:.1f}백만원" if kpis["day_rev"] >= 1_000_000
            else f"{kpis['day_rev']:,}원",
        )
        c3.metric("👤 ARPU",        f"₩{kpis['arpu']:,}")
        c4.metric("📊 순증 가입자", f"{kpis['net_add']}명")
        c5.metric("🚨 재고경보",    f"{inv_critical + inv_warning}개점",
                  f"긴급 {inv_critical} / 주의 {inv_warning}")

        st.divider()

        # 월별 판매·가입 추이 (Altair Mixed: Bar + Smooth Line)
        if not monthly.empty:
            line_cfg = [("신규가입", GREEN), ("번호이동", ORANGE), ("기기변경", PURPLE)]
            alt_mixed(monthly, "월", "판매건수", line_cfg,
                      title="월별 판매건수 & 가입유형 추이", height=320)

        col_a, col_b = st.columns(2)

        with col_a:
            if "가입유형" in sales.columns:
                vc = (sales[sales["상태"] == "개통완료"]["가입유형"].value_counts()
                      if "상태" in sales.columns else sales["가입유형"].value_counts())
                if not vc.empty:
                    alt_donut(vc.index.tolist(), vc.values.tolist(), "가입유형 비중", height=280)

        with col_b:
            if not brand_sh.empty:
                alt_donut(brand_sh["제조사"].tolist(), brand_sh["판매건수"].tolist(),
                          "브랜드 점유율", height=280)

        # 지역별 월간 판매 현황 (Altair Bar)
        if not regional.empty:
            alt_bar_v(regional, "권역", "판매건수",
                      title="지역별 월간 판매 현황", color=ACCENT, height=280)

    # ════════════════════════════════════════════════
    # Tab 2 — 단말분석
    # ════════════════════════════════════════════════
    with tab2:
        st.markdown("### 단말 라인업 성과 분석")

        fc1, fc2, fc3, fc4 = st.columns(4)
        maker_opts = ["전체"] + sorted(model["제조사"].dropna().unique().tolist()) if not model.empty else ["전체"]
        seg_opts   = ["전체"] + sorted(model["세그먼트"].dropna().unique().tolist()) if not model.empty else ["전체"]
        sel_maker  = fc1.selectbox("제조사",   maker_opts, key="d_maker")
        sel_seg    = fc2.selectbox("세그먼트", seg_opts,   key="d_seg")

        s_min = sales["거래일시"].dt.date.min() if not sales.empty else datetime.now().date()
        s_max = sales["거래일시"].dt.date.max() if not sales.empty else datetime.now().date()
        sel_from = fc3.date_input("시작일", value=s_min, min_value=s_min, max_value=s_max, key="d_from")
        sel_to   = fc4.date_input("종료일", value=s_max, min_value=s_min, max_value=s_max, key="d_to")

        dev_df = compute_device_perf(sales, inv, model, sel_from, sel_to)
        if sel_maker != "전체" and "제조사" in dev_df.columns:
            dev_df = dev_df[dev_df["제조사"] == sel_maker]
        if sel_seg != "전체" and "세그먼트" in dev_df.columns:
            dev_df = dev_df[dev_df["세그먼트"] == sel_seg]

        if not dev_df.empty:
            alt_mixed(dev_df, "기기명", "판매건수",
                      [("마진율(%)", ORANGE)],
                      title="단말별 판매건수 & 마진율", height=320)

            st.markdown("#### 단말별 상세 현황")
            show = [c for c in ["기기명", "제조사", "세그먼트", "네트워크", "출고가",
                                 "마진율(%)", "판매건수", "일평균", "월매출추정", "전국재고"]
                    if c in dev_df.columns]
            st.dataframe(
                dev_df[show].style.format({
                    "출고가": "{:,.0f}", "판매건수": "{:,.0f}",
                    "월매출추정": "{:,.0f}", "마진율(%)": "{:.1f}%",
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("선택 조건에 해당하는 단말이 없습니다.")

    # ════════════════════════════════════════════════
    # Tab 3 — 단말재고현황
    # ════════════════════════════════════════════════
    with tab3:
        st.markdown("### 단말 재고현황")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("📦 전국 총 재고",  f"{total_stock:,}대")
        k2.metric("🔴 긴급 대리점",   f"{inv_critical}개점", "2일 이내 소진")
        k3.metric("🟠 주의 대리점",   f"{inv_warning}개점",  "5일 이내 소진")
        k4.metric("🟢 정상 대리점",   f"{inv_normal}개점")

        st.divider()

        # ── 비즈니스 규칙 토글 패널 ───────────────────────
        rules = st.session_state["biz_rules"]

        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:10px;"
            f"padding:14px 18px;margin-bottom:14px;'>"
            f"<div style='font-size:13px;font-weight:700;color:{TEXT};margin-bottom:10px;'>"
            f"⚙️ 비즈니스 규칙 선택 — 체크된 규칙의 Score 합산 기준으로 우선순위 즉시 재계산</div>",
            unsafe_allow_html=True,
        )

        # 토글 2열 배치
        toggle_changed = False
        cols_per_row = 2
        for row_start in range(0, len(rules), cols_per_row):
            row_rules = rules[row_start: row_start + cols_per_row]
            tcols = st.columns(cols_per_row)
            for ci, r in enumerate(row_rules):
                i = row_start + ci
                new_val = tcols[ci].toggle(
                    f"**{r['id']}** · {r['name']}  `+{r['score']}점`",
                    value=r["enabled"],
                    key=f"t3_tog_{i}_{r['id']}",
                )
                if new_val != r["enabled"]:
                    rules[i]["enabled"] = new_val
                    toggle_changed = True

        if toggle_changed:
            st.session_state["biz_rules"] = rules
            st.rerun()

        # 활성 규칙 Score 요약 바
        active_rules   = [r for r in rules if r["enabled"]]
        max_total      = sum(r["score"] for r in rules) or 1
        active_total   = sum(r["score"] for r in active_rules)
        pct            = int(active_total / max_total * 100)

        badge_html = " ".join(
            f"<span style='background:{ACCENT};color:#fff;font-size:10px;"
            f"padding:2px 8px;border-radius:10px;font-weight:600;'>{r['id']} +{r['score']}점</span>"
            for r in active_rules
        ) or f"<span style='color:{MUTED};font-size:11px;'>활성 규칙 없음</span>"

        st.markdown(
            f"<div style='margin-top:10px;'>"
            f"<div style='display:flex;justify-content:space-between;margin-bottom:4px;'>"
            f"<div>{badge_html}</div>"
            f"<span style='color:{ORANGE};font-size:12px;font-weight:700;'>"
            f"최대 {active_total}점 / 전체 {max_total}점</span></div>"
            f"<div style='background:{BORDER};border-radius:4px;height:6px;'>"
            f"<div style='background:linear-gradient(90deg,{ACCENT},{PURPLE});"
            f"width:{pct}%;height:6px;border-radius:4px;transition:width 0.3s;'></div></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        # 규칙 추가 expander
        with st.expander("➕ 새 규칙 추가"):
            fa1, fa2, fa3, fa4, fa5 = st.columns([3, 2, 2, 1, 1])
            new_name  = fa1.text_input("규칙 이름", placeholder="예: 7일 이하 관심", key="t3_rname")
            new_cond  = fa2.selectbox("조건 유형", list(CONDITION_LABELS.keys()),
                                      format_func=lambda k: CONDITION_LABELS[k], key="t3_rcond")
            new_thr   = fa3.text_input("임계값", placeholder="예: 7 또는 S", key="t3_rthr")
            new_score = fa4.number_input("점수", min_value=1, max_value=999, value=20, key="t3_rscore")
            if fa5.button("추가", key="t3_radd", use_container_width=True):
                if new_name.strip() and new_thr.strip():
                    rules.append({
                        "id": f"R{len(rules)+1}", "name": new_name.strip(),
                        "condition": new_cond, "threshold": new_thr.strip(),
                        "score": int(new_score), "enabled": True,
                    })
                    st.session_state["biz_rules"] = rules
                    st.rerun()

        # 규칙 기반 우선순위 재계산
        inv_df = apply_priority(inv_raw, st.session_state["biz_rules"])
        # 최대 가능 점수 (진행 바 스케일 기준)
        _max_score = max(int(inv_df["우선순위점수"].max()), 1) if not inv_df.empty else 1

        if not inv_df.empty:
            # ── 발주 우선순위 검색·필터 리스트 ──────────────
            st.markdown("#### 🏆 발주 우선순위 리스트")

            sf1, sf2, sf3, sf4 = st.columns([3, 2, 2, 1])
            p_srch = sf1.text_input("🔍 검색", placeholder="대리점명·단말명·권역 입력",
                                    key="p_srch", label_visibility="collapsed")
            p_rg_opts = ["전체 권역"] + sorted(
                inv_df["권역"].dropna().unique().tolist()) if "권역" in inv_df.columns else ["전체 권역"]
            p_st_opts = ["전체 긴급도", "🔴 긴급", "🟠 주의", "🔵 관심", "🟢 정상"]
            p_rg  = sf2.selectbox("권역 필터",    p_rg_opts, key="p_rg",
                                  label_visibility="collapsed")
            p_st  = sf3.selectbox("긴급도 필터",  p_st_opts, key="p_st",
                                  label_visibility="collapsed")
            p_lim = sf4.selectbox("표시 수", [10, 20, 50, 100], key="p_lim",
                                  label_visibility="collapsed")

            # 필터 적용 (전체 우선순위 리스트에서)
            plist = inv_df.copy()
            if p_rg != "전체 권역" and "권역" in plist.columns:
                plist = plist[plist["권역"] == p_rg]
            if p_st != "전체 긴급도":
                sm = {"🔴 긴급": "긴급", "🟠 주의": "주의", "🔵 관심": "관심", "🟢 정상": "정상"}
                plist = plist[plist["재고상태"] == sm[p_st]]
            if p_srch.strip():
                mask = pd.Series(False, index=plist.index)
                for col in ["상호명", "기기명", "권역", "대리점코드", "모델코드"]:
                    if col in plist.columns:
                        mask |= plist[col].astype(str).str.contains(
                            p_srch.strip(), case=False, na=False)
                plist = plist[mask]

            plist = plist.head(int(p_lim))

            if plist.empty:
                st.info("검색 조건에 해당하는 항목이 없습니다.")
            else:
                st.caption(f"총 {len(plist)}건 표시 중  ·  종합 Score 내림차순 정렬")
                for rank, (_, row) in enumerate(plist.iterrows(), 1):
                    status    = row.get("재고상태", "정상")
                    sclr      = STATUS_COLOR.get(status, GREEN)
                    icon      = STATUS_ICON.get(status, "🟢")
                    score     = int(row.get("우선순위점수", 0))
                    grade     = row.get("점포등급", "-")
                    perf_g    = row.get("성과등급", "")
                    seg       = row.get("세그먼트", "-")
                    days      = row.get("잔여일수", 999)
                    stock     = int(row.get("재고현황", 0))
                    order_key = (str(row.get("대리점코드", "")), str(row.get("모델코드", "")))
                    ordered   = st.session_state["orders"].get(order_key, False)

                    # Score 진행 바 (최대 점수 대비 비율)
                    score_pct = min(int(score / _max_score * 100), 100)
                    score_clr = RED if score_pct >= 80 else (ORANGE if score_pct >= 50 else ACCENT)

                    # 기여 규칙 배지 계산
                    rule_badges = ""
                    for r in active_rules:
                        hit = False
                        try:
                            if r["condition"] == "days_lte" and days <= float(r["threshold"]):
                                hit = True
                            elif r["condition"] == "grade_eq" and grade == str(r["threshold"]):
                                hit = True
                            elif r["condition"] == "segment_eq" and seg == str(r["threshold"]):
                                hit = True
                            elif r["condition"] == "perf_grade_eq" and perf_g == str(r["threshold"]):
                                hit = True
                        except Exception:
                            pass
                        if hit:
                            rule_badges += (
                                f"<span style='background:{ACCENT}22;color:{ACCENT};"
                                f"font-size:9px;padding:1px 5px;border-radius:3px;"
                                f"margin-right:3px;font-weight:600;border:1px solid {ACCENT}44;'>"
                                f"{r['id']} +{r['score']}</span>"
                            )

                    perf_badge = ""
                    if perf_g in ("S", "A"):
                        pg_clr = PURPLE if perf_g == "S" else GREEN
                        perf_badge = (
                            f"<span style='background:{pg_clr};color:#fff;"
                            f"font-size:9px;padding:1px 5px;border-radius:3px;"
                            f"margin-left:4px;font-weight:700;'>통계{perf_g}</span>"
                        )

                    card_col, btn_col = st.columns([9, 1])
                    with card_col:
                        st.markdown(
                            f"<div style='background:{CARD};border:1px solid {BORDER};"
                            f"border-left:4px solid {score_clr};border-radius:8px;"
                            f"padding:10px 16px 8px 16px;margin-bottom:2px;'>"

                            # 상단 행: 순위 | 상태 | 대리점 정보
                            f"<div style='display:flex;align-items:center;gap:10px;'>"
                            f"<span style='color:{MUTED};font-size:12px;font-weight:700;"
                            f"min-width:28px;'>#{rank}</span>"
                            f"<span style='font-size:13px;'>{icon}</span>"
                            f"<div style='flex:1;'>"
                            f"<span style='color:{TEXT};font-weight:700;font-size:13px;'>"
                            f"{row.get('상호명','')}</span>"
                            f"<span style='color:{DIM};font-size:11px;margin-left:8px;'>"
                            f"{row.get('권역','')}</span>"
                            f"<span style='background:{CARD2};color:{DIM};font-size:10px;"
                            f"padding:1px 6px;border-radius:3px;margin-left:5px;'>{grade}등급</span>"
                            f"<span style='background:{CARD2};color:{ORANGE};font-size:10px;"
                            f"padding:1px 6px;border-radius:3px;margin-left:3px;'>{seg}</span>"
                            f"{perf_badge}"
                            f"<br/><span style='color:{DIM};font-size:11px;'>"
                            f"{row.get('기기명','')} · 재고 {stock}대 · 잔여 {days}일</span>"
                            f"</div>"
                            # 우측: 종합 Score 숫자
                            f"<div style='text-align:right;min-width:72px;'>"
                            f"<div style='color:{score_clr};font-size:20px;font-weight:800;"
                            f"line-height:1;'>{score}</div>"
                            f"<div style='color:{MUTED};font-size:9px;font-weight:600;"
                            f"letter-spacing:0.5px;'>SCORE</div>"
                            f"<div style='color:{sclr};font-size:10px;font-weight:600;"
                            f"margin-top:2px;'>{status}</div>"
                            f"</div></div>"

                            # 기여 규칙 배지
                            f"<div style='margin-top:5px;'>"
                            f"<span style='color:{MUTED};font-size:9px;margin-right:4px;'>적용 규칙:</span>"
                            + (rule_badges if rule_badges else f"<span style='color:{MUTED};font-size:9px;'>없음</span>") +
                            f"</div></div></div>",
                            unsafe_allow_html=True,
                        )
                    with btn_col:
                        if ordered:
                            st.markdown(
                                f"<div style='background:{GREEN};color:#fff;font-size:11px;"
                                f"font-weight:700;border-radius:6px;padding:6px 4px;"
                                f"text-align:center;margin-top:8px;'>✓ 완료</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            if st.button("📦 발주", key=f"order_{rank}_{order_key}",
                                         use_container_width=True):
                                st.session_state["orders"][order_key] = True
                                st.rerun()

            st.divider()

            # 필터 + 전체 테이블
            fc1, fc2, fc3, fc4 = st.columns(4)
            rg_opts = ["전체"] + sorted(inv_df["권역"].dropna().unique().tolist()) if "권역" in inv_df.columns else ["전체"]
            gr_opts = ["전체"] + sorted(inv_df["점포등급"].dropna().unique().tolist()) if "점포등급" in inv_df.columns else ["전체"]
            st_opts = ["전체", "🔴 긴급", "🟠 주의", "🔵 관심", "🟢 정상"]
            sel_rg  = fc1.selectbox("권역",    rg_opts, key="i_rg")
            sel_gr  = fc2.selectbox("점포등급", gr_opts, key="i_gr")
            sel_st  = fc3.selectbox("재고상태", st_opts, key="i_st")
            i_srch  = fc4.text_input("검색",   placeholder="대리점/단말명", key="i_srch")

            filt = inv_df.copy()
            if sel_rg != "전체" and "권역" in filt.columns:
                filt = filt[filt["권역"] == sel_rg]
            if sel_gr != "전체" and "점포등급" in filt.columns:
                filt = filt[filt["점포등급"] == sel_gr]
            if sel_st != "전체":
                sm = {"🔴 긴급": "긴급", "🟠 주의": "주의", "🔵 관심": "관심", "🟢 정상": "정상"}
                filt = filt[filt["재고상태"] == sm[sel_st]]
            if i_srch.strip():
                mask = pd.Series(False, index=filt.index)
                for col in ["상호명", "기기명", "대리점코드", "모델코드"]:
                    if col in filt.columns:
                        mask |= filt[col].astype(str).str.contains(i_srch.strip(), case=False, na=False)
                filt = filt[mask]

            st.markdown(f"#### 재고 현황 테이블 ({len(filt)}건)")
            show_cols = [c for c in ["상호명", "권역", "점포등급", "기기명", "세그먼트",
                                      "재고현황", "일평균판매", "잔여일수", "재고상태",
                                      "권장발주", "부족예상일", "우선순위점수"]
                         if c in filt.columns]
            st.dataframe(
                filt[show_cols].style.apply(
                    lambda col: _inv_style(col) if col.name == "재고상태" else [""] * len(col),
                ).format({"일평균판매": "{:.1f}", "잔여일수": "{:.1f}",
                           "권장발주": "{:.0f}", "우선순위점수": "{:.0f}"}),
                use_container_width=True, hide_index=True,
            )

        # 물류창고 현황
        if not wh.empty:
            st.divider()
            st.markdown("#### 🏭 물류창고 재고현황")
            wh_cols = [c for c in ["창고명", "권역", "기기명", "현재재고", "가용재고",
                                    "금일입고", "금일출고", "재고금액", "발주필요여부"]
                       if c in wh.columns]
            st.dataframe(
                wh[wh_cols].style.format({"재고금액": "{:,.0f}"}),
                use_container_width=True, hide_index=True,
            )

    # ════════════════════════════════════════════════
    # Tab 4 — 지역·대리점
    # ════════════════════════════════════════════════
    with tab4:
        st.markdown("### 지역·대리점 분석")

        if not regional.empty:
            col_a, col_b = st.columns(2)

            with col_a:
                grp_cols = ["판매건수"]
                if "재고합계" in regional.columns:
                    grp_cols.append("재고합계")
                alt_bar_grouped(regional, "권역", grp_cols,
                                title="권역별 판매량 & 재고량", height=300)

            with col_b:
                alt_bar_h(regional, "권역", "매출합계",
                          title="권역별 매출 현황", height=300)
        else:
            st.warning("지역 데이터가 없습니다.")

        if not dealer_rk.empty:
            st.markdown("#### 대리점 성과 랭킹")
            show = [c for c in ["상호명", "권역", "점포등급", "판매건수",
                                 "매출합계", "리베이트합계", "월목표건수", "목표달성률(%)"]
                    if c in dealer_rk.columns]
            ranked = dealer_rk[show].copy()
            ranked.index = range(1, len(ranked) + 1)
            st.dataframe(
                ranked.style.format({
                    "매출합계": "{:,.0f}",
                    "리베이트합계": "{:,.0f}",
                    "목표달성률(%)": "{:.1f}%",
                }),
                use_container_width=True,
            )

    # ════════════════════════════════════════════════
    # Tab 5 — AI 전략 Agent  (3-Step Workflow)
    # ════════════════════════════════════════════════
    with tab5:
        # ── 스텝 헤더 렌더링 ──────────────────────────
        cur_step = st.session_state["agent_step"]

        def _step_badge(n, label, active, done):
            bg   = ACCENT if active else (GREEN if done else BORDER)
            fg   = "#fff"  if (active or done) else DIM
            icon = "✓" if done and not active else str(n)
            return (
                f"<div style='display:flex;align-items:center;gap:6px;'>"
                f"<div style='width:28px;height:28px;border-radius:50%;background:{bg};"
                f"color:{fg};font-size:12px;font-weight:700;"
                f"display:flex;align-items:center;justify-content:center;'>{icon}</div>"
                f"<span style='font-size:12px;font-weight:{'700' if active else '400'};"
                f"color:{TEXT if active else (GREEN if done else MUTED)};'>{label}</span>"
                f"</div>"
            )

        h1, hc1, h2, hc2, h3 = st.columns([2, 0.4, 2, 0.4, 2])
        h1.markdown(_step_badge(1, "데이터 확인",        cur_step == 1, cur_step > 1), unsafe_allow_html=True)
        hc1.markdown(f"<div style='text-align:center;color:{BORDER};font-size:20px;margin-top:4px;'>→</div>", unsafe_allow_html=True)
        h2.markdown(_step_badge(2, "우수 대리점 분석",   cur_step == 2, cur_step > 2), unsafe_allow_html=True)
        hc2.markdown(f"<div style='text-align:center;color:{BORDER};font-size:20px;margin-top:4px;'>→</div>", unsafe_allow_html=True)
        h3.markdown(_step_badge(3, "발주 우선순위 연동", cur_step == 3, False), unsafe_allow_html=True)

        st.markdown(f"<div style='height:1px;background:{BORDER};margin:10px 0 18px 0;'></div>",
                    unsafe_allow_html=True)

        # ══════════════════════════════════════════
        # STEP 1 — 데이터 확인
        # ══════════════════════════════════════════
        if cur_step == 1:
            st.markdown(f"### 📂 Step 1 · 데이터 확인")
            st.caption("분석에 사용할 데이터 현황을 확인합니다.")

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("📋 전체 거래건수", f"{len(sales):,}건")
            s2.metric("✅ 개통완료",
                      f"{len(sales[sales['상태']=='개통완료']) if '상태' in sales.columns else len(sales):,}건")
            s3.metric("🏪 대리점 수",    f"{len(agency):,}개")
            s4.metric("📱 단말 모델 수", f"{len(model):,}종")

            st.divider()

            col_l, col_r = st.columns(2)
            with col_l:
                st.markdown(f"#### 📊 시트별 데이터 현황")
                sheet_info = [
                    ("세일즈_원장",       len(sales),   f"{sales['거래일시'].min().date()} ~ {sales['거래일시'].max().date()}" if not sales.empty else "-"),
                    ("일일_재고흐름",     len(inv),     f"{inv['기준일'].min().date()} ~ {inv['기준일'].max().date()}" if not inv.empty else "-"),
                    ("단말_마스터",       len(model),   f"{len(model['제조사'].unique()) if not model.empty else 0}개 제조사"),
                    ("유통망_마스터",     len(agency),  f"{agency['권역'].nunique() if not agency.empty else 0}개 권역"),
                    ("물류창고_재고현황", len(wh),      "창고 재고 데이터"),
                ]
                for nm, cnt, note in sheet_info:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;align-items:center;"
                        f"padding:7px 12px;background:{CARD};border:1px solid {BORDER};"
                        f"border-radius:7px;margin-bottom:5px;'>"
                        f"<span style='color:{TEXT};font-size:12px;font-weight:600;'>{nm}</span>"
                        f"<span style='color:{ACCENT};font-size:12px;font-weight:700;'>{cnt:,}행</span>"
                        f"<span style='color:{MUTED};font-size:11px;'>{note}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            with col_r:
                st.markdown(f"#### 🗓️ 분석 기간 현황")
                min_d = sales["거래일시"].min()
                max_d = sales["거래일시"].max()
                period_days = (max_d - min_d).days + 1 if not sales.empty else 0
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:10px;padding:20px;'>"
                    f"<div style='color:{DIM};font-size:11px;margin-bottom:4px;'>분석 기간</div>"
                    f"<div style='color:{TEXT};font-size:18px;font-weight:700;'>{period_days}일간</div>"
                    f"<div style='color:{MUTED};font-size:11px;margin-top:6px;'>{min_d.date()} ~ {max_d.date()}</div>"
                    f"<div style='margin-top:16px;'>"
                    f"<div style='color:{DIM};font-size:11px;margin-bottom:2px;'>총 매출</div>"
                    f"<div style='color:{GREEN};font-size:16px;font-weight:700;'>₩{kpis['total_rev']/1_000_000:.1f}M</div>"
                    f"</div>"
                    f"<div style='margin-top:12px;'>"
                    f"<div style='color:{DIM};font-size:11px;margin-bottom:2px;'>ARPU</div>"
                    f"<div style='color:{ACCENT};font-size:16px;font-weight:700;'>₩{kpis['arpu']:,}</div>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.divider()
            if st.button("▶  우수 대리점 통계 분석 시작  →", type="primary", use_container_width=False):
                st.session_state["agent_step"] = 2
                st.rerun()

        # ══════════════════════════════════════════
        # STEP 2 — 우수 대리점 통계 분석
        # ══════════════════════════════════════════
        elif cur_step == 2:
            st.markdown(f"### 🔬 Step 2 · 우수 대리점 통계 분석")
            st.caption("Z-score 정규화 복합지표(판매건수 35% · 매출 35% · 목표달성률 20% · 리베이트효율 10%)로 대리점을 채점합니다.")

            ds = st.session_state["dealer_scores"]
            if ds is None or ds.empty:
                st.warning("대리점 성과 데이터를 계산할 수 없습니다. 데이터를 확인해 주세요.")
            else:
                # 등급 요약
                cnt_s = int((ds["성과등급"] == "S").sum())
                cnt_a = int((ds["성과등급"] == "A").sum())
                cnt_b = int((ds["성과등급"] == "B").sum())

                g1, g2, g3, g4 = st.columns(4)
                g1.metric("🏆 전체 대리점",  f"{len(ds)}개")
                g2.metric("🥇 S등급 (상위 20%)", f"{cnt_s}개",  f"성과점수 ≥ {ds['성과점수'].quantile(0.80):.0f}점")
                g3.metric("🥈 A등급 (상위 50%)", f"{cnt_a}개",  f"성과점수 ≥ {ds['성과점수'].quantile(0.50):.0f}점")
                g4.metric("🥉 B등급",            f"{cnt_b}개")

                st.divider()

                col_chart, col_table = st.columns([1, 1])

                with col_chart:
                    st.markdown("#### 성과점수 분포")
                    # 점수 히스토그램
                    hist_df = ds[["상호명", "성과점수", "성과등급"]].copy()
                    grade_colors = {"S": PURPLE, "A": GREEN, "B": ACCENT}
                    chart = (
                        alt.Chart(hist_df)
                        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                        .encode(
                            x=alt.X("성과점수:Q", bin=alt.Bin(maxbins=15), title="성과점수"),
                            y=alt.Y("count():Q", title="대리점 수"),
                            color=alt.Color("성과등급:N",
                                            scale=alt.Scale(
                                                domain=["S", "A", "B"],
                                                range=[PURPLE, GREEN, ACCENT]),
                                            legend=alt.Legend(title="등급")),
                            tooltip=["성과등급:N", "count():Q"],
                        )
                        .properties(title="대리점 성과점수 분포")
                    )
                    st.altair_chart(chart.properties(height=260), use_container_width=True)

                with col_table:
                    st.markdown("#### 대리점 성과 랭킹 (상위 15개)")
                    show_ds = ds[["상호명", "권역", "점포등급", "판매건수",
                                  "매출합계", "목표달성률", "성과점수", "성과등급"]].head(15).copy()
                    show_ds["목표달성률"] = (show_ds["목표달성률"] * 100).round(1)
                    show_ds.index = range(1, len(show_ds) + 1)

                    def _grade_style(col):
                        clrs = {"S": f"color:{PURPLE};font-weight:700",
                                "A": f"color:{GREEN};font-weight:700",
                                "B": f"color:{ACCENT}"}
                        return [clrs.get(str(v), "") for v in col]

                    st.dataframe(
                        show_ds.style.apply(
                            lambda c: _grade_style(c) if c.name == "성과등급" else [""] * len(c)
                        ).format({
                            "매출합계": "{:,.0f}", "판매건수": "{:.0f}",
                            "목표달성률": "{:.1f}%", "성과점수": "{:.1f}",
                        }),
                        use_container_width=True,
                    )

                st.divider()
                nav1, nav2, nav3 = st.columns([2, 3, 2])
                with nav1:
                    if st.button("← Step 1로 돌아가기", key="nav2_back"):
                        st.session_state["agent_step"] = 1
                        st.rerun()
                with nav3:
                    if st.button("▶  발주 우선순위 연동  →", type="primary", key="nav2_next",
                                 use_container_width=True):
                        if not st.session_state["stat_rule_applied"]:
                            existing_ids = [r["id"] for r in st.session_state["biz_rules"]]
                            if "RS" not in existing_ids:
                                st.session_state["biz_rules"].append({
                                    "id": "RS",
                                    "name": "통계 S등급 대리점 → 발주 우선 (자동)",
                                    "condition": "perf_grade_eq",
                                    "threshold": "S",
                                    "score": 60,
                                    "enabled": True,
                                })
                            st.session_state["stat_rule_applied"] = True
                        st.session_state["agent_step"] = 3
                        st.rerun()

        # ══════════════════════════════════════════
        # STEP 3 — 발주 우선순위 연동 확인
        # ══════════════════════════════════════════
        elif cur_step == 3:
            st.markdown(f"### 🔗 Step 3 · 발주 우선순위 연동")
            st.caption("통계 분석 결과가 단말재고현황 탭의 발주 우선순위에 자동 반영됩니다.")

            if st.session_state["stat_rule_applied"]:
                st.success("✅ 통계 S등급 대리점 규칙(RS)이 발주 우선순위에 적용되었습니다.")
            else:
                st.info("ℹ️ Step 2에서 '발주 우선순위 연동' 버튼을 클릭하면 자동 반영됩니다.")

            ds = st.session_state["dealer_scores"]

            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown("#### 📐 현재 적용 중인 발주 규칙")
                for r in st.session_state["biz_rules"]:
                    enabled_tag = "활성" if r["enabled"] else "비활성"
                    bclr = ACCENT if r["enabled"] else MUTED
                    is_stat = r["id"] == "RS"
                    highlight = f"border-left:3px solid {PURPLE};" if is_stat else ""
                    new_tag   = f"<span style='background:{PURPLE};color:#fff;font-size:9px;padding:1px 5px;border-radius:3px;margin-left:4px;'>NEW</span>" if is_stat else ""
                    st.markdown(
                        f"<div style='background:{CARD};border:1px solid {BORDER};{highlight}"
                        f"border-radius:7px;padding:8px 12px;margin-bottom:5px;'>"
                        f"<span style='color:{bclr};font-weight:700;font-size:11px;'>{r['id']}</span>"
                        f"<span style='color:{TEXT};font-size:11px;margin-left:8px;'>{r['name']}</span>{new_tag}"
                        f"<span style='color:{ORANGE};font-size:10px;float:right;'>+{r['score']}점 · {enabled_tag}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            with col_right:
                st.markdown("#### 🏆 우선순위 Top 5 (업데이트됨)")
                inv_updated = apply_priority(inv_raw, st.session_state["biz_rules"])
                top5 = inv_updated[inv_updated["urgency"] >= 1].head(5)
                if not top5.empty:
                    for i, (_, row) in enumerate(top5.iterrows(), 1):
                        status  = row.get("재고상태", "정상")
                        sclr    = STATUS_COLOR.get(status, GREEN)
                        icon    = STATUS_ICON.get(status, "🟢")
                        pg      = row.get("성과등급", "")
                        pg_tag  = ""
                        if pg == "S":
                            pg_tag = f"<span style='background:{PURPLE};color:#fff;font-size:9px;padding:1px 5px;border-radius:3px;margin-left:4px;font-weight:700;'>통계S</span>"
                        st.markdown(
                            f"<div style='display:flex;align-items:center;gap:8px;"
                            f"background:{CARD};border:1px solid {BORDER};"
                            f"border-left:3px solid {sclr};border-radius:7px;padding:8px 12px;margin-bottom:5px;'>"
                            f"<span style='color:{MUTED};font-weight:700;font-size:12px;'>#{i}</span>"
                            f"<span>{icon}</span>"
                            f"<div style='flex:1;'>"
                            f"<span style='color:{TEXT};font-weight:600;font-size:12px;'>{row.get('상호명','')}</span>{pg_tag}"
                            f"<br/><span style='color:{DIM};font-size:11px;'>{row.get('기기명','')} · {status}</span>"
                            f"</div>"
                            f"<span style='color:{ORANGE};font-size:11px;font-weight:700;'>{int(row.get('우선순위점수',0))}점</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("우선순위 대상 항목이 없습니다.")

            st.divider()
            st.markdown(
                f"<div style='background:#EEF2FF;border:1px solid {ACCENT};"
                f"border-radius:10px;padding:14px 18px;'>"
                f"<div style='color:{ACCENT};font-weight:700;font-size:13px;margin-bottom:6px;'>💡 다음 단계 안내</div>"
                f"<div style='color:{TEXT};font-size:12px;line-height:1.7;'>"
                f"<b>단말재고현황 탭</b>에서 각 대리점별 발주 우선순위 리스트를 확인하고 <b>📦 발주</b> 버튼으로 발주를 처리하세요.<br>"
                f"통계 S등급 대리점에는 <span style='background:{PURPLE};color:#fff;font-size:10px;padding:1px 5px;border-radius:3px;'>통계S</span> 배지가 표시됩니다."
                f"</div></div>",
                unsafe_allow_html=True,
            )

            st.divider()
            btn_back, btn_rules = st.columns(2)
            with btn_back:
                if st.button("← Step 2로 돌아가기"):
                    st.session_state["agent_step"] = 2
                    st.rerun()
            with btn_rules:
                pass

            # ── 비즈니스 규칙 편집기 ──────────────────
            st.markdown("---")
            updated = rules_editor(st.session_state["biz_rules"])
            st.session_state["biz_rules"] = updated


if __name__ == "__main__":
    main()
