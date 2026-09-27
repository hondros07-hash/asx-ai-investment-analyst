"""Additional statement-derived ratios with explicit period and sector safeguards."""
import math
from datetime import date

METRICS={
 "Returns & Capital":["ROIC (effective tax proxy)","Net Debt / EBITDA","Interest Coverage"],
 "Working Capital":["Working Capital","DSO (days)","DIO (days)","DPO (days)","Cash Conversion Cycle (days)"],
 "Cash & Debt Coverage":["Operating Cash Flow / Debt","Free Cash Flow / Debt"],
}
PERCENT={"ROIC (effective tax proxy)"}
DAYS={"DSO (days)","DIO (days)","DPO (days)","Cash Conversion Cycle (days)"}

def finite(x):
 return isinstance(x,(int,float)) and math.isfinite(x)

def divide(a,b,positive=True):
 return a/b if finite(a) and finite(b) and (b>0 if positive else b!=0) else None

def compute(data):
 periods=data.get("periods") or []
 tables=data.get("statements") or {}
 inc=tables.get("Income Statement") or {}
 bal=tables.get("Balance Sheet") or {}
 cf=tables.get("Cash Flow") or {}
 frequency=data.get("frequency")
 sector=data.get("category")
 output={}
 notes={}
 def val(table,key,p): return (table.get(key) or {}).get(p)
 for i,p in enumerate(periods):
  prior=periods[i+1] if i+1<len(periods) and frequency!="TTM" else None
  def avg(key):
   now=val(bal,key,p); before=val(bal,key,prior) if prior else None
   return (now+before)/2 if finite(now) and finite(before) else None
  revenue=val(inc,"Revenue",p); cogs=val(inc,"Cost of Revenue",p)
  ebit=val(inc,"Operating Income (EBIT)",p); ebitda=val(inc,"EBITDA",p)
  debt=val(bal,"Total Debt",p); net_debt=val(bal,"Net Debt",p)
  current_assets=val(bal,"Current Assets",p); current_liabilities=val(bal,"Current Liabilities",p)
  interest=val(inc,"Interest Expense",p); tax=val(inc,"Tax Provision",p); pretax=val(inc,"Pretax Income",p)
  rate=divide(tax,pretax)
  if rate is not None: rate=max(0,min(.5,rate))
  capital_now=debt+val(bal,"Stockholders Equity",p)-val(bal,"Cash & Equivalents",p) if all(finite(x) for x in (debt,val(bal,"Stockholders Equity",p),val(bal,"Cash & Equivalents",p))) else None
  prior_capital=None
  if prior:
   parts=[val(bal,k,prior) for k in ("Total Debt","Stockholders Equity","Cash & Equivalents")]
   if all(finite(x) for x in parts): prior_capital=parts[0]+parts[1]-parts[2]
  invested=(capital_now+prior_capital)/2 if finite(capital_now) and finite(prior_capital) else None
  roic=divide(ebit*(1-rate),invested) if finite(ebit) and rate is not None else None
  days=None
  if frequency=="Annual (5Y)": days=365
  elif frequency=="Quarterly (8Q)" and prior:
   try:
    delta=(date.fromisoformat(p)-date.fromisoformat(prior)).days
    if 70<=delta<=110: days=delta
   except ValueError: pass
  dso=divide(avg("Receivables"),revenue)*days if days and avg("Receivables") is not None else None
  dio=divide(avg("Inventory"),abs(cogs))*days if days and avg("Inventory") is not None and finite(cogs) and cogs!=0 else None
  dpo=divide(avg("Accounts Payable"),abs(cogs))*days if days and avg("Accounts Payable") is not None and finite(cogs) and cogs!=0 else None
  output[p]={
   "ROIC (effective tax proxy)":roic,
   "Net Debt / EBITDA":divide(net_debt,ebitda),
   "Interest Coverage":divide(ebit,abs(interest)) if finite(interest) and interest!=0 else None,
   "Working Capital":current_assets-current_liabilities if finite(current_assets) and finite(current_liabilities) else None,
   "DSO (days)":dso,"DIO (days)":dio,"DPO (days)":dpo,
   "Cash Conversion Cycle (days)":dso+dio-dpo if all(finite(x) for x in (dso,dio,dpo)) else None,
   "Operating Cash Flow / Debt":divide(val(cf,"Operating Cash Flow",p),debt),
   "Free Cash Flow / Debt":divide(val(cf,"Free Cash Flow",p),debt),
  }
  if sector in ("bank","bnpl"):
   for metric in ("ROIC (effective tax proxy)","Net Debt / EBITDA","DSO (days)","DIO (days)","DPO (days)","Cash Conversion Cycle (days)"):
    output[p][metric]=None
  notes[p]="ROIC uses an effective tax-rate proxy and average debt + equity − cash; requires both periods. Working-capital days use average balances and reported period length. Provider figures are unverified."
 return output,notes
