import { useState, useMemo, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, RadarChart, Radar, PolarGrid, PolarAngleAxis, Legend } from "recharts";

// ─── 휴대폰 판매 데이터 ───
const SALES_DATA = {
  monthly: [
    { month: "2025-01", revenue: 48200, cost: 28900, orders: 3120, returns: 180, newCustomers: 870 },
    { month: "2025-02", revenue: 51300, cost: 30100, orders: 3380, returns: 220, newCustomers: 940 },
    { month: "2025-03", revenue: 56700, cost: 32000, orders: 3890, returns: 150, newCustomers: 1120 },
    { month: "2025-04", revenue: 53400, cost: 31500, orders: 3610, returns: 280, newCustomers: 980 },
    { month: "2025-05", revenue: 62100, cost: 34800, orders: 4210, returns: 190, newCustomers: 1350 },
    { month: "2025-06", revenue: 68900, cost: 37200, orders: 4670, returns: 240, newCustomers: 1480 },
    { month: "2025-07", revenue: 74500, cost: 39500, orders: 4980, returns: 210, newCustomers: 1620 },
    { month: "2025-08", revenue: 71200, cost: 38700, orders: 4790, returns: 310, newCustomers: 1410 },
    { month: "2025-09", revenue: 78900, cost: 41000, orders: 5230, returns: 170, newCustomers: 1780 },
    { month: "2025-10", revenue: 83400, cost: 42800, orders: 5510, returns: 230, newCustomers: 1920 },
    { month: "2025-11", revenue: 92100, cost: 45900, orders: 6120, returns: 260, newCustomers: 2180 },
    { month: "2025-12", revenue: 105800, cost: 51200, orders: 6980, returns: 320, newCustomers: 2560 },
  ],
  products: [
    { id: "P001", name: "Galaxy S25 Ultra", brand: "Samsung", category: "프리미엄", revenue: 284000, units: 14200, margin: 0.32, growth: 0.28, satisfaction: 4.5 },
    { id: "P002", name: "iPhone 16 Pro Max", brand: "Apple", category: "프리미엄", revenue: 221000, units: 8900, margin: 0.38, growth: 0.22, satisfaction: 4.6 },
    { id: "P003", name: "Galaxy S25+", brand: "Samsung", category: "프리미엄", revenue: 187000, units: 12400, margin: 0.28, growth: 0.18, satisfaction: 4.3 },
    { id: "P004", name: "iPhone 16 Pro", brand: "Apple", category: "프리미엄", revenue: 153000, units: 9800, margin: 0.36, growth: 0.15, satisfaction: 4.4 },
    { id: "P005", name: "Galaxy Z Fold6", brand: "Samsung", category: "폴더블", revenue: 128000, units: 3800, margin: 0.35, growth: 0.42, satisfaction: 4.2 },
    { id: "P006", name: "Galaxy Z Flip6", brand: "Samsung", category: "폴더블", revenue: 94000, units: 6200, margin: 0.30, growth: 0.38, satisfaction: 4.1 },
    { id: "P007", name: "Galaxy S25", brand: "Samsung", category: "프리미엄", revenue: 87000, units: 9100, margin: 0.25, growth: 0.12, satisfaction: 4.2 },
    { id: "P008", name: "iPhone 16", brand: "Apple", category: "스탠다드", revenue: 76000, units: 8200, margin: 0.32, growth: 0.08, satisfaction: 4.3 },
    { id: "P009", name: "Galaxy A55", brand: "Samsung", category: "미드레인지", revenue: 42000, units: 18500, margin: 0.20, growth: 0.55, satisfaction: 4.0 },
    { id: "P010", name: "Pixel 9 Pro", brand: "Google", category: "프리미엄", revenue: 28000, units: 2100, margin: 0.28, growth: 0.85, satisfaction: 4.1 },
  ],
  regions: [
    { region: "서울", revenue: 142300, customers: 18400, dealers: 48, penetration: 0.34, churn: 0.05 },
    { region: "경기", revenue: 98600, customers: 14200, dealers: 52, penetration: 0.28, churn: 0.06 },
    { region: "인천", revenue: 42800, customers: 5600, dealers: 18, penetration: 0.22, churn: 0.07 },
    { region: "부산", revenue: 56200, customers: 7100, dealers: 22, penetration: 0.25, churn: 0.07 },
    { region: "대구", revenue: 38400, customers: 4800, dealers: 16, penetration: 0.20, churn: 0.08 },
    { region: "광주", revenue: 24600, customers: 3200, dealers: 12, penetration: 0.18, churn: 0.08 },
    { region: "대전", revenue: 28900, customers: 3700, dealers: 14, penetration: 0.19, churn: 0.07 },
    { region: "강원/제주", revenue: 18600, customers: 2400, dealers: 10, penetration: 0.15, churn: 0.09 },
  ],
  channels: [
    { channel: "대리점", revenue: 224000, cost: 89000, deals: 38000, cycle: 1 },
    { channel: "직영점", revenue: 182000, cost: 62400, deals: 12450, cycle: 1 },
    { channel: "온라인몰", revenue: 148700, cost: 28800, deals: 28200, cycle: 1 },
    { channel: "제휴/홈쇼핑", revenue: 68600, cost: 32200, deals: 8900, cycle: 2 },
    { channel: "기업영업", revenue: 48800, cost: 21100, deals: 3120, cycle: 5 },
  ],
  customerSegments: [
    { segment: "5G 헤비유저", revenue: 152000, count: 48000, ltv: 3167, acqCost: 420, retention: 0.88 },
    { segment: "프리미엄고객", revenue: 128400, count: 25600, ltv: 5016, acqCost: 680, retention: 0.85 },
    { segment: "가족결합", revenue: 98100, count: 68000, ltv: 1443, acqCost: 280, retention: 0.92 },
    { segment: "청소년/대학생", revenue: 52400, count: 42000, ltv: 1248, acqCost: 180, retention: 0.72 },
    { segment: "시니어", revenue: 38600, count: 32000, ltv: 1206, acqCost: 220, retention: 0.78 },
  ]
};

