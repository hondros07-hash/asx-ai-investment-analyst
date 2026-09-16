
# V7 Streamlit integration.
# Add universe_engine.py beside app.py, then paste/adapt this block into app.py.

from universe_engine import (
    download_universe, build_panel, cross_sectional_scores,
    strategy_backtest, strategy_summary, universe_latest
)

st.header("V7 — ASX Multi-Stock Factor Lab")

default_universe = """BHP,CBA,CSL,NAB,WBC,ANZ,WES,MQG,GMG,WOW,TLS,RIO,FMG,WDS,
XRO,REA,PME,ALL,CAR,COH,ZIP,MIN,LYC,PLS,S32,QBE,STO,ORG,TCL,JBH"""

universe_text = st.text_area(
    "Research universe (comma-separated ASX tickers)",
    default_universe.replace("\n",""),
    height=100
)
u_tickers=[x.strip() for x in universe_text.split(",") if x.strip()]
u_horizon=st.selectbox("Factor-test horizon",["1M","3M","6M"],index=1,key="v7_h")
u_cost=st.slider("Round-trip cost assumption (bps)",0,100,10,5,key="v7_cost")
u_top=st.slider("Top fraction selected",10,50,20,5,key="v7_top")/100

if st.button("Run V7 Universe Backtest",type="primary"):
    with st.spinner("Downloading universe and building point-in-time price factors..."):
        frames=download_universe(u_tickers,"10y")
        bm=yf.Ticker("^AXJO").history(period="10y",auto_adjust=True)
        panel=build_panel(frames,bm)
        scored=cross_sectional_scores(panel)
        bt=strategy_backtest(scored,u_horizon,"multi_factor_score",u_top,21,u_cost)
        summary=strategy_summary(bt)
        latest=universe_latest(scored)

    st.session_state["v7_panel"]=scored
    st.session_state["v7_bt"]=bt
    st.session_state["v7_summary"]=summary
    st.session_state["v7_latest"]=latest

if "v7_summary" in st.session_state:
    s=st.session_state["v7_summary"]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Test periods",s.get("periods",0))
    c2.metric("Mean period return",f"{s.get('mean_period_return',0)*100:.2f}%")
    c3.metric("Hit rate",f"{s.get('hit_rate',0)*100:.1f}%")
    c4.metric("Max drawdown",f"{s.get('max_drawdown',0)*100:.1f}%")

    st.subheader("Latest cross-sectional factor ranking")
    latest=st.session_state["v7_latest"].copy()
    for c in ["multi_factor_score","mom1","mom3","mom6","mom12","vol60","drawdown","rel3"]:
        if c in latest:
            latest[c]=latest[c].map(lambda x:f"{x*100:.1f}%" if pd.notna(x) else "N/A")
    st.dataframe(latest,use_container_width=True,hide_index=True)

    st.subheader("Strategy history")
    bt=st.session_state["v7_bt"]
    st.dataframe(bt.tail(100),use_container_width=True,hide_index=True)

st.warning(
    "V7 is a cross-sectional PRICE-FACTOR research prototype. "
    "The fields labelled quality/growth/value proxy are not yet true point-in-time fundamental factors. "
    "Do not interpret the ranking as a buy list. V8 should replace these proxies with point-in-time "
    "fundamentals, valuation, sector-neutral factors and a survivorship-bias-controlled ASX universe."
)
