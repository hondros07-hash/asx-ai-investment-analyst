"""AXÍA fundamentals: provider statements, conservative derivations and provenance."""
from functools import lru_cache
import math
import pandas as pd
import yfinance as yf

ROWS = {
 "Income Statement": {
  "Revenue": ["Total Revenue", "Operating Revenue"],
  "Cost of Revenue": ["Cost Of Revenue", "Cost of Revenue"],
  "Gross Profit": ["Gross Profit"],
  "R&D": ["Research And Development", "Research Development"],
  "SG&A": ["Selling General And Administration", "Selling General Administrative"],
  "Operating Income (EBIT)": ["Operating Income", "EBIT"],
  "EBITDA": ["EBITDA", "Normalized EBITDA"],
  "Net Income": ["Net Income", "Net Income Common Stockholders"],
  "Diluted EPS": ["Diluted EPS", "Basic EPS"],
 },
 "Balance Sheet": {
  "Cash & Equivalents": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
  "Receivables": ["Accounts Receivable", "Net Receivables"],
  "Current Assets": ["Current Assets"],
  "Current Liabilities": ["Current Liabilities"],
  "Inventory": ["Inventory"],
  "Total Assets": ["Total Assets"],
  "Total Debt": ["Total Debt"],
  "Net Debt": ["Net Debt"],
  "Stockholders Equity": ["Stockholders Equity", "Total Equity Gross Minority Interest"],
 },
 "Cash Flow": {
  "Operating Cash Flow": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
  "Capital Expenditure": ["Capital Expenditure", "Capital Expenditures"],
  "Free Cash Flow": ["Free Cash Flow"],
  "Financing Cash Flow": ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"],
 },
}
SECTOR = {
 "bank": ["Net Interest Margin", "Non-performing Loans Ratio", "Tier 1 Capital Ratio", "Provision for Credit Losses", "Efficiency Ratio"],
 "bnpl": ["Total Payment Volume", "Net Transaction Margin", "Bad Debt / TPV", "Cash EBITDA", "Cash Burn Rate"],
 "resources": ["Realized Commodity Price", "Cash Cost per Unit", "All-in Sustaining Cost", "Reserve Life"],
 "general": ["Revenue Growth", "Operating Margin", "Free Cash Flow", "Return on Equity"],
}

def number(value):
 try:
  x=float(value)
  return x if math.isfinite(x) else None
 except (TypeError, ValueError): return None

def pick(frame, aliases, col):
 for key in aliases:
  if key in frame.index:
   v=number(frame.at[key,col])
   if v is not None: return v
 return None

def category(meta):
 s=" ".join(str(meta.get(k) or "") for k in ("sector","industry","longName")).lower()
 if any(x in s for x in ("bank","bancorp","banking")): return "bank"
 if any(x in s for x in ("buy now pay later","bnpl","payment services","consumer finance")): return "bnpl"
 if any(x in s for x in ("mining","metals","gold","oil & gas","energy minerals")): return "resources"
 return "general"

def derive(data):
 inc,bal,cf=(data.get(k,{}) for k in ("Income Statement","Balance Sheet","Cash Flow"))
 out={}
 for period in data.get("periods",[]):
  def get(group,key): return group.get(key,{}).get(period)
  revenue=get(inc,"Revenue"); net=get(inc,"Net Income"); op=get(inc,"Operating Income (EBIT)")
  assets=get(bal,"Total Assets"); equity=get(bal,"Stockholders Equity")
  cash=get(bal,"Cash & Equivalents"); debt=get(bal,"Total Debt")
  current=get(bal,"Current Assets"); liabilities=get(bal,"Current Liabilities")
  inventory=get(bal,"Inventory"); ocf=get(cf,"Operating Cash Flow"); capex=get(cf,"Capital Expenditure")
  def ratio(a,b): return a/b if a is not None and b not in (None,0) else None
  if get(cf,"Free Cash Flow") is None and ocf is not None and capex is not None:
   cf["Free Cash Flow"][period]=ocf-abs(capex)
   out[("Free Cash Flow",period)]="Derived: OCF − absolute CapEx"
  if get(bal,"Net Debt") is None and debt is not None and cash is not None:
   bal["Net Debt"][period]=debt-cash
   out[("Net Debt",period)]="Derived: debt − cash"
  if get(inc,"Gross Profit") is None and revenue is not None and get(inc,"Cost of Revenue") is not None:
   inc["Gross Profit"][period]=revenue-abs(get(inc,"Cost of Revenue"))
   out[("Gross Profit",period)]="Derived: revenue − cost of revenue"
  if get(inc,"EBITDA") is None and op is not None:
   # Never substitute EBIT for EBITDA without depreciation and amortisation.
   pass
  data.setdefault("ratios",{})[period]={
   "Gross Margin":ratio(get(inc,"Gross Profit"),revenue),
   "Operating Margin":ratio(op,revenue),"Net Margin":ratio(net,revenue),
   "ROE":ratio(net,equity),"ROA":ratio(net,assets),
   "Asset Turnover":ratio(revenue,assets),
   "Equity Multiplier":ratio(assets,equity),
   "Current Ratio":ratio(current,liabilities),
   "Quick Ratio":ratio(current-inventory,liabilities) if current is not None and inventory is not None else None,
   "Debt / Equity":ratio(debt,equity),
  }
  r=data["ratios"][period]
  r["Du Pont ROE"]=r["Net Margin"]*r["Asset Turnover"]*r["Equity Multiplier"] if all(r[k] is not None for k in ("Net Margin","Asset Turnover","Equity Multiplier")) else None
 data["derived"]=out
 return data

