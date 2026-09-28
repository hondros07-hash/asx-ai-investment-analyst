import type {Kpi,KpiResponse} from "../lib/api";
const names=["Revenue","Operating Income","Net Income","Free Cash Flow","Operating Margin"];
const icons=["▤","▣","♧","▢","◉"];
function format(value:number|null,percent:boolean,currency:string|null) {
 if(value===null||!Number.isFinite(value))return "Unavailable";
 if(percent)return (value*100).toFixed(1)+"%";
 const n=Math.abs(value),unit=n>=1e12?"T":n>=1e9?"B":n>=1e6?"M":n>=1e3?"K":"",scale=unit==="T"?1e12:unit==="B"?1e9:unit==="M"?1e6:unit==="K"?1e3:1;
 return (value<0?"−":"")+(currency==="AUD"?"A$":currency==="USD"?"$":currency==="EUR"?"€":"")+ (n/scale).toFixed(2)+unit;
}
function date(s:string){const m=/^(\d{4})-(\d{2})-(\d{2})/.exec(s||"");return m?`${m[3]}/${m[2]}/${m[1]}`:s||"Period unavailable";}
function Bars({history,currency,percent}:{history:Kpi["history"];currency:string|null;percent:boolean}){
 const valid=history.filter((x):x is [string,number]=>typeof x[1]==="number"&&Number.isFinite(x[1]));
 if(valid.length<2)return <span className="no-trend">Trend unavailable</span>;
 const max=Math.max(1,...valid.map(x=>Math.abs(x[1])));
 return <div className="spark" aria-label="Historical reported financial values">{valid.slice(-8).map(([p,v])=><span key={p} title={date(p)+": "+format(v,percent,currency)+" (reported)"} className={v<0?"bar negative":"bar"} style={{height:Math.max(3,Math.round(Math.abs(v)/max*34))}} />)}</div>;
}
export function KpiCards({response}:{response:KpiResponse}){
 return <div className="kpi-grid">{names.map((name,i)=>{const k=response.metrics?.[name];const delta=k?.delta;const state=k?.comparison_status;const direction=state==="turnaround"||state==="improving"?"positive":state==="turned_negative"||state==="declining"?"negative":delta?.startsWith("+")?"positive":delta?.startsWith("-")?"negative":"neutral";
 return <article className="kpi" key={name}><div className="kpi-icon">{icons[i]}</div><div className="kpi-body"><div className="kpi-title">{name} <small>({date(k?.period||"")})</small></div><div className="kpi-value">{format(k?.value??null,k?.percent??false,response.currency)}</div><div className={`kpi-delta ${direction}`}>{delta|| (k?.status==="error"?"Metric unavailable":"Comparison unavailable")}</div></div>{k&&<Bars history={k.history||[]} currency={response.currency} percent={k.percent}/>}</article>})}</div>;
}
