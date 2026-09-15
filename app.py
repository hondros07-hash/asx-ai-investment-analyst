
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="ASX AI Investment Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {max-width: 1400px; padding-top: 2rem;}
.hero {padding: 1.2rem 1.4rem; border: 1px solid #ddd; border-radius: 14px; margin-bottom: 1rem;}
.small {color: #666; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>📈 ASX AI Investment Analyst</h1><p class="small">Enter any ASX ticker to research the company.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Research")
    ticker = st.text_input("ASX ticker", "ZIP").strip().upper()
    period = st.selectbox("Price history", ["6mo", "1y", "2y", "5y"], index=2)
    analyse = st.button("🔎 Analyse stock", type="primary", use_container_width=True)
    st.divider()
    st.caption("Prototype data layer: Yahoo Finance. Production version should use licensed market-data sources.")

if analyse or "last_ticker" not in st.session_state:
    st.session_state.last_ticker = ticker

ticker = st.session_state.last_ticker
symbol = ticker + ".AX"

@st.cache_data(ttl=900)
def load_data(symbol, period):
    t = yf.Ticker(symbol)
    info = t.info
    hist = t.history(period=period, auto_adjust=False)
    return info, hist

if not ticker:
    st.warning("Enter an ASX ticker.")
    st.stop()

try:
    info, hist = load_data(symbol, period)
except Exception as e:
    st.error(f"Data request failed for ASX:{ticker}. {e}")
    st.stop()

if hist.empty:
    st.error(f"No data was returned for ASX:{ticker}. Check the ticker.")
    st.stop()

price = float(hist["Close"].iloc[-1])
h52 = float(hist["High"].tail(252).max())
l52 = float(hist["Low"].tail(252).min())
sma50 = float(hist["Close"].rolling(50).mean().iloc[-1])
sma200 = float(hist["Close"].rolling(200).mean().iloc[-1]) if len(hist) >= 200 else np.nan

delta = hist["Close"].diff()
gain = delta.clip(lower=0).rolling(14).mean()
loss = (-delta.clip(upper=0)).rolling(14).mean()
rsi = float((100 - 100/(1 + gain/loss.replace(0, np.nan))).iloc[-1])

name = info.get("longName") or info.get("shortName") or ticker
sector = info.get("sector", "Unavailable")
industry = info.get("industry", "Unavailable")

st.subheader(f"{name}  ·  ASX:{ticker}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Price", f"${price:,.2f}")
m2.metric("52-week high", f"${h52:,.2f}")
m3.metric("52-week low", f"${l52:,.2f}")
m4.metric("RSI (14)", f"{rsi:.1f}" if np.isfinite(rsi) else "N/A")

tabs = st.tabs(["Overview", "Financials", "Valuation", "Technical", "AI Analysis", "Risk"])

with tabs[0]:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Price history")
        st.line_chart(hist["Close"], height=380)
    with c2:
        st.subheader("Company")
        st.write(f"**Sector:** {sector}")
        st.write(f"**Industry:** {industry}")
        st.write(f"**Market cap:** {info.get('marketCap', 'Unavailable'):,}" if isinstance(info.get('marketCap'), (int,float)) else f"**Market cap:** {info.get('marketCap','Unavailable')}")
        st.write(f"**Employees:** {info.get('fullTimeEmployees','Unavailable')}")
        st.write(f"**Website:** {info.get('website','Unavailable')}")

with tabs[1]:
    rows = [
        ("Revenue", info.get("totalRevenue")),
        ("Gross margin", info.get("grossMargins")),
        ("Operating margin", info.get("operatingMargins")),
        ("Profit margin", info.get("profitMargins")),
        ("ROE", info.get("returnOnEquity")),
        ("ROA", info.get("returnOnAssets")),
        ("Free cash flow", info.get("freeCashflow")),
        ("Operating cash flow", info.get("operatingCashflow")),
        ("Debt / equity", info.get("debtToEquity")),
    ]
    df = pd.DataFrame(rows, columns=["Metric","Value"])
    st.dataframe(df, use_container_width=True, hide_index=True)

with tabs[2]:
    rows = [
        ("Trailing P/E", info.get("trailingPE")),
        ("Forward P/E", info.get("forwardPE")),
        ("PEG", info.get("pegRatio")),
        ("Price / book", info.get("priceToBook")),
        ("Price / sales", info.get("priceToSalesTrailing12Months")),
        ("Enterprise value", info.get("enterpriseValue")),
        ("EV / EBITDA", info.get("enterpriseToEbitda")),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Metric","Value"]), use_container_width=True, hide_index=True)
    st.info("Valuation scenarios and sector-specific multiples are planned for the AI layer.")

with tabs[3]:
    a,b,c = st.columns(3)
    a.metric("50-day SMA", f"${sma50:,.2f}")
    b.metric("200-day SMA", f"${sma200:,.2f}" if np.isfinite(sma200) else "N/A")
    c.metric("Trend", "Above 200D" if np.isfinite(sma200) and price > sma200 else "Below 200D")
    st.line_chart(pd.DataFrame({"Price": hist["Close"], "50D SMA": hist["Close"].rolling(50).mean(), "200D SMA": hist["Close"].rolling(200).mean()}))

with tabs[4]:
    st.subheader("AI Investment Committee — framework")
    st.write("This is the next layer of the application. It is deliberately separated from raw market data so every AI conclusion can be traced back to evidence.")
    st.markdown("""
**Fundamental Analyst**
- revenue and earnings growth
- cash-flow quality
- margins and returns
- balance-sheet strength

**Valuation Analyst**
- sector-appropriate multiples
- DCF / earnings scenarios
- bear, base and bull cases
- margin of safety

**Bear Analyst — “Kill My Thesis”**
- searches for evidence that the investment thesis is wrong
- identifies deteriorating KPIs
- tests management guidance
- highlights structural risks

**Investment Committee**
- combines the evidence
- scores the stock 0–10
- identifies thesis-changing events
- produces a written conclusion
""")
    st.warning("AI conclusions are not yet connected in this prototype. The next production step is to connect a model plus ASX/company-document retrieval.")

with tabs[5]:
    st.subheader("Risk checklist")
    risks = [
        "Valuation risk",
        "Balance-sheet / liquidity risk",
        "Earnings deterioration",
        "Margin pressure",
        "Industry / competitive risk",
        "Regulatory risk",
        "Management / execution risk",
        "Macro / interest-rate risk",
    ]
    for r in risks:
        st.checkbox(r, key=r, disabled=True)
    st.info("The production AI layer will populate these automatically from financial statements, announcements and company reports.")

st.divider()
st.caption("Research tool only — not financial advice. Market-data availability and accuracy depend on the underlying data provider.")
