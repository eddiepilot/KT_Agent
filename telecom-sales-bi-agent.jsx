import { useState, useEffect, useMemo, useCallback } from "react";
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Legend, ComposedChart } from "recharts";

// ═══════════════════════════════════════════
// 📱 정형 데이터
// ═══════════════════════════════════════════
const PHONE_MODELS = [
  { id: "SM01", name: "갤럭시 S25 Ultra", brand: "삼성", tier: "플래그십", price: 1798000, margin: 0.12, color: "#3B82F6" },
  { id: "SM02", name: "갤럭시 S25+", brand: "삼성", tier: "플래그십", price: 1353000, margin: 0.11, color: "#60A5FA" },
  { id: "SM03", name: "갤럭시 S25", brand: "삼성", tier: "플래그십", price: 1155000, margin: 0.10, color: "#93C5FD" },
  { id: "SM04", name: "갤럭시 Z 폴드6", brand: "삼성", tier: "폴더블", price: 2339000, margin: 0.13, color: "#8B5CF6" },
  { id: "SM05", name: "갤럭시 Z 플립6", brand: "삼성", tier: "폴더블", price: 1419000, margin: 0.12, color: "#A78BFA" },
  { id: "SM06", name: "갤럭시 A36", brand: "삼성", tier: "중저가", price: 429000, margin: 0.08, color: "#06B6D4" },
  { id: "SM07", name: "갤럭시 버디4", brand: "삼성", tier: "보급형", price: 253000, margin: 0.06, color: "#22D3EE" },
  { id: "AP01", name: "iPhone 17 Pro Max", brand: "애플", tier: "플래그십", price: 1990000, margin: 0.09, color: "#F43F5E" },
  { id: "AP02", name: "iPhone 17 Pro", brand: "애플", tier: "플래그십", price: 1690000, margin: 0.09, color: "#FB7185" },
  { id: "AP03", name: "iPhone 17", brand: "애플", tier: "프리미엄", price: 1350000, margin: 0.08, color: "#FDA4AF" },
  { id: "AP04", name: "iPhone SE 4", brand: "애플", tier: "중저가", price: 690000, margin: 0.07, color: "#FECDD3" },
  { id: "XI01", name: "샤오미 14T Pro", brand: "샤오미", tier: "프리미엄", price: 649000, margin: 0.10, color: "#F59E0B" },
];

const REGIONS = ["서울","경기","인천","부산","대구","대전","광주","울산","세종","강원","충북","충남","전북","전남","경북","경남","제주"];

const seed = (x) => Math.abs(Math.sin(x * 9301 + 49297) % 1);

function generateDealers() {
  const dealerNames = {
    "서울":["강남본점","홍대점","명동점","잠실점","영등포점","노원점"],"경기":["수원점","분당점","일산점","용인점","안양점"],
    "인천":["부평점","송도점","인천공항점"],"부산":["서면점","해운대점","남포점"],"대구":["동성로점","수성점"],
    "대전":["둔산점","유성점"],"광주":["충장로점","상무점"],"울산":["삼산점"],"세종":["세종점"],
    "강원":["춘천점","원주점"],"충북":["청주점"],"충남":["천안점","아산점"],"전북":["전주점"],
    "전남":["순천점","목포점"],"경북":["포항점","구미점"],"경남":["창원점","김해점"],"제주":["제주시점","서귀포점"],
  };
  const dealers = [];
  let id = 1;
  Object.entries(dealerNames).forEach(([region, names]) => {
    names.forEach((name) => {
      const sz = region === "서울" ? 2.2 : region === "경기" ? 1.8 : region === "부산" ? 1.4 : 1.0;
      const inventory = {}, dailySales = {}, weeklyTrend = {};
      PHONE_MODELS.forEach((phone, pi) => {
        const s = seed(id * 100 + pi);
        const base = Math.round((phone.tier === "플래그십" ? 3.5 : phone.tier === "폴더블" ? 1.8 : phone.tier === "프리미엄" ? 2.5 : phone.tier === "중저가" ? 4.0 : 3.0) * sz * (0.6 + s * 0.8));
        const stock = Math.round((5 + s * 25) * sz * (phone.tier === "보급형" ? 0.6 : 1));
        dailySales[phone.id] = base;
        inventory[phone.id] = stock;
        weeklyTrend[phone.id] = [0,1,2,3,4,5,6].map(d => Math.max(0, Math.round(base * (0.5 + seed(id*1000+pi*10+d) * 1.0))));
      });
      dealers.push({
        id: `D${String(id).padStart(3,"0")}`, name: `${region} ${name}`, region,
        grade: sz >= 2 ? "S" : sz >= 1.4 ? "A" : "B",
        inventory, dailySales, weeklyTrend,
        monthlySales: Math.round(Object.values(dailySales).reduce((s,v)=>s+v,0)*30),
        monthlyRevenue: Math.round(PHONE_MODELS.reduce((s,p)=>s+dailySales[p.id]*p.price*30,0)/10000),
      });
      id++;
    });
  });
  return dealers;
}
const DEALERS = generateDealers();

const MONTHLY_SALES = [
  { month:"2025-07", units:142300, revenue:1428, newSubs:38200, churn:12400, arpu:52300, newAct:18600, mnp:12400, deviceChange:7200 },
  { month:"2025-08", units:138700, revenue:1394, newSubs:36800, churn:13100, arpu:52100, newAct:17200, mnp:12800, deviceChange:6800 },
  { month:"2025-09", units:168400, revenue:1842, newSubs:48600, churn:11200, arpu:53200, newAct:22400, mnp:16800, deviceChange:9400 },
  { month:"2025-10", units:155200, revenue:1624, newSubs:42100, churn:12800, arpu:52800, newAct:19800, mnp:14200, deviceChange:8100 },
  { month:"2025-11", units:161800, revenue:1712, newSubs:44300, churn:11900, arpu:53100, newAct:20600, mnp:15200, deviceChange:8500 },
  { month:"2025-12", units:178600, revenue:1956, newSubs:52800, churn:10800, arpu:53800, newAct:25200, mnp:18400, deviceChange:9200 },
  { month:"2026-01", units:189200, revenue:2124, newSubs:56200, churn:10200, arpu:54200, newAct:27800, mnp:18800, deviceChange:9600 },
  { month:"2026-02", units:172400, revenue:1878, newSubs:48900, churn:11400, arpu:53600, newAct:23200, mnp:16400, deviceChange:9300 },
  { month:"2026-03", units:183600, revenue:2048, newSubs:52400, churn:10600, arpu:54000, newAct:25600, mnp:17200, deviceChange:9600 },
];

function generateDailyData() {
  const days = [];
  const baseDate = new Date(2026, 2, 27);
  for (let i = 89; i >= 0; i--) {
    const d = new Date(baseDate); d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0,10);
    const dow = d.getDay();
    const wm = (dow===0||dow===6)?1.35:1.0;
    const phones = {};
    PHONE_MODELS.forEach((p,pi) => {
      const tb = DEALERS.reduce((s,dl)=>s+dl.dailySales[p.id],0);
      phones[p.id] = Math.round(tb*(0.7+seed(i*100+pi)*0.6)*wm);
    });
    days.push({date:dateStr,phones,total:Object.values(phones).reduce((s,v)=>s+v,0)});
  }
  return days;
}
const DAILY_DATA = generateDailyData();

