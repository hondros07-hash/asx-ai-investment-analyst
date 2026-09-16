
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from valuation_lab import scenarios, margin_of_safety
from reverse_dcf import implied_growth, expectations_gap
from expectations_engine import earnings_surprise_table, surprise_score
from confidence_engine import research_confidence, disagreement_confidence, data_health
from evidence_engine import evidence_for, thesis_rules, add_thesis_rule
from watchlist_engine import add as watch_add, remove as watch_remove, get as watch_get
from portfolio_engine import portfolio_analytics, concentration
from sector_models import SECTOR_KPIS
from model_monitor import registry
from breadth_engine import market_breadth

st.set_page_config(page_title="ASX AI Investment Analyst",layout="wide")
st.title("ASX AI Investment Analyst — Unified Build")
st.caption("V6–V10 research engines + expectations, reverse DCF, confidence, watchlist and production-readiness layers.")

page=st.sidebar.radio("Research workspace",[
 "Company Dashboard","Valuation & Expectations","Evidence & Thesis",
 "Portfolio","Market Breadth","Model Lab","Watchlist","Data & Production"
])
ticker=st.sidebar.text_input("ASX ticker","ZIP.AX").upper().strip()

@st.cache_data(ttl=900)
def history(t,period="5y"):
    return yf.Ticker(t).history(period=period,auto_adjust=True)

if page=="Company Dashboard":
    st.header(ticker)
    h=history(ticker)
    if h.empty:
        st.error("No market data returned.")
    else:
        close=h["Close"]
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Price",f"${close.iloc[-1]:.3f}")
        c2.metric("1M",f"{(close.iloc[-1]/close.iloc[-22]-1)*100:.1f}%" if len(close)>22 else "n/a")
        c3.metric("3M",f"{(close.iloc[-1]/close.iloc[-64]-1)*100:.1f}%" if len(close)>64 else "n/a")
        dd=(close/close.cummax()-1).min()
        c4.metric("5Y max drawdown",f"{dd*100:.1f}%")
        st.line_chart(close)
        st.subheader("Sector KPI frameworks")
        st.json(SECTOR_KPIS)

elif page=="Valuation & Expectations":
    st.header("Valuation laboratory")
    price=st.number_input("Current price",value=2.0,step=.01)
    fcf=st.number_input("Starting annual FCF",value=100_000_000.0,step=1_000_000.0)
    shares=st.number_input("Shares outstanding",value=1_000_000_000.0,step=1_000_000.0)
    net_debt=st.number_input("Net debt",value=0.0,step=1_000_000.0)
    wacc=st.number_input("Reverse-DCF WACC",value=.10,step=.005,format="%.3f")
    tg=st.number_input("Terminal growth",value=.03,step=.005,format="%.3f")
    assumptions={
      "Bear":{"growth":.04,"wacc":.12,"terminal_growth":.02},
      "Base":{"growth":.10,"wacc":.10,"terminal_growth":.03},
      "Bull":{"growth":.16,"wacc":.09,"terminal_growth":.035}}
    vals=scenarios(fcf,shares,net_debt,assumptions)
    vals["margin_of_safety"]=vals.value_per_share.map(lambda v:margin_of_safety(price,v))
    st.dataframe(vals,use_container_width=True,hide_index=True)
    ig=implied_growth(price,fcf,shares,net_debt,wacc,tg)
    st.metric("5Y FCF growth implied by price", "n/a" if pd.isna(ig) else f"{ig*100:.1f}%")
    st.subheader("Earnings surprise")
    st.caption("Enter consensus and actual values. This is descriptive, not a return forecast.")
    cons=st.number_input("Consensus metric",value=100.0)
    actual=st.number_input("Actual metric",value=105.0)
    sdf=earnings_surprise_table([{"metric":"Selected metric","consensus":cons,"actual":actual}])
    st.dataframe(sdf,use_container_width=True,hide_index=True)
    st.metric("Surprise score (-10 to +10)",f"{surprise_score(sdf):.1f}")

