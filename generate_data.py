"""
generated_data.xlsx 재생성 스크립트
- 유통망_마스터: 12개 권역, 권역별 3~4개 대리점 (총 40개)
- 세일즈_원장: 2개월치 일별 거래 (지역별 실제 시장 규모 반영)
- 일일_재고흐름: 동일 기간 대리점별 재고 흐름
- 물류창고_재고현황: 전국 10개 물류센터 재고
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
np.random.seed(42)

# ── 날짜 범위 (2개월) ─────────────────────────────────────────────────────────
END_DATE   = datetime(2026, 3, 27)
START_DATE = END_DATE - timedelta(days=59)   # 2026-01-27 ~ 2026-03-27
DATE_RANGE = [START_DATE + timedelta(days=i) for i in range(60)]

# ── 단말 마스터 ───────────────────────────────────────────────────────────────
MODELS = [
    # (모델코드, 펫네임, 제조사, 세그먼트, 네트워크, 출고가)
    ("S24-U-256",  "갤럭시 S24 울트라 256G", "삼성전자", "플래그십", "5G",  1698400),
    ("S24-U-512",  "갤럭시 S24 울트라 512G", "삼성전자", "플래그십", "5G",  1848400),
    ("S24-256",    "갤럭시 S24 256G",        "삼성전자", "프리미엄", "5G",  1199000),
    ("IP15-P-256", "아이폰 15 프로 256G",    "애플",    "플래그십", "5G",  1550000),
    ("IP15-P-512", "아이폰 15 프로 512G",    "애플",    "플래그십", "5G",  1750000),
    ("IP15-128",   "아이폰 15 128G",         "애플",    "프리미엄", "5G",  1250000),
    ("ZFLIP5-256", "갤럭시 Z플립5 256G",     "삼성전자", "폴더블",  "5G",  1299200),
    ("ZFOLD5-256", "갤럭시 Z폴드5 256G",     "삼성전자", "폴더블",  "5G",  2199000),
    ("A54-5G-256", "갤럭시 A54 256G",        "삼성전자", "보급형",  "5G",   599000),
    ("A15-5G-128", "갤럭시 A15 128G",        "삼성전자", "보급형",  "LTE",  319000),
    ("V50S-128",   "LG V50S 128G",           "LG전자",  "구형",    "5G",   199000),
    ("G8-64",      "LG G8 64G",              "LG전자",  "구형",    "LTE",   99000),
]
MODEL_DICT = {m[0]: m for m in MODELS}

# ── 요금제 ───────────────────────────────────────────────────────────────────
PLANS_PREMIUM  = ["5G 프리미어", "5G 시그니처"]
PLANS_STANDARD = ["5G 스탠다드", "5G 라이트", "5G 청소년"]
PLANS_BUDGET   = ["LTE 슬림", "LTE 키즈", "LTE 시니어"]
JOIN_TYPES     = ["기기변경", "번호이동", "신규가입"]
# 상태: 개통완료 85%, 14일철회 8%, 정지 4%, 취소 3%
STATUS_CHOICES = (["개통완료"]*85 + ["14일철회"]*8 + ["정지"]*4 + ["취소"]*3)

# ── 유통망 마스터 (12권역 × 3~4개 대리점) ─────────────────────────────────────
# (대리점코드, 상호명, 권역, 상권유형, 점포등급, 월목표건수)
AGENCIES = [
    # 서울 (강남권, 고소득 밀집) - 4개
    ("AG-SEL01", "강남직영점",   "서울", "오피스밀집",  "S", 600),
    ("AG-SEL02", "역삼테크점",   "서울", "오피스밀집",  "A", 450),
    ("AG-SEL03", "삼성동복합점", "서울", "복합상권",    "A", 420),
    ("AG-SEL04", "서초직영점",   "서울", "주거단지",    "A", 380),
    # 경기 (최대 인구권) - 4개
    ("AG-GYG01", "수원직영점",   "경기", "복합상권",    "A", 400),
    ("AG-GYG02", "성남분당점",   "경기", "오피스밀집",  "A", 380),
    ("AG-GYG03", "고양일산점",   "경기", "주거단지",    "B", 280),
    ("AG-GYG04", "용인수지점",   "경기", "주거단지",    "B", 260),
    # 인천 - 3개
    ("AG-ICN01", "부평직영점",   "인천", "복합상권",    "A", 320),
    ("AG-ICN02", "연수송도점",   "인천", "주거단지",    "B", 260),
    ("AG-ICN03", "남동점",       "인천", "주거단지",    "B", 200),
    # 부산 (비수도권 최대) - 4개
    ("AG-BSN01", "서면직영점",   "부산", "오피스밀집",  "S", 500),
    ("AG-BSN02", "해운대점",     "부산", "복합상권",    "A", 360),
    ("AG-BSN03", "사상점",       "부산", "대학가/유흥", "B", 240),
    ("AG-BSN04", "동래직영점",   "부산", "주거단지",    "B", 220),
    # 강북 (서울 강북권) - 4개
    ("AG-GBK01", "종로직영점",   "강북", "오피스밀집",  "A", 340),
    ("AG-GBK02", "노원점",       "강북", "주거단지",    "B", 260),
    ("AG-GBK03", "마포홍대점",   "강북", "대학가/유흥", "B", 280),
    ("AG-GBK04", "은평점",       "강북", "주거단지",    "C", 180),
    # 대전 - 3개
    ("AG-DJN01", "둔산직영점",   "대전", "복합상권",    "A", 300),
    ("AG-DJN02", "유성대학점",   "대전", "대학가/유흥", "B", 200),
    ("AG-DJN03", "은행동점",     "대전", "오피스밀집",  "B", 180),
    # 광주 - 3개
    ("AG-GJU01", "충장직영점",   "광주", "복합상권",    "A", 280),
    ("AG-GJU02", "상무점",       "광주", "오피스밀집",  "B", 210),
    ("AG-GJU03", "첨단점",       "광주", "주거단지",    "B", 170),
    # 충남 - 3개
    ("AG-CNM01", "천안직영점",   "충남", "복합상권",    "B", 220),
    ("AG-CNM02", "아산점",       "충남", "주거단지",    "C", 150),
    ("AG-CNM03", "서산점",       "충남", "주거단지",    "C", 100),
    # 경남 - 3개
    ("AG-GNM01", "창원직영점",   "경남", "복합상권",    "A", 280),
    ("AG-GNM02", "진주점",       "경남", "주거단지",    "B", 180),
    ("AG-GNM03", "거제점",       "경남", "주거단지",    "C", 130),
    # 전남 - 3개
    ("AG-JNM01", "순천직영점",   "전남", "복합상권",    "B", 170),
    ("AG-JNM02", "여수점",       "전남", "주거단지",    "C", 130),
    ("AG-JNM03", "목포점",       "전남", "주거단지",    "C", 110),
    # 강원 - 3개
    ("AG-GWN01", "춘천직영점",   "강원", "복합상권",    "B", 140),
    ("AG-GWN02", "원주점",       "강원", "주거단지",    "C", 110),
    ("AG-GWN03", "강릉점",       "강원", "복합상권",    "C", 90),
    # 제주 - 3개
    ("AG-JJU01", "제주직영점",   "제주", "복합상권",    "B", 160),
    ("AG-JJU02", "서귀포점",     "제주", "주거단지",    "C", 90),
    ("AG-JJU03", "제주중앙점",   "제주", "복합상권",    "C", 110),
]
AGENCY_DICT = {a[0]: a for a in AGENCIES}

# 권역별 프리미엄 모델 선호 비율 (서울/경기 높음, 지방 낮음)
REGION_PREMIUM = {
    "서울": 0.55, "강북": 0.42, "경기": 0.45, "인천": 0.38,
    "부산": 0.40, "대전": 0.35, "광주": 0.33, "경남": 0.32,
    "충남": 0.28, "전남": 0.25, "강원": 0.23, "제주": 0.30,
}

def pick_model(region: str) -> tuple:
    """권역별 프리미엄 비율에 따라 모델 선택"""
    p = REGION_PREMIUM.get(region, 0.35)
    r = random.random()
    if r < p * 0.5:          # 플래그십
        pool = [m for m in MODELS if m[3] == "플래그십"]
    elif r < p:               # 프리미엄
        pool = [m for m in MODELS if m[3] in ("플래그십", "프리미엄")]
    elif r < p + 0.35:        # 보급형
        pool = [m for m in MODELS if m[3] == "보급형"]
    else:                     # 폴더블/구형
        pool = [m for m in MODELS if m[3] in ("폴더블", "구형")]
    return random.choice(pool)

def pick_plan(region: str, model_segment: str) -> str:
    """모델 세그먼트·권역에 따라 요금제 선택"""
    p = REGION_PREMIUM.get(region, 0.35)
    if model_segment in ("플래그십", "폴더블"):
        plans = PLANS_PREMIUM + PLANS_STANDARD
        weights = [p*60, p*40, (1-p)*40, (1-p)*30, (1-p)*20]
    elif model_segment == "프리미엄":
        plans = PLANS_PREMIUM + PLANS_STANDARD
        weights = [p*30, p*20, (1-p)*50, (1-p)*40, (1-p)*30]
    else:
        plans = PLANS_STANDARD + PLANS_BUDGET
        weights = [30, 25, 20, 15, 10, 5, 5][:len(PLANS_STANDARD + PLANS_BUDGET)]
    return random.choices(plans, weights=weights[:len(plans)], k=1)[0]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 세일즈_원장: 2개월 × 일별 × 대리점별 트랜잭션
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("세일즈_원장 생성 중...")
sales_rows = []
tx_id = 1

for date in DATE_RANGE:
    is_weekend = date.weekday() >= 5   # 토·일
    is_holiday = date in [             # 설 연휴
        datetime(2026, 1, 28), datetime(2026, 1, 29), datetime(2026, 1, 30),
    ]
    for ag in AGENCIES:
        ag_code, _, region, shop_type, grade, monthly_target = ag
        # 일 평균 거래 = 월목표 / 30일
        daily_avg = monthly_target / 30
        # 주말·공휴일 조정 (상권유형에 따라 다름)
        if is_holiday:
            mult = 0.3
        elif is_weekend:
            mult = 1.3 if shop_type in ("복합상권", "대학가/유흥") else 0.6
        else:
            mult = 1.0
        n_tx = max(0, int(np.random.poisson(daily_avg * mult)))  # 하루 거래수

        for _ in range(n_tx):
            hour   = random.choices(range(10, 21), weights=[5,8,10,12,14,12,10,8,7,6,5], k=1)[0]
            minute = random.randint(0, 59)
            dt     = date.replace(hour=hour, minute=minute)
            model  = pick_model(region)
            price  = model[5]
            rebate = int(price * random.uniform(0.15, 0.35))
            sales_rows.append({
                "거래일시":    dt,
                "거래ID":      f"TR-{tx_id:05d}",
                "대리점코드":  ag_code,
                "모델코드":    model[0],
                "가입유형":    random.choice(JOIN_TYPES),
                "요금제":      pick_plan(region, model[3]),
                "고객ID":      f"kt{tx_id+10000:06d}",
                "단말매출(원)": price,
                "리베이트(원)": rebate,
                "상태":        random.choice(STATUS_CHOICES),
            })
            tx_id += 1

df_sales = pd.DataFrame(sales_rows).sort_values("거래일시").reset_index(drop=True)
print(f"  → {len(df_sales):,}건 생성")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 일일_재고흐름: 각 대리점 × 각 날짜 × 취급 모델
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("일일_재고흐름 생성 중...")
# 대리점별 취급 모델 (등급별로 취급 모델 수 결정)
GRADE_MODEL_COUNT = {"S": 10, "A": 8, "B": 6, "C": 4}

inv_rows = []
for ag in AGENCIES:
    ag_code, _, region, _, grade, _ = ag
    n_models = GRADE_MODEL_COUNT[grade]
    ag_models = random.sample(MODELS, min(n_models, len(MODELS)))
    # 초기 재고
    stock = {m[0]: random.randint(5, 30) for m in ag_models}

    for date in DATE_RANGE:
        daily_sales = df_sales[
            (df_sales["대리점코드"] == ag_code) &
            (df_sales["거래일시"].dt.date == date.date()) &
            (df_sales["상태"] == "개통완료")
        ]
        sold_by_model = daily_sales.groupby("모델코드").size().to_dict()

        for model in ag_models:
            mc = model[0]
            sold    = sold_by_model.get(mc, 0)
            inbound = random.randint(0, 5) if stock[mc] < 10 else 0
            stock[mc] = max(0, stock[mc] + inbound - sold)
            inv_rows.append({
                "기준일":    date.date(),
                "대리점코드": ag_code,
                "모델코드":   mc,
                "판매출고":   sold,
                "입고":       inbound,
                "재고현황":   stock[mc],
            })

df_inv = pd.DataFrame(inv_rows)
print(f"  → {len(df_inv):,}건 생성")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 유통망_마스터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df_agency = pd.DataFrame(AGENCIES, columns=["대리점코드","상호명","권역","상권유형","점포등급","월목표건수"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 단말_마스터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df_model = pd.DataFrame(MODELS, columns=["모델코드","펫네임(기기명)","제조사","세그먼트","네트워크","출고가(원)"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 물류창고_재고현황 (기존 유지)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WAREHOUSES = [
    ("WH-SEL", "서울 물류센터", "서울",  "서울 강서구",  (100, 250)),
    ("WH-ICN", "인천 물류센터", "인천",  "인천 남동구",  (60,  160)),
    ("WH-GYG", "경기 물류센터", "경기",  "경기 수원시",  (80,  200)),
    ("WH-DJN", "대전 물류센터", "대전",  "대전 유성구",  (40,  100)),
    ("WH-DGU", "대구 물류센터", "경남",  "대구 달서구",  (50,  130)),
    ("WH-BSN", "부산 물류센터", "부산",  "부산 사상구",  (60,  150)),
    ("WH-GJU", "광주 물류센터", "광주",  "광주 광산구",  (35,   95)),
    ("WH-JNM", "전남 물류센터", "전남",  "전남 순천시",  (25,   70)),
    ("WH-GWN", "강원 물류센터", "강원",  "강원 원주시",  (20,   60)),
    ("WH-JJU", "제주 물류센터", "제주",  "제주 제주시",  (20,   55)),
]
MODEL_WEIGHT = {
    "S24-U-256":0.6,"S24-U-512":0.4,"S24-256":0.9,"IP15-P-256":0.7,
    "IP15-P-512":0.4,"IP15-128":0.8,"ZFLIP5-256":0.5,"ZFOLD5-256":0.3,
    "A54-5G-256":1.2,"A15-5G-128":1.5,"V50S-128":0.3,"G8-64":0.2,
}
wh_rows = []
for wh_code, wh_name, region, address, (lo, hi) in WAREHOUSES:
    for model in MODELS:
        mc = model[0]; price = model[5]
        wt = MODEL_WEIGHT.get(mc, 0.5)
        stock  = max(0, int(random.randint(lo, hi) * wt))
        inbound  = max(0, int(random.randint(10, 50) * wt))
        outbound = max(0, int(random.randint(5,  30) * wt))
        reorder  = max(5, int(hi * wt * 0.2))
        wh_rows.append({
            "기준일시": END_DATE, "창고코드": wh_code, "창고명": wh_name,
            "권역": region, "창고주소": address, "모델코드": mc,
            "펫네임(기기명)": model[1], "현재재고(대)": stock,
            "금일입고(대)": inbound, "금일출고(대)": outbound,
            "가용재고(대)": stock, "재고금액(원)": stock * price,
            "재주문기준(대)": reorder,
            "발주필요여부": "필요" if stock <= reorder else "정상",
        })
df_wh = pd.DataFrame(wh_rows)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
out = Path("/workspaces/KT_Agent/generated_data.xlsx")
print(f"\n저장 중: {out}")
with pd.ExcelWriter(out, engine="openpyxl") as w:
    df_sales.to_excel(w,  sheet_name="세일즈_원장 (Sales_Transactions)",    index=False)
    df_inv.to_excel(w,    sheet_name="일일_재고흐름 (Inventory_Log)",        index=False)
    df_model.to_excel(w,  sheet_name="단말_마스터 (Master_Model)",           index=False)
    df_agency.to_excel(w, sheet_name="유통망_마스터 (Master_Agency)",        index=False)
    df_wh.to_excel(w,     sheet_name="물류창고_재고현황 (Warehouse_Stock)",  index=False)

print("\n=== 생성 결과 ===")
print(f"세일즈_원장     : {len(df_sales):>6,}건  ({START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')})")
print(f"일일_재고흐름   : {len(df_inv):>6,}건")
print(f"단말_마스터     : {len(df_model):>6,}종")
print(f"유통망_마스터   : {len(df_agency):>6,}개 대리점")
print(f"물류창고_재고현황: {len(df_wh):>6,}건")

print("\n=== 권역별 거래 건수 ===")
df_sales["권역"] = df_sales["대리점코드"].map(lambda x: AGENCY_DICT[x][2])
region_summary = df_sales.groupby("권역").agg(
    거래건수=("거래ID","count"),
    총매출=("단말매출(원)","sum")
).sort_values("거래건수", ascending=False)
region_summary["총매출"] = region_summary["총매출"].apply(lambda x: f"{x:,.0f}")
print(region_summary.to_string())

print("\n=== 일별 평균 거래건수 (상위 5일) ===")
df_sales["날짜"] = df_sales["거래일시"].dt.date
daily = df_sales.groupby("날짜").size().sort_values(ascending=False).head(5)
print(daily.to_string())
