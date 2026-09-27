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
from services.fundamentals_integrity_engine import validate, summary
from services.fundamentals_statement_view_engine import display_frame, row_trend, statement_table
from services.advanced_fundamental_ratios_engine import compute as advanced_ratios, METRICS as ADVANCED_GROUPS, PERCENT as ADVANCED_PERCENT, DAYS as ADVANCED_DAYS
from services.earnings_quality_engine import calculate as earnings_quality, export_rows as earnings_export
from services.fundamentals_performance_chart_engine import performance as financial_performance

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
 quality_notes=list(data.get("quality",[]))
 if currency=="Unconfirmed":
  quality_notes.insert(0,"Provider statement currency is unconfirmed. "+("Qantas issuer reports in AUD, but QAN.MU provider monetary units are not verified. " if is_qantas else "")+"Do not interpret or convert monetary values until reconciled to a dated issuer filing.")
 if quality_notes:
  with st.expander("Data quality and source limitations · "+str(len(quality_notes))+" notice(s)",expanded=False):
   for issue in quality_notes: st.caption("• "+str(issue))
 periods=data.get("periods",[])
 negative_equity={p for p in periods if (data.get("statements",{}).get("Balance Sheet",{}).get("Stockholders Equity",{}).get(p) or 0)<0}
 if negative_equity: st.warning("Negative shareholders’ equity: ROE, debt/equity and equity multiplier are suppressed for affected periods.")
 health=assess(data)
 with st.container(border=True):
  left,right=st.columns([3,1])
  with left:
   st.markdown("**Fundamental Health · Financial Strength Indicator**")
   st.caption("Provisional generic statement-ratio assessment"+(" · Airline operating KPIs not yet integrated" if sector=="airline" else "")+" · Not a stock recommendation.")
  with right:
   st.metric("Provisional ratio score" if sector=="airline" else "Health score",str(health["score"])+"/100" if health["score"] is not None else "Not assessed")
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
   st.caption("Composite unavailable: less than 60% of weighted statement-ratio evidence is available.")
  c1,c2=st.columns(2)
  c1.metric("Statement-ratio coverage" if sector=="airline" else "Data coverage",str(health["coverage"])+"%")
  c2.metric("Provider-data confidence" if sector=="airline" else "Data confidence",str(health["confidence"])+"%")
  st.caption("This is not an airline-specific health assessment. Confidence is capped because provider statements have not been reconciled to official filings." if sector=="airline" else "Confidence is capped because the source data has not been reconciled to official filings.")
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
 tabs=st.tabs(["Financial Statements","Key Ratios","Sector KPIs","Growth & Trends","Earnings Quality","Sources & Verification"])
 with tabs[0]:
  st.caption("Provider-transcribed figures, not reconciled to issuer filings. Monetary units: "+currency+". EPS is per share; missing values are not estimated.")
  mode=st.segmented_control("Statement display",["Reported values","Period growth","Common size"],default="Reported values",key="axia_statement_mode")
  mode=mode or "Reported values"
  if mode=="Period growth":
   st.caption("Change against the preceding available reporting period. Annual = annual change; quarterly = sequential quarter change, not year-on-year. Non-positive or missing bases are withheld.")
  elif mode=="Common size":
   st.caption("Income statement: % of revenue · Balance sheet: % of total assets · Cash flow: % of operating cash flow. Non-positive or missing denominators are withheld; EPS and share counts are excluded.")
  col_a,col_b=st.columns(2)
  with col_a: show_sparks=st.checkbox("Show inline sparklines",value=True,key="axia_statement_inline_sparks")
  with col_b: reverse_order=st.checkbox("Oldest period first",value=False,key="axia_statement_reverse")
  for group,table in data["statements"].items():
   with st.expander(group,expanded=True):
    if not data["periods"]: st.info("No complete periods available.");continue
    df=statement_table(data,group,mode,fmt,reverse=reverse_order,sparklines=show_sparks)
    config={"10Y Trend":st.column_config.ImageColumn("Trend · oldest → newest",width="small",help="Raw reported values; number of periods depends on available data.")} if show_sparks else {}
    st.dataframe(df,hide_index=True,use_container_width=True,column_config=config)
    export=df.drop(columns=["10Y Trend"],errors="ignore")
    st.download_button("Export "+group+" CSV",export.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_"+group.replace(" ","_")+"_"+mode.replace(" ","_")+".csv",mime="text/csv",key="axia_export_"+group)
    if mode=="Reported values": st.caption("† Derived from provider statement components; not directly reported.")
    if show_sparks: st.caption("Inline trends use raw available statement values, oldest to newest; no interpolation or estimates. TTM may have only one point.")
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
  st.markdown("### Advanced returns, solvency & working capital")
  advanced,method_notes=advanced_ratios(data)
  st.caption("Additional ratios use provider-transcribed inputs. Missing inputs, unsuitable denominators and sector-inapplicable metrics are withheld, not estimated.")
  for group,keys in ADVANCED_GROUPS.items():
   with st.expander(group,expanded=True):
    rows=[]
    for key in keys:
     row={"Ratio":key}
     for period in data["periods"]:
      value=advanced.get(period,{}).get(key)
      row[period]=fmt(value,ratio=key in ADVANCED_PERCENT) if key in ADVANCED_PERCENT else (f"{value:,.1f} days" if key in ADVANCED_DAYS and value is not None else fmt(value))
     rows.append(row)
    df=pd.DataFrame(rows)
    st.dataframe(df,hide_index=True,use_container_width=True)
    st.download_button("Export "+group+" CSV",df.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_"+group.replace(" ","_")+"_advanced.csv",mime="text/csv",key="axia_advanced_"+group)
  with st.expander("Advanced ratio definitions & limitations",expanded=False):
   st.caption("ROIC = EBIT × (1 − effective tax proxy) / average (debt + equity − cash). The effective tax proxy is clamped to 0–50%; this is not issuer-reported ROIC.")
   st.caption("Net debt / EBITDA uses positive EBITDA. Interest coverage = EBIT / absolute reported interest expense. Debt cash coverage uses positive total debt.")
   st.caption("DSO = average receivables / revenue × days; DIO = average inventory / absolute cost of revenue × days; DPO = average payables / absolute cost of revenue × days; CCC = DSO + DIO − DPO.")
   st.caption("Annual calculations use 365 days; quarterly calculations require a preceding reporting date 70–110 days earlier. TTM working-capital cycle is withheld pending matching average balances.")
   st.caption("Bank and BNPL ROIC, net debt/EBITDA and conventional working-capital-cycle metrics are withheld pending sector-specific methods. All figures remain provider-transcribed, not filing-verified.")

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
  performance_rows=financial_performance(chart_data)
  st.markdown("### Financial Performance Intelligence")
  st.caption("Grouped reported financial metrics and separate percentage-margin trends. No interpolation; unavailable inputs remain blank.")
  if len(performance_rows)<2:
   st.info("At least two comparable periods are required for the combined performance charts.")
  else:
   labels=[r["Period"] for r in performance_rows]
   st.markdown("**Revenue, operating income, net income & free cash flow**")
   fig=go.Figure()
   for metric,color in (("Revenue","#173b63"),("Operating income","#178d67"),("Net income","#a7cb2b"),("Free cash flow","#35465d")):
    fig.add_trace(go.Bar(name=metric,x=labels,y=[r[metric] for r in performance_rows],marker_color=color,hovertemplate="%{x}<br>%{y:,.2f}<extra>"+metric+"</extra>"))
   fig.update_layout(barmode="group",height=365,margin=dict(l=8,r=8,t=16,b=42),paper_bgcolor="white",plot_bgcolor="white",legend=dict(orientation="h",y=1.15),xaxis=dict(type="category",tickangle=-25),yaxis=dict(automargin=True,zeroline=True))
   st.plotly_chart(fig,use_container_width=True,key="axia_fund_combined_performance")
   st.caption("Monetary units: "+str(chart_data.get("currency") or "Unconfirmed")+" · Financial-statement values are provider-transcribed, not filing-verified.")
   st.markdown("**Operating and net income margins**")
   fig=go.Figure()
   for metric,color in (("Operating margin","#178d67"),("Net income margin","#a7cb2b")):
    fig.add_trace(go.Scatter(name=metric,x=labels,y=[r[metric] for r in performance_rows],mode="lines+markers",line=dict(color=color,width=3),marker=dict(size=7),connectgaps=False,hovertemplate="%{x}<br>%{y:.2f}%<extra>"+metric+"</extra>"))
   fig.update_layout(height=315,margin=dict(l=8,r=8,t=16,b=42),paper_bgcolor="white",plot_bgcolor="white",legend=dict(orientation="h",y=1.15),xaxis=dict(type="category",tickangle=-25),yaxis=dict(title="Margin (%)",ticksuffix="%",automargin=True,zeroline=True))
   st.plotly_chart(fig,use_container_width=True,key="axia_fund_margin_performance")
   with st.expander("Performance data table and export",expanded=False):
    df=pd.DataFrame(performance_rows)
    st.dataframe(df,hide_index=True,use_container_width=True)
    st.download_button("Export financial performance CSV",df.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_financial_performance.csv",mime="text/csv",key="axia_fund_performance_export")
  st.markdown("### Individual financial trends")
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
  st.subheader("Earnings Quality Intelligence")
  st.caption("Evidence-led diagnostics · Provider-transcribed statements · Not an accounting misconduct assessment or investment rating.")
  quality_data=data
  if frequency=="TTM":
   st.info("TTM uses aggregated flow figures without matched average balance sheets or diluted-share series. Select Annual or Quarterly for multi-period diagnostics.")
  records=earnings_quality(quality_data)
  if not records: st.info("No comparable statement periods available; no earnings-quality figures are estimated.")
  else:
   latest=records[0]
   metric_cards=[("Operating cash conversion","Operating cash conversion"),("Free cash flow conversion","Free cash flow conversion"),("Accruals / average assets","Accruals / average assets"),("Diluted share count change","Diluted share count change")]
   cols=st.columns(4)
   for col,(label,key) in zip(cols,metric_cards):
    value=latest["metrics"][key]
    with col: st.metric(label,fmt(value,ratio=True))
   st.caption("Latest period: "+str(latest["period"])+" · Cash conversion = cash flow / positive net income; accruals = (net income − operating cash flow) / average assets.")
   st.markdown("**Earnings versus cash generation**")
   chart_rows=list(reversed(records))
   labels=[r["period"] for r in chart_rows]
   fig=go.Figure()
   for key,color in (("Net income","#173b63"),("Operating cash flow","#0868d8"),("Free cash flow","#169a76")):
    fig.add_trace(go.Bar(name=key,x=labels,y=[r["inputs"].get(key) for r in chart_rows],marker_color=color))
   fig.update_layout(barmode="group",height=315,margin=dict(l=8,r=8,t=10,b=35),paper_bgcolor="white",plot_bgcolor="white",legend=dict(orientation="h",y=1.15),xaxis=dict(type="category"),yaxis=dict(automargin=True))
   st.plotly_chart(fig,use_container_width=True,key="axia_earnings_cash_chart")
   st.caption("Amounts in provider statement units: "+currency+". Derived FCF may equal OCF less absolute CapEx; not an independent source.")
   c1,c2=st.columns(2)
   with c1:
    st.markdown("**Cash conversion trend**")
    fig=go.Figure()
    for key,color in (("Operating cash conversion","#0868d8"),("Free cash flow conversion","#169a76")):
     fig.add_trace(go.Scatter(x=labels,y=[r["metrics"][key]*100 if r["metrics"][key] is not None else None for r in chart_rows],mode="lines+markers",name=key,line=dict(color=color),connectgaps=False))
    fig.update_layout(height=270,margin=dict(l=8,r=8,t=12,b=35),paper_bgcolor="white",plot_bgcolor="white",legend=dict(orientation="h",y=1.2),xaxis=dict(type="category"),yaxis=dict(title="%",automargin=True))
    st.plotly_chart(fig,use_container_width=True,key="axia_earnings_conversion_chart")
   with c2:
    st.markdown("**Accruals / average assets**")
    fig=go.Figure(go.Bar(x=labels,y=[r["metrics"]["Accruals / average assets"]*100 if r["metrics"]["Accruals / average assets"] is not None else None for r in chart_rows],marker_color="#0868d8"))
    fig.update_layout(height=270,margin=dict(l=8,r=8,t=12,b=35),paper_bgcolor="white",plot_bgcolor="white",xaxis=dict(type="category"),yaxis=dict(title="%",automargin=True))
    st.plotly_chart(fig,use_container_width=True,key="axia_earnings_accrual_chart")
   st.markdown("**Diluted share count history**")
   fig=go.Figure(go.Bar(x=labels,y=[r["inputs"]["Diluted shares"] for r in chart_rows],marker_color="#173b63"))
   fig.update_layout(height=225,margin=dict(l=8,r=8,t=8,b=30),paper_bgcolor="white",plot_bgcolor="white",xaxis=dict(type="category"),yaxis=dict(automargin=True))
   st.plotly_chart(fig,use_container_width=True,key="axia_earnings_shares_chart")
   st.caption("Diluted weighted-average shares are not the same as end-of-period shares outstanding. Changes may reflect several causes.")
   st.markdown("**Diagnostic observations**")
   for r in records:
    with st.expander(str(r["period"])+" · Evidence and observations",expanded=r is latest):
     for note in r["notes"]: st.caption("• "+note)
     if r["derived_fcf"]: st.caption("FCF is derived from OCF and CapEx, not independently reported.")
     st.dataframe(pd.DataFrame([{"Input":k,"Value":fmt(v)} for k,v in r["inputs"].items()]),hide_index=True,use_container_width=True)
   st.download_button("Export earnings quality CSV",pd.DataFrame(earnings_export(records)).to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_earnings_quality.csv",mime="text/csv",key="axia_earnings_export")
   with st.expander("Calculation methods and limitations"):
    st.caption("Operating cash conversion = OCF / net income; FCF conversion = FCF / net income. Both require positive net income.")
    st.caption("Accruals / average assets = (net income − OCF) / average of current and preceding period-end assets. Requires positive balances and comparable reporting periods.")
    st.caption("Dilution trend = change in diluted weighted-average shares from preceding reported period. Quarterly changes are sequential, not year-on-year.")
    st.caption("Receivables and inventory ratios use reported revenue, and may not be comparable for banks, BNPL companies or issuers with different business models.")
    st.caption("No official filing reconciliation, segment-level cash-flow bridge or issuer-specific accounting adjustments are claimed. Missing values remain unavailable.")
 with tabs[5]:
  st.subheader("Data lineage & verification")
  checks=validate(data)
  counts=summary(checks)
  st.markdown("**Statement integrity diagnostics**")
  st.caption("Automated checks assess internal consistency only; a pass is not an audit or issuer-filing verification.")
  st.dataframe(pd.DataFrame(checks),hide_index=True,use_container_width=True)
  st.caption(" · ".join(k+": "+str(v) for k,v in counts.items() if v))
  st.download_button("Export integrity diagnostics CSV",pd.DataFrame(checks).to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_integrity.csv",mime="text/csv",key="axia_integrity_export")
  st.warning("Provider-transcribed figures have not been reconciled to audited issuer filings. No filing-page verification is claimed.")
  metadata={"Provider":data.get("provider","Unavailable"),"Reporting currency":currency,"Period basis":data.get("frequency",frequency),"Audit status":"Provider-transcribed; unverified","Restatement status":"Not established","Issuer filing reference":"Not linked to a specific reporting period"}
  st.dataframe(pd.DataFrame([{"Field":k,"Value":v} for k,v in metadata.items()]),hide_index=True,use_container_width=True)
  st.caption("A company website is not evidence of an individual financial statement value. Official filing links must be matched to the selected period before verification badges are shown.")
  if data.get("derived"):
   st.dataframe(pd.DataFrame([{"Metric":k[0],"Period":k[1],"Method":v} for k,v in data["derived"].items()]),hide_index=True,use_container_width=True)
