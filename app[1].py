
import os, math, json
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="ASX AI Investment Analyst", page_icon="📈", layout="wide")

def sf(v):
    try:
        x=float(v)
        return None if math.isnan(x) or math.isinf(x) else x
    except: return None
def money(v):
    v=sf(v)
    if v is None:return "N/A"
    if abs(v)>=1e9:return f"${v/1e9:,.2f}B"
    if abs(v)>=1e6:return f"${v/1e6:,.2f}M"
    return f"${v:,.2f}"
def pct(v):
    v=sf(v); return "N/A" if v is None else f"{v*100:.1f}%"
def num(v,d=2):
    v=sf(v); return "N/A" if v is None else f"{v:,.{d}f}"
def symbol(raw):
    x=raw.strip().upper()
    return x if "." in x else x+".AX"
def secret(name):
    try:
        return st.secrets[name]
    except:
        return os.getenv(name)
def row(df,names,i=0):
    if df is None or df.empty or len(df.columns)<=i:return None
    for n in names:
        if n in df.index:return sf(df.loc[n,df.columns[i]])
    return None
def growth(a,b):
    a,b=sf(a),sf(b)
    return None if a is None or b in (None,0) else (a-b)/abs(b)

@st.cache_data(ttl=300)
def market_data(sym):
    t=yf.Ticker(sym)
    try: info=t.get_info() or {}
    except: info={}
    try: hist=t.history(period="5y",interval="1d",auto_adjust=False)
    except: hist=pd.DataFrame()
    def stmt(name):
        try:
            x=getattr(t,name); return x if x is not None else pd.DataFrame()
        except:return pd.DataFrame()
    try: news=t.get_news(count=20,tab="all") or []
    except: news=[]
    try: targets=t.analyst_price_targets
    except: targets=None
    try: estimates=t.get_earnings_estimate()
    except: estimates=pd.DataFrame()
    try: revisions=t.get_eps_revisions()
    except: revisions=pd.DataFrame()
    return dict(info=info,hist=hist,inc=stmt("income_stmt"),qinc=stmt("quarterly_income_stmt"),
                bal=stmt("balance_sheet"),qbal=stmt("quarterly_balance_sheet"),
                cf=stmt("cashflow"),qcf=stmt("quarterly_cashflow"),news=news,
                targets=targets,estimates=estimates,revisions=revisions)

def fundamental(d):
    i,b,c,info=d["inc"],d["bal"],d["cf"],d["info"]
    rev=row(i,["Total Revenue","Operating Revenue"])
    prev=row(i,["Total Revenue","Operating Revenue"],1)
    ni=row(i,["Net Income","Net Income Common Stockholders"])
    ocf=row(c,["Operating Cash Flow","Total Cash From Operating Activities"])
    capex=row(c,["Capital Expenditure","Capital Expenditures"])
    cash=row(b,["Cash Cash Equivalents And Short Term Investments","Cash And Cash Equivalents","Cash"])
    debt=row(b,["Total Debt","Long Term Debt And Capital Lease Obligation"])
    fcf=(ocf+capex) if ocf is not None and capex is not None else sf(info.get("freeCashflow"))
    return {
      "revenue":rev,"revenue_growth":growth(rev,prev),"net_income":ni,"ocf":ocf,"fcf":fcf,
      "cash":cash,"debt":debt,"net_debt":debt-cash if debt is not None and cash is not None else None,
      "market_cap":sf(info.get("marketCap")),"pe":sf(info.get("trailingPE")),
      "forward_pe":sf(info.get("forwardPE")),"ps":sf(info.get("priceToSalesTrailing12Months")),
      "pb":sf(info.get("priceToBook")),"ev_ebitda":sf(info.get("enterpriseToEbitda")),
      "gross_margin":sf(info.get("grossMargins")),"op_margin":sf(info.get("operatingMargins")),
      "profit_margin":sf(info.get("profitMargins")),"roe":sf(info.get("returnOnEquity")),
      "roa":sf(info.get("returnOnAssets")),"beta":sf(info.get("beta")),
      "earnings_growth":sf(info.get("earningsGrowth")),"yf_rev_growth":sf(info.get("revenueGrowth")),
      "eps":sf(info.get("trailingEps")),"forward_eps":sf(info.get("forwardEps")),
      "debt_equity":sf(info.get("debtToEquity")),"current_ratio":sf(info.get("currentRatio"))
    }

