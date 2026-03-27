# Telecom Sales BI Agent — Python 실행 계획

> 작성일: 2026-03-27
> 목적: `sample_data.xlsx` 기반, `telecom-sales-bi-agent.jsx` UI 구조를 Python으로 재현하는 실행 가능한 BI Agent 개발

---

## 1. 기술 스택 결정

| 역할 | 선택 라이브러리 | 이유 |
|------|------------|------|
| Web UI | `streamlit` | JSX 탭/차트 구조를 Python으로 가장 빠르게 재현 가능 |
| 데이터 처리 | `pandas`, `openpyxl` | Excel 5개 시트 파싱·조인·집계 |
| 차트 | `plotly` | recharts 대응 (Bar, Line, Pie, ComposedChart) |
| AI Agent | `anthropic` SDK | Claude API 직접 호출, 스트리밍 지원 |
| 환경변수 | `python-dotenv` | ANTHROPIC_API_KEY 관리 |

---

## 2. 시스템 아키텍처

```
agent.py (Streamlit App)
│
├── [DataLoader]          Excel → pandas DataFrame 변환
│   ├── load_sales()      세일즈_원장 시트
│   ├── load_inventory()  일일_재고흐름 시트
│   ├── load_marketing()  채널별_마케팅 시트
│   ├── load_models()     단말_마스터 시트
│   └── load_agencies()   유통망_마스터 시트
│
├── [BusinessLogic]       핵심 비즈니스 로직
│   ├── compute_kpis()            월간 KPI 계산
│   ├── analyze_inventory()       재고 긴급도 분류
│   ├── compute_sales_trend()     판매 추이 분석
│   ├── compute_regional_stats()  지역별 집계
│   └── compute_marketing_roi()   마케팅 채널 ROI
│
├── [UI Tabs]             5개 탭 화면
│   ├── Tab1: 종합 현황   KPI 카드 + 월별 차트 + 지역 현황
│   ├── Tab2: 단말 분석   모델별 판매량/마진 분석 + 기간 필터
│   ├── Tab3: 재고 현황   대리점별 재고 경보 테이블 + 발주 계획
│   ├── Tab4: 지역·대리점 지역 비교 차트 + 대리점 랭킹
│   └── Tab5: AI 전략 Agent  Claude API 챗 인터페이스
│
└── [AIAgent]             Anthropic Claude 연동
    ├── build_context()   데이터 요약 → 시스템 프롬프트 구성
    ├── ask_claude()      스트리밍 응답 호출
    └── suggested_questions  추천 질문 8개 제공
```

---

## 3. Excel 데이터 시트 구조 분석

### 시트 1 — 세일즈_원장 (Sales_Transactions)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| 거래일시 | datetime | 거래 발생 시각 |
| 거래ID | str | 트랜잭션 고유키 |
| 대리점코드 | str | FK → 유통망_마스터 |
| 모델코드 | str | FK → 단말_마스터 |
| 가입유형 | str | 신규가입/번호이동/기기변경 |
| 요금제 | str | 5G 프리미어 등 |
| 고객세그먼트 | str | 연령대_직군 |
| 단말매출(원) | int | 실제 판매가 |
| 리베이트(원) | int | 대리점 리베이트 |
| 상태 | str | 개통완료/14일철회 등 |

### 시트 2 — 일일_재고흐름 (Inventory_Log)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| 기준일 | datetime | 재고 기준 날짜 |
| 대리점코드 | str | FK |
| 모델코드 | str | FK |
| 기초물량 | int | 당일 시작 재고 |
| 본사입고 | int | 본사 공급 수량 |
| 타점포이관 | int | 대리점 간 이관 (+입고, -출고) |
| 판매출고 | int | 당일 판매 수량 |
| 기말보유량 | int | 당일 말 재고 |