// ─── 전국 대리점 재고 데이터 ───
const DEALERS_RAW = [
  { id: "D001", name: "서울 강남 직영점",     region: "서울", type: "직영",
    inventory: { "Galaxy S25 Ultra": 12, "iPhone 16 Pro Max": 8,  "Galaxy Z Fold6": 5,  "Galaxy S25+": 18, "Galaxy A55": 45 },
    dailySales: { "Galaxy S25 Ultra": 4.2, "iPhone 16 Pro Max": 2.8, "Galaxy Z Fold6": 1.5, "Galaxy S25+": 3.1, "Galaxy A55": 5.2 },
    weeklySales: [320, 345, 298, 412, 387, 356, 421] },
  { id: "D002", name: "서울 홍대 대리점",     region: "서울", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 6,  "iPhone 16 Pro Max": 3,  "Galaxy Z Flip6": 8,  "Galaxy S25+": 14, "Galaxy A55": 32 },
    dailySales: { "Galaxy S25 Ultra": 2.8, "iPhone 16 Pro Max": 2.1, "Galaxy Z Flip6": 1.8, "Galaxy S25+": 2.4, "Galaxy A55": 3.6 },
    weeklySales: [210, 198, 225, 248, 231, 256, 268] },
  { id: "D003", name: "서울 종로 대리점",     region: "서울", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 3,  "iPhone 16 Pro Max": 2,  "Galaxy S25": 22,     "Galaxy A55": 58,  "Pixel 9 Pro": 4 },
    dailySales: { "Galaxy S25 Ultra": 1.9, "iPhone 16 Pro Max": 1.4, "Galaxy S25": 3.2,  "Galaxy A55": 4.8, "Pixel 9 Pro": 0.8 },
    weeklySales: [185, 192, 178, 201, 195, 188, 210] },
  { id: "D004", name: "서울 신촌 대리점",     region: "서울", type: "대리점",
    inventory: { "Galaxy Z Flip6": 4,    "iPhone 16": 5,          "Galaxy S25+": 9,     "Galaxy A55": 28,  "Pixel 9 Pro": 2 },
    dailySales: { "Galaxy Z Flip6": 2.2, "iPhone 16": 2.8,        "Galaxy S25+": 2.1,   "Galaxy A55": 3.2, "Pixel 9 Pro": 0.6 },
    weeklySales: [168, 172, 185, 192, 178, 196, 201] },
  { id: "D005", name: "서울 잠실 직영점",     region: "서울", type: "직영",
    inventory: { "Galaxy S25 Ultra": 20, "iPhone 16 Pro Max": 15, "Galaxy Z Fold6": 8,  "Galaxy Z Flip6": 12, "Galaxy S25+": 25 },
    dailySales: { "Galaxy S25 Ultra": 3.8, "iPhone 16 Pro Max": 3.2, "Galaxy Z Fold6": 1.8, "Galaxy Z Flip6": 2.4, "Galaxy S25+": 3.6 },
    weeklySales: [298, 312, 325, 345, 338, 362, 378] },
  { id: "D006", name: "수원 영통 대리점",     region: "경기", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 8,  "iPhone 16 Pro": 6,      "Galaxy S25+": 15,    "Galaxy A55": 42,  "Galaxy Z Flip6": 7 },
    dailySales: { "Galaxy S25 Ultra": 2.4, "iPhone 16 Pro": 2.0,  "Galaxy S25+": 2.8,   "Galaxy A55": 4.5, "Galaxy Z Flip6": 1.6 },
    weeklySales: [245, 258, 242, 271, 265, 279, 285] },
  { id: "D007", name: "성남 분당 직영점",     region: "경기", type: "직영",
    inventory: { "Galaxy S25 Ultra": 14, "iPhone 16 Pro Max": 10, "Galaxy Z Fold6": 6,  "Galaxy S25+": 20, "Galaxy A55": 38 },
    dailySales: { "Galaxy S25 Ultra": 3.2, "iPhone 16 Pro Max": 2.6, "Galaxy Z Fold6": 1.4, "Galaxy S25+": 3.0, "Galaxy A55": 4.2 },
    weeklySales: [278, 285, 292, 308, 298, 315, 322] },
  { id: "D008", name: "고양 일산 대리점",     region: "경기", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 5,  "iPhone 16": 4,          "Galaxy S25": 12,     "Galaxy A55": 35,  "Galaxy Z Flip6": 3 },
    dailySales: { "Galaxy S25 Ultra": 1.8, "iPhone 16": 1.6,      "Galaxy S25": 2.1,    "Galaxy A55": 3.8, "Galaxy Z Flip6": 1.2 },
    weeklySales: [198, 205, 192, 218, 212, 225, 231] },
  { id: "D009", name: "용인 기흥 대리점",     region: "경기", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 2,  "iPhone 16 Pro": 1,      "Galaxy S25+": 6,     "Galaxy A55": 22,  "Pixel 9 Pro": 1 },
    dailySales: { "Galaxy S25 Ultra": 2.1, "iPhone 16 Pro": 1.8,  "Galaxy S25+": 2.2,   "Galaxy A55": 3.5, "Pixel 9 Pro": 0.5 },
    weeklySales: [178, 185, 172, 195, 188, 198, 205] },
  { id: "D010", name: "인천 부평 대리점",     region: "인천", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 7,  "iPhone 16 Pro": 5,      "Galaxy S25+": 13,    "Galaxy A55": 38,  "Galaxy Z Flip6": 5 },
    dailySales: { "Galaxy S25 Ultra": 1.9, "iPhone 16 Pro": 1.6,  "Galaxy S25+": 2.1,   "Galaxy A55": 3.9, "Galaxy Z Flip6": 1.3 },
    weeklySales: [178, 185, 175, 195, 188, 198, 205] },
  { id: "D011", name: "인천 송도 직영점",     region: "인천", type: "직영",
    inventory: { "Galaxy S25 Ultra": 10, "iPhone 16 Pro Max": 7,  "Galaxy Z Fold6": 4,  "Galaxy S25+": 16, "Galaxy A55": 32 },
    dailySales: { "Galaxy S25 Ultra": 2.2, "iPhone 16 Pro Max": 1.8, "Galaxy Z Fold6": 0.9, "Galaxy S25+": 2.4, "Galaxy A55": 3.5 },
    weeklySales: [192, 198, 188, 208, 202, 215, 222] },
  { id: "D012", name: "부산 서면 직영점",     region: "부산", type: "직영",
    inventory: { "Galaxy S25 Ultra": 11, "iPhone 16 Pro Max": 9,  "Galaxy Z Fold6": 5,  "Galaxy S25+": 18, "Galaxy A55": 42 },
    dailySales: { "Galaxy S25 Ultra": 2.8, "iPhone 16 Pro Max": 2.4, "Galaxy Z Fold6": 1.2, "Galaxy S25+": 2.7, "Galaxy A55": 4.2 },
    weeklySales: [245, 258, 248, 272, 265, 278, 285] },
  { id: "D013", name: "부산 해운대 대리점",   region: "부산", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 4,  "iPhone 16": 3,          "Galaxy Z Flip6": 5,  "Galaxy A55": 28,  "Galaxy S25": 8 },
    dailySales: { "Galaxy S25 Ultra": 1.8, "iPhone 16": 1.5,      "Galaxy Z Flip6": 1.6, "Galaxy A55": 3.2, "Galaxy S25": 1.8 },
    weeklySales: [158, 165, 155, 175, 168, 178, 185] },
  { id: "D014", name: "부산 동래 대리점",     region: "부산", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 1,  "iPhone 16 Pro": 2,      "Galaxy S25+": 4,     "Galaxy A55": 18,  "Galaxy Z Flip6": 2 },
    dailySales: { "Galaxy S25 Ultra": 1.9, "iPhone 16 Pro": 1.4,  "Galaxy S25+": 1.8,   "Galaxy A55": 2.8, "Galaxy Z Flip6": 1.1 },
    weeklySales: [148, 152, 145, 162, 156, 168, 172] },
  { id: "D015", name: "대구 동성로 직영점",   region: "대구", type: "직영",
    inventory: { "Galaxy S25 Ultra": 9,  "iPhone 16 Pro Max": 6,  "Galaxy S25+": 14,    "Galaxy A55": 36,  "Galaxy Z Flip6": 6 },
    dailySales: { "Galaxy S25 Ultra": 2.1, "iPhone 16 Pro Max": 1.7, "Galaxy S25+": 2.2, "Galaxy A55": 3.6, "Galaxy Z Flip6": 1.4 },
    weeklySales: [198, 205, 195, 218, 212, 225, 231] },
  { id: "D016", name: "대구 수성 대리점",     region: "대구", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 3,  "iPhone 16": 5,          "Galaxy S25": 10,     "Galaxy A55": 24,  "Pixel 9 Pro": 2 },
    dailySales: { "Galaxy S25 Ultra": 1.6, "iPhone 16": 1.8,      "Galaxy S25": 2.0,    "Galaxy A55": 3.0, "Pixel 9 Pro": 0.5 },
    weeklySales: [145, 152, 142, 162, 155, 165, 172] },
  { id: "D017", name: "광주 충장로 직영점",   region: "광주", type: "직영",
    inventory: { "Galaxy S25 Ultra": 7,  "iPhone 16 Pro": 5,      "Galaxy S25+": 12,    "Galaxy A55": 30,  "Galaxy Z Flip6": 4 },
    dailySales: { "Galaxy S25 Ultra": 1.8, "iPhone 16 Pro": 1.4,  "Galaxy S25+": 1.9,   "Galaxy A55": 3.2, "Galaxy Z Flip6": 1.2 },
    weeklySales: [158, 165, 155, 175, 168, 178, 185] },
  { id: "D018", name: "광주 상무지구 대리점", region: "광주", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 2,  "iPhone 16": 3,          "Galaxy S25": 8,      "Galaxy A55": 20,  "Galaxy Z Flip6": 1 },
    dailySales: { "Galaxy S25 Ultra": 1.4, "iPhone 16": 1.2,      "Galaxy S25": 1.8,    "Galaxy A55": 2.6, "Galaxy Z Flip6": 0.9 },
    weeklySales: [125, 132, 122, 142, 135, 145, 152] },
  { id: "D019", name: "대전 둔산 직영점",     region: "대전", type: "직영",
    inventory: { "Galaxy S25 Ultra": 8,  "iPhone 16 Pro Max": 6,  "Galaxy S25+": 13,    "Galaxy A55": 34,  "Galaxy Z Flip6": 5 },
    dailySales: { "Galaxy S25 Ultra": 2.0, "iPhone 16 Pro Max": 1.6, "Galaxy S25+": 2.1, "Galaxy A55": 3.4, "Galaxy Z Flip6": 1.3 },
    weeklySales: [178, 185, 175, 195, 188, 198, 205] },
  { id: "D020", name: "대전 유성 대리점",     region: "대전", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 3,  "iPhone 16": 4,          "Galaxy S25": 9,      "Galaxy A55": 25,  "Pixel 9 Pro": 1 },
    dailySales: { "Galaxy S25 Ultra": 1.5, "iPhone 16": 1.4,      "Galaxy S25": 1.7,    "Galaxy A55": 2.8, "Pixel 9 Pro": 0.4 },
    weeklySales: [138, 145, 135, 152, 148, 158, 165] },
  { id: "D021", name: "춘천 직영점",          region: "강원/제주", type: "직영",
    inventory: { "Galaxy S25 Ultra": 4,  "iPhone 16 Pro": 3,      "Galaxy S25+": 8,     "Galaxy A55": 22,  "Galaxy Z Flip6": 2 },
    dailySales: { "Galaxy S25 Ultra": 1.2, "iPhone 16 Pro": 0.9,  "Galaxy S25+": 1.4,   "Galaxy A55": 2.4, "Galaxy Z Flip6": 0.7 },
    weeklySales: [98, 105, 95, 112, 108, 118, 125] },
  { id: "D022", name: "제주시 대리점",        region: "강원/제주", type: "대리점",
    inventory: { "Galaxy S25 Ultra": 3,  "iPhone 16": 2,          "Galaxy S25": 6,      "Galaxy A55": 15,  "Galaxy Z Flip6": 1 },
    dailySales: { "Galaxy S25 Ultra": 1.1, "iPhone 16": 1.0,      "Galaxy S25": 1.3,    "Galaxy A55": 2.0, "Galaxy Z Flip6": 0.8 },
    weeklySales: [85, 92, 82, 98, 94, 105, 112] },
];

