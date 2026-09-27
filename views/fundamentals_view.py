"""AXÍA Fundamentals workspace — independent from Overview rendering."""
import math
import html
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from services.fundamentals_engine import load, SECTOR, category
from services.sector_kpi_engine import kpi_rows, disclosure_destinations
from services.fundamental_health_engine import assess

def fmt(v,ratio=False,eps=False):
 if v is None or not isinstance(v,(int,float)) or not math.isfinite(v): return "—"
 if ratio: return f"{v:.2%}"
 if eps: return f"{v:,.2f}"
 if abs(v)>=1e12: return f"{v/1e12:,.2f}T"
 if abs(v)>=1e9: return f"{v/1e9:,.2f}B"
 if abs(v)>=1e6: return f"{v/1e6:,.2f}M"
 if abs(v)>=1e3: return f"{v/1e3:,.2f}K"
 return f"{v:,.2f}"

def render(ticker):
 st.markdown("<style>\n.st-key-axia_fund_workspace [data-testid=\"stVerticalBlock\"]{gap:.55rem}\n.st-key-axia_fund_workspace [data-baseweb=\"tab-list\"]{border-bottom:1px solid #d9e5f3;gap:10px}\n.st-key-axia_fund_workspace [data-baseweb=\"tab\"]{color:#47617d;font-weight:650;padding:8px}\n.st-key-axia_fund_workspace [aria-selected=\"true\"]{color:#0868d8!important;border-bottom-color:#0868d8!important}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"]{background:#fff;border:1px solid #d9e5f3;border-radius:10px;overflow:hidden;margin-bottom:8px}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"] summary{background:#f6f9fe;color:#173b63;font-weight:750;padding:10px 14px}\n.st-key-axia_fund_workspace [data-testid=\"stDataFrame\"]{border:1px solid #e0e9f3;border-radius:8px;overflow:hidden}\n.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-checked=\"true\"],.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-pressed=\"true\"]{background:#0868d8!important;color:white!important;border-color:#0868d8!important}\n</style>",unsafe_allow_html=True)
 with st.container(key="axia_fund_workspace"):
  _render_workspace(ticker)

def _render_workspace(ticker):
 st.markdown("<div style=\"background:white;border:1px solid #d9e5f3;border-radius:12px;padding:16px 20px;margin-bottom:12px\"><div style=\"color:#0868d8;font-size:11px;font-weight:800;letter-spacing:.1em\">AXÍA / COMPANY COMMAND CENTRE / FUNDAMENTALS</div><h2 style=\"margin:5px 0;color:#142d4d\">Financial Intelligence</h2><p style=\"margin:0;color:#60758f;font-size:12px\">Three-statement history, ratios and sector-adaptive research.</p></div>",unsafe_allow_html=True)

 frequency=st.segmented_control("Reporting period",["Annual (5Y)","Quarterly (8Q)","TTM"],default="Annual (5Y)",key="axia_fund_period")
 try: data=load(ticker,frequency or "Annual (5Y)")
 except Exception as exc:
  st.error("Financial statements could not be loaded. Try again or inspect the issuer's filings.")
  st.caption(f"Provider error: {type(exc).__name__}")
  return
 sector=data.get("category") or category(data.get("meta") or {},ticker)
 if sector not in SECTOR: sector="general"
 currency=data.get("currency") or "Unconfirmed"
 is_qantas=str(ticker).upper() in ("QAN.MU","QAN.AX")
 if is_qantas:
  st.markdown("**Qantas Airways Limited**")
  st.caption("Trading listing: "+str(ticker).upper()+(" (Munich)" if str(ticker).upper()=="QAN.MU" else " (ASX)")+" · Primary issuer listing: QAN.AX (ASX) · Issuer reporting currency: AUD")
  st.caption("Provider financial-statement currency: "+currency+" · Provider-transcribed data; not independently reconciled to issuer filings.")
 else:
  st.markdown("**"+html.escape(str(data.get("meta",{}).get("longName") or ticker))+"**")
  st.caption("Trading ticker: "+str(ticker)+" · Provider financial-statement currency: "+currency)
  st.caption("Provider-transcribed data; not independently reconciled to issuer filings.")
 if currency=="Unconfirmed":
  st.warning("The provider has not confirmed the currency of these financial-statement values. "+("Qantas reports in AUD, but that does not establish the units returned for QAN.MU. " if is_qantas else "")+"Do not interpret or convert displayed monetary amounts until the provider units are reconciled to a dated issuer filing.")
 for issue in data.get("quality",[]): st.warning(issue)
 periods=data.get("periods",[])
 negative_equity={p for p in periods if (data.get("statements",{}).get("Balance Sheet",{}).get("Stockholders Equity",{}).get(p) or 0)<0}
 if negative_equity: st.warning("Negative shareholders’ equity: ROE, debt/equity and equity multiplier are suppressed for affected periods.")
 health=assess(data)
 with st.container(border=True):
  left,right=st.columns([3,1])
  with left:
   st.markdown("**Fundamental Health · Financial Strength Indicator**")
   st.caption("A transparent, provisional statement-based assessment — not a stock recommendation.")
  with right:
   st.metric("Health score",str(health["score"])+"/100" if health["score"] is not None else "Insufficient data")
  if health["score"] is not None:
   score=health["score"]
   # The gradient and endpoint labels must occupy separate native Streamlit blocks.
   # A combined HTML block can collapse its measured height and overlap the next cards.
   st.markdown('<div style="position:relative;width:100%;height:15px;border-radius:99px;background:linear-gradient(90deg,#c83d4d 0%,#e8bb47 50%,#159b62 100%);overflow:hidden"><div style="position:absolute;left:calc('+str(score)+'% - 2px);top:0;height:100%;width:4px;background:white;border:1px solid #18324d;box-sizing:border-box"></div></div>',unsafe_allow_html=True)
   # Reserve a visible vertical gap so the gradient never touches the endpoint labels.
   st.markdown('<div aria-hidden="true" style="display:block;height:18px;min-height:18px;line-height:18px">&nbsp;</div>',unsafe_allow_html=True)
   weak_label,strong_label=st.columns(2)
   with weak_label:
    st.caption("0 · Financial weakness")
   with strong_label:
    st.markdown('<p style="margin:0;text-align:right;color:#60758f;font-size:12px;line-height:1.6">100 · Financial strength</p>',unsafe_allow_html=True)
  else:
   st.info("Composite indicator unavailable: "+("airline-specific evidence has not been integrated and verified." if sector=="airline" else "at least 60% of weighted evidence is required."))
  c1,c2=st.columns(2)
  c1.metric("Data coverage",str(health["coverage"])+"%")
  c2.metric("Data confidence",str(health["confidence"])+"%")
  st.caption("Confidence is capped because the source data has not been reconciled to official filings.")
  for component in health["components"]:
   value=component["score"]
   st.markdown("**"+component["name"]+"** · "+(str(value)+"/100" if value is not None else "Unavailable")+" · Evidence coverage "+str(component["coverage"])+"%")
   if value is not None: st.progress(int(value)/100)
   if component["missing"]: st.caption("Missing: "+", ".join(component["missing"]))
  with st.expander("Methodology, evidence and limitations"):
   st.caption("Latest period: "+str(health["period"])+" · Sector classification: "+str(health["sector"]))
   for component in health["components"]:
    st.markdown("**"+component["name"]+"** · Weight "+str(component["weight"])+"%")
    for evidence in component["evidence"]:
     st.caption(evidence["metric"]+": "+fmt(evidence["value"])+" · Normalised "+str(evidence["score"])+"/100")
   for note in health["notes"]: st.caption("• "+note)
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
    df=pd.DataFrame(rows)
    st.dataframe(df,hide_index=True,use_container_width=True)
    st.download_button("Export "+group+" CSV",df.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_"+group.replace(" ","_")+".csv",mime="text/csv",key="axia_export_"+group)
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
   # Match Financial Statements: title, table and export belong to one expander widget.
   with st.expander(group,expanded=True):
    rows=[]
    for key in keys:
     row={"Ratio":key}
     for period in data["periods"]:
      val=data["ratios"].get(period,{}).get(key)
      row[period]="N/A (negative equity)" if period in negative_equity and key in ("ROE","Debt / Equity","Equity Multiplier","Du Pont ROE") else fmt(val,ratio=key in ("Gross Margin","Operating Margin","Net Margin","ROE","ROA","Du Pont ROE"))
     rows.append(row)
    df=pd.DataFrame(rows)
    st.dataframe(df,hide_index=True,use_container_width=True)
    st.download_button("Export "+group+" ratios CSV",df.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_"+group.replace(" ","_")+"_ratios.csv",mime="text/csv",key="axia_ratio_"+group)
  st.caption("ROE uses period-end equity where average equity is unavailable. Du Pont is an algebraic breakdown, not an independent audit.")
 with tabs[2]:
  st.subheader(sector.upper()+" | Sector-adaptive KPIs")
  st.caption("Issuer-specific operating measures are separate from generic financial statement ratios.")
  st.markdown("**Issuer operating KPIs · Verification requirements (not a live filing feed)**")
  st.dataframe(pd.DataFrame(kpi_rows(sector)),hide_index=True,use_container_width=True)
  destinations=disclosure_destinations(ticker)
  if destinations:
   st.markdown("**Official disclosure sources**")
   for destination in destinations:
    st.link_button(destination["label"]+" ↗",destination["url"])
    st.caption(destination["status"])
  else: st.caption("No validated official disclosure destination configured for this listing.")
  st.caption("Disclosure links are discovery destinations, not citations for individual KPI values. No issuer KPI values are extracted or verified here.")
  source=data
  fallback=False
  if not periods and frequency=="TTM":
   try:
    source=load(ticker,"Annual (5Y)")
    fallback=bool(source.get("periods"))
   except Exception: source=data
  source_periods=source.get("periods",[])
  if fallback: st.info("TTM unavailable. Showing latest reported annual figures below, not TTM estimates.")
  standard={"Revenue Growth":None,"Operating Margin":None,"Free Cash Flow":None,"Return on Equity":None}
  p=source_periods[0] if source_periods else None
  if p:
   inc=source["statements"]["Income Statement"];cf=source["statements"]["Cash Flow"]
   revenue=inc["Revenue"].get(p)
   prev=inc["Revenue"].get(source_periods[1]) if len(source_periods)>1 else None
   standard["Revenue Growth"]=(revenue/prev-1) if revenue is not None and prev is not None and prev>0 and source.get("frequency")!="TTM" else None
   standard["Operating Margin"]=source.get("ratios",{}).get(p,{}).get("Operating Margin")
   standard["Free Cash Flow"]=cf["Free Cash Flow"].get(p)
   standard["Return on Equity"]=source.get("ratios",{}).get(p,{}).get("ROE")
  if sector!="general":
   st.info("Issuer-specific operating KPIs require official disclosures; they are not inferred from generic statement fields.")
   st.caption("Definitions and required evidence are listed above; values will remain unavailable until verified against a dated filing.")
  if p:
   st.caption("Provider-transcribed financial statement metrics (not issuer-verified) · "+str(p)+" · Currency: "+str(source.get("currency","Unconfirmed"))+" · "+str(source.get("frequency","")))
   rows=[{"Metric":k,"Value":fmt(v,ratio=k in ("Revenue Growth","Operating Margin","Return on Equity")),"Evidence":"Provider-transcribed / calculated; filing unverified" if v is not None else "Unavailable from compatible components"} for k,v in standard.items()]
   st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
  else: st.info("No compatible annual or quarterly statements are available from this provider. No values have been estimated.")
  st.caption("Statement-derived ratios are not substitutes for issuer-disclosed operational KPIs. Values may use different definitions from issuer-reported underlying metrics.")
 with tabs[3]:
  st.subheader("Historical financial trends")
  chart_data=data
  if frequency=="TTM":
   try: chart_data=load(ticker,"Quarterly (8Q)")
   except Exception: chart_data=data
   st.caption("TTM selected: charts show reported quarterly history where available; this is not a TTM trend.")
  pairs=(("Income Statement","Revenue"),("Income Statement","Net Income"),("Cash Flow","Operating Cash Flow"),("Cash Flow","Free Cash Flow"))
  for i in range(0,4,2):
   cols=st.columns(2)
   for col,(group,key) in zip(cols,pairs[i:i+2]):
    with col:
     st.markdown("**"+key+"**")
     series=chart_data["statements"][group].get(key,{})
     points=[(p,series.get(p)) for p in reversed(chart_data["periods"]) if series.get(p) is not None]
     if len(points)<2: st.caption("Insufficient comparable reported periods.");continue
     labels=[p[:7] if "Quarterly" in chart_data["frequency"] else p[:4] for p,v in points]
     fig=go.Figure(go.Bar(x=labels,y=[v for p,v in points],marker_color="#0868d8"))
     fig.update_layout(height=215,margin=dict(l=5,r=5,t=5,b=10),showlegend=False,plot_bgcolor="white",paper_bgcolor="white",xaxis=dict(type="category",tickangle=0),yaxis=dict(automargin=True,zeroline=True))
     st.plotly_chart(fig,use_container_width=True,key="axia_trend_"+key)
     if chart_data["frequency"]=="Annual (5Y)" and len(points)>=2 and points[0][1]>0 and points[-1][1]>0:
      years=len(points)-1
      st.caption(f"{years}-year CAGR: {(points[-1][1]/points[0][1])**(1/years)-1:+.1%}")
 with tabs[4]:
  st.subheader("Data lineage & verification")
  st.warning("Provider-transcribed figures have not been reconciled to audited issuer filings. No filing-page verification is claimed.")
  metadata={"Provider":data.get("provider","Unavailable"),"Reporting currency":currency,"Period basis":data.get("frequency",frequency),"Audit status":"Provider-transcribed; unverified","Restatement status":"Not established","Issuer filing reference":"Not linked to a specific reporting period"}
  st.dataframe(pd.DataFrame([{"Field":k,"Value":v} for k,v in metadata.items()]),hide_index=True,use_container_width=True)
  st.caption("A company website is not evidence of an individual financial statement value. Official filing links must be matched to the selected period before verification badges are shown.")
  if data.get("derived"):
   st.dataframe(pd.DataFrame([{"Metric":k[0],"Period":k[1],"Method":v} for k,v in data["derived"].items()]),hide_index=True,use_container_width=True)
