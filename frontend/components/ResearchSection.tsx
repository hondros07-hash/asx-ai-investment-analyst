import Link from "next/link";
type RecordValue=Record<string,unknown>;
const obj=(v:unknown):RecordValue=>v&&typeof v==="object"&&!Array.isArray(v)?v as RecordValue:{};
const str=(v:unknown)=>v===null||v===undefined?"Unavailable":typeof v==="object"?JSON.stringify(v):String(v);
const safeUrl=(v:unknown)=>typeof v==="string"&&/^https:\/\//i.test(v)?v:null;
export function ResearchSection({section,data}:{section:string;data:RecordValue}){
 const source=str(data.source||data.provider);
 const checked=str(data.checked_at);
 const status=str(data.status||obj(data.data).technical_status);
 const rows=section==="news"?data.articles:section==="catalysts"?data.events:section==="announcements"||section==="report-intelligence"?data.filings:null;
 const metrics=section==="technical"?obj(obj(data.data).signals):section==="quant"?obj(data.metrics):null;
 return <section className="panel research-section">
  <p className="method">Source: {source} · Checked: {checked} · Status: {status}</p>
  {typeof data.message==="string"&&<p role="status">{data.message}</p>}
  {Array.isArray(rows)&&<>{rows.length===0&&<p>No verified records returned. Nothing has been substituted.</p>}{rows.map((entry,i)=>{const item=obj(entry);const href=safeUrl(item.url);return <div className="research-entry" key={i}><strong>{str(item.title||item.event||item.form)}</strong><span>{str(item.date||item.published_at||"")}{item.publisher?" · "+str(item.publisher):""}</span>{href&&<a href={href} target="_blank" rel="noopener noreferrer">Open source ↗</a>}{item.status!==null&&item.status!==undefined&&<small>{str(item.status)}</small>}</div>})}</>}
  {metrics&&<dl className="model-values">{Object.entries(metrics).map(([key,value])=><div key={key}><dt>{key.replaceAll("_"," ")}</dt><dd>{typeof value==="object"?str(obj(value).value??obj(value).state??value):str(value)}</dd></div>)}</dl>}
  {section==="thesis"&&<><p>{str(data.message)}</p><p>Integrity: {str(obj(data.integrity).status)}. Saved user rules have not been migrated.</p></>}
  {section==="report-intelligence"&&<p>Filing links are not AI-generated document summaries. Report extraction remains pending.</p>}
  <p className="method">Provider information may be incomplete or delayed. Confirm material facts with official disclosures.</p>
  <Link href="/data-sources">Data methodology →</Link>
 </section>;
}
