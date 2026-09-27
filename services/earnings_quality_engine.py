"""Evidence-aware earnings quality diagnostics; not a fraud detector or investment rating."""
import math
import pandas as pd

METRICS=("Operating cash conversion","Free cash flow conversion","Accruals / average assets","Diluted share count change","Receivables / revenue","Inventory / revenue","FCF less net income")

def finite(x):
 return isinstance(x,(int,float)) and math.isfinite(x)

def ratio(a,b):
 return a/b if finite(a) and finite(b) and b>0 else None

def calculate(data):
 periods=data.get("periods") or []
 statements=data.get("statements") or {}
 inc=statements.get("Income Statement") or {}
 bal=statements.get("Balance Sheet") or {}
 cf=statements.get("Cash Flow") or {}
 frequency=data.get("frequency")
 results=[]
 def val(table,key,p): return (table.get(key) or {}).get(p)
 for i,p in enumerate(periods):
  previous=periods[i+1] if i+1<len(periods) and frequency!="TTM" else None
  net=val(inc,"Net Income",p);ocf=val(cf,"Operating Cash Flow",p);fcf=val(cf,"Free Cash Flow",p)
  assets=val(bal,"Total Assets",p);old_assets=val(bal,"Total Assets",previous) if previous else None
  average_assets=(assets+old_assets)/2 if finite(assets) and finite(old_assets) and assets>0 and old_assets>0 else None
  shares=val(inc,"Diluted Shares",p);old_shares=val(inc,"Diluted Shares",previous) if previous else None
  revenue=val(inc,"Revenue",p)
  metrics={
   "Operating cash conversion":ratio(ocf,net),
   "Free cash flow conversion":ratio(fcf,net),
   "Accruals / average assets":ratio(net-ocf,average_assets) if finite(net) and finite(ocf) else None,
   "Diluted share count change":shares/old_shares-1 if finite(shares) and finite(old_shares) and old_shares>0 else None,
   "Receivables / revenue":ratio(val(bal,"Receivables",p),revenue),
   "Inventory / revenue":ratio(val(bal,"Inventory",p),revenue),
   "FCF less net income":fcf-net if finite(fcf) and finite(net) else None,
  }
  # A TTM flow must not be divided by a point-in-time balance to imply an annual accrual ratio.
  if frequency=="TTM":
   metrics["Accruals / average assets"]=None
   metrics["Diluted share count change"]=None
  notes=[]
  if finite(net) and finite(ocf) and net>0 and ocf<net: notes.append("Operating cash flow is below net income; examine working capital and non-cash adjustments.")
  if finite(net) and finite(fcf) and net>0 and fcf<net: notes.append("Free cash flow is below net income; examine capital expenditure and reinvestment.")
  if metrics["Diluted share count change"] is not None and metrics["Diluted share count change"]>0: notes.append("Weighted-average diluted share count increased; this does not by itself establish an equity issuance.")
  if metrics["Accruals / average assets"] is not None and metrics["Accruals / average assets"]>0: notes.append("Net income exceeds operating cash flow relative to average assets; investigate drivers before interpreting.")
  if not notes: notes.append("No rule-triggered observation from available inputs; missing data and unverified figures limit interpretation.")
  results.append({"period":p,"metrics":metrics,"notes":notes,"inputs":{"Net income":net,"Operating cash flow":ocf,"Free cash flow":fcf,"Diluted shares":shares,"Revenue":revenue,"Receivables":val(bal,"Receivables",p),"Inventory":val(bal,"Inventory",p)},"derived_fcf":("Free Cash Flow",p) in (data.get("derived") or {})})
 return results

def export_rows(results):
 return [{"Period":r["period"],**r["metrics"],"Observations":" | ".join(r["notes"]),"FCF basis":"Derived from OCF and CapEx" if r["derived_fcf"] else "Provider-transcribed or unavailable"} for r in results]
