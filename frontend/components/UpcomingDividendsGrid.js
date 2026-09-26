"use client";
import {useMemo} from "react";

const DATE_FMT=new Intl.DateTimeFormat("en-AU",{day:"2-digit",month:"short",year:"numeric",timeZone:"UTC"});
function formatDate(value){if(!value||value==="—")return "—";const d=new Date(`${String(value).slice(0,10)}T00:00:00Z`);return Number.isNaN(d.valueOf())?String(value):DATE_FMT.format(d)}
function formatAmount(row){const n=Number(row?.amount);if(!Number.isFinite(n))return row?.amount??"—";const c=row?.currency;if(!c||c==="—")return n.toLocaleString(undefined,{maximumFractionDigits:4});try{return new Intl.NumberFormat("en-AU",{style:"currency",currency:c,minimumFractionDigits:2,maximumFractionDigits:4}).format(n)}catch{return `${n.toFixed(4)} ${c}`}}
function frankingLabel(v){if(v===null||v===undefined||v===""||v==="N/A"||v==="—")return "—";const n=Number(String(v).replace(/[^0-9.]/g,""));return Number.isFinite(n)?`${n}% Franked`:String(v)}

function Skeleton(){return <div className="overflow-hidden rounded-xl border border-[#d8e5f2] bg-white"><div className="h-14 animate-pulse border-b border-slate-100 bg-slate-50"/><div className="space-y-2 p-4">{[1,2,3,4,5].map(x=><div key={x} className="h-9 animate-pulse rounded bg-slate-100"/>)}</div></div>}

export default function UpcomingDividendsGrid({marketRegion="AU",payload,isLoading=false,onRetry}){
 const allRows=payload?.dividend_calendar||[]; const status=payload?.status||"UNAVAILABLE"; const au=marketRegion.toUpperCase()==="AU";
 const rows=useMemo(()=>[...allRows].sort((a,b)=>String(a.ex_date||"9999").localeCompare(String(b.ex_date||"9999"))).slice(0,5),[allRows]);
 if(isLoading)return <Skeleton/>;
 const unavailable=["UNAVAILABLE","PROVIDERS_NOT_CONFIGURED","INVALID_MARKET"].includes(status);
 return <section className="flex min-h-[290px] flex-col overflow-hidden rounded-xl border border-[#d8e5f2] bg-white shadow-[0_1px_3px_rgba(8,43,85,.05)]">
  <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e6edf5] px-5 py-4">
   <div><h2 className="text-[15px] font-extrabold tracking-tight text-[#082b55]">Upcoming Dividends — {payload?.market_name||marketRegion}</h2><p className="mt-1 text-[11px] text-slate-500">Confirmed declared corporate actions · Axía does not estimate undeclared dividends</p></div>
   <span className="rounded-full border border-[#d8e5f2] bg-[#f5f9fd] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[#35618d]">Confirmed ex-dates</span>
  </div>
  {rows.length===0?<div className="px-6 py-12 text-center"><div className="mx-auto max-w-xl text-sm font-semibold text-[#274a72]">{unavailable?"Dividend data unavailable":"No confirmed upcoming dividends found"}</div><p className="mx-auto mt-2 max-w-2xl text-xs leading-5 text-slate-500">{unavailable?"Axía could not establish a verified forward calendar from the configured provider chain. This is not a claim that no companies are paying dividends.":"The configured providers returned no verified declared events in the current horizon for this market."}</p>{onRetry&&<button onClick={onRetry} className="mt-4 rounded-lg border border-[#cbdced] px-3 py-1.5 text-xs font-bold text-[#0b63ce] hover:bg-[#f5f9fd]">Retry</button>}</div>:
  <div className="overflow-x-auto"><table className="w-full min-w-[900px] border-collapse text-left"><thead><tr className="border-b border-[#e6edf5] bg-[#f8fbfe] text-[10px] font-extrabold uppercase tracking-wider text-[#6c819b]"><th className="px-5 py-3">Ticker</th><th className="px-4 py-3">Company</th><th className="px-4 py-3">Ex-Date</th><th className="px-4 py-3">Pay-Date</th><th className="px-4 py-3 text-right">Amount</th>{au&&<th className="px-4 py-3 text-center">Franking</th>}<th className="px-5 py-3">Source</th></tr></thead>
  <tbody className="divide-y divide-[#edf2f7]">{rows.map((r,i)=><tr key={`${r.ticker}-${r.ex_date}-${i}`} className="text-xs text-[#355979] hover:bg-[#f8fbfe]"><td className="px-5 py-3 font-mono font-extrabold text-[#0b63ce]">{r.ticker||"—"}</td><td className="max-w-[280px] truncate px-4 py-3 font-semibold text-[#173b63]" title={r.company||""}>{r.company||"—"}</td><td className="whitespace-nowrap px-4 py-3">{formatDate(r.ex_date)}</td><td className="whitespace-nowrap px-4 py-3">{formatDate(r.pay_date)}</td><td className="whitespace-nowrap px-4 py-3 text-right font-mono font-bold text-[#173b63]">{formatAmount(r)}</td>{au&&<td className="px-4 py-3 text-center">{frankingLabel(r.franking)==="—"?<span className="text-slate-400">—</span>:<span className="inline-flex rounded-full border border-[#b9dcc7] bg-[#f1fbf5] px-2 py-1 text-[10px] font-bold text-[#247044]">{frankingLabel(r.franking)}</span>}</td>}<td className="max-w-[190px] truncate px-5 py-3 text-[10px] text-slate-500" title={r.source||""}>{r.source||"—"}</td></tr>)}</tbody></table></div>}
  <div className="mt-auto flex justify-end border-t border-[#e6edf5] bg-[#fbfdff] px-5 py-3"><a href="/dividends" className="text-xs font-semibold text-[#0874df] hover:underline">View all dividends →</a></div>
 </section>
}