### 시트 3 — 채널별_마케팅 (Marketing_Spend)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| 집행일자 | datetime | |
| 유입채널 | str | 인스타그램/카카오톡/오프라인/네이버SA |
| 캠페인명 | str | |
| 타겟팅 | str | |
| 소진예산(원) | int | |
| 노출수 | int or '-' | |
| 클릭수 | int or '-' | |
| 유효리드(명) | int | |

### 시트 4 — 단말_마스터 (Master_Model)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| 모델코드 | str | PK |
| 펫네임(기기명) | str | |
| 제조사 | str | 삼성전자/애플 |
| 세그먼트 | str | 플래그십/폴더블/보급형 |
| 네트워크 | str | 5G/LTE |
| 출고가(원) | int | |

### 시트 5 — 유통망_마스터 (Master_Agency)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| 대리점코드 | str | PK |
| 상호명 | str | |
| 권역 | str | 수도권/경상권/전라권/충청권 |
| 상권유형 | str | 오피스밀집/대학가 등 |
| 점포등급 | str | S/A/B |
| 월목표건수 | int | |

---

## 4. 핵심 비즈니스 로직

### 4-1. 재고 긴급도 분류 (JSX R1~R5 규칙 준용)

```
일평균판매 = 판매출고 합계 / 집계 일수
잔여일수   = 기말보유량 / 일평균판매

긴급 (urgency=3): 잔여일수 ≤ 2일  → 권장발주 = 일평균 × 14 - 현재재고
주의 (urgency=2): 잔여일수 ≤ 5일  → 발주 검토
관심 (urgency=1): 잔여일수 ≤ 7일
정상 (urgency=0): 잔여일수 > 7일

판매추세 급증: 최근 3일 평균 > 전체 평균 × 1.15
판매추세 감소: 최근 3일 평균 < 전체 평균 × 0.85
```

### 4-2. KPI 계산

```
총 거래건수  = count(거래ID)
개통완료건수 = count(상태 == '개통완료')
개통완료율   = 개통완료건수 / 총 거래건수 × 100
총 매출      = sum(단말매출(원)) for 개통완료 거래
총 리베이트  = sum(리베이트(원)) for 개통완료 거래
리베이트율   = 총 리베이트 / 총 매출 × 100

가입유형 분포: 신규가입 / 번호이동 / 기기변경 건수 및 비중
```

### 4-3. 마케팅 ROI

```
CPL (Cost Per Lead) = 소진예산(원) / 유효리드(명)
CTR = 클릭수 / 노출수 × 100  (오프라인 제외)
채널 효율 순위: CPL 오름차순
```

### 4-4. 지역별 집계

```
대리점코드 → 유통망_마스터 JOIN → 권역 획득
권역별:
  - 판매건수 합계
  - 매출 합계
  - 현재 재고 합계 (기말보유량)
  - 대리점 수
  - 평균 목표 달성률 = 실적 / 월목표건수
```

---

## 5. AI Agent 프롬프트 설계

### 시스템 프롬프트 구조

```
당신은 한국 이동통신사의 수석 마케팅 전략 컨설턴트입니다.

## 분석 데이터 현황
- 분석 기간: {min_date} ~ {max_date}
- 총 거래건수: {total_tx}건 (개통완료: {completed}건, 개통완료율: {rate}%)
- 총 매출: {total_revenue:,}원 / 리베이트율: {rebate_rate:.1f}%
- 가입유형: 신규개통 {new_act}건 / 번호이동 {mnp}건 / 기기변경 {device_chg}건

## 단말 판매 현황
{model_summary}

## 대리점 현황
- 전체 {n_agency}개 대리점
- 재고 긴급: {critical}개점 / 주의: {warning}개점
- 최고 실적 대리점: {top_agency}

## 권역별 현황
{regional_summary}

## 마케팅 채널 성과
{marketing_summary}

답변 원칙:
- 반드시 수치 근거를 포함하여 설명
- 실행 전략 3~5개를 우선순위와 함께 제시
- 한국어로 500자 이내 간결하게 작성
```

---

## 6. UI 탭별 구현 계획

