# Telecom Sales BI Agent — bi.py 실행 계획

> 작성일: 2026-03-27
> 입력: `generated_data.xlsx` (5개 시트, 500~행 규모)
> 출력: `bi.py` — Streamlit 단일 파일 BI 앱

---

## 1. 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| Web UI | `streamlit` |
| 데이터 처리 | `pandas`, `openpyxl` |
| 차트 | `plotly` (Bar, Line, Pie, ComposedChart) |
| AI Agent | `google-generativeai` (Gemini 2.0 Flash, 스트리밍) |
| 환경변수 | `python-dotenv` |

---

## 2. Excel 시트 구조

| 시트명 | 행수 | 주요 컬럼 |
|--------|------|----------|
| 세일즈_원장 | 500 | 거래일시, 거래ID, 대리점코드, 모델코드, 가입유형, 요금제, 단말매출(원), 리베이트(원), 상태 |
| 일일_재고흐름 | 500 | 기준일, 대리점코드, 모델코드, 판매출고, 재고현황 |
| 단말_마스터 | 15 | 모델코드, 펫네임(기기명), 제조사, 세그먼트, 네트워크, 출고가(원) |
| 유통망_마스터 | 15 | 대리점코드, 상호명, 권역, 상권유형, 점포등급, 월목표건수 |
| 물류창고_재고현황 | 150 | 창고코드, 창고명, 권역, 모델코드, 현재재고, 가용재고, 재고금액, 발주필요여부 |

---

## 3. 시스템 아키텍처

```
bi.py (Streamlit App)
│
├── [DataLoader]          Excel → pandas DataFrame
│   ├── load_excel()      5개 시트 파싱·정제
│   └── 컬럼 정규화       한글 컬럼 → 내부 영문 키
│
├── [BusinessLogic]
│   ├── compute_kpis()           일간 KPI (판매량·매출·ARPU·순증·경보)
│   ├── compute_monthly_trend()  월별 가입유형 추이
│   ├── compute_brand_share()    제조사별 판매 점유율
│   ├── compute_regional()       권역별 판매·매출·재고
│   ├── analyze_inventory()      대리점×모델 잔여일수·긴급도
│   ├── compute_priority()       비즈니스 룰 → 우선순위 점수
│   ├── compute_device_perf()    단말별 판매·마진 집계
│   └── compute_dealer_ranking() 대리점 성과 랭킹
│
├── [BusinessRules]       추가·삭제 가능한 규칙 엔진
│   ├── DEFAULT_RULES     4개 기본 규칙
│   ├── apply_rules()     규칙 → 우선순위 점수 계산
│   └── rules_editor_ui() Streamlit 규칙 추가/삭제 UI
│
├── [UI Tabs]             5개 탭
│   ├── Tab1: 종합현황    KPI카드 + 월추이 + 가입유형 + 브랜드 + 지역
│   ├── Tab2: 단말분석    라인업 ComposedChart + 상세 테이블
│   ├── Tab3: 단말재고현황 KPI + 우선순위 리스트 + 필터 테이블
│   ├── Tab4: 지역·대리점  판매/재고 차트 + 랭킹 테이블
│   └── Tab5: AI Agent    Gemini 스트리밍 챗 + 추천질문 + 규칙 표시
│
└── [AIAgent]             Gemini API
    ├── build_context()   데이터 요약 → 시스템 프롬프트
    └── stream_gemini()   스트리밍 응답 제너레이터
```

---

## 4. 비즈니스 로직 — 재고 우선순위 엔진

### 4-1. 잔여일수 계산
```
일평균판매 = 판매출고 평균 (대리점·모델 기준, 일일_재고흐름)
기말재고    = 재고현황 최신값
잔여일수   = 기말재고 / 일평균판매  (0 나누기 → 999)
```

### 4-2. 기본 규칙 (추가·삭제 가능)
```
R1: 잔여일수 ≤ 2일  → 긴급 발주   (priority_score +100)
R2: 잔여일수 ≤ 5일  → 발주 검토   (priority_score +50)
R3: S등급 대리점    → 우선순위 부여 (priority_score +30)
R4: 플래그십 부족   → 최우선 배정  (priority_score +40)
```

