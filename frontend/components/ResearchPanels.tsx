import Link from "next/link";
import type {StatementResponse} from "../lib/api";

export function StatementResearch({response}:{response:StatementResponse}) {
 const {data}=response;const periods=data.periods||[];
 return <><div className="research-context"><span>Financial currency: {data.currency||"Unconfirmed"}</span><span>Reporting period: {response.period}</span><span>Integrity: {data.integrity?.status||"Not assessed"}</span></div>
 {data.integrity?.issues&&data.integrity.issues.length>0&&<details className="panel"><summary>Data integrity notices ({data.integrity.issues.length})</summary><ul>{data.integrity.issues.map((item,i)=><li key={i}>{item.severity}: {item.detail}{item.period? " · "+item.period:""}</li>)}</ul></details>}
 {Object.entries(data.statements||{}).map(([group,rows])=><section className="panel" key={group}><h3>{group}</h3><div className="research-table-wrap"><table className="research-table"><thead><tr><th scope="col">Metric</th>{periods.map(p=><th scope="col" key={p}>{p}</th>)}</tr></thead><tbody>{Object.entries(rows).map(([metric,values])=><tr key={metric}><th scope="row">{metric}</th>{periods.map(p=><td key={p}>{typeof values[p]==="number"?new Intl.NumberFormat("en-US",{maximumFractionDigits:2}).format(values[p]):"—"}</td>)}</tr>)}</tbody></table></div></section>)}
 <p className="method">Source: {response.provenance?.source||"Provider unavailable"} · Checked: {response.provenance?.checked_at||"Unavailable"} · Issuer reconciled: {response.provenance?.issuer_reconciled?"Yes":"No"}. Values are in the reported financial currency and original provider units.</p>
 <Link className="button" href="/data-sources">Read data methodology →</Link></>;
}
export function ModelResearch({value,label,source}:{value:unknown;label:string;source?:string}) {
 if(!value||typeof value!=="object")return <div className="panel"><p>No {label.toLowerCase()} result was returned. No estimate has been substituted.</p></div>;
 return <section className="panel"><h3>{label} · model output</h3><p className="method">Source: {source||"Model/provider unavailable"}. These are scenarios, not guarantees or personal advice.</p><dl className="model-values">{Object.entries(value as Record<string,unknown>).filter(([,v])=>v===null||["string","number","boolean"].includes(typeof v)).map(([key,v])=><div key={key}><dt>{key.replaceAll("_"," ")}</dt><dd>{v===null?"Unavailable":String(v)}</dd></div>)}</dl><details><summary>Full model response and assumptions</summary><pre className="model-json">{JSON.stringify(value,null,2)}</pre></details></section>;
}
