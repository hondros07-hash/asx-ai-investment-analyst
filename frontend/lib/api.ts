export type ApiResult<T> = {data:T|null;error:string|null};
const base=process.env.AXIA_API_URL || "http://127.0.0.1:8000";
export async function api<T>(path:string):Promise<ApiResult<T>> {
 try {
  if(!path.startsWith("/") || path.startsWith("//")) return {data:null,error:"Invalid research API path"};
  const response=await fetch(base+path,{next:{revalidate:60}});
  if(!response.ok) return {data:null,error:response.status===504?"Data provider timed out":response.status===503?"Data provider temporarily unavailable":`API returned ${response.status}`};
  const data:unknown=await response.json();
  if(data===null || typeof data!=="object" || Array.isArray(data)) return {data:null,error:"Invalid research API response"};
  return {data:data as T,error:null};
 }catch(error){return {data:null,error:error instanceof Error && error.name==="TimeoutError"?"Research API request timed out":"Research API is unavailable"};}
}
export type History=[string,number|null][];
export type Kpi={metric:string;value:number|null;history:History;delta:string|null;period:string;percent:boolean;status:string;comparison_status?:string};
export type KpiResponse={ticker:string;currency:string|null;period:string;metrics:Record<string,Kpi>;checked_at?:string;source?:string};
export type StatementResponse={ticker:string;period:string;data:{identity?:{name?:string;exchange?:string;country?:string};currency?:string;periods?:string[];statements?:Record<string,Record<string,Record<string,number|null>>>;ratios?:Record<string,Record<string,number|null>>;integrity?:{status:string;issues:Array<{code:string;severity:string;detail:string;period?:string}>}};provenance?:{source?:string;checked_at?:string;issuer_reconciled?:boolean}};
export type ValuationResponse={ticker:string;valuation:unknown;source?:string;checked_at?:string};
export type ForecastResponse={ticker:string;forecast:unknown;source?:string;model?:string};
export type SearchResponse={results:Array<{symbol:string;name?:string;exchange?:string;quote_type?:string}>};