// ═══════════════════════════════════════════
// 🧠 비즈니스 로직
// ═══════════════════════════════════════════
function analyzeInventory(dealers) {
  return dealers.map(dealer => {
    const phoneAlerts = [];
    PHONE_MODELS.forEach(phone => {
      const stock=dealer.inventory[phone.id], avg=dealer.dailySales[phone.id];
      const trend=dealer.weeklyTrend[phone.id];
      const ra=trend.slice(-3).reduce((s,v)=>s+v,0)/3;
      const eff=Math.max(avg,ra);
      const dr=eff>0?Math.round(stock/eff*10)/10:999;
      const td=ra>avg*1.15?"급증":ra<avg*0.85?"감소":"보합";
      const ro=Math.max(0,Math.round(eff*14-stock));
      let status="정상",urgency=0;
      if(dr<=2){status="긴급";urgency=3;}else if(dr<=5){status="주의";urgency=2;}else if(dr<=7){status="관심";urgency=1;}
      const sd=dr<999?new Date(Date.now()+dr*86400000).toLocaleDateString("ko-KR",{month:"short",day:"numeric"}):"-";
      phoneAlerts.push({phoneId:phone.id,phoneName:phone.name,brand:phone.brand,stock,avgDaily:eff,daysRemaining:dr,trendDirection:td,status,urgency,recommendOrder:ro,shortageDate:sd});
    });
    return {...dealer,phoneAlerts,criticalCount:phoneAlerts.filter(a=>a.urgency>=2).length,maxUrgency:Math.max(...phoneAlerts.map(a=>a.urgency))};
  }).sort((a,b)=>(b.maxUrgency-a.maxUrgency)||(b.criticalCount-a.criticalCount)||(({S:3,A:2,B:1}[b.grade]||0)-({S:3,A:2,B:1}[a.grade]||0)));
}

function computeKPIs() {
  const latest=MONTHLY_SALES[MONTHLY_SALES.length-1],prev=MONTHLY_SALES[MONTHLY_SALES.length-2];
  return {latest,momGrowth:((latest.units-prev.units)/prev.units*100).toFixed(1),netAdd:MONTHLY_SALES.reduce((s,m)=>s+m.newSubs,0)-MONTHLY_SALES.reduce((s,m)=>s+m.churn,0)};
}

// ═══════════════════════════════════════════
// 🎨 스타일
// ═══════════════════════════════════════════
const C = {
  bg:"#06080F",card:"#0D1117",cardAlt:"#161B22",border:"#21262D",
  accent:"#58A6FF",accentDim:"rgba(88,166,255,0.12)",
  green:"#3FB950",greenDim:"rgba(63,185,80,0.12)",
  red:"#F85149",redDim:"rgba(248,81,73,0.12)",
  orange:"#D29922",orangeDim:"rgba(210,153,34,0.12)",
  purple:"#BC8CFF",purpleDim:"rgba(188,140,255,0.12)",
  cyan:"#39D2C0",cyanDim:"rgba(57,210,192,0.12)",
  text:"#E6EDF3",textDim:"#8B949E",textMuted:"#484F58",
  charts:["#58A6FF","#3FB950","#D29922","#F85149","#BC8CFF","#F778BA","#79C0FF","#56D364","#E3B341","#FF7B72"],
};
const F="'JetBrains Mono','Noto Sans KR',monospace";

// ═══════════════════════════════════════════
// 🧩 공통 컴포넌트
// ═══════════════════════════════════════════
const KPI=({label,value,sub,trend,color=C.accent,icon})=>(<div style={{background:C.card,borderRadius:10,padding:"16px 20px",border:`1px solid ${C.border}`,position:"relative",overflow:"hidden"}}><div style={{position:"absolute",top:0,left:0,right:0,height:2,background:color}}/><div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}><div><div style={{fontSize:10,color:C.textMuted,textTransform:"uppercase",letterSpacing:1.2,marginBottom:6,fontFamily:F}}>{label}</div><div style={{fontSize:24,fontWeight:700,color:C.text,fontFamily:F}}>{value}</div></div>{icon&&<span style={{fontSize:22,opacity:0.6}}>{icon}</span>}</div><div style={{display:"flex",alignItems:"center",gap:6,marginTop:6}}>{trend!==undefined&&<span style={{fontSize:11,fontWeight:600,fontFamily:F,color:parseFloat(trend)>=0?C.green:C.red,background:parseFloat(trend)>=0?C.greenDim:C.redDim,padding:"2px 7px",borderRadius:4}}>{parseFloat(trend)>=0?"▲":"▼"} {Math.abs(parseFloat(trend))}%</span>}{sub&&<span style={{fontSize:10,color:C.textMuted,fontFamily:F}}>{sub}</span>}</div></div>);
const Card=({children,style={}})=><div style={{background:C.card,borderRadius:10,padding:18,border:`1px solid ${C.border}`,...style}}>{children}</div>;
const Hdr=({icon,title,sub})=><div style={{marginBottom:14}}><div style={{display:"flex",alignItems:"center",gap:7}}><span style={{fontSize:15}}>{icon}</span><span style={{fontSize:14,fontWeight:700,color:C.text,fontFamily:F}}>{title}</span></div>{sub&&<div style={{fontSize:10,color:C.textMuted,marginTop:3,marginLeft:22,fontFamily:F}}>{sub}</div>}</div>;
const Bdg=({text,color,bg})=><span style={{fontSize:10.5,fontWeight:600,padding:"2px 8px",borderRadius:4,color,background:bg,fontFamily:F,whiteSpace:"nowrap"}}>{text}</span>;
const Tip=({active,payload,label})=>{if(!active||!payload?.length)return null;return <div style={{background:"#1C2128",border:`1px solid ${C.border}`,borderRadius:6,padding:"8px 12px",fontFamily:F,fontSize:10.5}}><div style={{color:C.textDim,marginBottom:4}}>{label}</div>{payload.map((p,i)=><div key={i} style={{color:p.color,display:"flex",justifyContent:"space-between",gap:14}}><span>{p.name}</span><span style={{fontWeight:600}}>{typeof p.value==="number"?p.value.toLocaleString():p.value}</span></div>)}</div>;};
const StatusBdg=({status})=>{const m={"긴급":{c:C.red,b:C.redDim,i:"🔴"},"주의":{c:C.orange,b:C.orangeDim,i:"🟠"},"관심":{c:C.accent,b:C.accentDim,i:"🔵"},"정상":{c:C.green,b:C.greenDim,i:"🟢"}};const s=m[status]||m["정상"];return <Bdg text={`${s.i} ${status}`} color={s.c} bg={s.b}/>;};
const TabBtn=({active,onClick,children})=><button onClick={onClick} style={{padding:"5px 14px",borderRadius:5,border:`1px solid ${active?C.accent:C.border}`,background:active?C.accentDim:"transparent",color:active?C.accent:C.textDim,fontFamily:F,fontSize:10.5,cursor:"pointer",transition:"all 0.15s"}}>{children}</button>;
const DateInput=({value,onChange})=><input type="date" value={value} onChange={e=>onChange(e.target.value)} style={{padding:"5px 8px",borderRadius:5,border:`1px solid ${C.border}`,background:C.cardAlt,color:C.text,fontFamily:F,fontSize:10.5,outline:"none"}}/>;

