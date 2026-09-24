
from valuation_lab import dcf, scenarios, margin_of_safety
from evidence_engine import evidence_for, save_evidence, add_thesis_rule, thesis_rules
from thesis_engine import thesis_score
from portfolio_engine import portfolio_analytics, concentration
from model_monitor import registry

st.header("V10 — Research Operating System")

v10_tabs=st.tabs([
 "Evidence","Valuation Lab","Thesis Monitor","Portfolio Risk",
 "Model Registry","Documents","Regime & Events","Production Readiness"
])

with v10_tabs[0]:
    st.subheader("Evidence & provenance")
    ticker_v10=st.text_input("Ticker",value="ZIP.AX",key="v10_ticker")
    ev=evidence_for(ticker_v10)
    st.dataframe(ev,use_container_width=True,hide_index=True)
    st.caption("Every research claim can carry source, publication date, reporting period, page, confidence and thesis impact.")

with v10_tabs[1]:
    st.subheader("Bear / Base / Bull DCF")
    fcf=st.number_input("Starting annual FCF",value=100000000.0,step=1000000.0)
    shares=st.number_input("Shares outstanding",value=1000000000.0,step=1000000.0)
    net_debt=st.number_input("Net debt (negative = net cash)",value=0.0,step=1000000.0)
    price=st.number_input("Current share price",value=2.0,step=.01)
    assumptions={
      "Bear":{"growth":.04,"wacc":.12,"terminal_growth":.02},
      "Base":{"growth":.10,"wacc":.10,"terminal_growth":.03},
      "Bull":{"growth":.16,"wacc":.09,"terminal_growth":.035}
    }
    vals=scenarios(fcf,shares,net_debt,assumptions)
    vals["margin_of_safety"]=vals["value_per_share"].map(lambda v:margin_of_safety(price,v))
    st.dataframe(vals,use_container_width=True,hide_index=True)

with v10_tabs[2]:
    st.subheader("Kill My Thesis")
    rules=thesis_rules(ticker_v10)
    st.dataframe(rules,use_container_width=True,hide_index=True)
    with st.form("add_rule"):
        metric=st.text_input("Metric e.g. credit_loss_rate")
        op=st.selectbox("Trigger when",["<","<=",">",">="])
        threshold=st.number_input("Threshold",value=0.0)
        desc=st.text_input("Why this would weaken/break the thesis")
        if st.form_submit_button("Add thesis-break rule"):
            add_thesis_rule(ticker_v10,metric,op,threshold,"",desc)
            st.success("Rule added.")

with v10_tabs[3]:
    st.subheader("Portfolio intelligence")
    st.caption("Paste holdings as TICKER,WEIGHT. Example: ZIP.AX,0.20")
    holdings=st.text_area("Holdings", "ZIP.AX,0.20\nBHP.AX,0.20\nCBA.AX,0.20\nCSL.AX,0.20\nWES.AX,0.20")
    if st.button("Analyse portfolio"):
        weights={}
        for line in holdings.splitlines():
            try:
                t,w=line.split(","); weights[t.strip().upper()]=float(w)
            except: pass
        data={}
        for t in weights:
            h=yf.Ticker(t).history(period="5y",auto_adjust=True)
            if not h.empty:data[t]=h["Close"]
        pf=pd.DataFrame(data)
        if not pf.empty:
            a=portfolio_analytics(pf,weights)
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Annualised return",f"{a['annualised_return']*100:.1f}%")
            c2.metric("Volatility",f"{a['annualised_volatility']*100:.1f}%")
            c3.metric("Max drawdown",f"{a['max_drawdown']*100:.1f}%")
            c4.metric("Concentration HHI",f"{concentration(weights):.3f}")
            st.dataframe(a["correlation"],use_container_width=True)

with v10_tabs[4]:
    st.subheader("Prediction/model governance")
    st.dataframe(registry(),use_container_width=True,hide_index=True)
    st.caption("V10 includes a model registry contract and drift-warning helper.")

with v10_tabs[5]:
    st.subheader("Announcement & annual-report intelligence")
    st.write("The package includes `document_intelligence.py` for structured extraction of metrics, guidance, management claims, risks, catalysts and thesis changes.")
    st.warning("Automated ASX document fetching still requires a permitted/official or licensed document provider. V10 does not scrape around access restrictions.")

with v10_tabs[6]:
    st.subheader("Market regime + event transmission")
    st.write("The package includes a regime classifier and a structured event → macro → sector → company → share-price transmission schema.")
    st.caption("Production macro scoring should be connected to point-in-time RBA, ABS, bond, FX, China and commodity feeds.")

with v10_tabs[7]:
    st.subheader("Production readiness")
    st.markdown("""
**Implemented architecture:** provider interfaces, provenance DB, point-in-time joins, model registry, portfolio risk, DCF scenarios, thesis rules, document schema.

**Still provider-dependent:** licensed real-time ASX quotes/order book, official announcement feed, survivorship-bias-free/delisted universe, point-in-time fundamentals and estimates, macro history, persistent cloud database, authentication and scheduled alert delivery.
""")
