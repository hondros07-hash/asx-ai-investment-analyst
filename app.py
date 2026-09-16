import streamlit as st
import pandas as pd
import numpy as np
import re
import yfinance as yf
from valuation_lab import scenarios, margin_of_safety
from reverse_dcf import implied_growth
from evidence_engine import evidence_for, thesis_rules, add_thesis_rule
from watchlist_engine import add as watch_add, remove as watch_remove, get as watch_get
from portfolio_engine import portfolio_analytics, concentration
from model_monitor import registry
from sector_models import SECTOR_KPIS
from live_data_provider import market_snapshot, twelve_price
from market_chart_engine import RANGES, range_data, summary as chart_summary, previous_close, price_figure
from market_universe import BENCHMARKS, resolve_bare_ticker, detect_market
from sector_peer_engine import classification, find_peers, peer_table, normalized_history, equal_weight_peer_basket, default_benchmark
from research_system import snapshot as research_snapshot, kpi_framework, technical_state, peer_fundamentals, evidence_status, thesis_checklist
from market_terminal import td_catalog, commodity_catalog, fallback_catalog, live_rows
from security_search import search_securities, resolve_listing, identity
from announcement_engine import announcements, fetch_document, extract_text, evidence_summary

st.set_page_config(page_title="Market Investment Analyst", page_icon="📈", layout="wide")

