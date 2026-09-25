const API=(process.env.NEXT_PUBLIC_CHRIMATA_API_URL||"http://localhost:8000").replace(/\/$/,"");
const cache=new Map();
const inflight=new Map();
const TTL=60_000;

async function request(path,{signal,force=false}={}){
  const key=path, now=Date.now(), hit=cache.get(key);
  if(!force && hit && now-hit.at<TTL) return hit.value;
  if(!force && inflight.has(key)) return inflight.get(key);
  const job=fetch(`${API}${path}`,{signal,headers:{Accept:"application/json"}}).then(async r=>{
    if(!r.ok) throw new Error(`API ${r.status}`);
    const value=await r.json(); cache.set(key,{at:Date.now(),value}); return value;
  }).finally(()=>inflight.delete(key));
  inflight.set(key,job); return job;
}
const q=t=>encodeURIComponent(t);
export async function prefetchTicker(ticker,{signal}={}){
  const endpoints={
    scorecard:`/api/v1/widget/scorecard?ticker=${q(ticker)}`,
    valuation:`/api/v1/widget/valuation?ticker=${q(ticker)}`,
    technicals:`/api/v1/widget/technicals?ticker=${q(ticker)}`,
    consensus:`/api/v1/widget/consensus?ticker=${q(ticker)}`,
    forecast:`/api/v1/widget/forecast?ticker=${q(ticker)}`
  };
  const pairs=await Promise.allSettled(Object.entries(endpoints).map(async([k,p])=>[k,await request(p,{signal})]));
  return Object.fromEntries(pairs.map((x,i)=>x.status==="fulfilled"?x.value:[Object.keys(endpoints)[i],{status:"error",data:null}]));
}
export function warmTicker(ticker){prefetchTicker(ticker).catch(()=>{});}
