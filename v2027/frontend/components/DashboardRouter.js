"use client";
import {useCallback,useEffect,useMemo,useRef,useState,useTransition} from "react";
import {prefetchTicker,warmTicker} from "../lib/api";
import CompanySearch from "./views/CompanySearch";
import CompanyCommandCentre from "./views/CompanyCommandCentre";
import NewsIntelligenceCentre from "./views/NewsIntelligenceCentre";

const VALID=new Set(["search","command_centre","news"]);
export default function DashboardRouter(){
 const [page,setPage]=useState("search");
 const [ticker,setTicker]=useState("CBA.AX");
 const [data,setData]=useState(null);
 const [loading,setLoading]=useState(false);
 const [error,setError]=useState(null);
 const [pending,startTransition]=useTransition();
 const abortRef=useRef(null);

 const load=useCallback(async(symbol)=>{
   abortRef.current?.abort(); const c=new AbortController(); abortRef.current=c;
   setLoading(true); setError(null);
   try{const next=await prefetchTicker(symbol,{signal:c.signal}); if(!c.signal.aborted)setData(next);}
   catch(e){if(e.name!=="AbortError")setError("Some research data could not be loaded.");}
   finally{if(!c.signal.aborted)setLoading(false);}
 },[]);

 useEffect(()=>{load(ticker);return()=>abortRef.current?.abort()},[ticker,load]);

 const navigate=useCallback(target=>{
   if(!VALID.has(target))return;
   startTransition(()=>setPage(target));
   // Keep URL/history useful without a server navigation.
   if(typeof window!=="undefined")history.replaceState(null,"",`#${target}`);
 },[]);

 const chooseTicker=useCallback(symbol=>{
   const next=(symbol||"").trim().toUpperCase(); if(!next)return;
   warmTicker(next); setTicker(next); navigate("command_centre");
 },[navigate]);

 const view=useMemo(()=>{
   if(page==="search")return <CompanySearch activeTicker={ticker} onSelectTicker={chooseTicker}/>;
   if(page==="news")return <NewsIntelligenceCentre ticker={ticker} data={data} loading={loading}/>;
   return <CompanyCommandCentre ticker={ticker} data={data} loading={loading} error={error} navigate={navigate}/>;
 },[page,ticker,data,loading,error,navigate,chooseTicker]);

 return <div className="min-h-screen bg-[#f4f7fb] text-[#082b55]">
  <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
   <div className="mx-auto flex max-w-[1800px] items-center justify-between px-5 py-3">
    <button onClick={()=>navigate("search")} onMouseEnter={()=>warmTicker(ticker)} className="text-xl font-bold tracking-wide">CHRÍMATA</button>
    <nav className="flex gap-2 text-sm">
     <button onClick={()=>navigate("search")} className="rounded-lg px-3 py-2 hover:bg-slate-100">Search</button>
     <button onMouseEnter={()=>warmTicker(ticker)} onClick={()=>navigate("command_centre")} className="rounded-lg px-3 py-2 hover:bg-slate-100">Command Centre</button>
     <button onClick={()=>navigate("news")} className="rounded-lg px-3 py-2 hover:bg-slate-100">News</button>
    </nav>
    <div className="text-sm text-slate-500">Researching: <b className="text-[#082b55]">{ticker}</b></div>
   </div>
  </header>
  <main className={`mx-auto max-w-[1800px] p-5 transition-[opacity,transform] duration-150 ease-out motion-reduce:transition-none ${pending?"translate-y-1 opacity-70":"translate-y-0 opacity-100"}`}>
   {view}
  </main>
 </div>
}