st.markdown("""
<style>
:root {
  --royal-blue: #4169E1;
  --royal-blue-dark: #2747A8;
  --white: #FFFFFF;
}
.stApp { background: #FFFFFF; color: #111827; }
[data-testid="stSidebar"] {
  background: #4169E1;
}
[data-testid="stSidebar"] * {
  color: #FFFFFF !important;
}
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
  color: #111827 !important;
  background: #FFFFFF !important;
}
h1, h2, h3 {
  color: #2747A8;
}
div[data-testid="stMetric"] {
  background: #FFFFFF;
  border: 1px solid #D9E2FF;
  border-top: 4px solid #4169E1;
  border-radius: 10px;
  padding: 10px;
}
.stButton > button {
  background: #4169E1;
  color: #FFFFFF;
  border: 1px solid #4169E1;
  border-radius: 8px;
}
.stButton > button:hover {
  background: #2747A8;
  color: #FFFFFF;
  border-color: #2747A8;
}
[data-baseweb="tab-highlight"] {
  background-color: #4169E1 !important;
}
a { color: #4169E1; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def history(t, period="5y"):
    try: return yf.Ticker(t).history(period=period, auto_adjust=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=900)
def info(t):
    try: return yf.Ticker(t).info
    except: return {}

def change(s,n):
    return np.nan if len(s)<=n else s.iloc[-1]/s.iloc[-n-1]-1

def rsi(s,n=14):
    d=s.diff(); u=d.clip(lower=0).rolling(n).mean(); dn=(-d.clip(upper=0)).rolling(n).mean()
    return 100-100/(1+u/dn.replace(0,np.nan))

def money(v):
    if v is None or pd.isna(v): return "—"
    if abs(v)>=1e9:return f"${v/1e9:.2f}B"
    if abs(v)>=1e6:return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"

st.sidebar.title("Market Investment Analyst")
try:
    _search_key=st.secrets.get("TWELVE_DATA_API_KEY","")
except Exception:
    _search_key=""
query=st.sidebar.text_input("Company or ticker","ZIP.AX",
    help="Search by company name or exchange ticker.")
matches=search_securities(query,_search_key)
if not matches.empty:
    _labels=[]; _map={}
    for i,r in matches.head(40).iterrows():
        lab=f"{r['Company']} — {r['Symbol']} — {r['Exchange']}"
        _labels.append(lab); _map[lab]=i
    _chosen=st.sidebar.selectbox("Matching listings",_labels)
    _row=matches.loc[_map[_chosen]]
    ticker=resolve_listing(_row["Symbol"],_row.get("Exchange",""),_row.get("Country",""))
    st.sidebar.caption(f"Selected: {identity(ticker)} • {ticker}")
else:
    ticker=resolve_bare_ticker(query.strip().upper())
    st.sidebar.caption("No company-directory match found; trying the entry as a ticker.")
thesis=st.sidebar.text_area("Investment thesis","Revenue and earnings continue growing, margins improve, cash generation strengthens and key operating KPIs remain healthy.",height=125)
page=st.sidebar.radio("Research workspace",["Markets","Dashboard","Announcements & Reports","Research Report","Investment Committee","Fundamentals","Valuation","Technical","Quant","Forecasts","News & Events","Evidence & Thesis","Portfolio","Watchlist","Model Lab","Data & Production"])

h=history(ticker); meta=info(ticker)
if h.empty:
    st.error(f"No market data returned for {ticker}. Try another matching listing or enter the exchange ticker directly.")
    st.stop()
close=h["Close"]; price=float(close.iloc[-1]); name=meta.get("longName") or ticker
rv=rsi(close); rv=float(rv.iloc[-1]) if len(rv) and pd.notna(rv.iloc[-1]) else np.nan

st.title("Market Investment Analyst")
st.caption("V12.1.1 • Market Investment Analyst • research terminal")

if page=="Markets":
    st.header("Global Market Terminal")
    st.caption("Browse exchange instrument catalogs and track selected symbols. Data labelled live is provider-dependent; Yahoo/yfinance fallback is not presented as exchange-grade real-time.")

    try:
        td_key=st.secrets.get("TWELVE_DATA_API_KEY","")
    except Exception:
        td_key=""

    source_msg=("Twelve Data connected — catalog and quote requests use your API entitlement."
                if td_key else
                "Twelve Data API key not configured — showing curated catalog fallback and Yahoo/yfinance prices. This is not a complete live exchange feed.")
    st.info(source_msg)

    market=st.radio("Market",["ASX","NASDAQ","NYSE","Commodities"],horizontal=True)
    c1,c2,c3=st.columns([1,1,2])
    page_no=c1.number_input("Catalog page",1,1000,1,1)
    page_size=c2.selectbox("Rows per page",[25,50,100,250],index=2)
    search=c3.text_input("Search symbol or company","").strip().lower()

    if market=="Commodities":
        catalog=commodity_catalog(td_key)
    else:
        catalog=td_catalog(td_key,market,int(page_no),int(page_size)) if td_key else fallback_catalog(market)

    if catalog.empty:
        st.warning("No catalog data returned by the configured provider.")
    else:
        if search:
            mask=pd.Series(False,index=catalog.index)
            for col in [x for x in ["symbol","name","instrument_name"] if x in catalog.columns]:
                mask=mask | catalog[col].astype(str).str.lower().str.contains(search,regex=False)
            catalog=catalog[mask]
        showcols=[c for c in ["symbol","name","instrument_name","exchange","country","currency","type","category"] if c in catalog.columns]
        st.subheader(f"{market} instrument catalog")
        st.dataframe(catalog[showcols] if showcols else catalog,use_container_width=True,hide_index=True,height=420)

        symbols=catalog["symbol"].astype(str).tolist() if "symbol" in catalog.columns else []
        defaults=symbols[:min(8,len(symbols))]
        selected=st.multiselect("Track prices",symbols,default=defaults,
                                help="Select a manageable group to avoid exhausting provider API credits.")
        refresh=st.button("Refresh tracked prices",type="primary")
        if selected:
            st.subheader("Tracked market data")
            quotes=live_rows(selected,td_key,market if market!="Commodities" else None,asx_suffix=(market=="ASX" and not td_key))
            if quotes.empty:
                st.warning("No quote data returned for the selected instruments.")
            else:
                st.dataframe(quotes.style.format({
                    "Price":"{:,.4f}","Change":"{:+,.4f}","% Change":"{:+.2f}",
                    "Open":"{:,.4f}","High":"{:,.4f}","Low":"{:,.4f}","Volume":"{:,.0f}"
                },na_rep="—"),use_container_width=True,hide_index=True)
                st.caption("Timestamp and Source are shown per row so delayed/fallback observations are not confused with licensed real-time exchange data.")

elif page=="Dashboard":
    st.header(f"{ticker} — {name}")
    _market_info = meta if isinstance(meta, dict) else {}
    market_meta = detect_market(ticker, _market_info)
    ex1,ex2,ex3,ex4=st.columns(4)
    ex1.metric("Market", market_meta["market"])
    ex2.metric("Exchange", market_meta["exchange"])
    ex3.metric("Currency", market_meta["currency"])
    ex4.metric("Default benchmark",
               "ASX 200" if market_meta["benchmark"]=="^AXJO" else
               "Nasdaq 100" if market_meta["benchmark"]=="^NDX" else "S&P 500")

    prev = previous_close(ticker)
    day_change = price-prev if prev not in (None,0) else np.nan
    day_pct = day_change/prev if prev not in (None,0) else np.nan
    day_hist = history(ticker, "5d")
    day_high = float(day_hist["High"].iloc[-1]) if not day_hist.empty else np.nan
    day_low = float(day_hist["Low"].iloc[-1]) if not day_hist.empty else np.nan
    day_vol = float(day_hist["Volume"].iloc[-1]) if not day_hist.empty else np.nan
    hi52 = float(h.tail(252)["High"].max()) if len(h) else np.nan
    lo52 = float(h.tail(252)["Low"].min()) if len(h) else np.nan

    q=st.columns(7)
    q[0].metric("Price",f"${price:.3f}",
                None if pd.isna(day_change) else f"{day_change:+.3f} ({day_pct*100:+.2f}%)")
    q[1].metric("Previous close","—" if prev is None else f"${prev:.3f}")
    q[2].metric("Day high","—" if pd.isna(day_high) else f"${day_high:.3f}")
    q[3].metric("Day low","—" if pd.isna(day_low) else f"${day_low:.3f}")
    q[4].metric("Volume","—" if pd.isna(day_vol) else f"{day_vol/1e6:.2f}M")
    q[5].metric("52W high","—" if pd.isna(hi52) else f"${hi52:.3f}")
    q[6].metric("52W low","—" if pd.isna(lo52) else f"${lo52:.3f}")

    st.subheader("Price chart")
    period = st.radio("Period", list(RANGES.keys()), horizontal=True, index=4)
    cc0,cc1,cc2,cc3=st.columns([1.2,1.2,1,2])
    chart_type=cc0.radio("Chart type",["Line","Candlestick"],horizontal=True)
    mode=cc1.radio("Display",["Price","Percentage"],horizontal=True)
    volume_on=cc2.checkbox("Show volume",value=True)
    with cc3:
        ma_cols=st.columns(3)
        sma20=ma_cols[0].checkbox("SMA 20")
        sma50=ma_cols[1].checkbox("SMA 50")
        sma200=ma_cols[2].checkbox("SMA 200")

    chart_d=range_data(ticker,period)
    s=chart_summary(chart_d)
    if chart_d.empty:
        st.warning("No chart data returned for this period.")
    else:
        m=st.columns(6)
        m[0].metric(f"{period} movement",f"{s['change']:+.3f}",
                    f"{s['change_pct']*100:+.2f}%")
        m[1].metric("Period start",f"${s['start']:.3f}")
        m[2].metric("Latest",f"${s['last']:.3f}")
        m[3].metric("Period high",f"${s['high']:.3f}")
        m[4].metric("Period low",f"${s['low']:.3f}")
        m[5].metric("Period volume","—" if pd.isna(s['volume']) else f"{s['volume']/1e6:.2f}M")

        compare_choice=st.selectbox("Compare performance with",
            ["None","ASX 200","S&P 500","Nasdaq 100","Dow Jones","Another ticker"])
        compare_map={"ASX 200":"^AXJO","S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI"}
        compare_ticker=""
        if compare_choice=="Another ticker":
            compare_ticker=st.text_input("Comparison ticker","BHP.AX").strip().upper()
            compare_ticker=resolve_bare_ticker(compare_ticker)
        elif compare_choice!="None":
            compare_ticker=compare_map[compare_choice]

        comp=None
        if compare_ticker:
            p,i=RANGES[period]
            try:
                comp=yf.Ticker(compare_ticker).history(period=p,interval=i,auto_adjust=True)
                if period=="3D" and not comp.empty:
                    dates=pd.Index(comp.index.date).unique()
                    if len(dates)>3: comp=comp[pd.Index(comp.index.date).isin(dates[-3:])]
            except Exception: comp=None
            if mode=="Price":
                st.caption("Comparison is displayed in Percentage mode so instruments with different price scales can be compared.")
                mode="Percentage"

        if chart_type=="Candlestick" and mode=="Percentage":
            st.info("Candlesticks use OHLC prices, so Percentage mode is displayed as a line chart.")
        st.plotly_chart(price_figure(
            chart_d,ticker,mode,volume_on,sma20,sma50,sma200,
            comp,compare_choice,chart_type
        ),use_container_width=True)

        if volume_on and "Volume" in chart_d:
            vol=chart_d[["Volume"]].copy()
            st.bar_chart(vol,height=150)

    st.caption("Intraday availability and delay depend on the active data provider. The displayed period movement is calculated from the first to last observation returned for the selected range.")

    st.subheader("Performance")
    perf=st.columns(6)
    for c,(lab,n) in zip(perf,[("1M",21),("3M",63),("6M",126),("1Y",252)]):
        v=change(close,n); c.metric(lab,"—" if pd.isna(v) else f"{v*100:+.1f}%")
    ytd=close[close.index.year==close.index[-1].year]
    ytdv=(ytd.iloc[-1]/ytd.iloc[0]-1) if len(ytd)>1 else np.nan
    perf[4].metric("YTD","—" if pd.isna(ytdv) else f"{ytdv*100:+.1f}%")
    perf[5].metric("RSI14","—" if pd.isna(rv) else f"{rv:.1f}")

    st.subheader("Research status")
    a,b,c=st.columns(3)
    a.info("**Thesis status**\n\nMonitoring")
    b.info("**Data confidence**\n\nMarket data connected; specialist KPIs need verified company data.")
    ma=close.rolling(200).mean().iloc[-1] if len(close)>=200 else np.nan
    c.info("**Market structure**\n\n"+("Above 200D MA" if pd.notna(ma) and price>ma else "Below 200D MA"))

    st.subheader("Live cross-market snapshot")
    try: td_key=st.secrets.get("TWELVE_DATA_API_KEY","")
    except Exception: td_key=""
    if td_key:
        snap=market_snapshot(td_key)
        st.dataframe(snap[["Market","Symbol","Price","Source","Status"]],use_container_width=True,hide_index=True)
    else:
        st.info("Add TWELVE_DATA_API_KEY to Streamlit Secrets to activate supported Twelve Data markets.")

    st.subheader("Sector KPI monitor")
    if ticker.startswith("ZIP"):
        labels={"ttv":"TTV / Payment Volume","active_customers":"Active Customers","transaction_margin":"Transaction Margin","credit_losses":"Credit Losses","revenue_growth":"Revenue Growth","cash_ebitda":"Cash EBITDA","operating_margin":"Operating Margin","us_growth":"US Growth","international_growth":"International Growth","regulatory_risk":"Regulatory Risk"}
        rows=[[labels.get(x,x.replace("_"," ").title()),"Awaiting verified company data","Not connected"] for x in SECTOR_KPIS["BNPL/Fintech"]]
        st.dataframe(pd.DataFrame(rows,columns=["KPI","Latest","Status"]),use_container_width=True,hide_index=True)
    else:
        st.info("Sector KPI selection will use verified sector metadata when connected.")


    st.divider()
    st.subheader("Sector & Peer Intelligence")
    cls=classification(ticker,meta)
    bm_ticker,bm_name=default_benchmark(ticker,meta)
    pc1,pc2,pc3=st.columns(3)
    pc1.metric("Sector",cls["sector"])
    pc2.metric("Industry",cls["industry"])
    pc3.metric("Market benchmark",bm_name)

    with st.spinner("Identifying comparable companies and calculating relative performance..."):
        peers=find_peers(ticker,meta,max_peers=8)

    if not peers:
        st.info("No sufficiently matched peers were found in the current curated universe. The company can still be compared with its market benchmark.")
    else:
        st.caption("Peers are selected automatically by industry first, then sector. Review the peer group before using it for investment decisions.")
        pt=peer_table(ticker,peers)
        fmt={"Price":"${:,.3f}","1M":"{:+.2%}","3M":"{:+.2%}","6M":"{:+.2%}","1Y":"{:+.2%}"}
        st.dataframe(pt.style.format(fmt,na_rep="—"),use_container_width=True,hide_index=True)

    peer_period_label=st.radio("Relative performance period",["1M","3M","6M","1Y","3Y","5Y"],horizontal=True,index=2)
    pp={"1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","3Y":"3y","5Y":"5y"}[peer_period_label]
    selected_peer_tickers=[x["ticker"] for x in peers]
    perf=normalized_history([ticker]+selected_peer_tickers+[bm_ticker],pp)
    if not perf.empty and ticker in perf.columns:
        import plotly.graph_objects as go
        figp=go.Figure()
        figp.add_trace(go.Scatter(x=perf.index,y=perf[ticker],mode="lines",name=ticker))
        basket=equal_weight_peer_basket(perf.drop(columns=[bm_ticker],errors="ignore"),ticker)
        if not basket.empty:
            figp.add_trace(go.Scatter(x=basket.index,y=basket,mode="lines",name="Peer basket"))
        if bm_ticker in perf.columns:
            figp.add_trace(go.Scatter(x=perf.index,y=perf[bm_ticker],mode="lines",name=bm_name))
        figp.update_layout(height=430,margin=dict(l=10,r=10,t=20,b=10),
                           yaxis_title="Return (%)",hovermode="x unified",
                           legend=dict(orientation="h"))
        st.plotly_chart(figp,use_container_width=True)

        latest_company=float(perf[ticker].dropna().iloc[-1])
        latest_peer=float(basket.dropna().iloc[-1]) if not basket.empty and not basket.dropna().empty else np.nan
        latest_bm=float(perf[bm_ticker].dropna().iloc[-1]) if bm_ticker in perf and not perf[bm_ticker].dropna().empty else np.nan
        rr=st.columns(5)
        rr[0].metric(f"{ticker} return",f"{latest_company:+.2f}%")
        rr[1].metric("Peer basket", "—" if pd.isna(latest_peer) else f"{latest_peer:+.2f}%")
        rr[2].metric(bm_name, "—" if pd.isna(latest_bm) else f"{latest_bm:+.2f}%")
        rr[3].metric("vs peers","—" if pd.isna(latest_peer) else f"{latest_company-latest_peer:+.2f} pp")
        rr[4].metric("vs market","—" if pd.isna(latest_bm) else f"{latest_company-latest_bm:+.2f} pp")
    else:
        st.warning("Insufficient price history to calculate the selected relative-performance period.")


elif page=="Announcements & Reports":
    st.header(f"Announcements & Reports — {ticker} — {name}")
    st.caption("Exchange/regulatory announcement history for the selected listing. ASX can use a licensed provider when configured; SEC EDGAR is used for US listings.")

    try:
        _ann_url=st.secrets.get("ASX_ANNOUNCEMENTS_API_URL","")
        _ann_key=st.secrets.get("ASX_ANNOUNCEMENTS_API_KEY","")
    except Exception:
        _ann_url=_ann_key=""

    c1,c2,c3=st.columns([1,1,2])
    ann_limit=c1.selectbox("Announcements to retrieve",[50,100,250],index=1)
    category=c2.selectbox("Category",["All","Annual Report","Half-Year Report","Quarterly Report","Results",
        "Investor Presentation","Trading Update","Guidance","Capital / Funding","Ownership","Director Notice","Corporate Action"])
    query_filter=c3.text_input("Search announcements","",placeholder="results, annual report, buy-back, substantial holder…")

    with st.spinner("Loading exchange announcements..."):
        ann,coverage=announcements(ticker,_ann_url,_ann_key,int(ann_limit))

    st.caption(f"Data route: {coverage}")
    if ticker.endswith(".AX") and not _ann_url:
        st.info("ASX provider credentials are not configured. The app is using the public ASX archive as a fallback. For CommSec-style complete/reliable coverage, connect an authorised ASX ComNews-capable feed in Streamlit Secrets.")

    if ann.empty:
        st.warning("No announcements were returned by this data route.")
        if ticker.endswith(".AX") and not _ann_url:
            st.error("ASX's public website is not a dependable application data feed. Connect an authorised ASX ComNews-capable provider for complete in-app ASX history, summaries and downloads.")
        elif not ticker.endswith(".AX"):
            st.caption("For US securities the app uses the SEC submissions API. If this persists, check the SEC request status/user-agent and the selected ticker-to-CIK mapping.")
    else:
        if category!="All":
            ann=ann[ann["Type"].astype(str).eq(category)]
        if query_filter:
            q=query_filter.lower().strip()
            aliases={
                "annual report":["annual report","10-k","20-f","40-f"],
                "quarterly":["quarterly","10-q"],
                "quarterly report":["quarterly","10-q"],
                "current report":["8-k","6-k"],
                "results":["results","10-k","10-q","20-f","40-f"],
            }
            terms=aliases.get(q,[q])
            ann=ann[ann.apply(lambda r:any(term in (str(r["Title"])+" "+str(r["Type"])).lower() for term in terms),axis=1)]
        st.metric("Announcements found",len(ann))
        show=ann[["Date","Type","Title","Price Sensitive","Source"]].copy()
        st.dataframe(show,use_container_width=True,hide_index=True,height=430)

        if not ann.empty:
            opts=[]; mapping={}
            for i,r in ann.iterrows():
                flag=" 🔴" if bool(r.get("Price Sensitive",False)) else ""
                lab=f"{r['Date']} — {r['Type']} — {r['Title']}{flag}"
                opts.append(lab); mapping[lab]=i
            selected=st.selectbox("Select announcement",opts)
            rr=ann.loc[mapping[selected]]
            st.subheader(str(rr["Title"]))
            a,b,c=st.columns(3)
            a.metric("Date",str(rr["Date"])); b.metric("Category",str(rr["Type"]))
            c.metric("Price sensitive","Yes" if bool(rr.get("Price Sensitive",False)) else "No / not supplied")

            if st.button("Open & summarise",type="primary"):
                with st.spinner("Downloading and reading the original announcement..."):
                    doc,ctype=fetch_document(str(rr["URL"]))
                    text=extract_text(doc,ctype)
                    summ=evidence_summary(text)
                st.session_state["ann_key"]=selected
                st.session_state["ann_doc"]=doc
                st.session_state["ann_ctype"]=ctype
                st.session_state["ann_summary"]=summ

            if st.session_state.get("ann_key")==selected:
                st.markdown("#### Evidence-based summary")
                st.write(st.session_state.get("ann_summary",""))
                doc=st.session_state.get("ann_doc")
                if doc:
                    ispdf=doc[:4]==b"%PDF" or "pdf" in st.session_state.get("ann_ctype","").lower()
                    ext=".pdf" if ispdf else ".html"
                    fname=re.sub(r"[^A-Za-z0-9_-]+","_",f"{ticker}_{rr['Date']}_{rr['Type']}")[:110]+ext
                    st.download_button("Download original announcement",doc,file_name=fname,
                        mime=st.session_state.get("ann_ctype") or "application/octet-stream")
                else:
                    st.error("The announcement metadata loaded, but the original document could not be retrieved.")

elif page=="Research Report":
    st.header(f"Research Report — {ticker} — {name}")
    cls=classification(ticker,meta)
    snap=research_snapshot(meta)
    tech=technical_state(h)
    peers=find_peers(ticker,meta,max_peers=8)
    bm_ticker,bm_name=default_benchmark(ticker,meta)

    st.subheader("1. Research identity")
    r1,r2,r3,r4=st.columns(4)
    r1.metric("Sector",cls["sector"]); r2.metric("Industry",cls["industry"])
    r3.metric("Market benchmark",bm_name); r4.metric("Price",f"${price:.3f}")

    st.subheader("2. Fundamental & valuation snapshot")
    rows=[]
    pct_keys={"Revenue growth","Earnings growth","Gross margin","Operating margin","Profit margin","ROE","ROA","Dividend yield"}
    for k,v in snap.items():
        if pd.isna(v): shown="—"
        elif k in pct_keys: shown=f"{v:.2%}"
        elif k in {"Market cap","Enterprise value","Free cash flow","Operating cash flow"}: shown=money(v)
        else: shown=f"{v:,.2f}"
        rows.append([k,shown])
    st.dataframe(pd.DataFrame(rows,columns=["Metric","Value"]),use_container_width=True,hide_index=True)
    st.caption("Provider fundamentals are screening inputs. Material figures should be verified against company filings before an investment decision.")

    st.subheader("3. Sector-specific operating KPIs")
    kp=kpi_framework(cls["sector"],cls["industry"])
    st.dataframe(pd.DataFrame({"KPI to monitor":kp,"Live verified value":["Not connected"]*len(kp),
                              "Trend":["Awaiting filings / KPI feed"]*len(kp)}),
                 use_container_width=True,hide_index=True)

    st.subheader("4. Peer fundamentals & valuation")
    if peers:
        pf=peer_fundamentals([ticker]+[p["ticker"] for p in peers])
        pctcols=["Revenue growth","Operating margin","ROE"]
        st.dataframe(pf.style.format({
            "P/E":"{:.2f}","Forward P/E":"{:.2f}","EV/EBITDA":"{:.2f}","P/B":"{:.2f}",
            **{x:"{:.2%}" for x in pctcols}
        },na_rep="—"),use_container_width=True,hide_index=True)
    else: st.info("No matched peers available in the current curated universe.")

    st.subheader("5. Price, momentum & risk")
    tr=[]
    for k,v in tech.items():
        if pd.isna(v): shown="—"
        elif "return" in k.lower() or "volatility" in k.lower() or "drawdown" in k.lower(): shown=f"{v:.2%}"
        else: shown=f"${v:,.3f}"
        tr.append([k,shown])
    st.dataframe(pd.DataFrame(tr,columns=["Measure","Value"]),use_container_width=True,hide_index=True)

    st.subheader("6. Thesis stress test")
    st.write("Current thesis:",thesis)
    st.dataframe(pd.DataFrame(thesis_checklist(cls["sector"],cls["industry"])),
                 use_container_width=True,hide_index=True)
    st.caption("V11 deliberately does not mark a thesis as supported or broken without verified operating evidence.")

    st.subheader("7. Evidence & data quality")
    es=evidence_status(meta,h)
    st.dataframe(pd.DataFrame(es.items(),columns=["Evidence source","Status"]),
                 use_container_width=True,hide_index=True)

    st.subheader("8. Forecast discipline")
    st.info("1M / 3M / 6M probabilities are withheld until the backtest is leakage-safe, horizon-correct and calibrated on unseen data. V11 will not manufacture forecast probabilities.")

    st.subheader("9. Research gaps")
    st.write("Before this can function as an institutional-grade research system, connect official ASX/SEC filings, point-in-time fundamentals, consensus estimates, corporate actions, a survivorship-safe universe and licensed production market data.")

elif page=="Investment Committee":
    st.header(f"{ticker} — Investment Committee"); st.info(thesis)
    st.warning("Missing evidence is not converted into artificial scores.")
    rows=[["Fundamental","Pending verified fundamentals"],["Valuation","DCF / reverse DCF available"],["Technical","Market data connected"],["Quant","Research engines included"],["Macro","Production feed required"],["Catalysts","Announcement/news feed required"],["Risk","Partial evidence"]]
    st.dataframe(pd.DataFrame(rows,columns=["Engine","Status"]),use_container_width=True,hide_index=True)

elif page=="Fundamentals":
    st.header("Fundamentals")
    fields={"Revenue growth":meta.get("revenueGrowth"),"Earnings growth":meta.get("earningsGrowth"),"Operating margin":meta.get("operatingMargins"),"Profit margin":meta.get("profitMargins"),"ROE":meta.get("returnOnEquity"),"ROA":meta.get("returnOnAssets"),"Current ratio":meta.get("currentRatio"),"Debt / Equity":meta.get("debtToEquity")}
    rows=[]
    for k,v in fields.items():
        if v is None: out="—"
        elif k in ["Current ratio","Debt / Equity"]: out=f"{v:.2f}"
        else: out=f"{v*100:.1f}%"
        rows.append([k,out])
    st.dataframe(pd.DataFrame(rows,columns=["Metric","Current feed value"]),use_container_width=True,hide_index=True)
    st.warning("Generic feed accounting fields must be verified against company reports before thesis decisions, especially for financial/BNPL businesses.")

elif page=="Valuation":
    st.header("Valuation & Expectations")
    fcf=st.number_input("Starting annual FCF",value=100_000_000.0,step=1_000_000.0)
    shares=st.number_input("Shares outstanding",value=1_000_000_000.0,step=1_000_000.0)
    debt=st.number_input("Net debt (negative = net cash)",value=0.0,step=1_000_000.0)
    assumptions={"Bear":{"growth":.04,"wacc":.12,"terminal_growth":.02},"Base":{"growth":.10,"wacc":.10,"terminal_growth":.03},"Bull":{"growth":.16,"wacc":.09,"terminal_growth":.035}}
    v=scenarios(fcf,shares,debt,assumptions); v["margin_of_safety"]=v.value_per_share.map(lambda x:margin_of_safety(price,x))
    st.dataframe(v,use_container_width=True,hide_index=True)
    ig=implied_growth(price,fcf,shares,debt,.10,.03)
    st.metric("Reverse-DCF implied 5Y FCF growth","—" if pd.isna(ig) else f"{ig*100:.1f}%")
    st.caption("Outputs are assumption-sensitive; validated inputs are required.")

elif page=="Technical":
    st.header("Technical")
    d=pd.DataFrame({"Price":close,"SMA20":close.rolling(20).mean(),"SMA50":close.rolling(50).mean(),"SMA200":close.rolling(200).mean()})
    st.line_chart(d)
    cs=st.columns(4)
    cs[0].metric("RSI14","—" if pd.isna(rv) else f"{rv:.1f}")
    for c,n in zip(cs[1:],[20,50,200]):
        m=close.rolling(n).mean().iloc[-1]; c.metric(f"vs SMA{n}",f"{(price/m-1)*100:.1f}%")

elif page=="Quant":
    st.header("Quant")
    ret=close.pct_change().dropna(); curve=(1+ret).cumprod(); dd=curve/curve.cummax()-1
    cs=st.columns(4); cs[0].metric("Annualised volatility",f"{ret.std()*np.sqrt(252)*100:.1f}%"); cs[1].metric("Max drawdown",f"{dd.min()*100:.1f}%")
    sh=ret.mean()/ret.std()*np.sqrt(252) if ret.std() else np.nan; cs[2].metric("Sharpe (0% RF)","—" if pd.isna(sh) else f"{sh:.2f}")
    cs[3].metric("12M momentum","—" if len(close)<253 else f"{change(close,252)*100:.1f}%")
    st.info("V6–V9 backtest, factor, ML ensemble and point-in-time modules remain packaged.")

elif page=="Forecasts":
    st.header("1M / 3M / 6M Forecast Research")
    st.info("V10.1 does not invent current probabilities when a validated model run is unavailable.")
    st.write("Target outputs: calibrated positive-return/outperformance probability, expected return, downside distribution, model disagreement and data confidence.")

elif page=="News & Events":
    st.header("News, Announcements & Catalysts")
    st.info("Document/event intelligence is included. Automated production use still needs an official/permitted ASX announcement and news feed.")
    st.write("Event analysis: direction • materiality • horizon • confidence • transmission mechanism • counterargument • thesis impact.")

elif page=="Evidence & Thesis":
    st.header("Evidence & Kill My Thesis"); st.info(thesis)
    st.dataframe(evidence_for(ticker),use_container_width=True,hide_index=True)
    st.subheader("Thesis-break rules"); st.dataframe(thesis_rules(ticker),use_container_width=True,hide_index=True)
    with st.form("rule"):
        metric=st.text_input("Metric e.g. credit_loss_rate"); op=st.selectbox("Trigger when",["<","<=",">",">="]); threshold=st.number_input("Threshold",value=0.0); reason=st.text_input("Why it matters")
        if st.form_submit_button("Add thesis rule"): add_thesis_rule(ticker,metric,op,threshold,"",reason); st.success("Rule saved.")

elif page=="Portfolio":
    st.header("Portfolio Intelligence")
    raw=st.text_area("TICKER,WEIGHT","ZIP.AX,0.20\nBHP.AX,0.20\nCBA.AX,0.20\nCSL.AX,0.20\nWES.AX,0.20")
    if st.button("Analyse portfolio"):
        w={}
        for line in raw.splitlines():
            try:t,x=line.split(","); w[t.strip().upper()]=float(x)
            except:pass
        px={}
        for t in w:
            x=history(t)
            if not x.empty:px[t]=x.Close
        if px:
            a=portfolio_analytics(pd.DataFrame(px),w); cs=st.columns(4)
            cs[0].metric("Annualised return",f"{a['annualised_return']*100:.1f}%"); cs[1].metric("Volatility",f"{a['annualised_volatility']*100:.1f}%"); cs[2].metric("Max drawdown",f"{a['max_drawdown']*100:.1f}%"); cs[3].metric("HHI",f"{concentration(w):.3f}")
            st.dataframe(a["correlation"],use_container_width=True)

elif page=="Watchlist":
    st.header("Watchlist"); note=st.text_input("Thesis / monitoring note"); a,b=st.columns(2)
    if a.button("Add/update"): watch_add(ticker,note); st.success("Saved.")
    if b.button("Remove"): watch_remove(ticker); st.success("Removed.")
    st.dataframe(watch_get(),use_container_width=True,hide_index=True)

elif page=="Model Lab":
    st.header("Model Lab"); st.dataframe(registry(),use_container_width=True,hide_index=True)
    st.write("V6 walk-forward, V7 universe/factors, V8 ensemble and V9 point-in-time architecture remain included.")

elif page=="Data & Production":
    st.header("Data & Production — V10.2")
    try:
        td_key = st.secrets.get("TWELVE_DATA_API_KEY", "")
    except Exception:
        td_key = ""
    c1,c2,c3=st.columns(3)
    c1.metric("Twelve Data API","Connected" if td_key else "Not configured")
    c2.metric("ASX prototype feed","Yahoo/yfinance")
    c3.metric("Provider architecture","Active")
    st.subheader("Market coverage")
    st.dataframe(pd.DataFrame([
        ["ASX","Australian equities","ZIP.AX / BHP.AX","ASX 200"],
        ["NASDAQ","US equities","AAPL / NVDA","Nasdaq 100 / S&P 500"],
        ["NYSE","US equities","KO / JPM","S&P 500 / Dow Jones"],
    ],columns=["Market","Coverage","Example symbols","Benchmarks"]),
    use_container_width=True,hide_index=True)

    st.subheader("Connection test")
    test_symbol=st.text_input("Twelve Data test symbol","AAPL")
    if st.button("Test Twelve Data"):
        q=twelve_price(test_symbol,td_key)
        if q.price is not None:
            st.success(f"{q.symbol}: {q.price} • source: {q.source}")
        else:
            st.error(q.message or q.status)
    st.subheader("Current routing")
    st.dataframe(pd.DataFrame([
        ["ASX equities","Yahoo/yfinance","Prototype / research","Replace later with licensed ASX feed"],
        ["NASDAQ equities","Twelve Data","Real-time where plan permits","US market feed"],
        ["NYSE equities","Twelve Data","Real-time where plan permits","US market feed"],
        ["FX","Twelve Data","Real-time where plan permits","Useful for AUD/USD macro signal"],
        ["Commodities","Twelve Data","Plan-dependent","Grow or higher coverage required"],
        ["ASX announcements","Not connected","—","Official/permitted feed required"],
        ["PIT fundamentals","Not connected","—","Production provider required"],
    ],columns=["Dataset","Provider","Mode","Next step"]),use_container_width=True,hide_index=True)
    st.warning("Licensing matters: individual Twelve Data plans are for personal/internal use and do not permit commercial redistribution. Twelve Data states ASX market data is restricted to internal use. Keep this build for your own research unless your data licences permit external display.")
    st.markdown("""**Streamlit secret required**

Create a secret named `TWELVE_DATA_API_KEY` in your Streamlit app settings. Do not commit the API key to GitHub.

V10.2 intentionally keeps the provider layer separate from the analytical engines, so a licensed ASX provider can later replace the ASX prototype feed without rewriting the application.""")
