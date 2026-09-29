"""AXÍA Fundamentals workspace — independent from Overview rendering."""
import math
import html
import io
from datetime import datetime, time
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, quote as url_quote
from watchlist_engine import add as watch_add, remove as watch_remove, get as watch_get
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

def _issuer_header(data, ticker, currency):
 """Compact issuer header. Provider values are displayed without estimating missing data."""
 m=data.get("meta") or {}
 def safe(value): return html.escape(str(value), quote=True)
 name=m.get("longName") or m.get("shortName") or ticker
 known={"KO":"coca-cola.com","NVDA":"nvidia.com","AAPL":"apple.com","MSFT":"microsoft.com","QAN.AX":"qantas.com","QAN.MU":"qantas.com","ZIP.AX":"zip.co"}
 domain=urlparse(str(m.get("website") or "")).hostname or known.get(str(ticker).upper(),"")
 domain=domain.removeprefix("www.")
 # Use a plain image URL: Streamlit's markdown sanitizer does not reliably preserve onerror JavaScript.
 logo=str(m.get("logo_url") or m.get("logoUrl") or "")
 if str(ticker).upper()=="KO":
  logo="https://commons.wikimedia.org/wiki/Special:FilePath/Coca-Cola_logo.svg"
 elif not logo.startswith("https://") and domain:
  logo="https://www.google.com/s2/favicons?domain="+url_quote(domain)+"&sz=256"
 initials="".join(part[0] for part in str(name).split() if part)[:2].upper() or str(ticker)[:1].upper()
 mark='<span class="axia-issuer-fallback">'+safe(initials)+'</span>'
 if logo.startswith("https://"):
  mark='<span class="axia-issuer-fallback">'+safe(initials)+'</span><img alt="" loading="eager" src="'+safe(logo)+'">'
 country=str(m.get("country") or "Country unconfirmed")
 flags={"United States":"🇺🇸","Australia":"🇦🇺","United Kingdom":"🇬🇧","Canada":"🇨🇦","Germany":"🇩🇪","Japan":"🇯🇵","Hong Kong":"🇭🇰","New Zealand":"🇳🇿"}
 country_codes={"United States":"us","Australia":"au","United Kingdom":"gb","Canada":"ca","Germany":"de","Japan":"jp","Hong Kong":"hk","New Zealand":"nz"}
 flag_code=country_codes.get(country)
 country_label=('<img class="axia-issuer-flag" alt="" src="https://flagcdn.com/24x18/'+flag_code+'.png"> ' if flag_code else "")+safe(country)
 identity=' <span class="axia-issuer-separator">|</span> '.join((safe(str(ticker).upper()),safe(m.get("fullExchangeName") or m.get("exchange") or "Exchange unconfirmed"),country_label,safe(m.get("sector") or "Sector unconfirmed"),safe(m.get("industry") or "Industry unconfirmed")))
 slogan=m.get("slogan") or m.get("tagline") or ""
 if not slogan:
  slogan={"KO":"Refresh the world. Make a difference.","NVDA":"Accelerated computing for a better tomorrow."}.get(str(ticker).upper(),"")
 if not slogan: slogan=m.get("longBusinessSummary") or ""
 if slogan and len(str(slogan))>115: slogan=str(slogan).split(". ")[0][:112].rstrip()+"…"
 price=m.get("currentPrice")
 if not isinstance(price,(int,float)) or not math.isfinite(price): price=m.get("regularMarketPrice")
 quote_text=(f"{price:,.2f} "+safe(m.get("currency") or "")) if isinstance(price,(int,float)) and math.isfinite(price) else "Quote unavailable"
 change=m.get("regularMarketChangePercent")
 delta=f"{change:+.2f}%" if isinstance(change,(int,float)) and math.isfinite(change) else "Change unavailable"
 delta_color="#168b62" if isinstance(change,(int,float)) and change>=0 else "#c54450" if isinstance(change,(int,float)) else "#60758f"
 def stat(label,v,kind="number"):
  if not isinstance(v,(int,float)) or not math.isfinite(v): display="—"
  elif kind=="yield":
   # yfinance commonly reports dividendYield as percentage points (2.41, not .0241).
   display=f"{v if abs(v)>1 else v*100:.2f}%"
  elif kind=="multiple": display=f"{v:.1f}×"
  else: display=fmt(v)
  return '<div class="axia-issuer-stat"><strong>'+display+'</strong><span>'+label+'</span></div>'
 stats=stat("Market Cap",m.get("marketCap"))+stat("P/E (TTM)",m.get("trailingPE"),"multiple")+stat("Dividend Yield",m.get("dividendYield"),"yield")+stat("Beta (5Y)",m.get("beta"))
 exchange=str(m.get("exchange") or m.get("fullExchangeName") or "").upper()
 market_zone=None
 if exchange in ("NMS","NGM","NCM","NYQ","NYSE","NASDAQ","ASE","AMEX") or str(ticker).upper() in ("KO","NVDA","AAPL","MSFT"): market_zone="America/New_York"
 elif str(ticker).upper().endswith(".AX"): market_zone="Australia/Sydney"
 elif str(ticker).upper().endswith(".L"): market_zone="Europe/London"
 market_open=False
 if market_zone:
  local_now=datetime.now(ZoneInfo(market_zone))
  market_open=local_now.weekday()<5 and time(9,30)<=local_now.time()<time(16,0) if market_zone=="America/New_York" else local_now.weekday()<5 and time(10,0)<=local_now.time()<time(16,0)
 session_note=("Market session open · provider quote may be delayed" if market_open else "Market session closed · provider quote snapshot") if market_zone else "Market hours unconfirmed · provider quote snapshot"
 session_color="#168b62" if market_open else "#60758f"
 left,right=st.columns([5,4],gap="small",vertical_alignment="center")
 with left:
  st.markdown('<div class="axia-issuer-left"><div class="axia-issuer-mark">'+mark+'</div><div class="axia-issuer-identity"><h2>'+safe(name)+'</h2><div class="axia-issuer-details">'+identity+'</div><div class="axia-issuer-tagline">'+safe(slogan)+'</div></div></div>',unsafe_allow_html=True)
 with right:
  quote_col,action_col=st.columns([3,2],vertical_alignment="center",gap="small")
  with quote_col:
   st.markdown('<div class="axia-issuer-quote">'+quote_text+' <span style="color:'+delta_color+'">'+delta+'</span></div><div class="axia-issuer-quote-note" style="color:'+session_color+'">'+session_note+'</div>',unsafe_allow_html=True)
  with action_col:
   try: saved=str(ticker).upper() in set(watch_get()["ticker"].astype(str).str.upper())
   except Exception: saved=False
   if st.button("✓ In Watchlist" if saved else "＋ Add to Watchlist",key="axia_fund_watch_"+str(ticker),use_container_width=True):
    try:
     if saved: watch_remove(ticker); st.toast(str(ticker)+" removed from Watchlist.")
     else: watch_add(ticker,""); st.toast(str(ticker)+" added to Watchlist.")
     st.rerun()
    except Exception as exc: st.warning("Watchlist could not be updated: "+str(exc))
  st.markdown('<div class="axia-issuer-market"><div class="axia-issuer-stats">'+stats+'</div></div>',unsafe_allow_html=True)