// ═══════════════════════════════════════════
// 📦 발주 모달
// ═══════════════════════════════════════════
const OrderModal=({dealer,onClose})=>{
  const[quantities,setQuantities]=useState({});
  const[submitting,setSubmitting]=useState(false);
  const[submitted,setSubmitted]=useState(false);
  useEffect(()=>{if(dealer){const init={};dealer.phoneAlerts.filter(a=>a.recommendOrder>0).forEach(a=>{init[a.phoneId]=a.recommendOrder;});setQuantities(init);setSubmitted(false);}},[dealer]);
  if(!dealer)return null;
  const totalItems=Object.values(quantities).reduce((s,v)=>s+(parseInt(v)||0),0);
  const handleSubmit=()=>{setSubmitting(true);setTimeout(()=>{setSubmitting(false);setSubmitted(true);},1500);};

  return(
    <div style={{position:"fixed",inset:0,zIndex:1000,display:"flex",alignItems:"center",justifyContent:"center",background:"rgba(0,0,0,0.7)",backdropFilter:"blur(4px)"}}>
      <div style={{background:C.card,border:`1px solid ${C.border}`,borderRadius:12,width:700,maxHeight:"82vh",overflow:"hidden",display:"flex",flexDirection:"column"}}>
        <div style={{padding:"16px 20px",borderBottom:`1px solid ${C.border}`,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div>
            <div style={{fontSize:14,fontWeight:700,color:C.text,fontFamily:F}}>📦 재고 발주 — {dealer.name}</div>
            <div style={{fontSize:10,color:C.textMuted,fontFamily:F,marginTop:2}}>물류센터 발주 주문서 · {dealer.id} · {dealer.grade}등급</div>
          </div>
          <button onClick={onClose} style={{background:"none",border:"none",color:C.textDim,fontSize:18,cursor:"pointer",padding:4}}>✕</button>
        </div>
        {submitted?(
          <div style={{padding:"60px 20px",textAlign:"center"}}>
            <div style={{fontSize:48,marginBottom:12}}>✅</div>
            <div style={{fontSize:16,fontWeight:700,color:C.green,fontFamily:F}}>발주 주문이 완료되었습니다</div>
            <div style={{fontSize:12,color:C.textDim,fontFamily:F,marginTop:8,lineHeight:1.8}}>
              주문번호: ORD-{Date.now().toString().slice(-8)}<br/>
              대리점: {dealer.name} ({dealer.id})<br/>
              총 {totalItems}대 · 물류센터 배송 예정: {new Date(Date.now()+86400000*2).toLocaleDateString("ko-KR")}
            </div>
            <button onClick={onClose} style={{marginTop:20,padding:"8px 24px",borderRadius:6,border:"none",background:C.accent,color:"#06080F",fontWeight:700,fontFamily:F,fontSize:12,cursor:"pointer"}}>확인</button>
          </div>
        ):(
          <>
            <div style={{flex:1,overflowY:"auto",padding:"12px 20px"}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
                <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
                  {["단말명","현재재고","일평균","잔여일","권장수량","발주수량"].map(h=><th key={h} style={{padding:"8px 6px",textAlign:"left",color:C.textMuted,fontWeight:500,fontSize:9.5}}>{h}</th>)}
                </tr></thead>
                <tbody>{dealer.phoneAlerts.sort((a,b)=>b.urgency-a.urgency).map((a,i)=>(
                  <tr key={i} style={{borderBottom:`1px solid ${C.border}22`,background:a.urgency>=2?C.redDim:"transparent"}}>
                    <td style={{padding:"7px 6px",color:C.text,fontWeight:500}}>{a.phoneName}</td>
                    <td style={{padding:"7px 6px",color:a.stock<5?C.red:C.textDim}}>{a.stock}대</td>
                    <td style={{padding:"7px 6px",color:C.textDim}}>{a.avgDaily.toFixed(1)}</td>
                    <td style={{padding:"7px 6px",color:a.daysRemaining<=2?C.red:a.daysRemaining<=5?C.orange:C.green,fontWeight:600}}>{a.daysRemaining<100?`${a.daysRemaining}일`:"충분"}</td>
                    <td style={{padding:"7px 6px",color:C.accent}}>{a.recommendOrder>0?`${a.recommendOrder}대`:"-"}</td>
                    <td style={{padding:"7px 6px"}}><input type="number" min="0" value={quantities[a.phoneId]||""} placeholder="0" onChange={e=>setQuantities(prev=>({...prev,[a.phoneId]:e.target.value}))} style={{width:70,padding:"4px 6px",borderRadius:4,border:`1px solid ${C.border}`,background:C.bg,color:C.text,fontFamily:F,fontSize:11,outline:"none",textAlign:"right"}}/></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <div style={{padding:"14px 20px",borderTop:`1px solid ${C.border}`,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
              <div style={{fontSize:12,fontFamily:F}}><span style={{color:C.textDim}}>총 발주: </span><span style={{color:C.accent,fontWeight:700}}>{totalItems.toLocaleString()}대</span><span style={{color:C.textMuted,marginLeft:8}}>배송: {new Date(Date.now()+86400000*2).toLocaleDateString("ko-KR")}</span></div>
              <div style={{display:"flex",gap:8}}>
                <button onClick={onClose} style={{padding:"8px 16px",borderRadius:6,border:`1px solid ${C.border}`,background:"transparent",color:C.textDim,fontFamily:F,fontSize:11,cursor:"pointer"}}>취소</button>
                <button onClick={handleSubmit} disabled={totalItems===0||submitting} style={{padding:"8px 20px",borderRadius:6,border:"none",background:totalItems>0?C.accent:C.textMuted,color:"#06080F",fontWeight:700,fontFamily:F,fontSize:11,cursor:totalItems>0?"pointer":"default",opacity:submitting?0.5:1}}>
                  {submitting?"발주 처리 중...":"🚚 물류센터 발주"}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════
// 📱 메인 앱
// ═══════════════════════════════════════════
export default function TelecomBIAgent(){
  const[tab,setTab]=useState("overview");
  const[aiQuery,setAiQuery]=useState("");
  const[aiLoading,setAiLoading]=useState(false);
  const[chatHistory,setChatHistory]=useState([]);
  const[invFilter,setInvFilter]=useState("all");
  const[invRegion,setInvRegion]=useState("전체");
  const[invGrade,setInvGrade]=useState("전체");
  const[invSearch,setInvSearch]=useState("");
  const[expandedDealer,setExpandedDealer]=useState(null);
  const[orderDealer,setOrderDealer]=useState(null);
  const[regionMetric,setRegionMetric]=useState("sales");
  const[devicePeriod,setDevicePeriod]=useState("30d");
  const[deviceDateFrom,setDeviceDateFrom]=useState("2026-02-25");
  const[deviceDateTo,setDeviceDateTo]=useState("2026-03-27");
  const[detailDateFrom,setDetailDateFrom]=useState("2026-03-20");
  const[detailDateTo,setDetailDateTo]=useState("2026-03-27");

  const kpis=useMemo(()=>computeKPIs(),[]);
  const dealerAnalysis=useMemo(()=>analyzeInventory(DEALERS),[]);

  const filteredDealers=useMemo(()=>{
    let list=dealerAnalysis;
    if(invFilter==="critical")list=list.filter(d=>d.maxUrgency>=2);
    else if(invFilter==="warning")list=list.filter(d=>d.maxUrgency>=1);
    if(invRegion!=="전체")list=list.filter(d=>d.region===invRegion);
    if(invGrade!=="전체")list=list.filter(d=>d.grade===invGrade);
    if(invSearch)list=list.filter(d=>d.name.includes(invSearch)||d.id.includes(invSearch));
    return list;
  },[dealerAnalysis,invFilter,invRegion,invGrade,invSearch]);

  const monthlyChart=MONTHLY_SALES.map(d=>({name:d.month.slice(5),판매량:d.units,신규가입:d.newSubs,해지:d.churn}));

  const subsTypeData=useMemo(()=>{
    const l=MONTHLY_SALES[MONTHLY_SALES.length-1];
    return[{name:"신규개통",value:l.newAct,color:C.accent},{name:"번호이동",value:l.mnp,color:C.green},{name:"기기변경",value:l.deviceChange,color:C.orange}];
  },[]);

  const brandShare=useMemo(()=>{const t={};DEALERS.forEach(d=>PHONE_MODELS.forEach(p=>{if(!t[p.brand])t[p.brand]=0;t[p.brand]+=d.dailySales[p.id]*30;}));return Object.entries(t).map(([name,value])=>({name,value}));},[]);

  const regionData=useMemo(()=>{
    const t={};
    DEALERS.forEach(d=>{if(!t[d.region])t[d.region]={region:d.region,판매량:0,매출:0,재고량:0,대리점수:0};t[d.region].판매량+=d.monthlySales;t[d.region].매출+=d.monthlyRevenue;t[d.region].재고량+=Object.values(d.inventory).reduce((s,v)=>s+v,0);t[d.region].대리점수+=1;});
    return Object.values(t).sort((a,b)=>b.매출-a.매출);
  },[]);

  const inventorySummary=useMemo(()=>{const cr=dealerAnalysis.filter(d=>d.maxUrgency>=2).length;const wr=dealerAnalysis.filter(d=>d.maxUrgency===1).length;const ts=DEALERS.reduce((s,d)=>s+Object.values(d.inventory).reduce((a,b)=>a+b,0),0);return{critical:cr,warning:wr,normal:DEALERS.length-cr-wr,totalStock:ts};},[dealerAnalysis]);

  const filteredDailyData=useMemo(()=>DAILY_DATA.filter(d=>d.date>=deviceDateFrom&&d.date<=deviceDateTo),[deviceDateFrom,deviceDateTo]);
  const detailDailyData=useMemo(()=>DAILY_DATA.filter(d=>d.date>=detailDateFrom&&d.date<=detailDateTo),[detailDateFrom,detailDateTo]);

  const devicePerfData=useMemo(()=>PHONE_MODELS.map(p=>{
    const total=filteredDailyData.reduce((s,d)=>s+(d.phones[p.id]||0),0);
    return{name:p.name.length>9?p.name.slice(0,9)+"..":p.name,fullName:p.name,판매량:total,마진:p.margin*100,color:p.color};
  }),[filteredDailyData]);

  // AI
  const askAI=useCallback(async()=>{
    if(!aiQuery.trim())return;setAiLoading(true);const cq=aiQuery;setAiQuery("");const nh=[...chatHistory,{role:"user",content:cq}];
    const ctx=`당신은 한국 이동통신사의 수석 마케팅 전략 컨설턴트입니다.
## 전사 KPI - 최근월: ${kpis.latest.units.toLocaleString()}대, ${kpis.latest.revenue}억원, ARPU ${kpis.latest.arpu.toLocaleString()}원, 전월대비 ${kpis.momGrowth}%
- 가입유형: 신규개통${kpis.latest.newAct.toLocaleString()}, 번호이동${kpis.latest.mnp.toLocaleString()}, 기기변경${kpis.latest.deviceChange.toLocaleString()}
## 단말 ${PHONE_MODELS.length}종
${PHONE_MODELS.map(p=>`- ${p.name}(${p.brand}/${p.tier}): ₩${p.price.toLocaleString()}, 마진${(p.margin*100)}%`).join("\n")}
## 대리점 ${DEALERS.length}개: 긴급${inventorySummary.critical}, 주의${inventorySummary.warning}, 전체재고${inventorySummary.totalStock.toLocaleString()}대
## 지역TOP5
${regionData.slice(0,5).map(r=>`- ${r.region}: ${r.판매량.toLocaleString()}대, ${r.매출.toLocaleString()}만원`).join("\n")}
답변: 수치근거, 실행전략3~5개, 우선순위, 한국어, 400단어이내`;
    try{const res=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1000,system:ctx,messages:nh})});const data=await res.json();const text=data.content?.map(c=>c.text||"").join("\n")||"응답 실패";setChatHistory([...nh,{role:"assistant",content:text}]);}catch{setChatHistory([...nh,{role:"assistant",content:"AI 분석 오류."}]);}
    setAiLoading(false);
  },[aiQuery,chatHistory,kpis,inventorySummary,regionData]);

  const tabs=[{id:"overview",label:"종합 현황",icon:"◉"},{id:"devices",label:"단말 분석",icon:"◆"},{id:"inventory",label:"단말 재고 현황",icon:"◈"},{id:"regions",label:"지역·대리점",icon:"◇"},{id:"strategy",label:"AI 전략 Agent",icon:"⚡"}];

  return(
    <div style={{fontFamily:"'Noto Sans KR',sans-serif",background:C.bg,minHeight:"100vh",color:C.text}}>
      <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet"/>
      {/* 헤더 */}
      <div style={{background:C.card,borderBottom:`1px solid ${C.border}`,padding:"16px 24px",display:"flex",alignItems:"center",justifyContent:"space-between",position:"sticky",top:0,zIndex:100}}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={{width:34,height:34,borderRadius:8,background:`linear-gradient(135deg,${C.accent},${C.purple})`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,fontWeight:700,color:"#06080F"}}>T</div>
          <div><div style={{fontSize:14.5,fontWeight:700,fontFamily:F,letterSpacing:-0.3}}>Telecom Sales BI Agent</div><div style={{fontSize:9.5,color:C.textMuted,fontFamily:F}}>통신사 휴대폰 판매 전략 · 재고 관리 · 마케팅 의사결정</div></div>
        </div>
        <div style={{display:"flex",gap:3,background:C.cardAlt,borderRadius:8,padding:3,flexWrap:"wrap"}}>
          {tabs.map(t=><button key={t.id} onClick={()=>setTab(t.id)} style={{padding:"7px 14px",borderRadius:6,border:"none",cursor:"pointer",fontFamily:F,fontSize:11,fontWeight:500,background:tab===t.id?C.accent:"transparent",color:tab===t.id?"#06080F":C.textDim,transition:"all 0.15s"}}>{t.icon} {t.label}</button>)}
        </div>
      </div>

      <div style={{padding:"20px 24px",maxWidth:1440,margin:"0 auto"}}>

        {/* ════════ 종합 현황 ════════ */}
        {tab==="overview"&&(<div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:12,marginBottom:20}}>
            <KPI label="월 판매량" value={`${(kpis.latest.units/10000).toFixed(1)}만대`} trend={kpis.momGrowth} sub="전월대비" icon="📱" color={C.accent}/>
            <KPI label="월 매출" value={`${kpis.latest.revenue}억`} sub="원" icon="💰" color={C.green}/>
            <KPI label="ARPU" value={`₩${kpis.latest.arpu.toLocaleString()}`} icon="👤" color={C.purple}/>
            <KPI label="순증 가입자" value={`${((kpis.latest.newSubs-kpis.latest.churn)/1000).toFixed(1)}K`} sub="신규-해지" icon="📊" color={C.orange}/>
            <KPI label="재고 경보" value={`${inventorySummary.critical}개점`} sub={`주의 ${inventorySummary.warning}개점`} icon="🚨" color={C.red}/>
          </div>

          <div style={{display:"grid",gridTemplateColumns:"5fr 3fr",gap:12,marginBottom:20}}>
            <Card>
              <Hdr icon="📈" title="월별 판매·가입 추이" sub="판매량(바) · 신규가입·해지(선)"/>
              <ResponsiveContainer width="100%" height={260}>
                <ComposedChart data={monthlyChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                  <XAxis dataKey="name" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                  <YAxis yAxisId="left" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                  <YAxis yAxisId="right" orientation="right" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                  <Tooltip content={<Tip/>}/>
                  <Bar yAxisId="left" dataKey="판매량" fill={C.accent} radius={[4,4,0,0]} barSize={26} fillOpacity={0.85}/>
                  <Line yAxisId="right" type="monotone" dataKey="신규가입" stroke={C.green} strokeWidth={2} dot={{r:3}}/>
                  <Line yAxisId="right" type="monotone" dataKey="해지" stroke={C.red} strokeWidth={1.5} strokeDasharray="4 4" dot={{r:2}}/>
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
            <div style={{display:"flex",flexDirection:"column",gap:12}}>
              <Card>
                <Hdr icon="🔄" title="가입유형 비중" sub={`${MONTHLY_SALES[MONTHLY_SALES.length-1].month} 기준`}/>
                <ResponsiveContainer width="100%" height={140}>
                  <PieChart><Pie data={subsTypeData} cx="50%" cy="50%" innerRadius={35} outerRadius={58} dataKey="value" stroke="none" paddingAngle={3}>
                    {subsTypeData.map((d,i)=><Cell key={i} fill={d.color}/>)}
                  </Pie><Tooltip content={<Tip/>}/></PieChart>
                </ResponsiveContainer>
                <div style={{display:"flex",justifyContent:"center",gap:12,flexWrap:"wrap"}}>
                  {subsTypeData.map((d,i)=>{const total=subsTypeData.reduce((s,x)=>s+x.value,0);return <span key={i} style={{fontSize:10,color:C.textDim,fontFamily:F}}><span style={{display:"inline-block",width:7,height:7,borderRadius:2,background:d.color,marginRight:4}}/>{d.name} {(d.value/total*100).toFixed(0)}%</span>;})}
                </div>
              </Card>
              <Card>
                <Hdr icon="🏭" title="브랜드 점유율"/>
                <ResponsiveContainer width="100%" height={100}>
                  <PieChart><Pie data={brandShare} cx="50%" cy="50%" innerRadius={25} outerRadius={44} dataKey="value" stroke="none">{brandShare.map((_,i)=><Cell key={i} fill={C.charts[i]}/>)}</Pie><Tooltip content={<Tip/>}/></PieChart>
                </ResponsiveContainer>
                <div style={{display:"flex",justifyContent:"center",gap:12,flexWrap:"wrap"}}>{brandShare.map((d,i)=>{const total=brandShare.reduce((s,b)=>s+b.value,0);return <span key={i} style={{fontSize:10,color:C.textDim,fontFamily:F}}><span style={{display:"inline-block",width:7,height:7,borderRadius:2,background:C.charts[i],marginRight:4}}/>{d.name} {(d.value/total*100).toFixed(0)}%</span>;})}</div>
              </Card>
            </div>
          </div>

          <Card>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:14}}>
              <Hdr icon="🗺" title="지역별 월간 판매 현황"/>
              <div style={{display:"flex",gap:4}}><TabBtn active={regionMetric==="sales"} onClick={()=>setRegionMetric("sales")}>판매량</TabBtn><TabBtn active={regionMetric==="revenue"} onClick={()=>setRegionMetric("revenue")}>매출</TabBtn></div>
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={regionData.slice(0,12)}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                <XAxis dataKey="region" tick={{fill:C.textDim,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                <YAxis tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                <Tooltip content={<Tip/>}/>
                {regionMetric==="sales"?<Bar dataKey="판매량" name="판매량(대)" fill={C.accent} radius={[4,4,0,0]} barSize={22}/>:<Bar dataKey="매출" name="매출(만원)" fill={C.purple} radius={[4,4,0,0]} barSize={22}/>}
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>)}

        {/* ════════ 단말 분석 ════════ */}
        {tab==="devices"&&(<div>
          <Card style={{marginBottom:20}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:10,marginBottom:14}}>
              <Hdr icon="📱" title="단말 라인업 성과 분석" sub="기간 내 총 판매량 · 마진율(%)"/>
              <div style={{display:"flex",gap:6,alignItems:"center",flexWrap:"wrap"}}>
                {[{id:"7d",label:"7일"},{id:"14d",label:"14일"},{id:"30d",label:"30일"},{id:"custom",label:"기간선택"}].map(p=>(
                  <TabBtn key={p.id} active={devicePeriod===p.id} onClick={()=>{setDevicePeriod(p.id);const end="2026-03-27";if(p.id==="7d")setDeviceDateFrom("2026-03-20");else if(p.id==="14d")setDeviceDateFrom("2026-03-13");else if(p.id==="30d")setDeviceDateFrom("2026-02-25");if(p.id!=="custom")setDeviceDateTo(end);}}>{p.label}</TabBtn>
                ))}
                {devicePeriod==="custom"&&<><DateInput value={deviceDateFrom} onChange={setDeviceDateFrom}/><span style={{color:C.textMuted,fontSize:11}}>~</span><DateInput value={deviceDateTo} onChange={setDeviceDateTo}/></>}
                <span style={{fontSize:10,color:C.textMuted,fontFamily:F}}>{filteredDailyData.length}일간</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={devicePerfData}>
                <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                <XAxis dataKey="name" tick={{fill:C.textDim,fontSize:9.5,fontFamily:F}} axisLine={{stroke:C.border}} angle={-20} textAnchor="end" height={50}/>
                <YAxis yAxisId="left" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                <YAxis yAxisId="right" orientation="right" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                <Tooltip content={<Tip/>}/>
                <Bar yAxisId="left" dataKey="판매량" name="판매량(대)" radius={[4,4,0,0]} barSize={24}>{devicePerfData.map((d,i)=><Cell key={i} fill={d.color}/>)}</Bar>
                <Line yAxisId="right" type="monotone" dataKey="마진" name="마진(%)" stroke={C.orange} strokeWidth={2} dot={{r:3}}/>
              </ComposedChart>
            </ResponsiveContainer>
          </Card>

          <Card>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:10,marginBottom:14}}>
              <Hdr icon="📋" title="단말별 상세 현황" sub="일 단위 기간 조회"/>
              <div style={{display:"flex",gap:6,alignItems:"center"}}><DateInput value={detailDateFrom} onChange={setDetailDateFrom}/><span style={{color:C.textMuted,fontSize:11}}>~</span><DateInput value={detailDateTo} onChange={setDetailDateTo}/><span style={{fontSize:10,color:C.textMuted,fontFamily:F}}>{detailDailyData.length}일간</span></div>
            </div>
            <div style={{overflowX:"auto"}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11.5}}>
                <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>
                  {["모델명","브랜드","등급","출고가","마진율","기간판매","일평균","월매출(추정)","전국재고"].map(h=><th key={h} style={{padding:"8px 10px",textAlign:"left",color:C.textMuted,fontWeight:500,fontSize:10}}>{h}</th>)}
                </tr></thead>
                <tbody>{PHONE_MODELS.map((p,i)=>{
                  const pt=detailDailyData.reduce((s,d)=>s+(d.phones[p.id]||0),0);
                  const da=detailDailyData.length>0?Math.round(pt/detailDailyData.length):0;
                  const ts=DEALERS.reduce((s,d)=>s+d.inventory[p.id],0);
                  const mr=Math.round(da*30*p.price/100000000*10)/10;
                  return(<tr key={i} style={{borderBottom:`1px solid ${C.border}22`}}>
                    <td style={{padding:"8px 10px",color:C.text,fontWeight:500}}><span style={{display:"inline-block",width:8,height:8,borderRadius:2,background:p.color,marginRight:6}}/>{p.name}</td>
                    <td style={{padding:"8px 10px",color:C.textDim}}>{p.brand}</td>
                    <td style={{padding:"8px 10px"}}><Bdg text={p.tier} color={p.tier==="플래그십"?C.accent:p.tier==="폴더블"?C.purple:p.tier==="프리미엄"?C.orange:C.green} bg={p.tier==="플래그십"?C.accentDim:p.tier==="폴더블"?C.purpleDim:p.tier==="프리미엄"?C.orangeDim:C.greenDim}/></td>
                    <td style={{padding:"8px 10px",color:C.text}}>₩{p.price.toLocaleString()}</td>
                    <td style={{padding:"8px 10px",color:C.orange}}>{(p.margin*100).toFixed(0)}%</td>
                    <td style={{padding:"8px 10px",color:C.accent,fontWeight:600}}>{pt.toLocaleString()}대</td>
                    <td style={{padding:"8px 10px",color:C.textDim}}>{da.toLocaleString()}대</td>
                    <td style={{padding:"8px 10px",color:C.purple}}>₩{mr}억</td>
                    <td style={{padding:"8px 10px",color:ts<da*5?C.red:C.text}}>{ts.toLocaleString()}대</td>
                  </tr>);
                })}</tbody>
              </table>
            </div>
          </Card>
        </div>)}

        {/* ════════ 단말 재고 현황 ════════ */}
        {tab==="inventory"&&(<div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:16}}>
            <KPI label="전국 총 재고" value={`${inventorySummary.totalStock.toLocaleString()}대`} icon="📦" color={C.accent}/>
            <KPI label="긴급 대리점" value={`${inventorySummary.critical}개점`} sub="2일 이내 소진" icon="🔴" color={C.red}/>
            <KPI label="주의 대리점" value={`${inventorySummary.warning}개점`} sub="5일 이내 소진" icon="🟠" color={C.orange}/>
            <KPI label="정상 대리점" value={`${inventorySummary.normal}개점`} icon="🟢" color={C.green}/>
          </div>
          <Card style={{marginBottom:16,padding:"12px 18px"}}>
            <div style={{display:"flex",gap:8,alignItems:"center",flexWrap:"wrap"}}>
              <span style={{fontSize:11,color:C.textMuted,fontFamily:F}}>상태:</span>
              {[{id:"all",label:"전체"},{id:"critical",label:"🔴 긴급/주의"},{id:"warning",label:"🔵 관심 이상"}].map(f=><TabBtn key={f.id} active={invFilter===f.id} onClick={()=>setInvFilter(f.id)}>{f.label}</TabBtn>)}
              <span style={{fontSize:11,color:C.textMuted,fontFamily:F,marginLeft:4}}>등급:</span>
              {["전체","S","A","B"].map(g=><TabBtn key={g} active={invGrade===g} onClick={()=>setInvGrade(g)}>{g==="전체"?"전체":g+"등급"}</TabBtn>)}
              <select value={invRegion} onChange={e=>setInvRegion(e.target.value)} style={{padding:"5px 10px",borderRadius:5,border:`1px solid ${C.border}`,background:C.cardAlt,color:C.text,fontFamily:F,fontSize:11,cursor:"pointer"}}><option value="전체">전체 지역</option>{REGIONS.map(r=><option key={r} value={r}>{r}</option>)}</select>
              <input placeholder="대리점 검색..." value={invSearch} onChange={e=>setInvSearch(e.target.value)} style={{padding:"5px 10px",borderRadius:5,border:`1px solid ${C.border}`,background:C.cardAlt,color:C.text,fontFamily:F,fontSize:11,flex:1,minWidth:100,outline:"none"}}/>
              <span style={{fontSize:10.5,color:C.textMuted,fontFamily:F}}>{filteredDealers.length}개점</span>
            </div>
          </Card>

          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {filteredDealers.slice(0,20).map(dealer=>{
              const isExp=expandedDealer===dealer.id;
              return(
                <Card key={dealer.id} style={{padding:0,overflow:"hidden"}}>
                  <div style={{padding:"12px 18px",display:"flex",alignItems:"center",justifyContent:"space-between",background:dealer.maxUrgency>=2?C.redDim:"transparent",borderLeft:`4px solid ${dealer.maxUrgency>=2?C.red:dealer.maxUrgency>=1?C.orange:C.green}`}}>
                    <div onClick={()=>setExpandedDealer(isExp?null:dealer.id)} style={{display:"flex",alignItems:"center",gap:12,flex:1,cursor:"pointer"}}>
                      <Bdg text={dealer.grade} color={dealer.grade==="S"?C.accent:dealer.grade==="A"?C.green:C.textDim} bg={dealer.grade==="S"?C.accentDim:dealer.grade==="A"?C.greenDim:C.border+"44"}/>
                      <div><div style={{fontSize:13,fontWeight:600,color:C.text,fontFamily:F}}>{dealer.name}</div><div style={{fontSize:10,color:C.textMuted,fontFamily:F}}>{dealer.id} · 월 {dealer.monthlySales.toLocaleString()}대 · ₩{dealer.monthlyRevenue.toLocaleString()}만</div></div>
                    </div>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      {dealer.maxUrgency>=2&&<Bdg text={`긴급 ${dealer.phoneAlerts.filter(a=>a.urgency>=2).length}건`} color={C.red} bg={C.redDim}/>}
                      {dealer.phoneAlerts.filter(a=>a.urgency===1).length>0&&<Bdg text={`관심 ${dealer.phoneAlerts.filter(a=>a.urgency===1).length}건`} color={C.accent} bg={C.accentDim}/>}
                      <button onClick={e=>{e.stopPropagation();setOrderDealer(dealer);}} style={{padding:"5px 12px",borderRadius:5,border:`1px solid ${C.cyan}44`,background:C.cyanDim,color:C.cyan,fontFamily:F,fontSize:10.5,fontWeight:600,cursor:"pointer",whiteSpace:"nowrap"}}
                        onMouseEnter={e=>{e.target.style.background=C.cyan;e.target.style.color="#06080F";}} onMouseLeave={e=>{e.target.style.background=C.cyanDim;e.target.style.color=C.cyan;}}>📦 재고 발주</button>
                      <span onClick={()=>setExpandedDealer(isExp?null:dealer.id)} style={{fontSize:12,color:C.textMuted,cursor:"pointer",padding:"4px"}}>{isExp?"▲":"▼"}</span>
                    </div>
                  </div>
                  {isExp&&(<div style={{padding:"0 18px 14px",background:C.cardAlt}}>
                    <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11}}>
                      <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["상태","단말명","현재재고","일평균","잔여일수","추세","부족예상일","권장발주"].map(h=><th key={h} style={{padding:"8px 8px",textAlign:"left",color:C.textMuted,fontWeight:500,fontSize:9.5}}>{h}</th>)}</tr></thead>
                      <tbody>{dealer.phoneAlerts.sort((a,b)=>b.urgency-a.urgency).map((a,i)=>(
                        <tr key={i} style={{borderBottom:`1px solid ${C.border}22`,background:a.urgency>=2?C.redDim:"transparent"}}>
                          <td style={{padding:"6px 8px"}}><StatusBdg status={a.status}/></td>
                          <td style={{padding:"6px 8px",color:C.text,fontWeight:500}}>{a.phoneName}</td>
                          <td style={{padding:"6px 8px",color:a.stock<5?C.red:C.text,fontWeight:a.stock<5?700:400}}>{a.stock}대</td>
                          <td style={{padding:"6px 8px",color:C.textDim}}>{a.avgDaily.toFixed(1)}대</td>
                          <td style={{padding:"6px 8px"}}><span style={{color:a.daysRemaining<=2?C.red:a.daysRemaining<=5?C.orange:a.daysRemaining<=7?C.accent:C.green,fontWeight:600}}>{a.daysRemaining<100?`${a.daysRemaining}일`:"충분"}</span></td>
                          <td style={{padding:"6px 8px"}}><span style={{color:a.trendDirection==="급증"?C.red:a.trendDirection==="감소"?C.green:C.textDim}}>{a.trendDirection==="급증"?"📈 급증":a.trendDirection==="감소"?"📉 감소":"➡ 보합"}</span></td>
                          <td style={{padding:"6px 8px",color:a.urgency>=2?C.red:a.urgency>=1?C.orange:C.textDim,fontWeight:a.urgency>=1?600:400}}>{a.shortageDate}</td>
                          <td style={{padding:"6px 8px"}}>{a.recommendOrder>0?<span style={{color:C.accent,fontWeight:600}}>{a.recommendOrder}대</span>:<span style={{color:C.textMuted}}>-</span>}</td>
                        </tr>
                      ))}</tbody>
                    </table>
                  </div>)}
                </Card>
              );
            })}
            {filteredDealers.length>20&&<div style={{textAlign:"center",padding:12,fontSize:11,color:C.textMuted,fontFamily:F}}>+ {filteredDealers.length-20}개 대리점 더 있음</div>}
          </div>
        </div>)}

        {/* ════════ 지역·대리점 ════════ */}
        {tab==="regions"&&(<div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:20}}>
            <Card>
              <Hdr icon="🗺" title="지역별 판매량 & 재고량" sub="월간 판매(대) · 현재 재고(대)"/>
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={regionData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                  <XAxis type="number" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                  <YAxis dataKey="region" type="category" tick={{fill:C.textDim,fontSize:10.5,fontFamily:F}} axisLine={{stroke:C.border}} width={50}/>
                  <Tooltip content={<Tip/>}/><Legend wrapperStyle={{fontSize:10,fontFamily:F}}/>
                  <Bar dataKey="판매량" name="판매량(대)" fill={C.accent} radius={[0,4,4,0]} barSize={10}/>
                  <Bar dataKey="재고량" name="재고량(대)" fill={C.orange} radius={[0,4,4,0]} barSize={10}/>
                </BarChart>
              </ResponsiveContainer>
            </Card>
            <Card>
              <Hdr icon="💰" title="지역별 매출 현황" sub="월간 매출(만원)"/>
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={regionData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke={C.border}/>
                  <XAxis type="number" tick={{fill:C.textMuted,fontSize:10,fontFamily:F}} axisLine={{stroke:C.border}}/>
                  <YAxis dataKey="region" type="category" tick={{fill:C.textDim,fontSize:10.5,fontFamily:F}} axisLine={{stroke:C.border}} width={50}/>
                  <Tooltip content={<Tip/>}/>
                  <Bar dataKey="매출" name="매출(만원)" radius={[0,6,6,0]} barSize={14}>{regionData.map((_,i)=><Cell key={i} fill={C.charts[i%C.charts.length]}/>)}</Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>
          <Card>
            <Hdr icon="📊" title="대리점 성과 랭킹" sub="월 매출 기준 TOP 15"/>
            <div style={{overflowX:"auto"}}>
              <table style={{width:"100%",borderCollapse:"collapse",fontFamily:F,fontSize:11.5}}>
                <thead><tr style={{borderBottom:`1px solid ${C.border}`}}>{["순위","대리점","등급","지역","월판매량","월매출","재고현황"].map(h=><th key={h} style={{padding:"8px 10px",textAlign:"left",color:C.textMuted,fontWeight:500,fontSize:10}}>{h}</th>)}</tr></thead>
                <tbody>{[...dealerAnalysis].sort((a,b)=>b.monthlyRevenue-a.monthlyRevenue).slice(0,15).map((d,i)=>(
                  <tr key={d.id} style={{borderBottom:`1px solid ${C.border}22`}}>
                    <td style={{padding:"8px 10px",color:i<3?C.accent:C.textDim,fontWeight:i<3?700:400}}>#{i+1}</td>
                    <td style={{padding:"8px 10px",color:C.text,fontWeight:500}}>{d.name}</td>
                    <td style={{padding:"8px 10px"}}><Bdg text={d.grade} color={d.grade==="S"?C.accent:d.grade==="A"?C.green:C.textDim} bg={d.grade==="S"?C.accentDim:d.grade==="A"?C.greenDim:C.border+"44"}/></td>
                    <td style={{padding:"8px 10px",color:C.textDim}}>{d.region}</td>
                    <td style={{padding:"8px 10px",color:C.text}}>{d.monthlySales.toLocaleString()}대</td>
                    <td style={{padding:"8px 10px",color:C.accent}}>₩{d.monthlyRevenue.toLocaleString()}만</td>
                    <td style={{padding:"8px 10px"}}>{d.maxUrgency>=2?<Bdg text={`긴급 ${d.criticalCount}`} color={C.red} bg={C.redDim}/>:d.maxUrgency>=1?<Bdg text="관심" color={C.orange} bg={C.orangeDim}/>:<Bdg text="정상" color={C.green} bg={C.greenDim}/>}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </Card>
        </div>)}

        {/* ════════ AI 전략 Agent ════════ */}
        {tab==="strategy"&&(<div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
          <div>
            <Card style={{marginBottom:12}}>
              <Hdr icon="⚡" title="AI 전략 분석 Agent" sub="통신사 판매 데이터 기반 전략 질의 & 추천"/>
              <div style={{background:C.bg,borderRadius:8,padding:14,minHeight:340,maxHeight:460,overflowY:"auto",marginBottom:10,border:`1px solid ${C.border}`}}>
                {chatHistory.length===0&&!aiLoading&&(<div style={{textAlign:"center",padding:"50px 16px"}}><div style={{fontSize:32,marginBottom:10}}>🤖</div><div style={{fontSize:13,color:C.textDim}}>통신사 판매 전략 AI Agent</div><div style={{fontSize:11,color:C.textMuted,lineHeight:1.9,marginTop:8}}>판매 데이터 기반 전략적 질문을 해보세요.<br/>예: "번호이동 점유율 확대 전략은?"</div></div>)}
                {chatHistory.map((msg,i)=>(<div key={i} style={{marginBottom:10,display:"flex",justifyContent:msg.role==="user"?"flex-end":"flex-start"}}><div style={{maxWidth:"85%",padding:"9px 13px",borderRadius:9,fontSize:12,lineHeight:1.8,fontFamily:F,whiteSpace:"pre-wrap",background:msg.role==="user"?C.accentDim:C.cardAlt,color:msg.role==="user"?C.accent:C.text,border:`1px solid ${msg.role==="user"?C.accent+"33":C.border}`}}>{msg.content}</div></div>))}
                {aiLoading&&<div style={{display:"flex",justifyContent:"flex-start"}}><div style={{padding:"9px 13px",borderRadius:9,background:C.cardAlt,border:`1px solid ${C.border}`,fontSize:12,color:C.textDim}}><span style={{animation:"pulse 1.5s infinite"}}>전략 분석 중...</span></div></div>}
              </div>
              <div style={{display:"flex",gap:8}}>
                <input value={aiQuery} onChange={e=>setAiQuery(e.target.value)} onKeyDown={e=>e.key==="Enter"&&askAI()} placeholder="전략 질문을 입력하세요..." style={{flex:1,padding:"9px 13px",borderRadius:7,border:`1px solid ${C.border}`,background:C.bg,color:C.text,fontFamily:F,fontSize:12,outline:"none"}}/>
                <button onClick={askAI} disabled={aiLoading||!aiQuery.trim()} style={{padding:"9px 18px",borderRadius:7,border:"none",cursor:"pointer",background:C.accent,color:"#06080F",fontWeight:700,fontFamily:F,fontSize:11.5,opacity:aiLoading||!aiQuery.trim()?0.4:1}}>분석</button>
              </div>
            </Card>
            <Card>
              <div style={{fontSize:10,color:C.textMuted,marginBottom:8,fontFamily:F}}>💡 추천 질문</div>
              <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                {["번호이동 점유율 확대 전략","갤럭시 S25 Ultra vs iPhone 17 Pro Max 판촉","재고 긴급 대리점 우선 발주 계획","중저가 단말 수익성 개선","서울 외 지역 판매 확대","폴더블폰 마케팅 차별화","ARPU 향상 프리미엄 번들","기기변경 고객 리텐션"].map((q,i)=>(
                  <button key={i} onClick={()=>setAiQuery(q)} style={{padding:"5px 10px",borderRadius:5,border:`1px solid ${C.border}`,background:"transparent",color:C.textDim,fontFamily:F,fontSize:10.5,cursor:"pointer"}}
                    onMouseEnter={e=>{e.target.style.borderColor=C.accent;e.target.style.color=C.accent;}} onMouseLeave={e=>{e.target.style.borderColor=C.border;e.target.style.color=C.textDim;}}>{q}</button>
                ))}
              </div>
            </Card>
          </div>
          <div>
            <Card style={{marginBottom:12}}>
              <Hdr icon="📊" title="핵심 지표 요약"/>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
                {[{l:"월 판매량",v:`${(kpis.latest.units/10000).toFixed(1)}만대`,c:C.accent},{l:"월 매출",v:`${kpis.latest.revenue}억`,c:C.green},{l:"ARPU",v:`₩${kpis.latest.arpu.toLocaleString()}`,c:C.purple},{l:"재고 경보",v:`${inventorySummary.critical}개점`,c:C.red}].map((item,i)=>(<div key={i} style={{padding:"10px 12px",borderRadius:6,background:C.bg,border:`1px solid ${C.border}`}}><div style={{fontSize:9.5,color:C.textMuted,fontFamily:F,marginBottom:3}}>{item.l}</div><div style={{fontSize:18,fontWeight:700,color:item.c,fontFamily:F}}>{item.v}</div></div>))}
              </div>
            </Card>
            <Card style={{marginBottom:12}}>
              <Hdr icon="🔄" title="가입유형 현황"/>
              <div style={{display:"flex",flexDirection:"column",gap:6}}>
                {subsTypeData.map((d,i)=>{const total=subsTypeData.reduce((s,x)=>s+x.value,0);return <div key={i} style={{display:"flex",alignItems:"center",gap:10,padding:"6px 10px",borderRadius:5,background:C.bg,border:`1px solid ${C.border}`}}><span style={{display:"inline-block",width:8,height:8,borderRadius:2,background:d.color}}/><span style={{fontSize:11.5,color:C.text,fontFamily:F,flex:1}}>{d.name}</span><span style={{fontSize:11.5,color:d.color,fontWeight:600,fontFamily:F}}>{d.value.toLocaleString()}명</span><span style={{fontSize:10,color:C.textMuted,fontFamily:F,minWidth:36,textAlign:"right"}}>{(d.value/total*100).toFixed(1)}%</span></div>;})}
              </div>
            </Card>
            <Card>
              <Hdr icon="📐" title="비즈니스 로직 규칙"/>
              <div style={{fontSize:10.5,color:C.textDim,fontFamily:F,lineHeight:2}}>
                {[{code:"R1",color:C.red,text:"잔여일수 ≤ 2일 → 긴급 발주 (14일치)"},{code:"R2",color:C.orange,text:"잔여일수 ≤ 5일 → 주의 (발주 검토)"},{code:"R3",color:C.accent,text:"판매 추세 급증 → 일평균 상향 재계산"},{code:"R4",color:C.green,text:"S등급 대리점 → 발주 우선순위 부여"},{code:"R5",color:C.purple,text:"플래그십 재고 부족 → 최우선 배정"}].map((r,i)=>(<div key={i} style={{display:"flex",gap:8,alignItems:"flex-start",marginBottom:2}}><span style={{color:r.color,flexShrink:0,fontWeight:600}}>{r.code}</span><span>{r.text}</span></div>))}
              </div>
            </Card>
          </div>
        </div>)}
      </div>

      <OrderModal dealer={orderDealer} onClose={()=>setOrderDealer(null)}/>
      <style>{`@keyframes pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}::-webkit-scrollbar{width:4px;}::-webkit-scrollbar-track{background:transparent;}::-webkit-scrollbar-thumb{background:#30363D;border-radius:2px;}*{box-sizing:border-box;}select option{background:${C.card};color:${C.text};}`}</style>
    </div>
  );
}