### Tab 1: 종합 현황
- KPI 카드 5개: 총 거래, 개통완료율, 총 매출, 리베이트율, 재고 경보 수
- 차트1: 가입유형별 건수 (Bar)
- 차트2: 고객세그먼트별 판매 (Pie)
- 차트3: 요금제별 매출 (Bar)
- 테이블: 대리점별 목표 달성 현황

### Tab 2: 단말 분석
- 필터: 제조사, 세그먼트 (멀티셀렉트)
- 차트1: 모델별 판매건수 + 출고가 (이중 축 ComposedChart)
- 차트2: 세그먼트별 매출 비중 (Pie)
- 테이블: 단말 상세 — 판매건수, 매출합계, 리베이트, 순이익(매출-리베이트)

### Tab 3: 재고 현황
- KPI 카드: 긴급/주의/관심/정상 대리점 수
- 필터: 권역, 점포등급, 긴급도
- 테이블: 대리점×모델 — 기말보유량, 일평균판매, 잔여일수, 긴급도 배지
- 발주 계획 섹션: 긴급 대리점 자동 권장 발주량 계산

### Tab 4: 지역·대리점
- 차트1: 권역별 판매/매출 가로 막대 차트
- 차트2: 마케팅 채널별 CPL 비교
- 테이블: 대리점 전체 랭킹 (매출 기준)

### Tab 5: AI 전략 Agent
- 좌측(2/3): Claude 스트리밍 챗 인터페이스
- 우측(1/3): 핵심 지표 요약 + 추천 질문 버튼 8개
- 추천 질문: 번호이동 확대, 재고 긴급 발주, 마케팅 ROI 개선, 프리미엄 단말 판촉, 리베이트 최적화 등

---

## 7. 파일 구성

```
KT_Agent/
├── agent.py              ← 메인 Streamlit 앱 (단일 파일)
├── sample_data.xlsx      ← 입력 데이터
├── .env                  ← ANTHROPIC_API_KEY (사용자 직접 설정)
├── execution_plan.md     ← 본 파일
└── telecom-sales-bi-agent.jsx  ← 참조 UI
```

---

## 8. 실행 방법

```bash
# 1. 의존성 설치
pip install streamlit pandas openpyxl plotly anthropic python-dotenv

# 2. API 키 설정 (.env 파일)
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > .env

# 3. 실행
streamlit run agent.py
```

---

## 9. 구현 단계

| 단계 | 작업 | 완료 기준 |
|------|------|-----------|
| 1 | DataLoader — 5개 시트 파싱 및 조인 | DataFrame 정상 생성 |
| 2 | BusinessLogic — KPI/재고/지역/마케팅 집계 | 수치 검증 완료 |
| 3 | Tab 1: 종합 현황 UI | KPI 카드 + 차트 렌더링 |
| 4 | Tab 2: 단말 분석 UI | 필터 + 차트 + 테이블 |
| 5 | Tab 3: 재고 현황 UI | 긴급도 배지 + 발주 계획 |
| 6 | Tab 4: 지역·대리점 UI | 권역 차트 + 랭킹 테이블 |
| 7 | Tab 5: AI Agent UI | Claude API 챗 인터페이스 |
| 8 | 통합 테스트 | 파일 업로드 → 분석 → 전략 도출 전 과정 |

---

## 10. 주요 고려사항

- **소규모 샘플 데이터**: sample_data.xlsx의 각 시트가 4~5행이므로 모든 기능이 데이터 없이도 의미 있게 동작하도록 방어 코드 포함
- **API 키 미설정 시**: AI 탭에서 안내 메시지 표시, 나머지 탭은 정상 동작
- **Excel 파일 업로드**: 사이드바에 파일 업로더 제공, 기본값으로 `sample_data.xlsx` 자동 로드
- **한글 폰트**: Plotly 차트 한글 깨짐 방지 (`font_family` 명시)
- **재고 잔여일수**: 단일 날짜 데이터인 경우 판매출고 기준으로 계산, 0 나누기 방어 처리