// ─── 비즈니스 로직 엔진 ───
function calcStockItems(inventory, dailySales) {
  return Object.entries(inventory).map(([model, stock]) => {
    const rate = dailySales[model] || 0;
    return { model, stock, dailySales: rate, daysUntilStockout: rate > 0 ? Math.round((stock / rate) * 10) / 10 : 999 };
  }).sort((a, b) => a.daysUntilStockout - b.daysUntilStockout);
}

function enrichDealers(dealers) {
  return dealers.map(d => {
    const stockItems = calcStockItems(d.inventory, d.dailySales);
    const criticalItems = stockItems.filter(i => i.daysUntilStockout <= 3);
    const warningItems  = stockItems.filter(i => i.daysUntilStockout > 3 && i.daysUntilStockout <= 7);
    const minDays = stockItems[0]?.daysUntilStockout ?? 999;
    const totalStock = Object.values(d.inventory).reduce((s, v) => s + v, 0);
    const totalDailySales = Object.values(d.dailySales).reduce((s, v) => s + v, 0);
    const urgency = criticalItems.length > 0 ? "critical" : warningItems.length > 0 ? "warning" : "ok";
    const weeklyTotal = d.weeklySales.reduce((s, v) => s + v, 0);
    return { ...d, stockItems, criticalItems, warningItems, minDays, totalStock, totalDailySales, urgency, weeklyTotal };
  }).sort((a, b) => a.minDays - b.minDays);
}

function analyzeMetrics(data) {
  const m = data.monthly;
  const latest = m[m.length - 1];
  const prev   = m[m.length - 2];
  const totalRevenue = m.reduce((s, d) => s + d.revenue, 0);
  const totalCost    = m.reduce((s, d) => s + d.cost, 0);
  const totalOrders  = m.reduce((s, d) => s + d.orders, 0);
  const totalNewCust = m.reduce((s, d) => s + d.newCustomers, 0);
  const h1Rev = m.slice(0, 6).reduce((s, d) => s + d.revenue, 0);
  const h2Rev = m.slice(6).reduce((s, d) => s + d.revenue, 0);
  const yoyGrowth  = ((h2Rev - h1Rev) / h1Rev * 100).toFixed(1);
  const momGrowth  = ((latest.revenue - prev.revenue) / prev.revenue * 100).toFixed(1);
  const grossMargin = ((totalRevenue - totalCost) / totalRevenue * 100).toFixed(1);
  const returnRate  = (m.reduce((s, d) => s + d.returns, 0) / totalOrders * 100).toFixed(1);

  const products = data.products.map(p => {
    let quadrant;
    if (p.growth > 0.3 && p.margin > 0.3) quadrant = "Star";
    else if (p.growth <= 0.3 && p.margin > 0.3) quadrant = "Cash Cow";
    else if (p.growth > 0.3 && p.margin <= 0.3) quadrant = "Question Mark";
    else quadrant = "Dog";
    return { ...p, quadrant };
  });

  const channels = data.channels.map(c => ({
    ...c,
    roi: ((c.revenue - c.cost) / c.cost * 100).toFixed(0),
    cpa: (c.cost / c.deals).toFixed(0),
  }));

  const segments = data.customerSegments.map(s => ({
    ...s,
    ltvCacRatio: (s.ltv / s.acqCost).toFixed(1),
    arpu: (s.revenue / s.count).toFixed(0),
  }));

  const signals = [];
  if (parseFloat(momGrowth) > 10) signals.push({ type: "positive", msg: `전월 대비 ${momGrowth}% 매출 성장 - 모멘텀 유지 중` });
  if (parseFloat(momGrowth) < 0)  signals.push({ type: "negative", msg: `전월 대비 매출 ${Math.abs(momGrowth)}% 하락 - 원인 분석 필요` });
  if (parseFloat(grossMargin) < 30) signals.push({ type: "warning", msg: `매출총이익률 ${grossMargin}%로 30% 미달 - 원가 관리 강화 필요` });
  if (parseFloat(returnRate) > 5)   signals.push({ type: "warning", msg: `반품률 ${returnRate}% - 품질/CS 점검 필요` });
  const highGrowth = products.filter(p => p.growth > 0.3);
  if (highGrowth.length > 0) signals.push({ type: "positive", msg: `고성장 단말 ${highGrowth.length}개 - 투자 확대 검토` });
  const lowRetention = segments.filter(s => s.retention < 0.75);
  if (lowRetention.length > 0) signals.push({ type: "warning", msg: `이탈률 높은 세그먼트: ${lowRetention.map(s => s.segment).join(", ")}` });
  const topCh = [...channels].sort((a, b) => parseFloat(b.roi) - parseFloat(a.roi))[0];
  signals.push({ type: "info", msg: `최고 ROI 채널: ${topCh.channel} (${topCh.roi}%)` });

  return { kpis: { totalRevenue, totalCost, totalOrders, totalNewCust, yoyGrowth, momGrowth, grossMargin, returnRate }, products, channels, segments, signals };
}