def _financial_overview(data,ticker,currency):
 """Provider-based overview; no sample values or estimated missing inputs."""
 periods=data.get("periods") or []
 if not periods:
  st.info("No financial periods available.");return
 inc=data["statements"]["Income Statement"];cf=data["statements"]["Cash Flow"];ratios=data.get("ratios",{})
 p=periods[0]
 def v(group,key,period):return group.get(key,{}).get(period)
 # Reference-inspired cards: values and growth are drawn exclusively from comparable provider periods.
 def _card_value(value,percent=False):
  if value is None or not isinstance(value,(int,float)) or not math.isfinite(value): return "—"
  if percent: return f"{value*100:,.1f}%"
  return fmt(value)
 def _display_date(value):
  raw=str(value).strip()
  suffix=" TTM" if raw.endswith(" TTM") else ""
  raw=raw[:-4] if suffix else raw
  try:
   return _kpi_date.fromisoformat(raw).strftime("%d/%m/%Y")+suffix
  except ValueError:
   return str(value)
 def _spark(items):
  valid=[(period,float(value)) for period,value in items if isinstance(value,(int,float)) and math.isfinite(value)]
  if len(valid)<2: return '<span class="axia-kpi-no-trend">Trend unavailable</span>'
  # Nine slim visual samples, interpolated only between genuine provider
  # observations. Intermediates are NOT additional reported financial periods.
  samples=[]
  last=len(valid)-1
  for index in range(9):
   position=index*last/8
   left=min(int(position),last)
   right=min(left+1,last)
   weight=position-left
   value=valid[left][1]*(1-weight)+valid[right][1]*weight
   if abs(weight)<1e-9 or left==right:
    period=valid[left][0]
    tip=_display_date(period)+": "+_card_value(value)+" "+str(currency)+" (reported)"
   else:
    tip="Visual interpolation between "+_display_date(valid[left][0])+" and "+_display_date(valid[right][0])+"; not a reported period"
   samples.append((value,tip))
  maximum=max(abs(value) for _,value in valid) or 1
  return '<span class="axia-kpi-spark" aria-label="Historical trend; intermediate bars are visual interpolation between reported periods">'+''.join(
   '<i title="'+html.escape(tip,quote=True)+'" style="height:'+str(max(3,round(abs(value)/maximum*34)))+'px;background:'+('#cf5260' if value<0 else '#14a57d')+'"></i>'
   for value,tip in samples)+'</span>'
 from datetime import date as _kpi_date
 from services.financial_kpi_engine import Observation as _KPIObservation, build_kpi as _build_kpi
 from services.independent_financial_kpi_engines import run_independently
 icons={"Revenue":"▤","Operating Income":"▣","Net Income":"♧","Free Cash Flow":"▢","Operating Margin":"◉"}
 cards=[]
 mode="ttm" if data.get("frequency")=="TTM" else "quarterly" if "Quarterly" in str(data.get("frequency")) else "annual"
 results=run_independently(data,currency)
 for label,icon in icons.items():
  item=results[label]
  current=item["value"]
  delta=item["delta"]
  display_period=_display_date(item["period"])
  if mode=="ttm" and not display_period.endswith(" TTM"):
   display_period+=" TTM"
  change_class=("up" if item.get("comparison_status") in ("turnaround","improving") else "down" if item.get("comparison_status") in ("turned_negative","declining") else ("up" if delta and delta.startswith("+") else "down" if delta and delta.startswith("-") else "neutral")) if label=="Operating Income" else ("up" if delta and delta.startswith("+") else "down" if delta and delta.startswith("-") else "neutral")
  tooltip=html.escape("Source: Yahoo Finance financial statements (not issuer-filing verified); "+str(display_period)+"; "+str(currency)+"; intermediate trend bars are interpolated visual samples, not reported periods",quote=True)
  try:
   spark=_spark(item["history"])
  except Exception:
   spark='<span class="axia-kpi-no-trend">Trend unavailable</span>'
  cards.append('<div class="axia-kpi-card'+(" axia-kpi-card-operating" if label=="Operating Income" else "")+'" title="'+tooltip+'"><div class="axia-kpi-icon">'+icon+'</div><div class="axia-kpi-body"><div class="axia-kpi-label">'+html.escape(label)+' <small>('+html.escape(display_period)+')</small></div><div class="axia-kpi-number">'+html.escape(_card_value(current,item["percent"]))+'</div><div class="axia-kpi-change '+change_class+'">'+html.escape(delta or ("Metric unavailable" if item["status"]=="error" else "Comparison unavailable"))+'</div></div>'+spark+'</div>')
 st.markdown('<div class="axia-kpi-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)
 # Native evidence control aligned with the Revenue card, without a full-width disclosure.
 evidence_columns=st.columns([1,1,1,1,1],gap="small")
 with evidence_columns[1]:
   with st.popover("ⓘ Operating Income evidence",help="Inspect the reported input, comparable period and provider limitations",use_container_width=True):
    operating=results["Operating Income"]
    st.caption("Independent calculation · Shared Yahoo Finance financial-statement snapshot. Not reconciled to an issuer filing.")
    st.markdown("**Current period:** "+str(operating.get("period") or "Unavailable"))
    st.markdown("**Operating income (EBIT):** "+(_card_value(operating.get("value"))+" "+str(currency) if operating.get("value") is not None else "Unavailable"))
    st.markdown("**Comparable period:** "+str(operating.get("previous_period") or "Unavailable"))
    st.markdown("**Comparable operating income:** "+(_card_value(operating.get("previous_value"))+" "+str(currency) if operating.get("previous_value") is not None else "Unavailable"))
    st.markdown("**Comparison:** "+str(operating.get("delta") or "Unavailable"))
    st.caption("Provider last checked: "+str(operating.get("provider_checked_at") or "Unavailable")+". Source field: Operating Income, fallback EBIT. Figures are provider-transcribed, not independently verified against the company's filing.")
    st.caption("The nine trend bars interpolate between actual available statement observations. Intermediate bars are not additional reported periods; hover for details.")
 with evidence_columns[0]:
   with st.popover("ⓘ Revenue evidence",help="Revenue source and official filing reconciliation",use_container_width=True):
    from services.revenue_verification_engine import reconcile_annual_revenue
    st.caption("Independent KPI calculation · Base data: shared Yahoo Finance financial statements.")
    revenue_period=(data.get("periods") or [""])[0]
    revenue_value=((data.get("statements") or {}).get("Income Statement") or {}).get("Revenue",{}).get(revenue_period)
    evidence_key=(str(ticker).upper(),str(data.get("frequency")),str(revenue_period),str(data.get("currency")),str(revenue_value))
    saved=st.session_state.get("axia_revenue_verification")
    if saved and saved.get("key")!=evidence_key:
     st.session_state.pop("axia_revenue_verification",None)
     saved=None
    # Verify the selected listing before choosing a regulator; USD is not a US-listing test.
    _identity=st.session_state.get("chr_security_identity") or {}
    _selected_symbol=str(_identity.get("provider_symbol") or ticker).upper()
    _selected_exchange=str(_identity.get("market") or _identity.get("exchange") or "").upper()
    _asx_listing=str(ticker).upper().endswith(".AX") or _selected_exchange=="ASX"
    _identity_conflict=bool(_identity.get("provider_symbol") and _selected_symbol!=str(ticker).upper())
    if _identity_conflict:
     st.error("The selected listing differs from the loaded financial security. Reselect the exact listing before verification.")
    elif _asx_listing:
     st.info("ASX issuer: official revenue reconciliation requires its matching ASX financial report. SEC verification is not applicable, including when statements are in USD.")
    elif st.button("Check official SEC revenue evidence",key="axia_verify_revenue"):
     with st.spinner("Checking SEC issuer identity and matching annual revenue…"):
      evidence=reconcile_annual_revenue(ticker,data)
     st.session_state["axia_revenue_verification"]={"key":evidence_key,"evidence":evidence}
     saved=st.session_state["axia_revenue_verification"]
    evidence=saved["evidence"] if saved and not (_asx_listing or _identity_conflict) else None
    if evidence:
     independent=evidence["independent"];filing=evidence["filing"];snapshot=evidence["snapshot"]
     st.markdown("**Independent data provider:** "+str(independent["status"]))
     st.caption(str(independent["reason"]))
     st.markdown("**Official filing verification:** "+str(filing["status"]))
     st.caption(str(filing["reason"]))
     if filing.get("url"): st.link_button("Open SEC filing evidence",filing["url"])
     st.markdown("**Live value confirmed:** "+str(snapshot["status"]))
     st.caption(str(snapshot["reason"]))
     st.caption("Checked: "+str(evidence["checked_at"])+" UTC · "+str(evidence["ticker"])+" · "+str(evidence["period"]))
    else:
     st.markdown("**Independent data provider:** Not checked")
     st.markdown("**Official filing verification:** "+("ASX filing connector pending" if _asx_listing else "Pending"))
     st.markdown("**Live value confirmed:** Not applicable to periodic revenue")
     st.caption("Revenue is a periodic filing metric, not a live quote. Verification requires evidence for the exact selected listing.")
 if st.button("Refresh financial statements",key="axia_refresh_fundamentals"):
  from services.fundamentals_engine import load as _load_fundamentals
  clear_cache=getattr(_load_fundamentals,"clear",None)
  if callable(clear_cache):
   clear_cache()
   st.rerun()
  else:
   st.warning("Financial refresh is unavailable in this deployment; the current provider data remains visible.")
 # Independent charts: each handles its own mode and errors without affecting KPI cards.
 from services.fundamentals_overview_chart_engine import performance_series, margin_series
 def _chart_snapshot(mode):
  return data if mode=="Annual" else load(ticker,"Quarterly (8Q)")
 def _chart_label(period,mode):
  try:
   stamp=pd.Timestamp(period)
   if mode=="Annual": return "FY"+str(stamp.year)[-2:]
   return "Q"+str((stamp.month-1)//3+1)+" · "+str(stamp.year)
  except (ValueError,TypeError): return str(period)
 def _chart_caption(snapshot,mode):
  return ("Source: Yahoo Finance via yfinance · "+mode+" financial statements · "+str(snapshot.get("currency") or "Currency unconfirmed")+
          " · provider checked "+str(snapshot.get("provider_checked_at") or "unknown")+
          " · not reconciled to official issuer filings.")
 left_chart,right_chart=st.columns([1.35,1],gap="small")
 with left_chart:
  with st.container(border=True,key="axia_financial_performance_widget"):
   st.markdown("### Financial Performance")
   performance_mode=st.radio("Financial Performance period",["Annual","Quarterly","5 Year","10 Year"],horizontal=True,label_visibility="collapsed",key="axia_financial_performance_mode")
   try:
    basis="Quarterly" if performance_mode=="Quarterly" else "Annual"
    snapshot=_chart_snapshot(basis)
    requested=10 if performance_mode=="10 Year" else 5 if performance_mode in ("5 Year","Annual") else 8
    series=performance_series(snapshot,requested)
    if not series or not any(row[k] is not None for row in series for k in ("Revenue","Operating Income","Net Income","Free Cash Flow")):
     st.info("No financial statement series available for this reporting basis.")
    else:
     labels=[_chart_label(row["Period"],basis) for row in series]
     fig=go.Figure()
     for metric,color in (("Revenue","#173b63"),("Operating Income","#0868d8"),("Net Income","#80b8ec"),("Free Cash Flow","#159b72")):
      fig.add_trace(go.Bar(name=metric,x=labels,y=[row[metric]/1e6 if row[metric] is not None else None for row in series],
                           marker_color=color,customdata=[row["Period"] for row in series],
                           hovertemplate="%{customdata}<br>"+metric+": %{y:,.2f} million "+str(snapshot.get("currency") or "")+"<extra></extra>"))
     fig.update_layout(barmode="group",height=355,margin=dict(l=8,r=8,t=44,b=18),
                       paper_bgcolor="white",plot_bgcolor="white",font=dict(color="#304965"),
                       legend=dict(orientation="h",y=1.18,x=0,font=dict(size=10)),
                       yaxis=dict(title="Millions ("+str(snapshot.get("currency") or "unconfirmed")+")",gridcolor="#e7eef6",zerolinecolor="#c9d6e5"),
                       xaxis=dict(type="category"),hovermode="x unified")
     st.plotly_chart(fig,use_container_width=True,key="axia_overview_performance")
     if len(series)<requested:
      st.caption("Only "+str(len(series))+" provider reporting periods are available for this selection; missing years are not estimated.")
    st.caption(_chart_caption(snapshot,basis))
   except Exception as exc:
    st.warning("Financial Performance chart is unavailable; the other widget and KPI cards remain available.")
    st.caption("Chart error: "+type(exc).__name__)
 with right_chart:
  with st.container(border=True,key="axia_margins_profitability_widget"):
   st.markdown("### Margins & Profitability")
   margin_mode=st.radio("Margins reporting period",["Quarterly","Annual"],horizontal=True,label_visibility="collapsed",key="axia_margins_mode")
   try:
    snapshot=_chart_snapshot(margin_mode)
    series=margin_series(snapshot,8 if margin_mode=="Quarterly" else 5)
    if not series or not any(row[k] is not None for row in series for k in ("Operating Margin","Net Income Margin")):
     st.info("Margins unavailable: comparable revenue and income observations were not returned.")
    else:
     labels=[_chart_label(row["Period"],margin_mode) for row in series]
     fig=go.Figure()
     for metric,color in (("Operating Margin","#087e53"),("Net Income Margin","#a0c72c")):
      fig.add_trace(go.Scatter(name=metric,x=labels,y=[row[metric] for row in series],mode="lines+markers",
                               connectgaps=False,line=dict(color=color,width=3),marker=dict(size=6),
                               customdata=[row["Period"] for row in series],
                               hovertemplate="%{customdata}<br>"+metric+": %{y:.1f}%<extra></extra>"))
     fig.update_layout(height=355,margin=dict(l=8,r=8,t=44,b=18),paper_bgcolor="white",plot_bgcolor="white",
                       font=dict(color="#304965"),legend=dict(orientation="h",y=1.18,x=0,font=dict(size=10)),
                       yaxis=dict(ticksuffix="%",gridcolor="#e7eef6",zerolinecolor="#c9d6e5"),
                       xaxis=dict(type="category"),hovermode="x unified")
     st.plotly_chart(fig,use_container_width=True,key="axia_overview_margins")
    st.caption(_chart_caption(snapshot,margin_mode))
   except Exception as exc:
    st.warning("Margins & Profitability chart is unavailable; the other widget and KPI cards remain available.")
    st.caption("Chart error: "+type(exc).__name__)
 # The statement and ratio cards have separate, provider-backed table models.
 from services.fundamentals_overview_table_engine import statements as overview_statements, ratio_rows as overview_ratio_rows
 def _table_period(period):
  try:
   stamp=pd.Timestamp(str(period).replace(" TTM",""))
   return "FY"+str(stamp.year)[-2:]+(" (TTM)" if "TTM" in str(period) else "")
  except (ValueError,TypeError): return str(period)
 def _million(value):
  return f"{value/1e6:,.0f}" if isinstance(value,(int,float)) and math.isfinite(value) else "—"
 def _ratio_display(value,metric):
  if not isinstance(value,(int,float)) or not math.isfinite(value): return "—"
  return f"{value:,.2f}" if metric=="EPS" else f"{value*100:,.1f}%"
 def _ratio_trend(values):
  if len(values)<2 or any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in values): return "—"
  low,high=min(values),max(values)
  if high==low: return "▅"*len(values)
  blocks="▁▂▃▄▅▆▇█"
  return "".join(blocks[min(7,max(0,round((v-low)/(high-low)*7)))] for v in values)
 statement_col,ratio_col=st.columns([1.35,1],gap="small")
 with statement_col:
  with st.container(border=True,key="axia_latest_financial_statements_widget"):
   heading,download=st.columns([3,1],vertical_alignment="center")
   with heading: st.markdown("### Latest Financial Statements")
   records=overview_statements(data)
   raw=pd.DataFrame(records)
   with download:
    st.download_button("↓ Download CSV",raw.to_csv(index=False).encode("utf-8"),file_name=ticker.replace(".","_")+"_financial_overview.csv",mime="text/csv",key="axia_overview_export",use_container_width=True,disabled=raw.empty)
   if raw.empty: st.info("No financial statements available for the selected company.")
   else:
    view=pd.DataFrame([{"Period":_table_period(row["Period"]),
     "Revenue":_million(row["Revenue"]),"Gross Profit":_million(row["Gross Profit"]),
     "Operating Income":_million(row["Operating Income"]),"Net Income":_million(row["Net Income"]),
     "EPS":f'{row["EPS"]:,.2f}' if isinstance(row["EPS"],(int,float)) and math.isfinite(row["EPS"]) else "—",
     "Free Cash Flow":_million(row["Free Cash Flow"])} for row in records])
    st.dataframe(view,hide_index=True,use_container_width=True,height=min(330,36*(len(view)+1)+8),
      column_config={"Period":st.column_config.TextColumn("Period"),"Revenue":st.column_config.TextColumn("Revenue (m)"),
       "Gross Profit":st.column_config.TextColumn("Gross Profit (m)"),
       "Operating Income":st.column_config.TextColumn("Operating Income (m)"),
       "Net Income":st.column_config.TextColumn("Net Income (m)"),
       "EPS":st.column_config.TextColumn("EPS"),
       "Free Cash Flow":st.column_config.TextColumn("Free Cash Flow (m)")})
   st.caption("Source: Yahoo Finance via yfinance · "+str(currency)+" · monetary columns in millions; EPS in "+str(currency)+" per share. Provider-transcribed, not issuer-filing verified.")
 with ratio_col:
  with st.container(border=True,key="axia_key_financial_ratios_widget"):
   st.markdown("### Key Financial Ratios")
   ratio_records=overview_ratio_rows(data)
   chronological=list(reversed(periods))
   selected=chronological[-4:]
   rows=[]
   for metric in ratio_records:
    indexed=dict(zip(metric["Periods"],metric["Values"]))
    values=[indexed.get(period) for period in selected]
    rows.append({"Metric":metric["Metric"],**{_table_period(period):_ratio_display(value,metric["Metric"]) for period,value in zip(selected,values)},
                 "Trend":_ratio_trend(values)})
   if rows:
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True,height=min(330,36*(len(rows)+1)+8))
   else: st.info("No ratio periods available for the selected company.")
   st.caption("Source: normalized provider statements · percentage metrics shown as %; EPS in "+str(currency)+". Trends represent actual comparable periods only. ROIC is withheld until verified invested-capital inputs are available.")
 from services.fundamentals_allocation_confidence_engine import capital_bridge as _capital_bridge, confidence as _confidence
 bridge=_capital_bridge(data)
 audit=_confidence(data)
 capital_col,confidence_col=st.columns([1.15,1],gap="small")
 with capital_col:
  with st.container(border=True,key="axia_capital_allocation_widget"):
   st.markdown("### Capital Allocation · Cash Flow Bridge")
   st.caption("Period: "+_table_period(bridge["period"])+" · "+str(bridge["currency"]))
   metric_col,chart_col=st.columns([1,3],vertical_alignment="center")
   with metric_col:
    st.caption("Free Cash Flow")
    st.markdown("#### "+_million(bridge["fcf"])+"m" if bridge["fcf"] is not None else "#### —")
    st.caption("Provider-derived" if bridge["fcf_derived"] else "Provider-reported" if bridge["fcf"] is not None else "Unavailable")
   with chart_col:
    if bridge["ocf"] is not None and bridge["capex"] is not None:
     # A waterfall communicates the actual OCF-to-FCF reconciliation; it does
     # not pretend dividends, buybacks or debt changes are allocation of FCF.
     complete=bridge["reconciles"]
     labels=["Operating cash flow","Capital expenditure"]
     values=[bridge["ocf"]/1e6,bridge["capex"]/1e6]
     measures=["absolute","relative"]
     if complete:
      labels.append("Free cash flow");values.append(bridge["fcf"]/1e6);measures.append("total")
     fig=go.Figure(go.Waterfall(x=labels,y=values,measure=measures,
       text=[f"{v:,.0f}" for v in values],textposition="outside",
       connector={"line":{"color":"#b6c7dc","width":1}},
       increasing={"marker":{"color":"#15a87c"}},
       decreasing={"marker":{"color":"#e75b65"}},
       totals={"marker":{"color":"#245d9e"}}))
     fig.update_layout(height=240,margin=dict(l=5,r=5,t=24,b=55),
       paper_bgcolor="white",plot_bgcolor="white",showlegend=False,
       yaxis_title=str(bridge["currency"])+" millions",
       xaxis={"tickfont":{"size":10}},yaxis={"gridcolor":"#e9eef5"})
     st.plotly_chart(fig,use_container_width=True,key="axia_overview_cash_bridge")
     if not complete:
      st.warning("Provider FCF does not reconcile with OCF less CapEx; the total bar is withheld.")
    else:
     st.info("Operating cash flow and capital expenditure are required to show the bridge.")
   st.caption(bridge["note"])
   st.caption("Dividends, buybacks, debt reduction and reinvestment are not shown: the current normalized feed does not provide separately verified allocation amounts.")
 with confidence_col:
  with st.container(border=True,key="axia_data_confidence_widget"):
   heading,detail=st.columns([3,1],vertical_alignment="center")
   with heading: st.markdown("### 🛡 Data Confidence & Verification")
   with detail:
    if st.button("View Details",key="axia_overview_confidence_details",use_container_width=True):
     st.session_state["axia_overview_confidence_open"]=not st.session_state.get("axia_overview_confidence_open",False)
   c1,c2,c3,c4=st.columns(4,gap="small")
   with c1: st.metric("Passed",audit["passed"],help="Internal consistency checks only; not independent filing verification.")
   with c2: st.metric("Mismatches",audit["mismatches"],help="Includes definition differences and invalid values.")
   with c3: st.metric("Provider-reported",audit["provider_reported"],help="Metadata reported by provider; not independently audited.")
   with c4: st.metric("Filing links",audit["filing_links"],help="Only issuer- and period-matched verified filing links count.")
   st.warning("Provider-transcribed figures have not been reconciled to audited issuer filings. Internal checks are not an audit.")
   st.caption("Not testable: "+str(audit["not_testable"])+" · Provisional: "+str(audit["provisional"])+" · Unconfirmed: "+str(audit["unconfirmed"]))
   if st.session_state.get("axia_overview_confidence_open",False):
    st.markdown("**Verification details**")
    st.caption(audit["provider"])
    st.dataframe(pd.DataFrame(audit["checks"]),hide_index=True,use_container_width=True,height=250)
 st.caption("Unavailable values are not estimated; figures are in provider-reported monetary units.")