@lru_cache(maxsize=128)
def load(ticker, frequency="Annual (5Y)"):
 stock=yf.Ticker(ticker)
 meta=stock.info or {}
 quarterly=frequency=="Quarterly (8Q)"
 attrs=("quarterly_income_stmt","quarterly_balance_sheet","quarterly_cashflow") if quarterly else ("income_stmt","balance_sheet","cashflow")
 frames=[]
 for attr in attrs:
  try:
   df=getattr(stock,attr)
   frames.append(df if isinstance(df,pd.DataFrame) else pd.DataFrame())
  except Exception: frames.append(pd.DataFrame())
 if frequency=="TTM":
  # TTM flows require four distinct quarters; balance sheet is latest quarter.
  try:
   frames=[getattr(stock,a) for a in ("quarterly_income_stmt","quarterly_balance_sheet","quarterly_cashflow")]
  except Exception: frames=[pd.DataFrame() for _ in range(3)]
 limit=8 if quarterly else 5
 if frequency=="TTM": limit=4
 periods=sorted(set(c for f in frames if isinstance(f,pd.DataFrame) for c in f.columns),reverse=True)[:limit]
 labels=[str(pd.Timestamp(c).date()) for c in periods]
 data={"ticker":ticker,"meta":meta,"currency":meta.get("financialCurrency") or "Unconfirmed","frequency":frequency,
       "periods":labels,"statements":{},"quality":[],"ratios":{}}
 if not periods: data["quality"].append("No financial statement periods returned by provider.")
 for (group,aliases),frame in zip(ROWS.items(),frames):
  table={}
  for label,names in aliases.items():
   vals={}
   for col,period in zip(periods,labels):
    if not isinstance(frame,pd.DataFrame) or frame.empty or col not in frame.columns: vals[period]=None;continue
    if frequency=="TTM" and group!="Balance Sheet":
     if len(periods)<4: vals[period]=None;continue
     # TTM is a single aggregate column, not four individual columns.
     vals[period]=pick(frame,names,col)
    else: vals[period]=pick(frame,names,col)
   table[label]=vals
  data["statements"][group]=table
 if frequency=="TTM":
  if len(periods)==4:
   end=labels[0];data["periods"]=[end+" TTM"]
   for group,table in data["statements"].items():
    for label,values in table.items():
     nums=list(values.values())
     table[label]={data["periods"][0]:(nums[0] if group=="Balance Sheet" else sum(nums) if all(v is not None for v in nums) else None)}
  else:
   data["periods"]=[]
   data["quality"].append("TTM requires four complete quarterly reporting periods.")
 # Drop wholly empty reporting periods, retaining partial years.
 if frequency!="TTM":
  usable=[p for p in data["periods"] if any(values.get(p) is not None for table in data["statements"].values() for values in table.values())]
  data["periods"]=usable
  for table in data["statements"].values():
   for values in table.values():
    for p in list(values):
     if p not in usable: del values[p]
 data["category"]=category(meta)
 data["provider"]="Yahoo Finance via yfinance; provider-transcribed figures, not independently audited."
 data["filing_url"]=meta.get("website") or ""
 derive_input={k:data["statements"][k] for k in data["statements"]}
 derive_input["periods"]=data["periods"]
 derive_input["ratios"]={}
 derive_input["derived"]={}
 derived=derive(derive_input)
 data["ratios"]=derived.get("ratios",{});data["derived"]=derived.get("derived",{})
 return data