def quant(hist):
    if hist.empty:return hist,{}
    x=hist.copy()
    x["ret"]=x.Close.pct_change()
    x["SMA20"]=x.Close.rolling(20).mean(); x["SMA50"]=x.Close.rolling(50).mean(); x["SMA200"]=x.Close.rolling(200).mean()
    delta=x.Close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    x["RSI"]=100-(100/(1+gain/loss.replace(0,np.nan)))
    e12=x.Close.ewm(span=12,adjust=False).mean(); e26=x.Close.ewm(span=26,adjust=False).mean()
    x["MACD"]=e12-e26; x["MACDSignal"]=x.MACD.ewm(span=9,adjust=False).mean()
    sd=x.Close.rolling(20).std(); x["BBU"]=x.SMA20+2*sd; x["BBL"]=x.SMA20-2*sd
    tr=pd.concat([x.High-x.Low,(x.High-x.Close.shift()).abs(),(x.Low-x.Close.shift()).abs()],axis=1).max(axis=1)
    x["ATR"]=tr.rolling(14).mean(); x["vol20"]=x.ret.rolling(20).std()*np.sqrt(252)
    x["volavg"]=x.Volume.rolling(20).mean(); x["drawdown"]=x.Close/x.Close.cummax()-1
    r=x.ret.dropna()
    sharpe=(r.mean()/r.std())*np.sqrt(252) if len(r)>2 and r.std()!=0 else None
    downside=r[r<0].std(); sortino=(r.mean()/downside)*np.sqrt(252) if downside and not np.isnan(downside) else None
    def mom(days): return sf(x.Close.iloc[-1]/x.Close.iloc[-days]-1) if len(x)>=days else None
    q={"sharpe":sf(sharpe),"sortino":sf(sortino),"max_drawdown":sf(x.drawdown.min()),
       "ann_vol":sf(r.std()*np.sqrt(252)),"m1":mom(21),"m3":mom(63),"m6":mom(126),"m12":mom(252),
       "rsi":sf(x.RSI.iloc[-1]),"atr":sf(x.ATR.iloc[-1]),
       "volume_ratio":sf(x.Volume.iloc[-1]/x.volavg.iloc[-1]) if sf(x.volavg.iloc[-1]) not in (None,0) else None}
    return x,q

def sector_kpis(sec,ind):
    s=f"{sec} {ind}".lower()
    if "bank" in s:return ["NIM","CET1","bad debts","arrears","ROE","loan/deposit growth"]
    if any(z in s for z in ["mining","metals","gold","copper","iron"]):return ["production","commodity prices","unit costs/AISC","reserves","capex","FCF"]
    if any(z in s for z in ["software","technology"]):return ["ARR","recurring revenue","customers","churn","gross margin","FCF"]
    if any(z in s for z in ["real estate","reit"]):return ["FFO","occupancy","WALE","gearing","NAV/NTA"]
    if any(z in s for z in ["credit services","fintech","financial services"]):return ["TTV/payment volume","customers","transaction margin","credit losses","cash EBITDA/EBTDA","operating leverage","international growth","regulation"]
    return ["revenue growth","earnings growth","margins","FCF","ROE/ROIC","balance sheet","competitive position"]

def empirical_forecast(hist):
    """Transparent baseline, not ML: historical rolling return distribution."""
    if hist.empty:return pd.DataFrame()
    out=[]
    for label,days in [("1 month",21),("3 months",63),("6 months",126)]:
        future=hist.Close.shift(-days)/hist.Close-1
        vals=future.dropna()
        if len(vals)<100:
            out.append([label,None,None,None,None,None,len(vals)])
        else:
            out.append([label,(vals>0).mean(),vals.mean(),vals.quantile(.10),(vals>.05).mean(),(vals<-.10).mean(),len(vals)])
    return pd.DataFrame(out,columns=["Horizon","P(positive)","Historical mean","10th percentile","P(>+5%)","P(<-10%)","Observations"])

