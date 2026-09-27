"""AXÍA Fundamentals workspace — independent from Overview rendering."""
import math
import pandas as pd
import streamlit as st
from services.fundamentals_engine import load, SECTOR, category

def fmt(v,ratio=False,eps=False):
 if v is None or not isinstance(v,(int,float)) or not math.isfinite(v): return "Not reported"
 if ratio: return f"{v:.2%}"
 if eps: return f"{v:,.2f}"
 if abs(v)>=1e12: return f"{v/1e12:,.2f}T"
 if abs(v)>=1e9: return f"{v/1e9:,.2f}B"
 if abs(v)>=1e6: return f"{v/1e6:,.2f}M"
 return f"{v:,.2f}"

def render(ticker):
 st.markdown("<style>\n.st-key-axia_fund_workspace [data-testid=\"stVerticalBlock\"]{gap:.55rem}\n.st-key-axia_fund_workspace [data-baseweb=\"tab-list\"]{border-bottom:1px solid #d9e5f3;gap:10px}\n.st-key-axia_fund_workspace [data-baseweb=\"tab\"]{color:#47617d;font-weight:650;padding:8px}\n.st-key-axia_fund_workspace [aria-selected=\"true\"]{color:#0868d8!important;border-bottom-color:#0868d8!important}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"]{background:#fff;border:1px solid #d9e5f3;border-radius:10px;overflow:hidden;margin-bottom:8px}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"] summary{background:#f6f9fe;color:#173b63;font-weight:750;padding:10px 14px}\n.st-key-axia_fund_workspace [data-testid=\"stDataFrame\"]{border:1px solid #e0e9f3;border-radius:8px;overflow:hidden}\n.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-checked=\"true\"],.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-pressed=\"true\"]{background:#0868d8!important;color:white!important;border-color:#0868d8!important}\n</style>",unsafe_allow_html=True)
 with st.container(key="axia_fund_workspace"):
  _render_workspace(ticker)

def _render_workspace(ticker):
 st.markdown("<div style=\"background:white;border:1px solid #d9e5f3;border-radius:12px;padding:16px 20px;margin-bottom:12px\"><div style=\"color:#0868d8;font-size:11px;font-weight:800;letter-spacing:.1em\">AXÍA / COMPANY COMMAND CENTRE / FUNDAMENTALS</div><h2 style=\"margin:5px 0;color:#142d4d\">Financial Intelligence</h2><p style=\"margin:0;color:#60758f;font-size:12px\">Three-statement history, ratios and sector-adaptive research.</p></div>",unsafe_allow_html=True)
 st.caption("Historical financial statements, derived ratios and sector-specific disclosures. Provider data is not an audited filing.")
 frequency=st.segmented_control("Reporting period",["Annual (5Y)","Quarterly (8Q)","TTM"],default="Annual (5Y)",key="axia_fund_period")
 try: data=load(ticker,frequency or "Annual (5Y)")
 except Exception as exc:
  st.error("Financial statements could not be loaded. Try again or inspect the issuer's filings.")
  st.caption(f"Provider error: {type(exc).__name__}")
  return
 sector=data.get("category") or category(data.get("meta") or {})
 if sector not in SECTOR: sector="general"
 currency=data.get("currency") or "Unconfirmed"
 st.caption(f"Company: {data.get('meta',{}).get('longName') or ticker} · Ticker: {ticker} · Reporting currency: {currency} · Provider-transcribed; not independently audited")
 for issue in data.get("quality",[]): st.warning(issue)
 tabs=st.tabs(["Financial Statements","Key Ratios","Sector KPIs","Growth & Trends","Sources & Verification"])
 with tabs[0]:
  st.caption("Amounts in reporting currency unless otherwise indicated. EPS is per share. Missing values are not estimated.")
  for group,table in data["statements"].items():
   with st.expander(group,expanded=True):
    if not data["periods"]: st.info("No complete periods available.");continue
    rows=[]
    for label,values in table.items():
     row={"Line item":label}
     for period in data["periods"]:
      value=values.get(period)
      row[period]=fmt(value,eps=label=="Diluted EPS")
      if (label,period) in data.get("derived",{}): row[period]+=" †"
     rows.append(row)
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
  st.caption("† Derived from reported statement components; not directly reported.")
 with tabs[1]:
  st.subheader("Profitability, liquidity and efficiency")
  groups={
   "Profitability":["Gross Margin","Operating Margin","Net Margin","ROE","ROA"],
   "Liquidity & Solvency":["Current Ratio","Quick Ratio","Debt / Equity"],
   "Efficiency":["Asset Turnover","Equity Multiplier"],
   "Du Pont":["Net Margin","Asset Turnover","Equity Multiplier","Du Pont ROE"],
  }
  for group,keys in groups.items():
   st.markdown(f"**{group}**")
   rows=[]
   for key in keys:
    row={"Ratio":key}
    for period in data["periods"]:
     val=data["ratios"].get(period,{}).get(key)
     row[period]=fmt(val,ratio=key in ("Gross Margin","Operating Margin","Net Margin","ROE","ROA","Du Pont ROE"))
    rows.append(row)
   st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
  st.caption("ROE uses period-end equity where average equity is unavailable. Du Pont is an algebraic breakdown, not an independent audit.")
 with tabs[2]:
  st.subheader(sector.upper()+" | Sector-adaptive KPIs")
  st.caption("Specialized operational KPIs require issuer disclosures. AXÍA will not invent them from generic financial feeds.")
  st.dataframe(pd.DataFrame([{"Metric":k,"Value":"Not verified","Evidence":"Issuer report required"} for k in SECTOR[sector]]),hide_index=True,use_container_width=True)
 with tabs[3]:
  st.subheader("Historical financial trends")
  for group,key in (("Income Statement","Revenue"),("Income Statement","Net Income"),("Cash Flow","Operating Cash Flow"),("Cash Flow","Free Cash Flow")):
   series=data["statements"][group].get(key,{})
   points={p:v for p,v in series.items() if v is not None}
   st.markdown(f"**{key}**")
   if len(points)>=2:
    st.line_chart(pd.Series(points).iloc[::-1],height=140)
    values=list(points.values())
    if frequency=="Annual (5Y)" and len(values)>=2 and values[-1]>0 and values[0]>0:
     years=len(values)-1
     st.caption(f"{years}-year CAGR: {(values[0]/values[-1])**(1/years)-1:+.1%} (positive endpoints only)")
   else: st.caption("Insufficient comparable reported periods.")
 with tabs[4]:
  st.subheader("Data lineage & verification")
  st.info("Provider-transcribed is not equivalent to audited. Filing-page verification is not available in this build.")
  st.write("Provider:",data.get("provider","Provider information unavailable"))
  st.write("Reporting currency:",currency)
  st.write("Period basis:",data.get("frequency",frequency))
  st.write("Restatement status: Not independently established")
  st.write("Issuer filing/page references: Not linked; verify against official filings.")
  if data.get("derived"):
   st.dataframe(pd.DataFrame([{"Metric":k[0],"Period":k[1],"Method":v} for k,v in data["derived"].items()]),hide_index=True,use_container_width=True)
