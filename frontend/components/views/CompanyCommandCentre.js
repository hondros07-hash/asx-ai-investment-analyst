export default function CompanyCommandCentre({ticker,data,loading,error,navigate}){
 return <section><div className="mb-4 flex items-end justify-between"><div><h1 className="text-2xl font-bold">Company Command Centre</h1><p className="text-slate-500">{ticker}</p></div>
 <button onClick={()=>navigate("news")} className="rounded-lg border bg-white px-4 py-2">News & Events →</button></div>
 {error&&<div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3">{error}</div>}
 <div className="grid gap-4 md:grid-cols-3">{["scorecard","valuation","technicals","consensus","forecast"].map(k=><article key={k} className="min-h-44 rounded-2xl border bg-white p-5 shadow-sm">
 <h2 className="font-bold capitalize">{k.replace("_"," ")}</h2>{loading&&!data?<div className="mt-4 h-20 animate-pulse rounded-xl bg-slate-100"/>:<pre className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap text-xs text-slate-600">{JSON.stringify(data?.[k]?.data??data?.[k]??"—",null,2)}</pre>}</article>)}</div></section>
}
