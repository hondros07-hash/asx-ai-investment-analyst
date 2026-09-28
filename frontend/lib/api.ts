export type ApiResult<T> = {data:T|null;error:string|null};
const base=process.env.AXIA_API_URL || "http://127.0.0.1:8000";
export async function api<T>(path:string):Promise<ApiResult<T>> {
 try {
  const response=await fetch(base+path,{next:{revalidate:60}});
  if(!response.ok) return {data:null,error:response.status===504?"Data provider timed out":response.status===503?"Data provider temporarily unavailable":`API returned ${response.status}`};
  return {data:await response.json() as T,error:null};
 }catch{return {data:null,error:"Research API is unavailable"};}
}
export type History=[string,number|null][];
export type Kpi={metric:string;value:number|null;history:History;delta:string|null;period:string;percent:boolean;status:string;comparison_status?:string};
export type KpiResponse={ticker:string;currency:string|null;period:string;metrics:Record<string,Kpi>;checked_at?:string};
export type SearchResponse={results:Array<{symbol:string;name?:string;exchange?:string;quote_type?:string}>};