def openai_report(key,company,ticker,sector,thesis,evidence):
    from openai import OpenAI
    client=OpenAI(api_key=key)
    prompt=f"""Act as an evidence-driven ASX research committee for {company} ({ticker}), sector {sector}.
Investor thesis: {thesis}
Local market/fundamental/technical/quant evidence:
{evidence}

Search the CURRENT web. Prefer primary company/ASX sources, official economic sources and high-quality reporting. Resolve contradictions.
Analyse:
- current macro regime: RBA, Australian inflation/jobs/growth, AUD, yields, global risk, relevant commodities
- current micro/company news, announcements, competitors, regulation and earnings revisions
- fundamentals, valuation, technicals and quantitative factors
- upcoming catalysts when dates are verifiable
- bull case
- bear case / Kill My Thesis
- risk
- why the share price may be moving
- potential impact of each material event: direction, materiality, horizon, confidence, mechanism, counterargument
- what the market may be missing
- top 5 things to monitor

Do NOT invent precise return probabilities. Any 1/3/6 month probability must come from a separately validated quantitative model, not your intuition.
Finish with thesis status: SUPPORTED/PARTIALLY SUPPORTED/UNPROVEN/WEAKENING/BROKEN and a 0-10 research-evidence score, not a buy/sell recommendation."""
    r=client.responses.create(model="gpt-5.6-luna",tools=[{"type":"web_search"}],input=prompt)
    return r.output_text

st.sidebar.title("ASX AI Analyst")
raw=st.sidebar.text_input("Ticker","ZIP"); sym=symbol(raw)
thesis=st.sidebar.text_area("Investment thesis","Revenue and earnings continue growing, margins improve, cash generation strengthens and key operating KPIs remain healthy.",height=150)
run=st.sidebar.button("Run Full AI Research",type="primary",use_container_width=True)
st.sidebar.caption("Yahoo market data is cached 5 minutes. Exchange-grade real-time ASX data requires a licensed feed.")

st.title("ASX AI Investment Analyst")
st.caption("Fundamental • Valuation • Technical • Quant • Macro • Micro News • Forecast Baseline • Kill My Thesis • Investment Committee")

with st.spinner("Loading data..."): d=market_data(sym)
if d["hist"].empty and not d["info"]: st.error("No data found."); st.stop()
info=d["info"]; hist=d["hist"]; ticker=sym.replace(".AX","")
company=info.get("longName") or info.get("shortName") or ticker; sector=info.get("sector","N/A"); industry=info.get("industry","N/A")
price=sf(info.get("currentPrice")); price=price if price is not None else sf(hist.Close.iloc[-1])
f=fundamental(d); tx,q=quant(hist); kpis=sector_kpis(sector,industry); forecast=empirical_forecast(hist)

st.header(f"{ticker} — {company}")
cols=st.columns(6)
for c,(lab,val) in zip(cols,[("Price",money(price)),("Market Cap",money(f["market_cap"])),("Forward P/E",num(f["forward_pe"])),("RSI",num(q.get("rsi"))),("1M Momentum",pct(q.get("m1"))),("6M Momentum",pct(q.get("m6"))) ]): c.metric(lab,val)

tabs=st.tabs(["Committee","Market","Fundamental","Technical","Quant","1/3/6M Model","Macro & Micro","Valuation","Statements","AI Research"])

with tabs[0]:
    st.header(f"{ticker} — INVESTMENT COMMITTEE")
    st.info(thesis); st.write("**Sector KPI lens:** "+", ".join(kpis))
    st.warning("Specialist KPIs must be verified from company reports/ASX announcements when they are absent from market feeds.")
    st.dataframe(pd.DataFrame([
      ["Revenue growth",pct(f["revenue_growth"] if f["revenue_growth"] is not None else f["yf_rev_growth"])],
      ["Operating margin",pct(f["op_margin"])],["ROE",pct(f["roe"])],["FCF",money(f["fcf"])],
      ["Net debt",money(f["net_debt"])],["Max drawdown",pct(q.get("max_drawdown"))]
    ],columns=["Evidence","Value"]),use_container_width=True,hide_index=True)

with tabs[1]:
    st.header("Market")
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=tx.index,open=tx.Open,high=tx.High,low=tx.Low,close=tx.Close,name=ticker))
    fig.add_trace(go.Scatter(x=tx.index,y=tx.SMA50,name="SMA50")); fig.add_trace(go.Scatter(x=tx.index,y=tx.SMA200,name="SMA200"))
    fig.update_layout(height=600,xaxis_rangeslider_visible=False); st.plotly_chart(fig,use_container_width=True)

with tabs[2]:
    st.header("Fundamental")
    st.dataframe(pd.DataFrame([
      ["Revenue",money(f["revenue"])],["Revenue growth",pct(f["revenue_growth"] if f["revenue_growth"] is not None else f["yf_rev_growth"])],
      ["Net income",money(f["net_income"])],["Operating cash flow",money(f["ocf"])],["Free cash flow",money(f["fcf"])],
      ["Gross margin",pct(f["gross_margin"])],["Operating margin",pct(f["op_margin"])],["ROE",pct(f["roe"])],
      ["Cash",money(f["cash"])],["Debt",money(f["debt"])]
    ],columns=["Metric","Value"]),use_container_width=True,hide_index=True)