// ─── 스타일 상수 ───
const C = {
  bg: "#0B0F1A", card: "#111827", border: "#1E293B",
  accent: "#06D6A0", accentDim: "rgba(6,214,160,0.15)",
  danger: "#EF4444", dangerDim: "rgba(239,68,68,0.15)",
  warning: "#F59E0B", warningDim: "rgba(245,158,11,0.15)",
  info: "#3B82F6", infoDim: "rgba(59,130,246,0.15)",
  text: "#F1F5F9", textDim: "#94A3B8", textMuted: "#64748B",
  chartColors: ["#06D6A0","#3B82F6","#F59E0B","#EF4444","#8B5CF6","#EC4899","#14B8A6","#F97316"],
};
const font = "'JetBrains Mono','Noto Sans KR',monospace";

// ─── 공통 컴포넌트 ───
const KPICard = ({ label, value, sub, trend, color = C.accent }) => (
  <div style={{ background: C.card, borderRadius: 12, padding: "20px 24px", border: `1px solid ${C.border}`, position: "relative", overflow: "hidden", minWidth: 0 }}>
    <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: color }} />
    <div style={{ fontSize: 11, color: C.textMuted, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 8, fontFamily: font }}>{label}</div>
    <div style={{ fontSize: 26, fontWeight: 700, color: C.text, fontFamily: font, lineHeight: 1.1 }}>{value}</div>
    <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8 }}>
      {trend !== undefined && (
        <span style={{ fontSize: 12, fontWeight: 600, fontFamily: font, color: parseFloat(trend) >= 0 ? C.accent : C.danger, background: parseFloat(trend) >= 0 ? C.accentDim : C.dangerDim, padding: "2px 8px", borderRadius: 4 }}>
          {parseFloat(trend) >= 0 ? "▲" : "▼"} {Math.abs(parseFloat(trend))}%
        </span>
      )}
      {sub && <span style={{ fontSize: 11, color: C.textMuted, fontFamily: font }}>{sub}</span>}
    </div>
  </div>
);

const SectionHeader = ({ icon, title, subtitle }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span style={{ fontSize: 15, fontWeight: 700, color: C.text, fontFamily: font }}>{title}</span>
    </div>
    {subtitle && <div style={{ fontSize: 11, color: C.textMuted, marginTop: 4, marginLeft: 26, fontFamily: font }}>{subtitle}</div>}
  </div>
);

const Card = ({ children, style = {} }) => (
  <div style={{ background: C.card, borderRadius: 12, padding: 20, border: `1px solid ${C.border}`, ...style }}>{children}</div>
);

const SignalBadge = ({ signal }) => {
  const clr  = { positive: C.accent, negative: C.danger, warning: C.warning, info: C.info };
  const bg   = { positive: C.accentDim, negative: C.dangerDim, warning: C.warningDim, info: C.infoDim };
  const icon = { positive: "✦", negative: "▲", warning: "⚠", info: "ℹ" };
  return (
    <div style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 14px", background: bg[signal.type], borderRadius: 8, borderLeft: `3px solid ${clr[signal.type]}` }}>
      <span style={{ fontSize: 13, flexShrink: 0 }}>{icon[signal.type]}</span>
      <span style={{ fontSize: 12.5, color: C.text, fontFamily: font, lineHeight: 1.5 }}>{signal.msg}</span>
    </div>
  );
};

const Tooltip2 = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#1E293B", border: "1px solid #334155", borderRadius: 8, padding: "10px 14px", fontFamily: font, fontSize: 11 }}>
      <div style={{ color: C.textDim, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: "flex", justifyContent: "space-between", gap: 16 }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 600 }}>{typeof p.value === "number" ? p.value.toLocaleString() : p.value}</span>
        </div>
      ))}
    </div>
  );
};

