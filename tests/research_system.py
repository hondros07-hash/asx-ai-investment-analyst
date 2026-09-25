
from __future__ import annotations
import numpy as np, pandas as pd, yfinance as yf

KPI_FRAMEWORKS={
"Financial Services":["Revenue growth","Operating margin","ROE","Debt / equity","Free cash flow"],
"Technology":["Revenue growth","Gross margin","Operating margin","Free cash flow","R&D intensity"],
"Industrials":["Revenue growth","EBITDA margin","Operating margin","ROIC","Free cash flow","Net debt"],
"Consumer Cyclical":["Revenue growth","Gross margin","Operating margin","Inventory","Free cash flow"],
"Consumer Defensive":["Revenue growth","Gross margin","Operating margin","Free cash flow","Dividend yield"],
"Healthcare":["Revenue growth","Gross margin","Operating margin","R&D","Free cash flow"],
"Basic Materials":["Revenue growth","EBITDA margin","Operating margin","Free cash flow","Net debt"],
"Energy":["Revenue growth","Operating margin","Free cash flow","Net debt","Dividend yield"],
"Real Estate":["Revenue growth","Operating margin","Debt / equity","Dividend yield","Book value"],
"Communication Services":["Revenue growth","Operating margin","Free cash flow","Debt / equity"],
"Utilities":["Revenue growth","Operating margin","Free cash flow","Debt / equity","Dividend yield"],
}

def safe_num(v):
    try:
        v=float(v)
        return v if np.isfinite(v) else np.nan
    except: return np.nan

def snapshot(meta):
    m=meta if isinstance(meta,dict) else {}
    return {
      "Market cap":safe_num(m.get("marketCap")),
      "Enterprise value":safe_num(m.get("enterpriseValue")),
      "Trailing P/E":safe_num(m.get("trailingPE")),
      "Forward P/E":safe_num(m.get("forwardPE")),
      "Price / book":safe_num(m.get("priceToBook")),
      "EV / EBITDA":safe_num(m.get("enterpriseToEbitda")),
      "Revenue growth":safe_num(m.get("revenueGrowth")),
      "Earnings growth":safe_num(m.get("earningsGrowth")),
      "Gross margin":safe_num(m.get("grossMargins")),
      "Operating margin":safe_num(m.get("operatingMargins")),
      "Profit margin":safe_num(m.get("profitMargins")),
      "ROE":safe_num(m.get("returnOnEquity")),
      "ROA":safe_num(m.get("returnOnAssets")),
      "Debt / equity":safe_num(m.get("debtToEquity")),
      "Free cash flow":safe_num(m.get("freeCashflow")),
      "Operating cash flow":safe_num(m.get("operatingCashflow")),
      "Dividend yield":safe_num(m.get("dividendYield")),
      "Beta":safe_num(m.get("beta")),
    }

def kpi_framework(sector, industry=""):
    ind=(industry or "").lower()
    if any(x in ind for x in ["bank","credit"]):
        return ["NIM","CET1","Bad debts / credit losses","Loan growth","Deposit growth","ROE"]
    if any(x in ind for x in ["software","internet","information technology"]):
        return ["Revenue / ARR growth","Recurring revenue","Customer growth","Churn / retention","Gross margin","Free cash flow"]
    if any(x in ind for x in ["airline","travel"]):
        return ["Revenue growth","Passenger / capacity growth","Load factor","Unit revenue / yield","Fuel costs","Operating margin","Net debt","Free cash flow"]
    if any(x in ind for x in ["metal","mining","gold","copper"]):
        return ["Production","Realised commodity price","Unit costs / AISC","Reserves / resources","Capex","Free cash flow","Net debt"]
    if any(x in ind for x in ["payment","financial data","credit service"]):
        return ["Payment / transaction volume","Active customers","Revenue growth","Transaction margin","Credit losses","Cash EBITDA","Operating margin","International growth"]
    return KPI_FRAMEWORKS.get(sector,["Revenue growth","Operating margin","Free cash flow","Debt / equity","ROE"])

def technical_state(h):
    if h is None or h.empty: return {}
    c=h["Close"].dropna()
    out={}
    for n in (20,50,200):
        out[f"SMA {n}"]=float(c.rolling(n).mean().iloc[-1]) if len(c)>=n else np.nan
    if len(c)>=2:
        r=c.pct_change().dropna()
        out["Annualised volatility"]=float(r.std()*np.sqrt(252))
        peak=c.cummax()
        out["Max drawdown"]=float((c/peak-1).min())
    for label,n in [("1M",21),("3M",63),("6M",126),("1Y",252)]:
        out[label+" return"]=float(c.iloc[-1]/c.iloc[-n]-1) if len(c)>=n else np.nan
    return out

def peer_fundamentals(tickers):
    rows=[]
    for t in tickers:
        try: m=yf.Ticker(t).info
        except: m={}
        s=snapshot(m if isinstance(m,dict) else {})
        rows.append({"Ticker":t,"P/E":s["Trailing P/E"],"Forward P/E":s["Forward P/E"],
                     "EV/EBITDA":s["EV / EBITDA"],"P/B":s["Price / book"],
                     "Revenue growth":s["Revenue growth"],"Operating margin":s["Operating margin"],
                     "ROE":s["ROE"]})
    return pd.DataFrame(rows)

def evidence_status(meta, history):
    s=snapshot(meta); t=technical_state(history)
    available=sum(pd.notna(v) for v in s.values())
    total=len(s)
    return {
      "Fundamental fields":f"{available}/{total}",
      "Price history":"Available" if history is not None and not history.empty else "Unavailable",
      "Filings / announcements":"Not connected",
      "Consensus estimates":"Limited provider metadata only",
      "Point-in-time fundamentals":"Not connected",
      "Model forecast":"Not published until validated",
    }

def thesis_checklist(sector,industry):
    return [{"Test":x,"Status":"Awaiting verified company KPI feed","Evidence":"Not connected"} for x in kpi_framework(sector,industry)]
