"use client";
import {useState} from "react";
export default function CompanySearch({activeTicker,onSelectTicker}){
 const [value,setValue]=useState(activeTicker);
 return <section className="rounded-2xl border bg-white p-6 shadow-sm"><h1 className="text-2xl font-bold">Company Search</h1>
 <p className="mt-1 text-slate-500">Select a security without losing the current browser session.</p>
 <form className="mt-5 flex max-w-xl gap-2" onSubmit={e=>{e.preventDefault();onSelectTicker(value)}}>
 <input value={value} onChange={e=>setValue(e.target.value)} className="min-w-0 flex-1 rounded-xl border px-4 py-3" placeholder="e.g. QAN.AX"/>
 <button className="rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white">Analyse</button></form></section>
}
