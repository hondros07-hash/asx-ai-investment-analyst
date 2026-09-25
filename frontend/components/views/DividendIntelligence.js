"use client";
import {useCallback,useEffect,useRef,useState} from "react";
import UpcomingDividendsGrid from "../UpcomingDividendsGrid";
import {fetchDividendCalendar} from "../../lib/api";
const MARKETS=[['AU','Australia'],['US','United States'],['GB','United Kingdom'],['JP','Japan'],['HK','Hong Kong'],['CA','Canada'],['GR','Greece']];
export default function DividendIntelligence(){
 const [market,setMarket]=useState('AU'),[payload,setPayload]=useState(null),[loading,setLoading]=useState(true),[error,setError]=useState(null);const abort=useRef(null);
 const load=useCallback(async(force=false)=>{abort.current?.abort();const c=new AbortController();abort.current=c;setLoading(true);setError(null);try{setPayload(await fetchDividendCalendar(market,{signal:c.signal,force}))}catch(e){if(e.name!=="AbortError"){setError("Dividend calendar request failed.");setPayload({status:"UNAVAILABLE",market_region:market,dividend_calendar:[]})}}finally{if(!c.signal.aborted)setLoading(false)}},[market]);
 useEffect(()=>{load(false);return()=>abort.current?.abort()},[load]);
 return <div className="space-y-4"><div><h1 className="text-2xl font-extrabold text-[#082b55]">Dividend Intelligence</h1><p className="mt-1 text-sm text-slate-500">Verified forward corporate actions across Chrímata markets.</p></div><div className="flex flex-wrap gap-2">{MARKETS.map(([code,name])=><button key={code} onClick={()=>setMarket(code)} className={`rounded-lg border px-3 py-2 text-xs font-bold transition ${market===code?'border-[#0b63ce] bg-[#0b63ce] text-white':'border-[#d8e5f2] bg-white text-[#355979] hover:bg-[#f5f9fd]'}`}>{name}</button>)}</div>{error&&<div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-800">{error}</div>}<UpcomingDividendsGrid marketRegion={market} payload={payload} isLoading={loading} onRetry={()=>load(true)}/></div>
}