elif page=="Evidence & Thesis":
    st.header("Evidence, provenance & Kill My Thesis")
    ev=evidence_for(ticker)
    st.dataframe(ev,use_container_width=True,hide_index=True)
    st.subheader("Thesis-break rules")
    st.dataframe(thesis_rules(ticker),use_container_width=True,hide_index=True)
    with st.form("rule"):
        metric=st.text_input("Metric")
        op=st.selectbox("Trigger",["<","<=",">",">="])
        threshold=st.number_input("Threshold",value=0.0)
        reason=st.text_input("Why it matters")
        if st.form_submit_button("Add rule"):
            add_thesis_rule(ticker,metric,op,threshold,"",reason)
            st.success("Rule saved.")

elif page=="Portfolio":
    st.header("Portfolio intelligence")
    raw=st.text_area("TICKER,WEIGHT", "ZIP.AX,0.20\nBHP.AX,0.20\nCBA.AX,0.20\nCSL.AX,0.20\nWES.AX,0.20")
    if st.button("Run portfolio analytics"):
        weights={}
        for line in raw.splitlines():
            try:
                t,w=line.split(",");weights[t.strip().upper()]=float(w)
            except:pass
        px={}
        for t in weights:
            h=history(t)
            if not h.empty:px[t]=h.Close
        frame=pd.DataFrame(px)
        if not frame.empty:
            a=portfolio_analytics(frame,weights)
            a1,a2,a3,a4=st.columns(4)
            a1.metric("Annualised return",f"{a['annualised_return']*100:.1f}%")
            a2.metric("Volatility",f"{a['annualised_volatility']*100:.1f}%")
            a3.metric("Max drawdown",f"{a['max_drawdown']*100:.1f}%")
            a4.metric("HHI",f"{concentration(weights):.3f}")
            st.dataframe(a["correlation"],use_container_width=True)

elif page=="Market Breadth":
    st.header("ASX breadth research")
    universe=st.text_input("Universe", "BHP.AX,CBA.AX,CSL.AX,NAB.AX,WBC.AX,ANZ.AX,WES.AX,MQG.AX,GMG.AX,WOW.AX,ZIP.AX")
    if st.button("Calculate breadth"):
        px={}
        for t in [x.strip().upper() for x in universe.split(",") if x.strip()]:
            h=history(t,"2y")
            if not h.empty:px[t]=h.Close
        b=market_breadth(pd.DataFrame(px))
        st.line_chart(b)
        st.dataframe(b.tail(20),use_container_width=True)

elif page=="Model Lab":
    st.header("Model governance")
    st.dataframe(registry(),use_container_width=True,hide_index=True)
    st.info("V6–V9 backtest, factor, ML ensemble and point-in-time modules remain in this package. Their integration files are retained for research/testing.")

elif page=="Watchlist":
    st.header("Watchlist")
    thesis=st.text_input("Thesis note")
    c1,c2=st.columns(2)
    if c1.button("Add/update"):
        watch_add(ticker,thesis);st.success("Saved.")
    if c2.button("Remove"):
        watch_remove(ticker);st.success("Removed.")
    st.dataframe(watch_get(),use_container_width=True,hide_index=True)

elif page=="Data & Production":
    st.header("Data confidence & production readiness")
    st.markdown("""
### Architecture now included
- price/technical/quant research
- historical forward-return validation
- multi-stock factor testing
- competing ML models and ensemble
- point-in-time fundamental schema
- macro/commodity adapter framework
- document/announcement intelligence schema
- evidence provenance
- DCF + reverse DCF
- expectations/surprise engine
- market regime/event-transmission framework
- Kill My Thesis
- portfolio risk
- watchlist
- model registry/drift
- sector KPI definitions
- peer-selection helper
- market breadth
- liquidity/transaction-cost helper
- provider abstraction

### External infrastructure still required for institutional-grade operation
- licensed exchange-grade ASX real-time/order-book feed
- official automated ASX announcements/documents feed
- survivorship-bias-free universe including delisted stocks
- historical point-in-time financials and analyst estimates
- historical sector membership
- robust corporate-action database
- short-interest/director-transaction feeds
- persistent Postgres/cloud database
- authentication/secrets management
- scheduled alert delivery
- production caching/retries/observability

The application deliberately does not fabricate these datasets.
""")