### 4-3. 우선순위 점수 → 정렬
```
최종 우선순위 = Σ(활성 규칙 점수) + (잔여일수 역수 가중)
긴급도 배지: 🔴 긴급(≤2일) / 🟠 주의(≤5일) / 🔵 관심(≤7일) / 🟢 정상
```

---

## 5. KPI 계산 정의

```
일 판매량  = 가장 최근 거래일자의 개통완료 건수
일 매출    = 가장 최근 거래일자의 단말매출 합계
ARPU      = 개통완료 단말매출 합계 / 개통완료 건수
순증 가입자 = 개통완료 건수 − 정지/철회 건수
재고경보   = 잔여일수 ≤ 5일인 대리점×모델 조합 수
```

---

## 6. 탭별 화면 상세

### Tab1 — 종합현황
- KPI 카드 5개: 일 판매량, 일 매출, ARPU, 순증 가입자, 재고경보
- 월별 판매·가입 추이: ComposedChart (Bar=판매건수, Line=신규/번호이동)
- 가입 유형 Pie: 신규개통 / 번호이동 / 기기변경
- 브랜드 점유율 Pie: 삼성전자 / 애플 / 기타
- 지역별 월간 판매 Bar

### Tab2 — 단말분석
- 기간 필터 (날짜 range)
- 제조사 / 세그먼트 필터
- ComposedChart: 단말별 판매량(Bar) + 마진율(Line)
- 상세 테이블: 모델명, 브랜드, 등급, 출고가, 마진율, 기간판매, 일평균, 월매출(추정), 전국재고

### Tab3 — 단말재고현황
- KPI 카드: 전국 총 재고량, 긴급 대리점 수, 정상 대리점 수
- 비즈니스 룰 적용 우선순위 리스트 (상위 10개 대리점×모델)
- 필터: 권역, 점포등급, 긴급도, 검색
- 전체 재고 테이블 (긴급도 색상 강조)

### Tab4 — 지역·대리점
- 권역별 판매량 & 재고량 그룹 Bar
- 권역별 매출 현황 수평 Bar
- 대리점 성과 랭킹 테이블 (매출 기준, 목표달성률 포함)
- 물류창고 재고 현황 테이블

### Tab5 — AI 전략 Agent
- 좌(2/3): Gemini 스트리밍 채팅 인터페이스
- 우(1/3): 추천 질문 8개 버튼 + 활성 비즈니스 규칙 목록
- 하단: 비즈니스 규칙 추가/삭제 편집기

---

## 7. 비즈니스 규칙 편집기 설계

```python
# 규칙 구조
rule = {
    "id": "R1",
    "name": "잔여일수 긴급",
    "condition": "days_lte",   # days_lte / grade_eq / segment_eq / custom
    "threshold": 2,
    "action": "긴급 발주",
    "priority_score": 100,
    "enabled": True,
}

# UI:
# - st.data_editor 로 규칙 테이블 inline 편집
# - "규칙 추가" 버튼 → 폼으로 새 규칙 입력
# - "삭제" 버튼 → 해당 규칙 제거
```

---

## 8. 실행 방법

```bash
pip install streamlit pandas openpyxl plotly google-generativeai python-dotenv

# .env 설정
echo "GEMINI_API_KEY=AIza..." > .env

streamlit run bi.py
```

---

## 9. 구현 단계

| 단계 | 내용 |
|------|------|
| 1 | DataLoader: 5개 시트 파싱·조인 |
| 2 | BusinessLogic: KPI·재고·지역·단말 집계 함수 |
| 3 | BusinessRules: 규칙 엔진 + 편집기 UI |
| 4 | Tab1–4: 차트·테이블 렌더링 |
| 5 | Tab5: Gemini 스트리밍 챗 + 규칙 표시 |
| 6 | 전체 통합 테스트 |