def render(ticker):
 st.markdown("<style>\n.st-key-axia_fund_workspace [data-testid=\"stVerticalBlock\"]{gap:.55rem}\n.st-key-axia_fund_workspace [data-baseweb=\"tab-list\"]{border-bottom:1px solid #d9e5f3;gap:10px}\n.st-key-axia_fund_workspace [data-baseweb=\"tab\"]{color:#47617d;font-weight:650;padding:8px}\n.st-key-axia_fund_workspace [aria-selected=\"true\"]{color:#0868d8!important;border-bottom-color:#0868d8!important}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"]{background:#fff;border:1px solid #d9e5f3;border-radius:10px;overflow:hidden;margin-bottom:8px}\n.st-key-axia_fund_workspace [data-testid=\"stExpander\"] summary{background:#f6f9fe;color:#173b63;font-weight:750;padding:10px 14px}\n.st-key-axia_fund_workspace [data-testid=\"stDataFrame\"]{border:1px solid #e0e9f3;border-radius:8px;overflow:hidden}\n.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-checked=\"true\"],.st-key-axia_fund_workspace [data-testid=\"stSegmentedControl\"] button[aria-pressed=\"true\"]{background:#0868d8!important;color:white!important;border-color:#0868d8!important}\n</style>",unsafe_allow_html=True)
 st.markdown("""<style>
/* Scoped AXÍA Fundamentals presentation: no changes to global navigation. */
.axia-kpi-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:1px 0 17px}
.axia-kpi-card{display:grid;grid-template-columns:38px minmax(0,1fr);grid-template-rows:auto 1fr;column-gap:12px;min-width:0;position:relative;background:#fff;border:1px solid #e4ebf4;border-radius:12px;padding:16px 13px 14px;min-height:145px;box-shadow:0 1px 5px rgba(20,45,77,.045)}
.axia-kpi-icon{grid-column:1;grid-row:1;flex:none;width:38px;height:38px;border-radius:7px;background:#174b82;color:#fff;display:flex;align-items:center;justify-content:center;font-size:21px;font-weight:700}
.axia-kpi-body{display:contents}
.axia-kpi-label{grid-column:2;grid-row:1;align-self:center;min-width:0;font-size:clamp(11px,.95vw,15px);font-weight:700;color:#49617d;white-space:normal;line-height:1.2}
.axia-kpi-label small{font-size:10px;font-weight:500;white-space:nowrap}
.axia-kpi-number{grid-column:2;grid-row:2;align-self:start;font-size:clamp(20px,2vw,31px);font-weight:800;color:#142d4d;white-space:nowrap;margin:12px 0 0;line-height:1.2;-webkit-text-size-adjust:100%;text-size-adjust:100%;font-variant-numeric:tabular-nums}
/* V23.8.5: all KPI figures share the Revenue typography; never enlarge a negative value. */
.axia-kpi-card-operating .axia-kpi-number{font-size:clamp(20px,2vw,31px);font-weight:800;line-height:1.2;letter-spacing:normal;transform:none}
/* Keep long negative YoY comparisons away from the trend sparkline. */
.axia-kpi-card-operating .axia-kpi-change{max-width:calc(100% - 105px);font-size:clamp(10px,.95vw,14px);line-height:1.2}
.axia-kpi-change{position:absolute;left:63px;bottom:17px;max-width:calc(100% - 105px);font-size:clamp(10px,.95vw,14px);font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.axia-kpi-change.up{color:#168b62}.axia-kpi-change.down{color:#c54450}.axia-kpi-change.neutral{font-size:10px;color:#60758f}
.axia-kpi-spark{position:absolute;right:12px;bottom:15px;height:34px;display:flex;align-items:flex-end;gap:2px}.axia-kpi-spark i{display:block;width:4px;border-radius:1px;flex:0 0 4px}
.axia-kpi-no-trend{position:absolute;right:10px;bottom:10px;font-size:9px;color:#8190a4}
@media(max-width:1250px){.axia-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.axia-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:480px){.axia-kpi-grid{grid-template-columns:1fr}}

.st-key-axia_fund_workspace {color:#173b63}
.st-key-axia_fund_workspace [data-testid="stMetric"]{background:linear-gradient(145deg,#fff,#f7faff);border:1px solid #dce7f2;border-radius:13px;padding:14px 16px;box-shadow:0 3px 12px rgba(20,45,77,.035)}
.st-key-axia_fund_workspace [data-testid="stMetricLabel"]{color:#60758f;font-size:.8rem;font-weight:650}
.st-key-axia_fund_workspace [data-testid="stMetricValue"]{color:#142d4d;font-weight:760}
.st-key-axia_fund_workspace [data-testid="stTabs"] [data-baseweb="tab-list"]{background:#f5f8fc;border:1px solid #e0e9f3;border-radius:11px;padding:4px;gap:3px;overflow-x:auto}
.st-key-axia_fund_workspace [data-testid="stTabs"] [data-baseweb="tab"]{border-radius:8px;white-space:nowrap;padding:9px 13px;font-size:.86rem}
.st-key-axia_fund_workspace [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]{background:white;color:#0868d8!important;box-shadow:0 1px 5px rgba(20,45,77,.1);border-bottom-color:transparent!important}
.st-key-axia_fund_workspace [data-testid="stExpander"]{box-shadow:0 2px 10px rgba(20,45,77,.035)}
.st-key-axia_fund_workspace [data-testid="stExpander"] summary{background:#f8fafd!important;border-bottom:1px solid #e6edf5}
.st-key-axia_fund_workspace [data-testid="stAlert"]{border-radius:10px;border-width:1px}
.st-key-axia_fund_workspace [data-testid="stDownloadButton"] button{background:#fff;color:#173b63;border:1px solid #cbd9e9;border-radius:9px;font-weight:650}
.st-key-axia_fund_workspace [data-testid="stDownloadButton"] button:hover{border-color:#0868d8;color:#0868d8}
.st-key-axia_fund_workspace h3{color:#142d4d;letter-spacing:-.025em}
.st-key-axia_fund_workspace [data-testid="stPlotlyChart"]{background:white;border:1px solid #e0e9f3;border-radius:12px;padding:7px}
@media(max-width:800px){.st-key-axia_fund_workspace [data-testid="stMetric"]{padding:10px}.st-key-axia_fund_workspace [data-baseweb="tab"]{font-size:.78rem!important}}
</style>""",unsafe_allow_html=True)
 st.markdown("""<style>
/* Fundamentals-only issuer header; global banner/sidebar untouched. */
.st-key-axia_fund_issuer{background:#fff;border:1px solid #d9e5f3;border-radius:9px;padding:12px 17px 19px;margin-bottom:0}
/* Tighten only the gap between the issuer banner and Fundamentals navigation. */
.st-key-axia_fund_workspace [data-testid="stTabs"]{margin-top:-21px!important}
.st-key-axia_fund_workspace [data-testid="stTabs"] [data-baseweb="tab-list"]{margin-top:0!important}
.st-key-axia_fund_issuer [data-testid="stHorizontalBlock"]{align-items:center}
.st-key-axia_fund_issuer [data-testid="stVerticalBlock"]{gap:0!important}
.st-key-axia_fund_issuer [data-testid="stMarkdownContainer"] p{margin:0}
.axia-issuer-left{display:flex;align-items:center;gap:13px;min-height:76px}
.axia-issuer-mark{width:88px;height:78px;flex:0 0 88px;display:flex;align-items:center;justify-content:center;background:#fff;position:relative;overflow:hidden}
.axia-issuer-mark img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#fff;font-size:0;color:transparent}
.axia-issuer-fallback{width:80px;height:72px;align-items:center;justify-content:center;background:#f5f9ff;color:#0868d8;font-size:29px;font-weight:800;border-radius:7px}
.axia-issuer-identity{min-width:0;display:flex;flex-direction:column;justify-content:center;gap:4px;transform:translateY(-6px)}
.axia-issuer-identity h2{font-size:clamp(20px,1.75vw,29px)!important;font-weight:800;line-height:1.05;margin:0!important;padding:0!important;color:#142d4d}
.axia-issuer-details{font-size:12px;color:#60758f;line-height:1.25;white-space:normal;margin-top:0}
.axia-issuer-separator{color:#b4c5d9;margin:0 6px}
.axia-issuer-flag{display:inline-block;width:20px;height:15px;object-fit:cover;vertical-align:-2px;margin-right:4px;border-radius:1px}
.axia-issuer-tagline{font-size:12px;color:#60758f;font-style:italic;margin-top:0}
.st-key-axia_fund_issuer [data-testid="stButton"]{display:flex;justify-content:flex-end}
.st-key-axia_fund_issuer [data-testid="stButton"] button{height:32px;min-height:32px;padding:0 12px;border:1px solid #1670eb;border-radius:5px;background:#fff;color:#0868d8;font-size:12px;font-weight:700;transform:translateY(-8px)}
.axia-issuer-market{text-align:right}
.axia-issuer-quote{font-size:clamp(18px,1.65vw,28px);font-weight:800;line-height:1.15;color:#142d4d;white-space:nowrap;text-align:left;transform:translate(-40px, -2px)}
.axia-issuer-quote span{font-size:14px;margin-left:5px}
.axia-issuer-quote-note{font-size:11px;color:#60758f;margin:5px 0 7px;text-align:left;white-space:nowrap;transform:translate(-40px, -4px)}
.axia-issuer-stats{display:flex;justify-content:flex-end;transform:translateY(-2px)}
.axia-issuer-stat{padding:0 12px;border-left:1px solid #dce6f2;text-align:center;white-space:nowrap}
.axia-issuer-stat:first-child{border-left:0}
.axia-issuer-stat strong{display:block;font-size:17px;line-height:1.1;color:#142d4d}
.axia-issuer-stat span{display:block;font-size:10px;color:#60758f;margin-top:2px}
@media(max-width:1100px){.axia-issuer-quote,.axia-issuer-quote-note{transform:none}.axia-issuer-left{gap:10px}.axia-issuer-mark{width:65px;flex-basis:65px}.axia-issuer-quote{white-space:normal}.axia-issuer-stat{padding:0 6px}}
@media(max-width:760px){.st-key-axia_fund_issuer{padding:10px}.axia-issuer-left{min-height:75px}.axia-issuer-mark{width:55px;height:65px;flex-basis:55px}.axia-issuer-mark img{max-height:65px}.axia-issuer-stats{justify-content:flex-start;flex-wrap:wrap}.axia-issuer-market{text-align:left}.st-key-axia_fund_issuer [data-testid="stButton"]{justify-content:flex-start}}
</style>""",unsafe_allow_html=True)
 with st.container(key="axia_fund_workspace"):
  _render_workspace(ticker)

def _render_workspace(ticker):
 frequency="Annual (5Y)"  # Fixed display basis while the selector is hidden.
 try: data=load(ticker,frequency)
 except Exception as exc:
  st.error("Financial statements could not be loaded. Try again or inspect the issuer's filings.")
  st.caption(f"Provider error: {type(exc).__name__}")
  return
 sector=data.get("category") or category(data.get("meta") or {},ticker)
 if sector not in SECTOR: sector="general"
 currency=data.get("currency") or "Unconfirmed"
 is_qantas=str(ticker).upper() in ("QAN.MU","QAN.AX")
 # Reporting basis remains Annual (5Y) by default; the visible selector is removed.
 quality_notes=list(data.get("quality",[]))
 if currency=="Unconfirmed":
  quality_notes.insert(0,"Provider statement currency is unconfirmed. "+("Qantas issuer reports in AUD, but QAN.MU provider monetary units are not verified. " if is_qantas else "")+"Do not interpret or convert monetary values until reconciled to a dated issuer filing.")
 if quality_notes:
  with st.expander("Data quality and source limitations · "+str(len(quality_notes))+" notice(s)",expanded=False):
   for issue in quality_notes: st.caption("• "+str(issue))
 periods=data.get("periods",[])
 # Derive this notice exclusively from the currently selected issuer's loaded balance sheet.
 # Missing/non-numeric equity is not treated as zero or negative.
 equity_by_period=(data.get("statements") or {}).get("Balance Sheet",{}).get("Stockholders Equity",{})
 negative_equity={p for p in periods if isinstance(equity_by_period.get(p),(int,float)) and math.isfinite(equity_by_period[p]) and equity_by_period[p]<0}
 with st.container(key="axia_fund_issuer"):
  _issuer_header(data,ticker,currency)
 if negative_equity:
  affected=[str(p) for p in periods if p in negative_equity]
  with st.expander("⚠ Financial ratio limitation · "+str(len(affected))+" affected period(s)",expanded=False):
   st.caption("Negative shareholders’ equity was reported in the following periods: "+", ".join(affected)+".")
   st.caption("ROE, debt-to-equity, equity multiplier and Du Pont ROE are withheld for those periods; other periods are unaffected.")
   st.caption("Source: provider-transcribed Balance Sheet → Stockholders Equity for "+str(ticker).upper()+". Issuer-filing reconciliation is pending; inspect Data & Verification and the original issuer filing before relying on these figures.")
 tabs=st.tabs(["Financial Overview","Income Statement","Balance Sheet","Cash Flow","Key Metrics","Growth & Trends","Capital Allocation","Valuation & Peers","Data & Verification"],on_change="rerun",key="axia_fund_active_tab")
 with tabs[0]:
  if tabs[0].open:
   _financial_overview(data,ticker,currency)
   with st.expander("Financial health methodology & detailed scorecard",expanded=False):
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
 for statement_tab, statement_group in ((1,"Income Statement"),(2,"Balance Sheet"),(3,"Cash Flow")):
  with tabs[statement_tab]:
   if tabs[statement_tab].open:
     st.caption("Provider-transcribed figures, not reconciled to issuer filings. Monetary units: "+currency+". EPS is per share; missing values are not estimated.")
     mode=st.segmented_control("Statement display",["Reported values","Period growth","Common size"],default="Reported values",key="axia_statement_mode_"+str(statement_tab))
     mode=mode or "Reported values"
     if mode=="Period growth":
      st.caption("Change against the preceding available reporting period. Annual = annual change; quarterly = sequential quarter change, not year-on-year. Non-positive or missing bases are withheld.")
     elif mode=="Common size":
      st.caption("Income statement: % of revenue · Balance sheet: % of total assets · Cash flow: % of operating cash flow. Non-positive or missing denominators are withheld; EPS and share counts are excluded.")
     col_a,col_b=st.columns(2)
     with col_a: show_sparks=st.checkbox("Show inline sparklines",value=True,key="axia_statement_inline_sparks_"+str(statement_tab))
     with col_b: reverse_order=st.checkbox("Oldest period first",value=False,key="axia_statement_reverse_"+str(statement_tab))
     for group,table in data["statements"].items():
       if group != statement_group: continue
       with st.expander(group,expanded=True):
        if not data["periods"]: st.info("No complete periods available.");continue
        df=statement_table(data,group,mode,fmt,reverse=reverse_order,sparklines=show_sparks)
        config={"10Y Trend":st.column_config.ImageColumn("Trend · oldest → newest",width="small",help="Raw reported values; number of periods depends on available data.")} if show_sparks else {}
        st.dataframe(df,hide_index=True,use_container_width=True,column_config=config)
        export=df.drop(columns=["10Y Trend"],errors="ignore")
        st.download_button("Export "+group+" CSV",export.to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_"+group.replace(" ","_")+"_"+mode.replace(" ","_")+".csv",mime="text/csv",key="axia_export_"+group)
        if mode=="Reported values": st.caption("† Derived from provider statement components; not directly reported.")
        if show_sparks: st.caption("Inline trends use raw available statement values, oldest to newest; no interpolation or estimates. TTM may have only one point.")
 with tabs[4]:
  if tabs[4].open:
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

 with tabs[4]:
  if tabs[4].open:
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
 with tabs[5]:
  if tabs[5].open:
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
 with tabs[6]:
  if tabs[6].open:
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
 with tabs[7]:
  if tabs[7].open:
   st.subheader("Valuation & Peers")
   st.info("Comparable peer valuation requires validated market and issuer data. Missing values are not estimated.")
 with tabs[8]:
  if tabs[8].open:
   st.markdown('<div style="background:linear-gradient(110deg,#102f51,#1a507b);color:white;border-radius:14px;padding:21px 24px;margin:2px 0 17px;box-shadow:0 7px 20px rgba(16,47,81,.13)"><div style="font-size:11px;font-weight:800;letter-spacing:.13em;color:#9ed1f3">AXÍA · RESEARCH TRANSPARENCY</div><div style="font-size:23px;font-weight:750;letter-spacing:-.025em;margin-top:5px">Data Confidence &amp; Verification</div><div style="font-size:12px;color:#d4e5f4;margin-top:5px">Traceable financial inputs · Internal consistency · Source limitations</div></div>',unsafe_allow_html=True)
   checks=validate(data)
   counts=summary(checks)
   st.markdown("**Statement integrity diagnostics**")
   st.caption("Automated checks assess internal consistency only; a pass is not an audit or issuer-filing verification.")
   summary_cols=st.columns(4)
   for col,label,status in zip(summary_cols,("Checks passed","Mismatches","Definition differences","Not testable"),("Pass","Mismatch","Definition differs","Not testable")):
    with col: st.metric(label,counts.get(status,0))
   st.caption(" · ".join(k+": "+str(v) for k,v in counts.items() if v))
   flagged=[r for r in checks if r["Status"] in ("Mismatch","Definition differs","Invalid","Unconfirmed","Provisional")]
   if flagged:
    st.warning(str(len(flagged))+" diagnostic item(s) need review. A mismatch does not necessarily indicate an error in issuer filings.")
    with st.expander("Review flagged checks and compared values",expanded=True):
     st.dataframe(pd.DataFrame(flagged),hide_index=True,use_container_width=True)
     st.caption("Difference = reported minus expected. Tolerance is shown for numerical comparisons; unavailable inputs remain blank.")
   with st.expander("All integrity checks",expanded=False):
    st.dataframe(pd.DataFrame(checks),hide_index=True,use_container_width=True)
   st.download_button("Export integrity diagnostics CSV",pd.DataFrame(checks).to_csv(index=False).encode(),file_name=ticker.replace(".","_")+"_integrity.csv",mime="text/csv",key="axia_integrity_export")
   st.info("Source status: provider-transcribed figures; issuer-filing reconciliation is pending. Internal checks do not establish audit verification.")
   with st.expander("Financial statement source and chart methodology",expanded=False):
    st.caption("Source: Yahoo Finance financial statements · "+str(currency)+" · "+str(data.get("frequency"))+". Provider last checked: "+str(data.get("provider_checked_at") or "Unavailable")+". Cached for up to 1 hour; source statements update on provider publication, not continuously. Hover over bars for source dates and values. Intermediate sparkline bars are visual interpolation, not additional reported periods. Provider history is not independently reconciled to issuer filings.")
   metadata={"Provider":data.get("provider","Unavailable"),"Reporting currency":currency,"Period basis":data.get("frequency",frequency),"Audit status":"Provider-transcribed; unverified","Restatement status":"Not established","Issuer filing reference":"Not linked to a specific reporting period"}
   st.dataframe(pd.DataFrame([{"Field":k,"Value":v} for k,v in metadata.items()]),hide_index=True,use_container_width=True)
   st.caption("A company website is not evidence of an individual financial statement value. Official filing links must be matched to the selected period before verification badges are shown.")
   if data.get("derived"):
    st.dataframe(pd.DataFrame([{"Metric":k[0],"Period":k[1],"Method":v} for k,v in data["derived"].items()]),hide_index=True,use_container_width=True)