with tabs[3]:
    st.header("Technical")
    last=tx.iloc[-1]
    st.dataframe(pd.DataFrame([
      ["SMA20",money(last.SMA20)],["SMA50",money(last.SMA50)],["SMA200",money(last.SMA200)],["RSI14",num(last.RSI)],
      ["MACD",num(last.MACD,4)],["MACD signal",num(last.MACDSignal,4)],["ATR",money(last.ATR)],["Volume/20D average",num(q.get("volume_ratio"))]
    ],columns=["Indicator","Value"]),use_container_width=True,hide_index=True)

with tabs[4]:
    st.header("Quant")
    st.dataframe(pd.DataFrame([
      ["Annualised volatility",pct(q.get("ann_vol"))],["Sharpe",num(q.get("sharpe"))],["Sortino",num(q.get("sortino"))],
      ["Max drawdown",pct(q.get("max_drawdown"))],["1M momentum",pct(q.get("m1"))],["3M momentum",pct(q.get("m3"))],
      ["6M momentum",pct(q.get("m6"))],["12M momentum",pct(q.get("m12"))],["Beta",num(f.get("beta"))]
    ],columns=["Metric","Value"]),use_container_width=True,hide_index=True)

with tabs[5]:
    st.header("1 / 3 / 6 Month Return Model")
    st.warning("This is a transparent historical baseline, NOT yet the trained/calibrated prediction engine. It uses the stock's historical forward-return distribution and does not claim predictive accuracy.")
    if not forecast.empty:
        view=forecast.copy()
        for c in ["P(positive)","Historical mean","10th percentile","P(>+5%)","P(<-10%)"]: view[c]=view[c].map(pct)
        st.dataframe(view,use_container_width=True,hide_index=True)
    st.subheader("Production model roadmap")
    st.write("Point-in-time factor database → walk-forward train/validation/test → separate 1M/3M/6M models → probability calibration → benchmark-relative testing → model registry → prediction ledger.")

with tabs[6]:
    st.header("Macro & Micro News")
    st.info("The AI Research tab performs current web research across macro and company-specific developments.")
    for item in d["news"][:12]:
        c=item.get("content",item); st.write("**"+(c.get("title") or item.get("title") or "Untitled")+"**")
        if c.get("summary"): st.caption(c["summary"])

with tabs[7]:
    st.header("Valuation")
    st.dataframe(pd.DataFrame([["Trailing P/E",num(f["pe"])],["Forward P/E",num(f["forward_pe"])],["P/S",num(f["ps"])],["P/B",num(f["pb"])],["EV/EBITDA",num(f["ev_ebitda"])]],columns=["Metric","Value"]),use_container_width=True,hide_index=True)

with tabs[8]:
    st.header("Statements")
    ch=st.selectbox("Statement",["Annual income","Quarterly income","Annual balance","Quarterly balance","Annual cash flow","Quarterly cash flow"])
    mp={"Annual income":d["inc"],"Quarterly income":d["qinc"],"Annual balance":d["bal"],"Quarterly balance":d["qbal"],"Annual cash flow":d["cf"],"Quarterly cash flow":d["qcf"]}
    st.dataframe(mp[ch],use_container_width=True)

with tabs[9]:
    st.header("AI Research Committee")
    key=secret("OPENAI_API_KEY")
    if not key: st.warning("Add OPENAI_API_KEY to Streamlit Secrets. Never commit it to GitHub.")
    elif run:
        evidence=json.dumps({"price":price,"fundamental":f,"quant":q,"sector_kpis":kpis,"historical_baseline":forecast.to_dict("records")},default=str)
        with st.spinner("Searching current macro, micro and company evidence..."):
            try: st.markdown(openai_report(key,company,ticker,sector,thesis,evidence))
            except Exception as ex: st.error(str(ex))
    else: st.info("Click Run Full AI Research in the sidebar.")

st.markdown("---")
with st.expander("Important limitations"):
    st.write("Yahoo/yfinance is a research data source, not an exchange-certified real-time ASX feed. The 1/3/6 month panel is deliberately labelled as a historical baseline until a point-in-time, out-of-sample prediction system is trained and calibrated. AI web research may miss inaccessible/paywalled material. Verify material facts against primary company and official ASX sources. This is a research tool, not personal financial advice.")