// ─── 재고 현황 탭 ───
function InventoryTab({ dealers }) {
  const [filterRegion, setFilterRegion] = useState("전체");
  const [filterUrgency, setFilterUrgency] = useState("전체");
  const [expandedId, setExpandedId] = useState(null);

  const regions = ["전체", ...Array.from(new Set(dealers.map(d => d.region)))];
  const urgencyLevels = ["전체", "위험(3일이내)", "주의(7일이내)", "정상"];

  const filtered = dealers.filter(d => {
    const rOk = filterRegion === "전체" || d.region === filterRegion;
    const uOk = filterUrgency === "전체"
      || (filterUrgency === "위험(3일이내)" && d.urgency === "critical")
      || (filterUrgency === "주의(7일이내)" && d.urgency === "warning")
      || (filterUrgency === "정상" && d.urgency === "ok");
    return rOk && uOk;
  });

  const urgencyColor = { critical: C.danger, warning: C.warning, ok: C.accent };
  const urgencyLabel = { critical: "위험", warning: "주의", ok: "정상" };
  const urgencyBg    = { critical: C.dangerDim, warning: C.warningDim, ok: C.accentDim };

  const criticalCount = dealers.filter(d => d.urgency === "critical").length;
  const warningCount  = dealers.filter(d => d.urgency === "warning").length;
  const okCount       = dealers.filter(d => d.urgency === "ok").length;

  return (
    <div>
      {/* 요약 KPI */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        <KPICard label="전체 대리점" value={dealers.length} sub="개소" color={C.info} />
        <KPICard label="재고 위험 (3일 이내)" value={criticalCount} sub="개 대리점" color={C.danger} />
        <KPICard label="재고 주의 (7일 이내)" value={warningCount} sub="개 대리점" color={C.warning} />
        <KPICard label="재고 정상" value={okCount} sub="개 대리점" color={C.accent} />
      </div>

      {/* 필터 */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: C.textMuted, fontFamily: font }}>지역:</span>
          {regions.map(r => (
            <button key={r} onClick={() => setFilterRegion(r)} style={{
              padding: "4px 12px", borderRadius: 6, border: `1px solid ${filterRegion === r ? C.accent : C.border}`,
              background: filterRegion === r ? C.accentDim : "transparent",
              color: filterRegion === r ? C.accent : C.textDim, fontFamily: font, fontSize: 11, cursor: "pointer",
            }}>{r}</button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 11, color: C.textMuted, fontFamily: font }}>긴급도:</span>
          {urgencyLevels.map(u => (
            <button key={u} onClick={() => setFilterUrgency(u)} style={{
              padding: "4px 12px", borderRadius: 6, border: `1px solid ${filterUrgency === u ? C.accent : C.border}`,
              background: filterUrgency === u ? C.accentDim : "transparent",
              color: filterUrgency === u ? C.accent : C.textDim, fontFamily: font, fontSize: 11, cursor: "pointer",
            }}>{u}</button>
          ))}
        </div>
      </div>

      {/* 대리점 목록 */}
      <Card>
        <SectionHeader icon="📦" title="대리점별 재고 현황" subtitle="재고 소진 예상 기준 우선순위 정렬 · 클릭하면 단말별 상세 보기" />
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: font, fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                {["긴급도","대리점명","지역","구분","총재고","일판매","최단소진","위험단말","주의단말","상세"].map(h => (
                  <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: C.textMuted, fontWeight: 500, fontSize: 10.5, textTransform: "uppercase", letterSpacing: 0.5, whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(d => (
                <>
                  <tr key={d.id} style={{ borderBottom: `1px solid ${C.border}22`, cursor: "pointer" }}
                    onClick={() => setExpandedId(expandedId === d.id ? null : d.id)}>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{ fontSize: 11, padding: "3px 10px", borderRadius: 4, background: urgencyBg[d.urgency], color: urgencyColor[d.urgency], fontWeight: 700 }}>
                        {urgencyLabel[d.urgency]}
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px", color: C.text, fontWeight: 500 }}>{d.name}</td>
                    <td style={{ padding: "10px 12px", color: C.textDim }}>{d.region}</td>
                    <td style={{ padding: "10px 12px", color: C.textDim }}>{d.type}</td>
                    <td style={{ padding: "10px 12px", color: C.text }}>{d.totalStock}대</td>
                    <td style={{ padding: "10px 12px", color: C.text }}>{d.totalDailySales.toFixed(1)}/일</td>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{ color: d.minDays <= 3 ? C.danger : d.minDays <= 7 ? C.warning : C.accent, fontWeight: 700 }}>
                        {d.minDays === 999 ? "-" : `${d.minDays}일`}
                      </span>
                      {d.minDays <= 7 && d.minDays !== 999 && (
                        <span style={{ fontSize: 10, color: C.textMuted, marginLeft: 4 }}>
                          ({d.stockItems[0]?.model?.replace("Galaxy ","").replace("iPhone ","")})
                        </span>
                      )}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {d.criticalItems.length > 0
                        ? <span style={{ color: C.danger, fontWeight: 600 }}>{d.criticalItems.length}종</span>
                        : <span style={{ color: C.textMuted }}>-</span>}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {d.warningItems.length > 0
                        ? <span style={{ color: C.warning, fontWeight: 600 }}>{d.warningItems.length}종</span>
                        : <span style={{ color: C.textMuted }}>-</span>}
                    </td>
                    <td style={{ padding: "10px 12px", color: C.textMuted, fontSize: 13 }}>{expandedId === d.id ? "▲" : "▼"}</td>
                  </tr>
                  {expandedId === d.id && (
                    <tr key={`${d.id}-detail`}>
                      <td colSpan={10} style={{ padding: "0 12px 16px 12px", background: "#0B0F1A" }}>
                        <div style={{ borderRadius: 8, overflow: "hidden", border: `1px solid ${C.border}` }}>
                          <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: font, fontSize: 11.5 }}>
                            <thead>
                              <tr style={{ background: C.card }}>
                                {["단말 모델","현재 재고","일 판매량","소진 예상일","소진 예상 시점","발주 권고"].map(h => (
                                  <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: C.textMuted, fontWeight: 500 }}>{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {d.stockItems.map((item, idx) => {
                                const isWarn = item.daysUntilStockout <= 7;
                                const isCrit = item.daysUntilStockout <= 3;
                                const today = new Date("2026-03-27");
                                const stockoutDate = item.daysUntilStockout < 999
                                  ? new Date(today.getTime() + item.daysUntilStockout * 86400000)
                                  : null;
                                const dateStr = stockoutDate
                                  ? `${stockoutDate.getMonth()+1}/${stockoutDate.getDate()} (${["일","월","화","수","목","금","토"][stockoutDate.getDay()]})`
                                  : "-";
                                const orderQty = Math.ceil(item.dailySales * 14);
                                return (
                                  <tr key={idx} style={{ borderTop: `1px solid ${C.border}22`, background: isCrit ? "rgba(239,68,68,0.05)" : isWarn ? "rgba(245,158,11,0.05)" : "transparent" }}>
                                    <td style={{ padding: "8px 12px", color: C.text, fontWeight: 500 }}>{item.model}</td>
                                    <td style={{ padding: "8px 12px", color: isCrit ? C.danger : isWarn ? C.warning : C.text, fontWeight: isCrit || isWarn ? 700 : 400 }}>{item.stock}대</td>
                                    <td style={{ padding: "8px 12px", color: C.textDim }}>{item.dailySales}/일</td>
                                    <td style={{ padding: "8px 12px" }}>
                                      <span style={{ color: isCrit ? C.danger : isWarn ? C.warning : C.accent, fontWeight: 600 }}>
                                        {item.daysUntilStockout === 999 ? "충분" : `${item.daysUntilStockout}일`}
                                      </span>
                                    </td>
                                    <td style={{ padding: "8px 12px", color: isCrit ? C.danger : isWarn ? C.warning : C.textDim }}>{dateStr}</td>
                                    <td style={{ padding: "8px 12px" }}>
                                      {(isCrit || isWarn)
                                        ? <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 4, background: isCrit ? C.dangerDim : C.warningDim, color: isCrit ? C.danger : C.warning, fontWeight: 600 }}>
                                            즉시 발주 {orderQty}대
                                          </span>
                                        : <span style={{ color: C.textMuted, fontSize: 11 }}>-</span>}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                        {/* 주간 판매 추이 */}
                        <div style={{ marginTop: 12, padding: "12px 16px", background: C.card, borderRadius: 8, border: `1px solid ${C.border}` }}>
                          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8, fontFamily: font }}>최근 7일 판매 추이</div>
                          <ResponsiveContainer width="100%" height={80}>
                            <BarChart data={d.weeklySales.map((v, i) => ({ day: `D-${6-i}`, sales: v }))}>
                              <XAxis dataKey="day" tick={{ fill: C.textMuted, fontSize: 9, fontFamily: font }} axisLine={false} tickLine={false} />
                              <YAxis hide />
                              <Bar dataKey="sales" fill={C.accent} radius={[3, 3, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 재고 부족 위험 단말 요약 */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <Card>
          <SectionHeader icon="🚨" title="즉시 발주 필요 현황" subtitle="3일 이내 소진 예상 단말" />
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {dealers.filter(d => d.criticalItems.length > 0).flatMap(d =>
              d.criticalItems.map((item, i) => (
                <div key={`${d.id}-${i}`} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderRadius: 6, background: C.dangerDim, border: `1px solid ${C.danger}33` }}>
                  <div>
                    <span style={{ fontSize: 12, color: C.text, fontWeight: 500 }}>{d.name}</span>
                    <span style={{ fontSize: 11, color: C.textMuted, marginLeft: 8 }}>{item.model}</span>
                  </div>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: C.textDim }}>재고 {item.stock}대</span>
                    <span style={{ fontSize: 12, color: C.danger, fontWeight: 700 }}>{item.daysUntilStockout}일 후 소진</span>
                  </div>
                </div>
              ))
            )}
            {dealers.filter(d => d.criticalItems.length > 0).length === 0 && (
              <div style={{ textAlign: "center", padding: 24, color: C.textMuted, fontSize: 12, fontFamily: font }}>즉시 발주 필요 대리점 없음</div>
            )}
          </div>
        </Card>
        <Card>
          <SectionHeader icon="⚠️" title="1주일 내 발주 권고 현황" subtitle="3~7일 이내 소진 예상 단말" />
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {dealers.filter(d => d.urgency === "warning").flatMap(d =>
              d.warningItems.map((item, i) => (
                <div key={`${d.id}-w-${i}`} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", borderRadius: 6, background: C.warningDim, border: `1px solid ${C.warning}33` }}>
                  <div>
                    <span style={{ fontSize: 12, color: C.text, fontWeight: 500 }}>{d.name}</span>
                    <span style={{ fontSize: 11, color: C.textMuted, marginLeft: 8 }}>{item.model}</span>
                  </div>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <span style={{ fontSize: 12, color: C.textDim }}>재고 {item.stock}대</span>
                    <span style={{ fontSize: 12, color: C.warning, fontWeight: 700 }}>{item.daysUntilStockout}일 후 소진</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── 메인 앱 ───
export default function PhoneSalesAgent() {
  const [activeTab, setActiveTab] = useState("overview");
  const [aiQuery, setAiQuery]     = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  const analysis = useMemo(() => analyzeMetrics(SALES_DATA), []);
  const dealers  = useMemo(() => enrichDealers(DEALERS_RAW), []);

  const monthlyChartData = SALES_DATA.monthly.map(d => ({
    name: d.month.slice(5),
    매출: d.revenue, 비용: d.cost, 이익: d.revenue - d.cost, 주문수: d.orders, 신규고객: d.newCustomers,
  }));

  const productChartData = analysis.products.map(p => ({
    name: p.name.length > 10 ? p.name.slice(0, 10) + ".." : p.name,
    매출: Math.round(p.revenue / 1000),
    마진율: (p.margin * 100).toFixed(0),
    성장률: (p.growth * 100).toFixed(0),
  }));

  const brandData = ["Samsung","Apple","Google"].map(brand => ({
    name: brand,
    value: analysis.products.filter(p => p.brand === brand).reduce((s, p) => s + p.revenue, 0),
  }));

  const channelRadarData = analysis.channels.map(c => ({
    channel: c.channel,
    ROI: Math.min(parseFloat(c.roi), 500) / 5,
    매출: c.revenue / 2500,
    효율: 100 - parseFloat(c.cpa) / 10,
  }));

  const segmentData = analysis.segments.map(s => ({
    name: s.segment,
    LTV_CAC: parseFloat(s.ltvCacRatio),
    ARPU: parseFloat(s.arpu) / 1000,
    유지율: (s.retention * 100).toFixed(0),
  }));

  const regionInventoryData = SALES_DATA.regions.map(r => {
    const regionDealers = dealers.filter(d => d.region === r.region);
    const criticalCount = regionDealers.filter(d => d.urgency === "critical").length;
    const warningCount  = regionDealers.filter(d => d.urgency === "warning").length;
    return { ...r, criticalCount, warningCount, dealerCount: regionDealers.length };
  });

  const askAI = useCallback(async () => {
    if (!aiQuery.trim()) return;
    setAiLoading(true);
    const currentQuery = aiQuery;
    setAiQuery("");
    const newHistory = [...chatHistory, { role: "user", content: currentQuery }];

    const ctx = `당신은 통신사 휴대폰 판매 전략 및 재고 관리 전문 컨설턴트입니다.
아래 데이터를 기반으로 구체적인 수치를 포함한 전략적 인사이트를 제공하세요.

## 월별 매출 현황
연간 총매출: ${analysis.kpis.totalRevenue.toLocaleString()}백만원
총이익률: ${analysis.kpis.grossMargin}%
전월대비 성장률: ${analysis.kpis.momGrowth}%
반기 성장률: ${analysis.kpis.yoyGrowth}%

## 단말별 데이터
${analysis.products.map(p => `- ${p.name}: 매출 ${p.revenue.toLocaleString()}백만, 마진 ${(p.margin*100).toFixed(0)}%, 성장률 ${(p.growth*100).toFixed(0)}%, BCG: ${p.quadrant}`).join("\n")}

## 재고 위험 대리점 (상위 5개)
${dealers.slice(0,5).map(d => `- ${d.name}(${d.region}): 최단소진 ${d.minDays}일, 위험단말 ${d.criticalItems.length}종`).join("\n")}

## 채널별 데이터
${analysis.channels.map(c => `- ${c.channel}: 매출 ${c.revenue.toLocaleString()}백만, ROI ${c.roi}%, CPA ${c.cpa}원`).join("\n")}

답변 형식: 한국어, 구체적 수치 근거, 실행 가능한 전략 3~5개, 300단어 이내`;

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: ctx,
          messages: newHistory.map(m => ({ role: m.role, content: m.content })),
        }),
      });
      const data = await res.json();
      const text = data.content?.map(c => c.text || "").join("\n") || "응답을 받지 못했습니다.";
      setChatHistory([...newHistory, { role: "assistant", content: text }]);
    } catch {
      setChatHistory([...newHistory, { role: "assistant", content: "AI 분석 요청 중 오류가 발생했습니다." }]);
    }
    setAiLoading(false);
  }, [aiQuery, analysis, dealers, chatHistory]);

  const tabs = [
    { id: "overview",   label: "종합 현황",     icon: "◉" },
    { id: "products",   label: "단말 분석",     icon: "◈" },
    { id: "channels",   label: "채널 & 고객",   icon: "◎" },
    { id: "inventory",  label: "단말 재고 현황", icon: "📦" },
    { id: "strategy",   label: "AI 전략 Agent", icon: "⚡" },
  ];

  return (
    <div style={{ fontFamily: "'Noto Sans KR',sans-serif", background: C.bg, minHeight: "100vh", color: C.text }}>
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet" />

      {/* 헤더 */}
      <div style={{ background: "linear-gradient(135deg,#0B0F1A,#111827)", borderBottom: `1px solid ${C.border}`, padding: "18px 28px", display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: `linear-gradient(135deg,${C.accent},${C.info})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 700, color: "#0B0F1A" }}>KT</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, fontFamily: font, letterSpacing: -0.5 }}>휴대폰 판매 전략 BI Agent</div>
            <div style={{ fontSize: 10.5, color: C.textMuted, fontFamily: font }}>전국 대리점 판매 · 재고 · 마케팅 의사결정 지원 · FY2025</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 4, background: "#1E293B", borderRadius: 8, padding: 3 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
              padding: "7px 14px", borderRadius: 6, border: "none", cursor: "pointer",
              fontFamily: font, fontSize: 11.5, fontWeight: 500, transition: "all 0.2s",
              background: activeTab === t.id ? C.accent : "transparent",
              color: activeTab === t.id ? "#0B0F1A" : C.textDim,
              whiteSpace: "nowrap",
            }}>{t.icon} {t.label}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "24px 28px", maxWidth: 1500, margin: "0 auto" }}>

        {/* ── 종합 현황 ── */}
        {activeTab === "overview" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 24 }}>
              <KPICard label="연간 총매출" value={`${(analysis.kpis.totalRevenue / 10).toFixed(0)}억원`} trend={analysis.kpis.yoyGrowth} sub="반기대비" color={C.accent} />
              <KPICard label="매출총이익률" value={`${analysis.kpis.grossMargin}%`} trend={analysis.kpis.momGrowth} sub="전월대비" color={C.info} />
              <KPICard label="연간 판매 대수" value={analysis.kpis.totalOrders.toLocaleString()} sub="대" color={C.warning} />
              <KPICard label="신규 가입자" value={analysis.kpis.totalNewCust.toLocaleString()} sub="명 (연간 누적)" trend="18.2" color="#8B5CF6" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 16, marginBottom: 24 }}>
              <Card>
                <SectionHeader icon="📈" title="월별 매출·이익 추이" subtitle="단위: 백만원" />
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="name" tick={{ fill: C.textMuted, fontSize: 11, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis tick={{ fill: C.textMuted, fontSize: 11, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Area type="monotone" dataKey="매출" fill="rgba(6,214,160,0.1)" stroke={C.accent} strokeWidth={2} />
                    <Area type="monotone" dataKey="이익" fill="rgba(59,130,246,0.1)" stroke={C.info} strokeWidth={2} />
                    <Bar dataKey="비용" fill="rgba(239,68,68,0.3)" radius={[3,3,0,0]} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
              <Card>
                <SectionHeader icon="🔔" title="전략 시그널" subtitle="비즈니스 로직 기반 자동 감지" />
                <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 280, overflowY: "auto" }}>
                  {analysis.signals.map((s, i) => <SignalBadge key={i} signal={s} />)}
                </div>
              </Card>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <Card>
                <SectionHeader icon="🗺️" title="지역별 매출 & 재고 현황" subtitle="단위: 백만원" />
                <ResponsiveContainer width="100%" height={260}>
                  <ComposedChart data={regionInventoryData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis type="number" tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis dataKey="region" type="category" tick={{ fill: C.textDim, fontSize: 11, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} width={72} />
                    <Tooltip content={<Tooltip2 />} />
                    <Bar dataKey="revenue" name="매출" radius={[0,4,4,0]}>
                      {regionInventoryData.map((_, i) => <Cell key={i} fill={C.chartColors[i]} />)}
                    </Bar>
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
              <Card>
                <SectionHeader icon="📊" title="월별 신규 가입자 & 판매 추이" />
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={monthlyChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="name" tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Line type="monotone" dataKey="주문수" stroke={C.accent} strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="신규고객" stroke={C.warning} strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        )}

        {/* ── 단말 분석 ── */}
        {activeTab === "products" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "3fr 1fr", gap: 16, marginBottom: 24 }}>
              <Card>
                <SectionHeader icon="📱" title="단말별 매출·마진·성장률" subtitle="매출(십억원), 마진율(%), 성장률(%)" />
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={productChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="name" tick={{ fill: C.textDim, fontSize: 9, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Bar dataKey="매출" fill={C.accent} radius={[4,4,0,0]} barSize={28} />
                    <Line type="monotone" dataKey="마진율" stroke={C.warning} strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="성장률" stroke={C.danger} strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
              <Card>
                <SectionHeader icon="🏷️" title="브랜드 비중" />
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={brandData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" stroke="none">
                      {brandData.map((_, i) => <Cell key={i} fill={C.chartColors[i]} />)}
                    </Pie>
                    <Tooltip content={<Tooltip2 />} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 8 }}>
                  {brandData.map((d, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, fontFamily: font, color: C.textDim }}>
                      <div style={{ width: 8, height: 8, borderRadius: 2, background: C.chartColors[i] }} />
                      {d.name} ({(d.value / brandData.reduce((s,c)=>s+c.value,0)*100).toFixed(0)}%)
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <Card>
              <SectionHeader icon="🧭" title="BCG 매트릭스 분류" subtitle="성장률·마진율 기반 단말 포지셔닝" />
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: font, fontSize: 12 }}>
                  <thead>
                    <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                      {["단말명","브랜드","카테고리","매출(백만)","마진율","성장률","만족도","BCG 분류"].map(h => (
                        <th key={h} style={{ padding: "10px 12px", textAlign: "left", color: C.textMuted, fontWeight: 500, fontSize: 10.5, textTransform: "uppercase", letterSpacing: 0.5 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.products.map((p, i) => {
                      const qc = { Star: C.accent, "Cash Cow": C.info, "Question Mark": C.warning, Dog: C.danger };
                      const ql = { Star: "⭐ Star", "Cash Cow": "💰 Cash Cow", "Question Mark": "❓ Question", Dog: "🐕 Dog" };
                      return (
                        <tr key={i} style={{ borderBottom: `1px solid ${C.border}22` }}>
                          <td style={{ padding: "10px 12px", color: C.text, fontWeight: 500 }}>{p.name}</td>
                          <td style={{ padding: "10px 12px", color: C.textDim }}>{p.brand}</td>
                          <td style={{ padding: "10px 12px", color: C.textDim }}>{p.category}</td>
                          <td style={{ padding: "10px 12px", color: C.text }}>{p.revenue.toLocaleString()}</td>
                          <td style={{ padding: "10px 12px" }}><span style={{ color: p.margin > 0.3 ? C.accent : C.warning }}>{(p.margin*100).toFixed(0)}%</span></td>
                          <td style={{ padding: "10px 12px" }}><span style={{ color: p.growth > 0.3 ? C.accent : C.textDim }}>{(p.growth*100).toFixed(0)}%</span></td>
                          <td style={{ padding: "10px 12px", color: C.text }}>{"★".repeat(Math.round(p.satisfaction))} {p.satisfaction}</td>
                          <td style={{ padding: "10px 12px" }}>
                            <span style={{ fontSize: 11, padding: "3px 10px", borderRadius: 4, background: `${qc[p.quadrant]}22`, color: qc[p.quadrant], fontWeight: 600 }}>{ql[p.quadrant]}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        )}

        {/* ── 채널 & 고객 ── */}
        {activeTab === "channels" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
              <Card>
                <SectionHeader icon="📡" title="채널별 ROI & 매출" subtitle="채널 효율성 비교" />
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={analysis.channels}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="channel" tick={{ fill: C.textDim, fontSize: 11, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Bar dataKey="revenue" name="매출(백만)" fill={C.accent} radius={[4,4,0,0]} barSize={28} />
                    <Bar dataKey="cost"    name="비용(백만)" fill="rgba(239,68,68,0.5)" radius={[4,4,0,0]} barSize={28} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
              <Card>
                <SectionHeader icon="🎯" title="채널 성과 레이더" subtitle="ROI·매출·효율 종합 비교" />
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={channelRadarData}>
                    <PolarGrid stroke="#1E293B" />
                    <PolarAngleAxis dataKey="channel" tick={{ fill: C.textDim, fontSize: 10, fontFamily: font }} />
                    <Radar name="ROI"  dataKey="ROI"  stroke={C.accent}  fill={C.accent}  fillOpacity={0.15} />
                    <Radar name="매출" dataKey="매출" stroke={C.info}    fill={C.info}    fillOpacity={0.15} />
                    <Radar name="효율" dataKey="효율" stroke={C.warning} fill={C.warning} fillOpacity={0.15} />
                    <Legend wrapperStyle={{ fontSize: 11, fontFamily: font }} />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>
            </div>

            <Card>
              <SectionHeader icon="👥" title="고객 세그먼트 분석" subtitle="LTV/CAC 비율 · ARPU · 유지율 비교" />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={segmentData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                    <XAxis dataKey="name" tick={{ fill: C.textDim, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <YAxis tick={{ fill: C.textMuted, fontSize: 10, fontFamily: font }} axisLine={{ stroke: "#1E293B" }} />
                    <Tooltip content={<Tooltip2 />} />
                    <Bar dataKey="LTV_CAC" name="LTV/CAC" fill={C.accent} radius={[4,4,0,0]} barSize={24} />
                    <Bar dataKey="ARPU"    name="ARPU(천원)" fill={C.info} radius={[4,4,0,0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
                <div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontFamily: font, fontSize: 12 }}>
                    <thead>
                      <tr style={{ borderBottom: `1px solid ${C.border}` }}>
                        {["세그먼트","고객수","LTV/CAC","유지율","ARPU"].map(h => (
                          <th key={h} style={{ padding: "8px 10px", textAlign: "left", color: C.textMuted, fontWeight: 500, fontSize: 10.5 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.segments.map((s, i) => (
                        <tr key={i} style={{ borderBottom: `1px solid ${C.border}22` }}>
                          <td style={{ padding: "8px 10px", color: C.text, fontWeight: 500 }}>{s.segment}</td>
                          <td style={{ padding: "8px 10px", color: C.textDim }}>{s.count.toLocaleString()}</td>
                          <td style={{ padding: "8px 10px" }}>
                            <span style={{ color: parseFloat(s.ltvCacRatio) >= 3 ? C.accent : C.warning, fontWeight: 600 }}>{s.ltvCacRatio}x</span>
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <div style={{ flex: 1, height: 4, background: "#1E293B", borderRadius: 2 }}>
                                <div style={{ width: `${s.retention * 100}%`, height: "100%", borderRadius: 2, background: s.retention > 0.85 ? C.accent : s.retention > 0.75 ? C.warning : C.danger }} />
                              </div>
                              <span style={{ fontSize: 11, color: C.textDim, minWidth: 36 }}>{(s.retention*100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td style={{ padding: "8px 10px", color: C.text }}>₩{parseInt(s.arpu).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ── 단말 재고 현황 ── */}
        {activeTab === "inventory" && <InventoryTab dealers={dealers} />}

        {/* ── AI 전략 Agent ── */}
        {activeTab === "strategy" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <Card style={{ marginBottom: 16 }}>
                <SectionHeader icon="⚡" title="AI 판매 전략 Agent" subtitle="판매 데이터 기반 전략 지원 & 재고 발주 의사결정" />
                <div style={{ background: "#0B0F1A", borderRadius: 8, padding: 16, minHeight: 360, maxHeight: 480, overflowY: "auto", marginBottom: 12, border: `1px solid ${C.border}` }}>
                  {chatHistory.length === 0 && !aiLoading && (
                    <div style={{ textAlign: "center", padding: "60px 20px" }}>
                      <div style={{ fontSize: 36, marginBottom: 12 }}>🤖</div>
                      <div style={{ fontSize: 13, color: C.textDim, marginBottom: 8 }}>휴대폰 판매 전략 AI Agent</div>
                      <div style={{ fontSize: 12, color: C.textMuted, lineHeight: 1.8 }}>
                        판매·재고 데이터 기반 전략적 질문을 해보세요.<br />
                        예: "재고 위험 대리점 대응 전략은?" <br />
                        "Galaxy S25 Ultra 판매 확대 방안은?"
                      </div>
                    </div>
                  )}
                  {chatHistory.map((msg, i) => (
                    <div key={i} style={{ marginBottom: 12, display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                      <div style={{ maxWidth: "85%", padding: "10px 14px", borderRadius: 10, fontSize: 12.5, lineHeight: 1.8, fontFamily: font,
                        background: msg.role === "user" ? C.accentDim : "#1E293B",
                        color: msg.role === "user" ? C.accent : C.text,
                        border: `1px solid ${msg.role === "user" ? C.accent+"33" : C.border}`,
                        whiteSpace: "pre-wrap" }}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {aiLoading && (
                    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
                      <div style={{ padding: "10px 14px", borderRadius: 10, background: "#1E293B", border: `1px solid ${C.border}`, fontSize: 13, color: C.textDim }}>
                        분석 중...
                      </div>
                    </div>
                  )}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <input value={aiQuery} onChange={e => setAiQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && askAI()}
                    placeholder="전략 질문을 입력하세요..."
                    style={{ flex: 1, padding: "10px 14px", borderRadius: 8, border: `1px solid ${C.border}`, background: "#0B0F1A", color: C.text, fontFamily: font, fontSize: 12.5, outline: "none" }} />
                  <button onClick={askAI} disabled={aiLoading || !aiQuery.trim()} style={{ padding: "10px 20px", borderRadius: 8, border: "none", cursor: "pointer", background: C.accent, color: "#0B0F1A", fontWeight: 700, fontFamily: font, fontSize: 12, opacity: aiLoading || !aiQuery.trim() ? 0.4 : 1 }}>분석</button>
                </div>
              </Card>
              <Card>
                <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 10, fontFamily: font }}>💡 추천 질문</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {[
                    "재고 위험 대리점 긴급 대응 전략은?",
                    "Galaxy S25 Ultra 판매 확대 방안",
                    "온라인몰 채널 ROI 극대화 전략",
                    "청소년/대학생 세그먼트 이탈 방지",
                    "경기 지역 신규 대리점 확장 전략",
                    "폴더블폰 성장세 활용 마케팅 전략",
                    "H2 vs H1 성과 비교 분석",
                    "프리미엄 고객 LTV 향상 방안",
                  ].map((q, i) => (
                    <button key={i} onClick={() => setAiQuery(q)} style={{ padding: "6px 12px", borderRadius: 6, border: `1px solid ${C.border}`, background: "transparent", color: C.textDim, fontFamily: font, fontSize: 11, cursor: "pointer" }}
                      onMouseEnter={e => { e.target.style.borderColor = C.accent; e.target.style.color = C.accent; }}
                      onMouseLeave={e => { e.target.style.borderColor = C.border; e.target.style.color = C.textDim; }}>
                      {q}
                    </button>
                  ))}
                </div>
              </Card>
            </div>

            <div>
              <Card style={{ marginBottom: 16 }}>
                <SectionHeader icon="📌" title="핵심 지표 요약" subtitle="AI Agent 참조 데이터" />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { label: "연간 총매출",    value: `${(analysis.kpis.totalRevenue/10).toFixed(0)}억원`, color: C.accent },
                    { label: "총이익률",       value: `${analysis.kpis.grossMargin}%`,   color: C.info },
                    { label: "성장률(H2/H1)", value: `${analysis.kpis.yoyGrowth}%`,   color: C.warning },
                    { label: "반품률",         value: `${analysis.kpis.returnRate}%`,    color: C.danger },
                  ].map((item, i) => (
                    <div key={i} style={{ padding: "12px 14px", borderRadius: 8, background: "#0B0F1A", border: `1px solid ${C.border}` }}>
                      <div style={{ fontSize: 10, color: C.textMuted, fontFamily: font, marginBottom: 4 }}>{item.label}</div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: item.color, fontFamily: font }}>{item.value}</div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card style={{ marginBottom: 16 }}>
                <SectionHeader icon="🚨" title="재고 긴급 현황" subtitle="즉시 조치 필요" />
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {dealers.filter(d => d.urgency !== "ok").slice(0, 8).map((d, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "7px 12px", borderRadius: 6, background: "#0B0F1A", border: `1px solid ${C.border}` }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: d.urgency === "critical" ? C.danger : C.warning }} />
                        <span style={{ fontSize: 11.5, color: C.text, fontFamily: font }}>{d.name}</span>
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ fontSize: 11, color: C.textDim, fontFamily: font }}>위험 {d.criticalItems.length}종</span>
                        <span style={{ fontSize: 11, color: d.urgency === "critical" ? C.danger : C.warning, fontWeight: 600, fontFamily: font }}>최단 {d.minDays}일</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              <Card>
                <SectionHeader icon="📋" title="비즈니스 로직 규칙" />
                <div style={{ fontSize: 11, color: C.textDim, fontFamily: font, lineHeight: 2.2 }}>
                  {[
                    { color: C.danger,   label: "R1", rule: "재고 ≤ 3일치 → 즉시 발주 (14일치 수량)" },
                    { color: C.warning,  label: "R2", rule: "재고 ≤ 7일치 → 이번 주 내 발주 권고" },
                    { color: C.accent,   label: "R3", rule: "성장률 >30% & 마진 >30% → Star 집중 투자" },
                    { color: C.info,     label: "R4", rule: "LTV/CAC >3x → 고수익 세그먼트 리텐션 강화" },
                    { color: "#8B5CF6",  label: "R5", rule: "유지율 <75% → 이탈 경보 CS 프로세스 개선" },
                  ].map((r, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                      <span style={{ color: r.color, flexShrink: 0, fontWeight: 700 }}>{r.label}</span>
                      <span>{r.rule}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
        * { box-sizing: border-box; }
      `}</style>
    </div>
  );
}
