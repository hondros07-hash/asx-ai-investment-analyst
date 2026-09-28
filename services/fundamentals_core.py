"""AXÍA fundamentals: provider statements, conservative derivations and provenance."""
from datetime import datetime, timezone
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
  "Interest Expense": ["Interest Expense", "Interest Expense Non Operating"],
  "Pretax Income": ["Pretax Income"],
  "Tax Provision": ["Tax Provision"],
  "Net Income": ["Net Income", "Net Income Common Stockholders"],
  "Diluted EPS": ["Diluted EPS"],
  "Diluted Shares": ["Diluted Average Shares", "Diluted Average Shares Outstanding"],
 },
 "Balance Sheet": {
  "Cash & Equivalents": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
  "Receivables": ["Accounts Receivable", "Net Receivables"],
  "Accounts Payable": ["Accounts Payable"],
  "Current Assets": ["Current Assets"],
  "Current Liabilities": ["Current Liabilities"],
  "Inventory": ["Inventory"],
  "Total Assets": ["Total Assets"],
  "Total Liabilities": ["Total Liabilities Net Minority Interest", "Total Liabilities"],
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
 "airline": ["Revenue Passenger Kilometres", "Available Seat Kilometres", "Passenger Load Factor", "Unit Revenue", "Unit Cost", "Net Capital Expenditure"],
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

def category(meta, ticker=""):
 if str(ticker).upper() in ("QAN.AX","QAN.MU"): return "airline"
 if str(ticker).upper() in ("ZIP.AX",): return "bnpl"
 if str(ticker).upper() in ("ZIP",): return "general"
 s=" ".join(str(meta.get(k) or "") for k in ("sector","industry","longName")).lower()
 if any(x in s for x in ("airline","air transport","airways","air carrier","aviation","qantas")): return "airline"
 if any(x in s for x in ("bank","bancorp","banking")): return "bank"
 if any(x in s for x in ("buy now pay later","bnpl","payment services","consumer finance", "credit services", "zip co")): return "bnpl"
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
  def ratio(a,b): return a/b if a is not None and b is not None and b>0 else None
  if get(cf,"Free Cash Flow") is None and ocf is not None and capex is not None:
   cf["Free Cash Flow"][period]=ocf-abs(capex)
   out[("Free Cash Flow",period)]="Derived: OCF − absolute CapEx"
  if get(bal,"Net Debt") is None and debt is not None and cash is not None:
   bal["Net Debt"][period]=debt-cash
   out[("Net Debt",period)]="Derived: debt − cash"
  if get(inc,"Gross Profit") is None and revenue is not None and get(inc,"Cost of Revenue") is not None:
   inc["Gross Profit"][period]=revenue-abs(get(inc,"Cost of Revenue"))
   out[("Gross Profit",period)]="Derived: revenue − cost of revenue"
  if get(inc,"Diluted EPS") is None and net is not None and not str(period).endswith(" TTM"):
   shares=get(inc,"Diluted Shares")
   if shares is not None and shares>0:
    inc["Diluted EPS"][period]=net/shares
    out[("Diluted EPS",period)]="Derived: net income / diluted weighted-average shares"
  data.setdefault("ratios",{})[period]={
   "Gross Margin":ratio(get(inc,"Gross Profit"),revenue),
   "Operating Margin":ratio(op,revenue),"Net Margin":ratio(net,revenue),
   "ROE":ratio(net,equity) if equity is not None and equity>0 else None,"ROA":ratio(net,assets),
   "Asset Turnover":ratio(revenue,assets),
   "Equity Multiplier":ratio(assets,equity) if equity is not None and equity>0 else None,
   "Current Ratio":ratio(current,liabilities),
   "Quick Ratio":ratio(current-inventory,liabilities) if current is not None and inventory is not None else ratio(cash+get(bal,"Receivables"),liabilities) if cash is not None and get(bal,"Receivables") is not None else None,
   "Debt / Equity":ratio(debt,equity) if equity is not None and equity>0 else None,
  }
  if equity is not None and equity<=0: out[("Equity warning",period)]="ROE, debt/equity and equity multiplier are not meaningful with non-positive equity."
  r=data["ratios"][period]
  r["Du Pont ROE"]=r["Net Margin"]*r["Asset Turnover"]*r["Equity Multiplier"] if all(r[k] is not None for k in ("Net Margin","Asset Turnover","Equity Multiplier")) else None
 data["derived"]=out
 return data

def load_uncached(ticker, frequency="Annual (5Y)"):
 # Cache key includes the selected ticker and reporting mode; provider data is
 # checked again after one hour, not misrepresented as live exchange data.
 checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds")
 stock=yf.Ticker(ticker)
 try: meta=stock.info or {}
 except Exception: meta={}
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
  frames=[]
  for attr in ("quarterly_income_stmt","quarterly_balance_sheet","quarterly_cashflow"):
   try:
    frame=getattr(stock,attr)
    frames.append(frame if isinstance(frame,pd.DataFrame) else pd.DataFrame())
   except Exception: frames.append(pd.DataFrame())
 limit=8 if quarterly else 5
 if frequency=="TTM": limit=8
 periods=sorted(set(c for f in frames if isinstance(f,pd.DataFrame) for c in f.columns),reverse=True)[:limit]
 labels=[str(pd.Timestamp(c).date()) for c in periods]
 data={"ticker":ticker,"meta":meta,"currency":meta.get("financialCurrency") or "Unconfirmed","frequency":frequency,
       "periods":labels,"statements":{},"quality":[],"ratios":{}, "provider_checked_at":checked_at}
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
  # Align the four most recent income-statement quarters. Never sum balance-sheet stocks.
  income, balance, cashflow=frames
  aligned=sorted(set(income.columns).intersection(cashflow.columns),reverse=True)[:4] if all(isinstance(x,pd.DataFrame) and not x.empty for x in (income,cashflow)) else []
  def _quarter_number(column):
   stamp=pd.Timestamp(column)
   return stamp.year*4+(stamp.month-1)//3
  if len(aligned)==4 and all(_quarter_number(a)-_quarter_number(b)==1 for a,b in zip(aligned,aligned[1:])):
   end=str(pd.Timestamp(aligned[0]).date()); label=end+" TTM"
   aligned_labels=[str(pd.Timestamp(c).date()) for c in aligned]
   latest_balance=sorted(balance.columns,reverse=True)[0] if isinstance(balance,pd.DataFrame) and not balance.empty else None
   latest_balance_label=str(pd.Timestamp(latest_balance).date()) if latest_balance is not None else None
   data["periods"]=[label]
   for group,table in data["statements"].items():
    for item,values in table.items():
     if group=="Balance Sheet":
      value=pick(balance,ROWS[group][item],latest_balance) if latest_balance is not None else None
     else:
      numbers=[pick(income if group=="Income Statement" else cashflow,ROWS[group][item],c) for c in aligned]
      value=sum(numbers) if all(v is not None for v in numbers) else None
      if item in ("Diluted EPS","Diluted Shares"): value=None
     table[item]={label:value}
   data["quality"].append("TTM flow metrics use four aligned reported quarters; balance sheet uses latest available quarter.")
  else:
   data["periods"]=[]
   data["quality"].append("TTM unavailable: four consecutive aligned quarterly income and cash-flow periods were not returned. Select Annual or Quarterly for reported figures.")
 # Drop wholly empty reporting periods, retaining partial years.
 if frequency!="TTM":
  usable=[p for p in data["periods"] if sum(values.get(p) is not None for table in data["statements"].values() for values in table.values()) >= 2]
  data["periods"]=usable
  for table in data["statements"].values():
   for values in table.values():
    for p in list(values):
     if p not in usable: del values[p]
 data["category"]=category(meta,ticker)
 data["provider"]="Yahoo Finance via yfinance; provider-transcribed figures, not independently audited."
 data["filing_url"]="" # A company homepage is not a filing citation.
 derive_input={k:data["statements"][k] for k in data["statements"]}
 derive_input["periods"]=data["periods"]
 derive_input["ratios"]={}
 derive_input["derived"]={}
 derived=derive(derive_input)
 data["ratios"]=derived.get("ratios",{});data["derived"]=derived.get("derived",{})
 return data
