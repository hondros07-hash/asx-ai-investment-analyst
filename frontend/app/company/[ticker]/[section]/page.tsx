import {notFound} from "next/navigation";
import type {Metadata} from "next";
import Link from "next/link";
import {Shell} from "../../../../components/Shell";
import {KpiCards} from "../../../../components/KpiCards";
import {StatementResearch,ModelResearch} from "../../../../components/ResearchPanels";
import {ResearchSection} from "../../../../components/ResearchSection";
import {ReportIntelligence} from "../../../../components/ReportIntelligence";
import {api,KpiResponse,StatementResponse,ValuationResponse,ForecastResponse} from "../../../../lib/research-api";

const sections=["overview","fundamentals","technical","announcements","report-intelligence","news","thesis","catalysts","quant","forecasts","finance"];
const names:Record<string,string>={overview:"Overview",fundamentals:"Fundamentals",technical:"Technical",announcements:"Announcements & Reports","report-intelligence":"Report Intelligence",news:"News",thesis:"Thesis Scorecard",catalysts:"Catalyst Calendar",quant:"Quant",forecasts:"Forecasts",finance:"Finance"};
export async function generateMetadata({params}:{params:Promise<{ticker:string;section:string}>}):Promise<Metadata>{
 const {ticker,section}=await params;
 const normalizedTicker=ticker.toUpperCase();
 const encoded=encodeURIComponent(normalizedTicker);

 const statements=await api<StatementResponse>(
  "/v1/companies/"+encoded+"/financial-statements?period="+encodeURIComponent("Annual (5Y)")
 );

 const companyName=statements.data?.data.identity?.name||normalizedTicker;

 return {
  title:`${companyName} — ${names[section]||"Company"}`,
  robots:{index:false,follow:false}
 };
}
export default async function Company({params,searchParams}:{params:Promise<{ticker:string;section:string}>;searchParams:Promise<{period?:string}>}){
 const {ticker,section}=await params;const {period:requested}=await searchParams;
 if(!sections.includes(section)||!/^[A-Za-z0-9.^=_-]{1,24}$/.test(ticker))notFound();
 const period=["Annual (5Y)","Quarterly (8Q)","TTM"].includes(requested||"")?requested!:"Annual (5Y)";
 const encoded=encodeURIComponent(ticker.toUpperCase());
 const base="/v1/companies/"+encoded;
 const needsKpis=section==="overview"||section==="fundamentals";
 const needsStatements=section==="overview"||section==="fundamentals"||section==="finance";
 const [kpis,statements,valuation,forecast]=await Promise.all([
  needsKpis?api<KpiResponse>(base+"/kpis?period="+encodeURIComponent(period)):Promise.resolve(null),
  needsStatements?api<StatementResponse>(base+"/financial-statements?period="+encodeURIComponent(period)):Promise.resolve(null),
  section==="finance"?api<ValuationResponse>(base+"/valuation"):Promise.resolve(null),
  section==="forecasts"?api<ForecastResponse>(base+"/forecast"):Promise.resolve(null)
 ]);
 const identity=statements?.data?.data.identity;const companyName=identity?.name||ticker.toUpperCase();
 const researchSections=["technical","announcements","report-intelligence","news","thesis","catalysts","quant"];
 const research=researchSections.includes(section)?await api<Record<string,unknown>>(base+"/"+section):null;
 return <Shell ticker={ticker}><div className="eyebrow">AXÍA / COMPANY COMMAND CENTRE</div>
 <div className="company-heading"><div className="company-logo" aria-hidden="true">{ticker.slice(0,2).toUpperCase()}</div><div><h1>{companyName}</h1><p className="muted">{ticker.toUpperCase()}{identity?.exchange?" · "+identity.exchange:""}{identity?.country&&identity.country!=="Unconfirmed"?" · "+identity.country:""} · All the evidence. A clearer perspective.</p></div></div>
 <nav className="subnav" aria-label="Company research sections">{sections.map(s=><Link key={s} className={s===section?"selected":""} aria-current={s===section?"page":undefined} href={`/company/${encoded}/${s}`}>{names[s]}</Link>)}</nav>
 <h2>{names[section]}</h2>
 {(section==="overview"||section==="fundamentals")&&<nav className="period-nav" aria-label="Financial reporting period">{["Annual (5Y)","Quarterly (8Q)","TTM"].map(p=><Link key={p} className={p===period?"selected":""} aria-current={p===period?"page":undefined} href={`/company/${encoded}/${section}?period=${encodeURIComponent(p)}`}>{p}</Link>)}</nav>}
 {kpis?.error&&<div role="alert" className="panel error">KPIs: {kpis.error}. Other research sections remain available.</div>}
 {statements?.error&&<div role="alert" className="panel error">Financial statements: {statements.error}. No figures have been substituted.</div>}
 {valuation?.error&&<div role="alert" className="panel error">Valuation: {valuation.error}. No estimate has been substituted.</div>}
 {forecast?.error&&<div role="alert" className="panel error">Forecast: {forecast.error}. No estimate has been substituted.</div>}
 {kpis?.data&&<><KpiCards response={kpis.data}/><p className="method">Source: {kpis.data.source||"Provider unavailable"} · Checked: {kpis.data.checked_at||"Unavailable"} · Provider-transcribed; not independently reconciled.</p></>}
 {section==="fundamentals"&&statements?.data&&<StatementResearch response={statements.data}/>}
 {section==="overview"&&statements?.data&&<div className="panel"><h3>Company research context</h3><p>Financial currency: {statements.data.data.currency||"Unconfirmed"} · Data integrity: {statements.data.data.integrity?.status||"Not assessed"}</p><Link className="button" href={`/company/${encoded}/fundamentals`}>Review financial statements →</Link></div>}
 {section==="finance"&&statements?.data&&<StatementResearch response={statements.data}/>}
 {section==="finance"&&valuation?.data&&<ModelResearch label="Valuation" value={valuation.data.valuation} source={valuation.data.source}/>}
 {section==="forecasts"&&forecast?.data&&<ModelResearch label="12-month forecast" value={forecast.data.forecast} source={forecast.data.source}/>}
 {research?.error&&<div role="alert" className="panel error">{names[section]}: {research.error}. No substitute results have been generated.</div>}
 {research?.data&&section==="report-intelligence"&&<ReportIntelligence data={research.data}/>}
 {research?.data&&section!=="report-intelligence"&&<ResearchSection section={section} data={research.data}/>}
 </Shell>;
}
