import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from valuation_lab import scenarios, margin_of_safety
from reverse_dcf import implied_growth
from evidence_engine import evidence_for, thesis_rules, add_thesis_rule
from watchlist_engine import add as watch_add, remove as watch_remove, get as watch_get
from portfolio_engine import portfolio_analytics, concentration
from model_monitor import registry
from sector_models import SECTOR_KPIS

st.set_page_config(page_title="ASX AI Investment Analyst", page_icon="📈", layout="wide")

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

st.sidebar.title("ASX AI Analyst")
ticker=st.sidebar.text_input("ASX ticker","ZIP.AX").strip().upper()
if ticker and "." not in ticker: ticker += ".AX"
thesis=st.sidebar.text_area("Investment thesis","Revenue and earnings continue growing, margins improve, cash generation strengthens and key operating KPIs remain healthy.",height=125)
page=st.sidebar.radio("Research workspace",["Dashboard","Investment Committee","Fundamentals","Valuation","Technical","Quant","Forecasts","News & Events","Evidence & Thesis","Portfolio","Watchlist","Model Lab","Data & Production"])

h=history(ticker); meta=info(ticker)
if h.empty:
    st.error("No market data returned for this ticker."); st.stop()
close=h["Close"]; price=float(close.iloc[-1]); name=meta.get("longName") or ticker
rv=rsi(close); rv=float(rv.iloc[-1]) if len(rv) and pd.notna(rv.iloc[-1]) else np.nan

st.title("ASX AI Investment Analyst")
st.caption("V10.1 • Unified investor research workspace")

if page=="Dashboard":
    st.header(f"{ticker} — {name}")
    cols=st.columns(6)
    vals=[("Price",f"${price:.3f}"),("Market Cap",money(meta.get("marketCap"))),
          ("1M","—" if pd.isna(change(close,21)) else f"{change(close,21)*100:.1f}%"),
          ("3M","—" if pd.isna(change(close,63)) else f"{change(close,63)*100:.1f}%"),
          ("6M","—" if pd.isna(change(close,126)) else f"{change(close,126)*100:.1f}%"),
          ("RSI14","—" if pd.isna(rv) else f"{rv:.1f}")]
    for c,(lab,val) in zip(cols,vals): c.metric(lab,val)
    st.line_chart(close)
    st.subheader("Research status")
    a,b,c=st.columns(3)
    a.info("**Thesis status**\n\nMonitoring")
    b.info("**Data confidence**\n\nMarket data connected; specialist KPIs need verified company data.")
    ma=close.rolling(200).mean().iloc[-1] if len(close)>=200 else np.nan
    c.info("**Market structure**\n\n"+("Above 200D MA" if pd.notna(ma) and price>ma else "Below 200D MA"))
    st.subheader("Sector KPI monitor")
    if ticker.startswith("ZIP"):
        labels={"ttv":"TTV / Payment Volume","active_customers":"Active Customers","transaction_margin":"Transaction Margin","credit_losses":"Credit Losses","revenue_growth":"Revenue Growth","cash_ebitda":"Cash EBITDA","operating_margin":"Operating Margin","us_growth":"US Growth","international_growth":"International Growth","regulatory_risk":"Regulatory Risk"}
        rows=[[labels.get(x,x.replace("_"," ").title()),"Awaiting verified company data","Not connected"] for x in SECTOR_KPIS["BNPL/Fintech"]]
        st.dataframe(pd.DataFrame(rows,columns=["KPI","Latest","Status"]),use_container_width=True,hide_index=True)
    else: st.info("Sector KPI selection will use verified sector metadata when connected.")

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
    st.header("Data & Production")
    st.success("V10.1 investor interface is active.")
    st.markdown("""**Connected now:** prototype Yahoo/yfinance price/history and local research storage.

**Production integrations still required:** licensed ASX real-time data, official announcements, point-in-time fundamentals/estimates, delisted universe, corporate actions, macro/commodity feeds, short interest/director transactions, persistent cloud database, authentication and automated alerts.

Missing data is deliberately shown as missing rather than treated as negative evidence.""")
