import streamlit as st
import pandas as pd
import numpy as np
import re
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

import sqlite3
import uuid
from datetime import datetime, timezone

import json

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


METRIC_HELP = {
    "Market": "The primary market classification detected for the selected security, such as ASX, NASDAQ or NYSE.",
    "Exchange": "The exchange reported for the selected security. This identifies the trading venue where its shares are listed.",
    "Currency": "The currency in which the selected security is quoted and traded.",
    "Default benchmark": "The broad market index used as the default reference for comparing this security's performance.",
    "Price": "The latest available price returned by the active market-data source. Data timing can vary by provider.",
    "Day high": "The highest price in the latest available trading session.",
    "Day low": "The lowest price in the latest available trading session.",
    "Volume": "The number of shares traded in the latest available session. Volume helps show the level of market participation.",
    "52W high": "The highest price observed over approximately the last 52 trading weeks.",
    "52W low": "The lowest price observed over approximately the last 52 trading weeks.",
    "RSI14": "14-period Relative Strength Index. It measures recent price momentum on a 0–100 scale. Above 70 is commonly considered overbought and below 30 oversold, but RSI should not be used by itself.",
    "1M": "Percentage price change over approximately one trading month (21 sessions).",
    "3M": "Percentage price change over approximately three trading months (63 sessions).",
    "6M": "Percentage price change over approximately six trading months (126 sessions).",
    "1Y": "Percentage price change over approximately one trading year (252 sessions).",
    "YTD": "Year-to-date price performance from the first available trading observation of the calendar year to the latest observation.",
    "Sector": "The broad business sector assigned to the company by the available classification data.",
    "Industry": "The more specific business industry assigned to the company by the available classification data.",
    "Market benchmark": "The market index used as a reference when comparing the company's performance.",
    "vs market": "The company's performance minus its benchmark performance over the same period, expressed in percentage points.",
    "Reverse-DCF implied 5Y FCF growth": "The approximate annual free-cash-flow growth rate required by the reverse DCF assumptions to reconcile the model with the current share price.",
    "Annualised volatility": "Historical variability of daily returns scaled to a 252-trading-day year. Higher values indicate larger historical price fluctuations.",
    "Max drawdown": "The largest historical peak-to-trough decline in the selected price history.",
    "Sharpe (0% RF)": "Annualised historical return divided by annualised volatility, using a 0% risk-free rate in this screen. It is a risk-adjusted performance measure, not a forecast.",
     "12M momentum": "Price performance over approximately the previous 252 trading sessions.",
    "Paper cash": "Simulated cash available in the V15 paper-trading account. It is not connected to a bank or broker.",
    "Paper shares held": "Number of simulated shares currently held for the selected ticker.",
    "Paper account value": "Simulated cash plus the latest estimated market value of all paper positions.",
}
def metric_box(target, label, value, delta=None, **kwargs):
    """Render a Streamlit metric card with contextual hover help."""
    help_text = METRIC_HELP.get(label)
    if help_text and "help" not in kwargs:
        kwargs["help"] = help_text
    return target.metric(label, value, delta=delta, **kwargs)


# ---------------- Technical Analysis Lab ----------------
TECH_INDICATOR_HELP = {
    "SMA 20":"20-session simple moving average. Tracks the short-term trend by averaging closing prices.",
    "SMA 50":"50-session simple moving average. Common intermediate-trend reference.",
    "SMA 200":"200-session simple moving average. Common long-term trend reference.",
    "EMA 20":"20-session exponential moving average. Similar to an SMA but gives more weight to recent prices.",
    "Bollinger Bands":"20-session moving average with bands two standard deviations away. Tracks price location and changing volatility.",
    "RSI":"14-period Relative Strength Index. Momentum oscillator from 0–100; 70/30 are commonly watched zones.",
    "MACD":"Difference between 12- and 26-period EMAs plus a 9-period signal line. Tracks trend and momentum changes.",
    "Stochastic":"Compares the close with the recent 14-period trading range. Shows where price sits within that range.",
    "ADX / DMI":"ADX estimates trend strength; +DI and -DI estimate positive versus negative directional pressure.",
    "ATR":"14-period Average True Range. Measures volatility in price units, not bullish or bearish direction.",
    "CCI":"20-period Commodity Channel Index. Measures how far price is from its recent statistical average.",
    "Williams %R":"14-period oscillator showing where the close sits within the recent high-low range.",
    "ROC":"12-period Rate of Change. Percentage change from the price 12 sessions earlier.",
    "Momentum":"Current close minus the close 10 sessions earlier.",
    "OBV":"On-Balance Volume adds volume on up sessions and subtracts it on down sessions to track participation.",
    "MFI":"Money Flow Index combines price and volume into a 0–100 momentum/flow oscillator.",
    "CMF":"Chaikin Money Flow estimates buying or selling pressure from close location and volume.",
    "VWAP 20":"Rolling 20-session volume-weighted average price. Compares price with the average level weighted by trading activity.",
    "Donchian Channels":"Highest high and lowest low over 20 sessions. Tracks range boundaries and breakouts.",
    "Keltner Channels":"20-period EMA surrounded by ATR-based bands. Tracks trend and volatility.",
    "Ichimoku Cloud":"Trend system combining conversion/base lines and projected support/resistance cloud.",
    "Parabolic SAR":"Trend-following stop-and-reversal points plotted above or below price.",
    "Volume":"Trading volume. Used to assess participation behind price moves."
}
TECH_OVERLAYS={"SMA 20","SMA 50","SMA 200","EMA 20","Bollinger Bands","VWAP 20",
               "Donchian Channels","Keltner Channels","Ichimoku Cloud","Parabolic SAR"}
TECH_PANELS={"RSI","MACD","Stochastic","ADX / DMI","ATR","CCI","Williams %R","ROC",
             "Momentum","OBV","MFI","CMF","Volume"}

def technical_indicators(df):
    x=df.copy()
    c=x["Close"].astype(float); h=x["High"].astype(float); l=x["Low"].astype(float); v=x["Volume"].astype(float)
    t=pd.DataFrame(index=x.index); t["Price"]=c; t["Volume"]=v
    for n in (20,50,200): t[f"SMA {n}"]=c.rolling(n).mean()
    t["EMA 20"]=c.ewm(span=20,adjust=False).mean()
    mid=c.rolling(20).mean(); sd=c.rolling(20).std()
    t["BB Upper"]=mid+2*sd; t["BB Middle"]=mid; t["BB Lower"]=mid-2*sd
    d=c.diff(); gain=d.clip(lower=0); loss=-d.clip(upper=0)
    ag=gain.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    al=loss.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    t["RSI"]=100-(100/(1+ag/al.replace(0,np.nan)))
    e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean()
    t["MACD"]=e12-e26; t["MACD Signal"]=t["MACD"].ewm(span=9,adjust=False).mean(); t["MACD Hist"]=t["MACD"]-t["MACD Signal"]
    lo14=l.rolling(14).min(); hi14=h.rolling(14).max()
    t["Stoch %K"]=100*(c-lo14)/(hi14-lo14).replace(0,np.nan); t["Stoch %D"]=t["Stoch %K"].rolling(3).mean()
    t["Williams %R"]=-100*(hi14-c)/(hi14-lo14).replace(0,np.nan)
    t["ROC"]=c.pct_change(12)*100; t["Momentum"]=c-c.shift(10)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    t["ATR"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    up=h.diff(); down=-l.diff()
    plusdm=up.where((up>down)&(up>0),0.0); minusdm=down.where((down>up)&(down>0),0.0)
    atr=t["ATR"].replace(0,np.nan)
    t["+DI"]=100*plusdm.ewm(alpha=1/14,adjust=False).mean()/atr
    t["-DI"]=100*minusdm.ewm(alpha=1/14,adjust=False).mean()/atr
    dx=100*(t["+DI"]-t["-DI"]).abs()/(t["+DI"]+t["-DI"]).replace(0,np.nan)
    t["ADX"]=dx.ewm(alpha=1/14,adjust=False).mean()
    tp=(h+l+c)/3; ma=tp.rolling(20).mean()
    md=tp.rolling(20).apply(lambda z: np.mean(np.abs(z-z.mean())),raw=True)
    t["CCI"]=(tp-ma)/(0.015*md.replace(0,np.nan))
    t["OBV"]=(np.sign(c.diff()).fillna(0)*v).cumsum()
    money=tp*v
    pos=money.where(tp.diff()>0,0).rolling(14).sum(); neg=money.where(tp.diff()<0,0).rolling(14).sum()
    t["MFI"]=100-(100/(1+pos/neg.replace(0,np.nan)))
    mfm=((c-l)-(h-c))/(h-l).replace(0,np.nan)
    t["CMF"]=(mfm*v).rolling(20).sum()/v.rolling(20).sum().replace(0,np.nan)
    t["VWAP 20"]=(tp*v).rolling(20).sum()/v.rolling(20).sum().replace(0,np.nan)
    t["Donchian Upper"]=h.rolling(20).max(); t["Donchian Lower"]=l.rolling(20).min()
    t["Keltner Upper"]=t["EMA 20"]+2*t["ATR"]; t["Keltner Lower"]=t["EMA 20"]-2*t["ATR"]
    conv=(h.rolling(9).max()+l.rolling(9).min())/2; base=(h.rolling(26).max()+l.rolling(26).min())/2
    t["Ichimoku Conversion"]=conv; t["Ichimoku Base"]=base
    t["Ichimoku Span A"]=((conv+base)/2).shift(26)
    t["Ichimoku Span B"]=((h.rolling(52).max()+l.rolling(52).min())/2).shift(26)
    sar=pd.Series(np.nan,index=x.index)
    if len(x):
        bull=True; af=.02; ep=h.iloc[0]; sar.iloc[0]=l.iloc[0]
        for i in range(1,len(x)):
            cur=sar.iloc[i-1]+af*(ep-sar.iloc[i-1])
            if bull:
                cur=min(cur,l.iloc[i-1],l.iloc[i-2] if i>1 else l.iloc[i-1])
                if l.iloc[i]<cur: bull=False; cur=ep; ep=l.iloc[i]; af=.02
                elif h.iloc[i]>ep: ep=h.iloc[i]; af=min(.2,af+.02)
            else:
                cur=max(cur,h.iloc[i-1],h.iloc[i-2] if i>1 else h.iloc[i-1])
                if h.iloc[i]>cur: bull=True; cur=ep; ep=h.iloc[i]; af=.02
                elif l.iloc[i]<ep: ep=l.iloc[i]; af=min(.2,af+.02)
            sar.iloc[i]=cur
    t["Parabolic SAR"]=sar
    return t

def technical_reading(name,t,px):
    z=t.iloc[-1]
    def q(k): return z.get(k,np.nan)
    if name.startswith("SMA") or name=="EMA 20":
        m=q(name); return f"Price is {abs(px/m-1)*100:.1f}% {'above' if px>=m else 'below'} {name}." if pd.notna(m) and m else "Not enough history yet."
    if name=="RSI":
        r=q("RSI"); state="above the commonly watched 70 zone" if r>=70 else "below the commonly watched 30 zone" if r<=30 else "between the 30 and 70 zones"
        return f"RSI is {r:.1f}, {state}."
    if name=="MACD":
        return f"MACD is {'above' if q('MACD')>q('MACD Signal') else 'below'} its signal line; histogram is {q('MACD Hist'):.3f}."
    if name=="Stochastic": return f"%K is {q('Stoch %K'):.1f} and %D is {q('Stoch %D'):.1f}; %K is {'above' if q('Stoch %K')>q('Stoch %D') else 'below'} %D."
    if name=="ADX / DMI": return f"ADX is {q('ADX'):.1f}; {'+DI is above -DI' if q('+DI')>q('-DI') else '-DI is above +DI'}. ADX measures strength rather than direction."
    if name=="ATR": return f"ATR is {q('ATR'):.3f}, equivalent to about {q('ATR')/px*100:.1f}% of the current price."
    if name=="CCI": return f"CCI is {q('CCI'):.1f}; +100 and -100 are commonly watched reference levels."
    if name=="Williams %R": return f"Williams %R is {q('Williams %R'):.1f}; -20 and -80 are commonly watched range-position levels."
    if name=="ROC": return f"12-session ROC is {q('ROC'):.2f}%."
    if name=="Momentum": return f"10-session momentum is {q('Momentum'):.3f} price units."
    if name=="OBV":
        d=t["OBV"].diff(10).iloc[-1]; return f"OBV has {'risen' if d>0 else 'fallen'} over the latest 10 sessions, showing {'positive' if d>0 else 'negative'} volume participation."
    if name=="MFI": return f"MFI is {q('MFI'):.1f} on its 0–100 scale."
    if name=="CMF": return f"CMF is {q('CMF'):.3f}; it is currently {'positive' if q('CMF')>0 else 'negative'}."
    if name=="VWAP 20":
        m=q("VWAP 20"); return f"Price is {abs(px/m-1)*100:.1f}% {'above' if px>=m else 'below'} the rolling 20-session VWAP."
    if name=="Bollinger Bands":
        u,lw=q("BB Upper"),q("BB Lower"); where="above the upper band" if px>u else "below the lower band" if px<lw else "inside the bands"
        return f"Price is {where}. Band width is {(u-lw)/px*100:.1f}% of price."
    if name=="Donchian Channels":
        u,lw=q("Donchian Upper"),q("Donchian Lower")
        return f"Price is {(px-lw)/(u-lw)*100:.0f}% of the way from the 20-session channel low to high." if pd.notna(u) and u>lw else "Channel unavailable."
    if name=="Keltner Channels":
        u,lw=q("Keltner Upper"),q("Keltner Lower"); return f"Price is {'above' if px>u else 'below' if px<lw else 'inside'} the Keltner channel."
    if name=="Ichimoku Cloud":
        a,b=q("Ichimoku Span A"),q("Ichimoku Span B")
        if pd.isna(a) or pd.isna(b): return "Not enough history for the projected cloud."
        return f"Price is {'above' if px>max(a,b) else 'below' if px<min(a,b) else 'inside'} the Ichimoku cloud."
    if name=="Parabolic SAR": return f"Parabolic SAR is {'below' if q('Parabolic SAR')<px else 'above'} price."
    if name=="Volume":
        av=t["Volume"].rolling(20).mean().iloc[-1]; return f"Latest volume is {q('Volume')/av:.2f}× its 20-session average." if av else "Volume comparison unavailable."
    return ""

def combined_technical_reading(selected,t,px):
    z=t.iloc[-1]; parts=[]
    trend_votes=[]
    for n in selected:
        if n.startswith("SMA") or n=="EMA 20" or n=="VWAP 20":
            if pd.notna(z.get(n,np.nan)): trend_votes.append(1 if px>z[n] else -1)
    if trend_votes:
        parts.append(f"Trend references are {'mostly positive' if sum(trend_votes)>0 else 'mostly negative' if sum(trend_votes)<0 else 'mixed'} ({sum(v>0 for v in trend_votes)} above-price vs {sum(v<0 for v in trend_votes)} below-price readings).")
    mom=[]
    if "RSI" in selected and pd.notna(z["RSI"]): mom.append(1 if z["RSI"]>50 else -1)
    if "MACD" in selected: mom.append(1 if z["MACD"]>z["MACD Signal"] else -1)
    if "Stochastic" in selected: mom.append(1 if z["Stoch %K"]>z["Stoch %D"] else -1)
    if "ROC" in selected and pd.notna(z["ROC"]): mom.append(1 if z["ROC"]>0 else -1)
    if mom: parts.append(f"Selected momentum readings are {'mostly positive' if sum(mom)>0 else 'mostly negative' if sum(mom)<0 else 'mixed'}.")
    if any(n in selected for n in {"OBV","MFI","CMF","Volume"}):
        parts.append("Use the selected volume/flow readings as confirmation: price and participation moving together generally provide more consistent evidence than price moving without participation.")
    if any(n in selected for n in {"ADX / DMI","ATR"}):
        parts.append("ADX and ATR add context rather than a direction call: ADX addresses trend strength and ATR addresses movement size/volatility.")
    parts.append("Do not count correlated indicators as independent confirmation. RSI, Stochastic, Williams %R and CCI overlap; moving averages and MACD also share price-trend information. A more balanced combination uses different families: trend + momentum + volume/flow + volatility/strength.")
    return " ".join(parts)


# ---------------- V15 Paper Trading + Order Management ----------------
PAPER_DB="paper_trading.db"

def paper_db():
    con=sqlite3.connect(PAPER_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS paper_orders(
        id TEXT PRIMARY KEY, created_at TEXT, ticker TEXT, side TEXT, order_type TEXT,
        quantity REAL, limit_price REAL, stop_price REAL, tif TEXT, status TEXT,
        reference_price REAL, fill_price REAL, estimated_value REAL, notes TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS paper_positions(
        ticker TEXT PRIMARY KEY, quantity REAL, avg_cost REAL, updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS paper_cash(
        id INTEGER PRIMARY KEY CHECK(id=1), balance REAL)""")
    con.execute("INSERT OR IGNORE INTO paper_cash(id,balance) VALUES(1,100000.0)")
    con.commit()
    return con

def paper_cash_balance():
    con=paper_db(); x=con.execute("SELECT balance FROM paper_cash WHERE id=1").fetchone(); con.close()
    return float(x[0] if x else 0)

def paper_orders_df():
    con=paper_db()
    df=pd.read_sql_query("SELECT * FROM paper_orders ORDER BY created_at DESC",con)
    con.close(); return df

def paper_positions_df():
    con=paper_db()
    df=pd.read_sql_query("SELECT * FROM paper_positions ORDER BY ticker",con)
    con.close(); return df

def estimate_order(side,qty,price):
    gross=max(float(qty),0)*max(float(price),0)
    # Simulator assumption only, deliberately not presented as broker pricing.
    sim_cost=max(3.0,gross*0.0005) if gross else 0.0
    return gross,sim_cost

def submit_paper_order(ticker,side,order_type,qty,reference_price,limit_price=None,stop_price=None,tif="DAY",notes=""):
    qty=float(qty); reference_price=float(reference_price)
    if qty<=0: return False,"Quantity must be greater than zero."
    if reference_price<=0: return False,"A valid reference price is required."
    if order_type=="Limit" and (not limit_price or float(limit_price)<=0): return False,"Enter a valid limit price."
    if order_type in {"Stop","Stop Limit"} and (not stop_price or float(stop_price)<=0): return False,"Enter a valid stop price."
    if order_type=="Stop Limit" and (not limit_price or float(limit_price)<=0): return False,"Enter a valid limit price."

    # V15 paper engine fills market orders immediately; conditional orders remain OPEN.
    fill = reference_price if order_type=="Market" else None
    status="FILLED" if fill else "OPEN"
    gross,_=estimate_order(side,qty,reference_price)
    oid=str(uuid.uuid4())[:8].upper()
    now=datetime.now(timezone.utc).isoformat()
    con=paper_db()
    try:
        if status=="FILLED":
            cash=float(con.execute("SELECT balance FROM paper_cash WHERE id=1").fetchone()[0])
            if side=="Buy":
                if gross>cash: return False,f"Insufficient paper cash. Required ${gross:,.2f}; available ${cash:,.2f}."
                con.execute("UPDATE paper_cash SET balance=? WHERE id=1",(cash-gross,))
                row=con.execute("SELECT quantity,avg_cost FROM paper_positions WHERE ticker=?",(ticker,)).fetchone()
                oq,oc=(row if row else (0.0,0.0))
                nq=oq+qty; navg=((oq*oc)+(qty*fill))/nq
                con.execute("""INSERT INTO paper_positions(ticker,quantity,avg_cost,updated_at) VALUES(?,?,?,?)
                               ON CONFLICT(ticker) DO UPDATE SET quantity=excluded.quantity,avg_cost=excluded.avg_cost,updated_at=excluded.updated_at""",
                            (ticker,nq,navg,now))
            else:
                row=con.execute("SELECT quantity,avg_cost FROM paper_positions WHERE ticker=?",(ticker,)).fetchone()
                oq,oc=(row if row else (0.0,0.0))
                if qty>oq: return False,f"Paper position only contains {oq:g} shares; short selling is disabled in V15."
                nq=oq-qty
                con.execute("UPDATE paper_cash SET balance=? WHERE id=1",(cash+qty*fill,))
                if nq<=0: con.execute("DELETE FROM paper_positions WHERE ticker=?",(ticker,))
                else: con.execute("UPDATE paper_positions SET quantity=?,updated_at=? WHERE ticker=?",(nq,now,ticker))
        con.execute("""INSERT INTO paper_orders VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (oid,now,ticker,side,order_type,qty,float(limit_price or 0),float(stop_price or 0),
                     tif,status,reference_price,float(fill or 0),gross,notes))
        con.commit()
        return True,f"Paper order {oid} {status.lower()}."
    finally:
        con.close()

def cancel_paper_order(order_id):
    con=paper_db()
    cur=con.execute("UPDATE paper_orders SET status='CANCELLED' WHERE id=? AND status='OPEN'",(order_id,))
    con.commit(); con.close()
    return cur.rowcount>0

def reset_paper_account():
    con=paper_db()
    con.execute("DELETE FROM paper_orders"); con.execute("DELETE FROM paper_positions")
    con.execute("UPDATE paper_cash SET balance=100000.0 WHERE id=1")
    con.commit(); con.close()

BROKER_ADAPTER_REQUIREMENTS=pd.DataFrame([
    {"Route":"Australia / ASX","Requirement":"CHESS/HIN-capable execution partner","Status":"Adapter interface only","Live execution":"Disabled"},
    {"Route":"Global","Requirement":"Broker API supporting international markets/FX","Status":"Adapter interface only","Live execution":"Disabled"},
    {"Route":"Market data","Requirement":"Licensed real-time/Level 2 feed for production","Status":"Existing prototype feeds","Live execution":"N/A"},
])


# ---------------- V16 Institutional Workstation ----------------
WORKSPACE_DB="workstation.db"

def ws_db():
    con=sqlite3.connect(WORKSPACE_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS thesis_rules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,metric TEXT,operator TEXT,
        threshold REAL,current_value REAL,status TEXT,source TEXT,updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS catalysts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,event_date TEXT,event TEXT,
        category TEXT,source TEXT,status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,metric TEXT,operator TEXT,
        threshold REAL,enabled INTEGER,notes TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS strategy_rules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,ticker TEXT,rule_json TEXT,created_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS user_layout(
        id INTEGER PRIMARY KEY CHECK(id=1),preset TEXT,default_period TEXT,default_benchmark TEXT,
        widgets TEXT)""")
    con.execute("""INSERT OR IGNORE INTO user_layout VALUES
        (1,'Investor','1y','Auto','Price,Thesis,Fundamentals,Technical,Valuation,Catalysts,Risks,Latest announcement,Portfolio')""")
    con.commit(); return con

def company_kpi_template(ticker,sector="",industry=""):
    name=(company_name(ticker) if 'company_name' in globals() else ticker)
    text=f"{name} {sector} {industry}".lower()
    if "zip" in text or "financial" in text or "credit" in text:
        return ["Transaction / TTV growth","Revenue growth","Revenue margin","Credit losses / bad debts",
                "Cash EBITDA / EBTDA","Operating margin","Active customers","Cash generation"]
    if any(x in text for x in ["bank","banks"]):
        return ["Net interest margin","CET1 ratio","Loan growth","Deposit growth","Bad debts","ROE","Cost-to-income"]
    if any(x in text for x in ["mining","miner","materials","gold","copper","lithium"]):
        return ["Production","Realised commodity price","AISC / unit cost","Cash flow","Capex","Reserves/resources","Net cash/debt"]
    if any(x in text for x in ["reit","real estate"]):
        return ["FFO/AFFO","Occupancy","WALE","NTA","Gearing","Distribution per security","Cap rate"]
    return ["Revenue growth","Earnings growth","Operating margin","Free cash flow","ROIC / ROE","Net debt","Guidance"]

def provenance_badge(kind):
    return {"Reported":"🟢 Company reported","Exchange":"🔵 Exchange / regulatory",
            "Market":"🟣 Market data","Calculated":"🟠 Model calculated",
            "AI":"⚪ AI interpretation","Unavailable":"⚫ Unavailable"}.get(kind,kind)

def market_structure(df):
    if df is None or df.empty: return {}
    c=df["Close"].astype(float); h=df["High"].astype(float); l=df["Low"].astype(float); v=df["Volume"].astype(float)
    last=float(c.iloc[-1]); hi=float(h.max()); lo=float(l.min())
    sma20=float(c.rolling(20).mean().iloc[-1]) if len(c)>=20 else np.nan
    sma50=float(c.rolling(50).mean().iloc[-1]) if len(c)>=50 else np.nan
    sma200=float(c.rolling(200).mean().iloc[-1]) if len(c)>=200 else np.nan
    vol20=float(v.rolling(20).mean().iloc[-1]) if len(v)>=20 else np.nan
    recent_hi=float(h.tail(min(20,len(h))).max()); recent_lo=float(l.tail(min(20,len(l))).min())
    return {"Price":last,"Period high":hi,"Period low":lo,"SMA20":sma20,"SMA50":sma50,"SMA200":sma200,
            "20D resistance":recent_hi,"20D support":recent_lo,"Volume vs 20D":float(v.iloc[-1]/vol20) if vol20 else np.nan}

def confluence_snapshot(df):
    if df is None or df.empty: return pd.DataFrame()
    ti=technical_indicators(df); z=ti.iloc[-1]; px=float(df["Close"].iloc[-1]); rows=[]
    def add(family,indicator,reading,state):
        rows.append({"Family":family,"Indicator":indicator,"Reading":reading,"State":state})
    if pd.notna(z.get("SMA 50",np.nan)): add("Trend","Price vs SMA50",f"{(px/z['SMA 50']-1)*100:+.1f}%","Positive" if px>z["SMA 50"] else "Negative")
    if pd.notna(z.get("SMA 200",np.nan)): add("Trend","Price vs SMA200",f"{(px/z['SMA 200']-1)*100:+.1f}%","Positive" if px>z["SMA 200"] else "Negative")
    if pd.notna(z.get("RSI",np.nan)): add("Momentum","RSI14",f"{z['RSI']:.1f}","Positive" if z["RSI"]>50 else "Negative")
    if pd.notna(z.get("MACD",np.nan)): add("Momentum","MACD",f"{z['MACD Hist']:.3f} hist","Positive" if z["MACD"]>z["MACD Signal"] else "Negative")
    if pd.notna(z.get("ADX",np.nan)): add("Strength","ADX",f"{z['ADX']:.1f}","Strong trend" if z["ADX"]>=25 else "Weak / range")
    if len(ti)>=11:
        d=ti["OBV"].diff(10).iloc[-1]
        add("Participation","OBV 10D","Rising" if d>0 else "Falling","Positive" if d>0 else "Negative")
    if pd.notna(z.get("ATR",np.nan)): add("Volatility","ATR",f"{z['ATR']/px*100:.1f}% of price","Context")
    return pd.DataFrame(rows)

def strategy_eval(df,rules):
    if df is None or df.empty: return []
    ti=technical_indicators(df); z=ti.iloc[-1]; px=float(df["Close"].iloc[-1]); results=[]
    values={"Price":px,"SMA20":z.get("SMA 20"),"SMA50":z.get("SMA 50"),"SMA200":z.get("SMA 200"),
            "RSI":z.get("RSI"),"ADX":z.get("ADX"),"ROC":z.get("ROC"),"VolumeRatio":float(df["Volume"].iloc[-1]/df["Volume"].rolling(20).mean().iloc[-1])}
    for r in rules:
        lhs=values.get(r["metric"],np.nan); rhs=values.get(r["compare_metric"],r.get("value",0))
        if isinstance(rhs,str): rhs=values.get(rhs,np.nan)
        op=r["operator"]
        passed=False if pd.isna(lhs) or pd.isna(rhs) else {"gt":lhs>rhs,"lt":lhs<rhs,"gte":lhs>=rhs,"lte":lhs<=rhs}.get(op,False)
        results.append({**r,"lhs":lhs,"rhs":rhs,"passed":bool(passed)})
    return results

def portfolio_risk_snapshot():
    pos=paper_positions_df()
    if pos.empty: return pd.DataFrame(),{}
    rows=[]
    for _,r in pos.iterrows():
        h=history(r["ticker"],"1y")
        if h.empty: continue
        ret=h["Close"].pct_change().dropna()
        last=float(h["Close"].iloc[-1]); mv=float(r["quantity"])*last
        rows.append({"Ticker":r["ticker"],"Market value":mv,"Volatility":float(ret.std()*np.sqrt(252)) if len(ret)>20 else np.nan,
                     "Max drawdown":float((h["Close"]/h["Close"].cummax()-1).min())})
    d=pd.DataFrame(rows)
    if d.empty:return d,{}
    total=d["Market value"].sum()
    d["Weight"]=d["Market value"]/total
    stats={"Invested":total,"Largest position":float(d["Weight"].max()),"Weighted volatility":float((d["Weight"]*d["Volatility"]).sum())}
    return d,stats


# ---------------- V17 Decision Brief + Thesis Monitor ----------------
def v17_db_upgrade():
    con=ws_db()
    con.execute("""CREATE TABLE IF NOT EXISTS portfolio_holdings(
        ticker TEXT PRIMARY KEY, quantity REAL, avg_cost REAL, source TEXT, updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS thesis_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,snapshot_at TEXT,metric TEXT,
        current_value REAL,status TEXT,source TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS review_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,reviewed_at TEXT,amount REAL,
        price REAL,shares_before REAL,avg_cost_before REAL,shares_after REAL,
        avg_cost_after REAL,notes TEXT)""")
    con.commit(); con.close()

def holding_for(ticker):
    v17_db_upgrade(); con=ws_db()
    row=con.execute("SELECT quantity,avg_cost,source FROM portfolio_holdings WHERE ticker=?",(ticker,)).fetchone()
    con.close()
    return {"quantity":float(row[0]),"avg_cost":float(row[1]),"source":row[2]} if row else {"quantity":0.0,"avg_cost":0.0,"source":"Manual"}

def save_holding(ticker,quantity,avg_cost,source="Manual"):
    v17_db_upgrade(); con=ws_db()
    con.execute("""INSERT INTO portfolio_holdings(ticker,quantity,avg_cost,source,updated_at) VALUES(?,?,?,?,?)
                   ON CONFLICT(ticker) DO UPDATE SET quantity=excluded.quantity,avg_cost=excluded.avg_cost,
                   source=excluded.source,updated_at=excluded.updated_at""",
                (ticker,float(quantity),float(avg_cost),source,datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

def thesis_table(ticker):
    con=ws_db()
    d=pd.read_sql_query("""SELECT id,metric,operator,threshold,current_value,status,source,updated_at
                           FROM thesis_rules WHERE ticker=? ORDER BY id""",(ticker,),con)
    con.close(); return d

def snapshot_thesis(ticker):
    d=thesis_table(ticker)
    if d.empty:return 0
    con=ws_db(); now=datetime.now(timezone.utc).isoformat()
    for _,r in d.iterrows():
        con.execute("INSERT INTO thesis_snapshots(ticker,snapshot_at,metric,current_value,status,source) VALUES(?,?,?,?,?,?)",
                    (ticker,now,r["metric"],float(r["current_value"]),str(r["status"]),str(r["source"] or "")))
    con.commit(); con.close(); return len(d)

def thesis_changes(ticker):
    con=ws_db()
    d=pd.read_sql_query("""SELECT snapshot_at,metric,current_value,status,source
                           FROM thesis_snapshots WHERE ticker=? ORDER BY snapshot_at DESC,id DESC""",(ticker,),con)
    con.close()
    cur=thesis_table(ticker)
    if cur.empty:return pd.DataFrame()
    if d.empty:
        out=cur[["metric","current_value","status","source"]].copy()
        out["Previous"]=np.nan; out["Change"]="No prior snapshot"; return out
    times=d["snapshot_at"].drop_duplicates().tolist()
    prev=d[d["snapshot_at"]==times[0]].drop_duplicates("metric").set_index("metric")
    rows=[]
    for _,r in cur.iterrows():
        p=prev.loc[r["metric"]] if r["metric"] in prev.index else None
        pv=float(p["current_value"]) if p is not None else np.nan
        cv=float(r["current_value"])
        delta=cv-pv if pd.notna(pv) else np.nan
        change="New" if pd.isna(pv) else ("↑ Increased" if delta>0 else "↓ Decreased" if delta<0 else "→ Unchanged")
        rows.append({"Metric":r["metric"],"Previous":pv,"Latest":cv,"Change":change,
                     "Status":r["status"],"Source":r["source"]})
    return pd.DataFrame(rows)

def decision_brief_data(ticker,amount):
    h=history(ticker,"1y")
    if h.empty:return None
    price=float(h["Close"].iloc[-1]); hold=holding_for(ticker)
    qty0=hold["quantity"]; avg0=hold["avg_cost"]; add_qty=int(float(amount)//price) if price>0 else 0
    spend=add_qty*price; qty1=qty0+add_qty
    avg1=((qty0*avg0)+spend)/qty1 if qty1>0 else 0
    mv0=qty0*price; mv1=qty1*price
    cash=paper_cash_balance()
    # Portfolio weight uses paper portfolio plus manually entered selected holding; avoid pretending it is full wealth.
    pp=paper_positions_df()
    other=0.0
    if not pp.empty:
        for _,r in pp.iterrows():
            if r["ticker"]==ticker: continue
            hh=history(r["ticker"],"5d")
            last=float(hh["Close"].iloc[-1]) if not hh.empty else float(r["avg_cost"])
            other+=float(r["quantity"])*last
    denom0=mv0+other+cash
    denom1=mv1+other+max(cash-spend,0)
    w0=mv0/denom0 if denom0 else np.nan; w1=mv1/denom1 if denom1 else np.nan
    ms=market_structure(h); conf=confluence_snapshot(h)
    return {"price":price,"qty0":qty0,"avg0":avg0,"mv0":mv0,"add_qty":add_qty,"spend":spend,
            "qty1":qty1,"avg1":avg1,"mv1":mv1,"w0":w0,"w1":w1,"market":ms,"confluence":conf}

def attention_items(ticker):
    items=[]
    t=thesis_table(ticker)
    if not t.empty:
        for _,r in t.iterrows():
            if str(r["status"])!="Met": items.append(("⚠",f"{r['metric']}: {r['status']}"))
    h=history(ticker,"1y")
    if not h.empty:
        ms=market_structure(h)
        if pd.notna(ms.get("SMA200",np.nan)) and ms["Price"]<ms["SMA200"]:
            items.append(("⚠","Price is below the 200-day moving average"))
        if pd.notna(ms.get("Volume vs 20D",np.nan)) and ms["Volume vs 20D"]>=2:
            items.append(("●",f"Volume is {ms['Volume vs 20D']:.1f}× its 20-day average"))
    if not items: items.append(("✓","No stored thesis condition currently requires attention"))
    return items

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
page=st.sidebar.radio("Research workspace",["Markets","Dashboard","Announcements & Reports","Research Report","Investment Committee","Fundamentals","Valuation","Technical","Trade Centre","Orders","Paper Portfolio","Broker Connections","Company Command Centre","Before I Invest","Monitor My Thesis","Thesis Scorecard","Catalyst Calendar","Strategy Builder","Risk Centre","Portfolio Intelligence","Alerts","Workspace Settings","Quant","Forecasts","News & Events","Evidence & Thesis","Portfolio","Watchlist","Model Lab","Data & Production"])

h=history(ticker); meta=info(ticker)
if h.empty:
    st.error(f"No market data returned for {ticker}. Try another matching listing or enter the exchange ticker directly.")
    st.stop()
close=h["Close"]; price=float(close.iloc[-1]); name=meta.get("longName") or ticker
rv=rsi(close); rv=float(rv.iloc[-1]) if len(rv) and pd.notna(rv.iloc[-1]) else np.nan

st.title("Market Investment Analyst")
st.caption("V17 • Market Investment Analyst • decision brief + thesis monitor")

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
    metric_box(ex1, "Market", market_meta["market"])
    metric_box(ex2, "Exchange", market_meta["exchange"])
    metric_box(ex3, "Currency", market_meta["currency"])
    metric_box(ex4, "Default benchmark",
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
    metric_box(q[0], "Price",f"${price:.3f}",
                None if pd.isna(day_change) else f"{day_change:+.3f} ({day_pct*100:+.2f}%)")
    metric_box(q[1], "Previous close","—" if prev is None else f"${prev:.3f}")
    metric_box(q[2], "Day high","—" if pd.isna(day_high) else f"${day_high:.3f}")
    metric_box(q[3], "Day low","—" if pd.isna(day_low) else f"${day_low:.3f}")
    metric_box(q[4], "Volume","—" if pd.isna(day_vol) else f"{day_vol/1e6:.2f}M")
    metric_box(q[5], "52W high","—" if pd.isna(hi52) else f"${hi52:.3f}")
    metric_box(q[6], "52W low","—" if pd.isna(lo52) else f"${lo52:.3f}")

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
        metric_box(m[0], f"{period} movement",f"{s['change']:+.3f}",
                    f"{s['change_pct']*100:+.2f}%")
        metric_box(m[1], "Period start",f"${s['start']:.3f}")
        metric_box(m[2], "Latest",f"${s['last']:.3f}")
        metric_box(m[3], "Period high",f"${s['high']:.3f}")
        metric_box(m[4], "Period low",f"${s['low']:.3f}")
        metric_box(m[5], "Period volume","—" if pd.isna(s['volume']) else f"{s['volume']/1e6:.2f}M")

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
        v=change(close,n); metric_box(c, lab,"—" if pd.isna(v) else f"{v*100:+.1f}%")
    ytd=close[close.index.year==close.index[-1].year]
    ytdv=(ytd.iloc[-1]/ytd.iloc[0]-1) if len(ytd)>1 else np.nan
    metric_box(perf[4], "YTD","—" if pd.isna(ytdv) else f"{ytdv*100:+.1f}%")
    metric_box(perf[5], "RSI14","—" if pd.isna(rv) else f"{rv:.1f}")

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
    metric_box(pc1, "Sector",cls["sector"])
    metric_box(pc2, "Industry",cls["industry"])
    metric_box(pc3, "Market benchmark",bm_name)

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
        metric_box(rr[0], f"{ticker} return",f"{latest_company:+.2f}%")
        metric_box(rr[1], "Peer basket", "—" if pd.isna(latest_peer) else f"{latest_peer:+.2f}%")
        metric_box(rr[2], bm_name, "—" if pd.isna(latest_bm) else f"{latest_bm:+.2f}%")
        metric_box(rr[3], "vs peers","—" if pd.isna(latest_peer) else f"{latest_company-latest_peer:+.2f} pp")
        metric_box(rr[4], "vs market","—" if pd.isna(latest_bm) else f"{latest_company-latest_bm:+.2f} pp")
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
    category=c2.selectbox("Category",["All","Financial Reports","Quarterly Reports","Company Announcements",
        "Proxy / Governance","ASX Announcements","Annual Report","Half-Year Report","Quarterly Report","Results",
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
            groupmatch=ann["Group"].astype(str).eq(category) if "Group" in ann.columns else False
            typematch=ann["Type"].astype(str).eq(category)
            ann=ann[groupmatch | typematch]
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
        metric_box(st, "Announcements found",len(ann))
        display_cols=[c for c in ["Date","Group","Type","Title","Has PDF","Price Sensitive","Source"] if c in ann.columns]
        show=ann[display_cols].copy()
        st.dataframe(show,use_container_width=True,hide_index=True,height=430)

        if not ann.empty:
            opts=[]; mapping={}
            for i,r in ann.iterrows():
                flag=" 🔴" if bool(r.get("Price Sensitive",False)) else ""
                pdfmark=" 📄 PDF" if bool(r.get("Has PDF",False)) else ""
                lab=f"{r['Date']} — {r.get('Group',r['Type'])} — {r['Type']}{pdfmark}{flag}"
                opts.append(lab); mapping[lab]=i
            selected=st.selectbox("Select announcement",opts)
            rr=ann.loc[mapping[selected]]
            friendly=str(rr["Title"])
            if str(rr.get("Source","")).startswith("SEC"):
                friendly={"10-K":"Annual Report (10-K)","10-Q":"Quarterly Report (10-Q)",
                          "8-K":"Current Report (8-K)","20-F":"Annual Report (20-F)",
                          "40-F":"Annual Report (40-F)","6-K":"Foreign Issuer Report (6-K)",
                          "ARS":"Annual Report to Shareholders","DEF 14A":"Proxy Statement"}.get(str(rr["Type"]),str(rr["Type"]))
            st.subheader(friendly)
            a,b,c=st.columns(3)
            metric_box(a, "Date",str(rr["Date"])); metric_box(b, "Category",str(rr["Type"]))
            metric_box(c, "Price sensitive","Yes" if bool(rr.get("Price Sensitive",False)) else ("N/A (SEC filing)" if str(rr.get("Source","")).startswith("SEC") else "No / not supplied"))

            pdf_url=str(rr.get("PDFURL","") or "")
            read_url=str(rr.get("ReadURL","") or rr.get("URL",""))
            b1,b2=st.columns(2)
            if pdf_url:
                b1.link_button("View original PDF",pdf_url,use_container_width=True)
            else:
                b1.caption("No company-filed PDF was supplied with this filing.")

            if b2.button("Summarise document",type="primary",use_container_width=True):
                target=pdf_url or read_url
                with st.spinner("Reading the company document..."):
                    doc,ctype=fetch_document(target,str(rr.get("IndexURL","")))
                    text=extract_text(doc,ctype)
                    summ=evidence_summary(text)
                st.session_state["ann_key"]=selected
                st.session_state["ann_doc"]=doc
                st.session_state["ann_ctype"]=ctype
                st.session_state["ann_summary"]=summ
                st.session_state["ann_is_pdf"]=bool(doc and (doc[:4]==b"%PDF" or "pdf" in ctype.lower()))

            if pdf_url:
                pdfbytes,pdfctype=fetch_document(pdf_url)
                if pdfbytes and pdfbytes[:4]==b"%PDF":
                    fname=re.sub(r"[^A-Za-z0-9_-]+","_",f"{ticker}_{rr['Date']}_{rr['Type']}")[:110]+".pdf"
                    st.download_button("Download company PDF",pdfbytes,file_name=fname,mime="application/pdf")

            if st.session_state.get("ann_key")==selected:
                st.markdown("#### Document summary")
                st.write(st.session_state.get("ann_summary",""))
                if not pdf_url:
                    st.info("This SEC filing was supplied as an official HTML filing rather than a company-filed PDF. It can be read and summarised here, but the app will not manufacture or label an HTML/XML file as the company's PDF.")

elif page=="Research Report":
    st.header(f"Research Report — {ticker} — {name}")
    cls=classification(ticker,meta)
    snap=research_snapshot(meta)
    tech=technical_state(h)
    peers=find_peers(ticker,meta,max_peers=8)
    bm_ticker,bm_name=default_benchmark(ticker,meta)

    st.subheader("1. Research identity")
    r1,r2,r3,r4=st.columns(4)
    metric_box(r1, "Sector",cls["sector"]); metric_box(r2, "Industry",cls["industry"])
    metric_box(r3, "Market benchmark",bm_name); metric_box(r4, "Price",f"${price:.3f}")

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
    metric_box(st, "Reverse-DCF implied 5Y FCF growth","—" if pd.isna(ig) else f"{ig*100:.1f}%")
    st.caption("Outputs are assumption-sensitive; validated inputs are required.")

elif page=="Technical":
    st.header(f"Technical Analysis Lab — {ticker}")
    st.caption("Select one or several indicators and compare them directly with the selected share. The readings describe historical price and volume behaviour, not guaranteed future direction.")

    a,b=st.columns([1,2])
    period=a.selectbox("History",["6mo","1y","2y","5y"],index=1,help="Amount of price history used for the chart and indicators.")
    selected=b.multiselect("Indicators",list(TECH_INDICATOR_HELP),
        default=["SMA 20","SMA 50","RSI","MACD","Volume"],
        help="Select multiple indicators. For broader confirmation, combine indicators from different families rather than several that measure the same thing.")

    th=history(ticker,period)
    if th.empty:
        st.warning("No price history returned for technical analysis.")
    else:
        ti=technical_indicators(th); px=float(th["Close"].iloc[-1])
        overlays=[x for x in selected if x in TECH_OVERLAYS]
        panels=[x for x in selected if x in TECH_PANELS]
        rows=1+len(panels)
        heights=[0.55]+([0.45/len(panels)]*len(panels) if panels else [])
        fig=make_subplots(rows=rows,cols=1,shared_xaxes=True,vertical_spacing=.025,row_heights=heights)
        fig.add_trace(go.Candlestick(x=th.index,open=th["Open"],high=th["High"],low=th["Low"],close=th["Close"],name="Price"),row=1,col=1)

        def overlay(col,name=None,mode="lines"):
            fig.add_trace(go.Scatter(x=ti.index,y=ti[col],name=name or col,mode=mode),row=1,col=1)

        for ind in overlays:
            if ind.startswith("SMA") or ind in {"EMA 20","VWAP 20"}: overlay(ind)
            elif ind=="Bollinger Bands":
                for c in ["BB Upper","BB Middle","BB Lower"]: overlay(c)
            elif ind=="Donchian Channels":
                overlay("Donchian Upper"); overlay("Donchian Lower")
            elif ind=="Keltner Channels":
                overlay("Keltner Upper"); overlay("Keltner Lower")
            elif ind=="Ichimoku Cloud":
                for c in ["Ichimoku Conversion","Ichimoku Base","Ichimoku Span A","Ichimoku Span B"]: overlay(c)
            elif ind=="Parabolic SAR": overlay("Parabolic SAR",mode="markers")

        for r,ind in enumerate(panels,start=2):
            if ind=="RSI":
                fig.add_trace(go.Scatter(x=ti.index,y=ti["RSI"],name="RSI"),row=r,col=1)
                fig.add_hline(y=70,line_dash="dot",row=r,col=1); fig.add_hline(y=30,line_dash="dot",row=r,col=1)
            elif ind=="MACD":
                fig.add_trace(go.Scatter(x=ti.index,y=ti["MACD"],name="MACD"),row=r,col=1)
                fig.add_trace(go.Scatter(x=ti.index,y=ti["MACD Signal"],name="MACD Signal"),row=r,col=1)
                fig.add_trace(go.Bar(x=ti.index,y=ti["MACD Hist"],name="MACD Histogram"),row=r,col=1)
            elif ind=="Stochastic":
                for c in ["Stoch %K","Stoch %D"]: fig.add_trace(go.Scatter(x=ti.index,y=ti[c],name=c),row=r,col=1)
                fig.add_hline(y=80,line_dash="dot",row=r,col=1); fig.add_hline(y=20,line_dash="dot",row=r,col=1)
            elif ind=="ADX / DMI":
                for c in ["ADX","+DI","-DI"]: fig.add_trace(go.Scatter(x=ti.index,y=ti[c],name=c),row=r,col=1)
                fig.add_hline(y=25,line_dash="dot",row=r,col=1)
            elif ind in {"ATR","CCI","Williams %R","ROC","Momentum","OBV","MFI","CMF"}:
                fig.add_trace(go.Scatter(x=ti.index,y=ti[ind],name=ind),row=r,col=1)
                if ind=="MFI":
                    fig.add_hline(y=80,line_dash="dot",row=r,col=1); fig.add_hline(y=20,line_dash="dot",row=r,col=1)
                elif ind=="CCI":
                    fig.add_hline(y=100,line_dash="dot",row=r,col=1); fig.add_hline(y=-100,line_dash="dot",row=r,col=1)
                elif ind=="Williams %R":
                    fig.add_hline(y=-20,line_dash="dot",row=r,col=1); fig.add_hline(y=-80,line_dash="dot",row=r,col=1)
                elif ind in {"ROC","Momentum","CMF"}: fig.add_hline(y=0,line_dash="dot",row=r,col=1)
            elif ind=="Volume":
                fig.add_trace(go.Bar(x=ti.index,y=ti["Volume"],name="Volume"),row=r,col=1)

        fig.update_layout(height=max(650,390+185*len(panels)),hovermode="x unified",
                          xaxis_rangeslider_visible=False,legend_orientation="h",margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig,use_container_width=True)

        st.subheader("What each selected indicator is doing")
        if not selected:
            st.info("Select one or more indicators above.")
        for ind in selected:
            with st.expander(f"{ind} — current reading",expanded=len(selected)<=4):
                st.write(TECH_INDICATOR_HELP[ind])
                st.markdown("**How it is tracking this share now:**")
                st.write(technical_reading(ind,ti,px))

        if len(selected)>1:
            st.subheader("How to read the selected indicators together")
            st.info(combined_technical_reading(selected,ti,px))
            st.markdown("""**Multi-indicator reading order:**  
1. **Trend** — start with moving averages, Ichimoku, Donchian, Keltner or Parabolic SAR.  
2. **Momentum** — check RSI, MACD, Stochastic, CCI, Williams %R or ROC.  
3. **Participation** — use Volume, OBV, MFI or CMF to see whether trading activity supports the move.  
4. **Strength & volatility** — use ADX and ATR to understand trend strength and the size of price movement.  

Agreement across different families is more informative than several similar indicators saying the same thing. Conflicting families should be treated as a mixed technical picture.""")

        st.subheader("Technical indicator library")
        guide=[]
        for name,desc in TECH_INDICATOR_HELP.items():
            family=("Trend / price overlay" if name in TECH_OVERLAYS else
                    "Volume / money flow" if name in {"OBV","MFI","CMF","Volume"} else
                    "Volatility / trend strength" if name in {"ATR","ADX / DMI"} else "Momentum / oscillator")
            guide.append({"Indicator":name,"Family":family,"What it tracks":desc})
        st.dataframe(pd.DataFrame(guide),use_container_width=True,hide_index=True)


elif page=="Trade Centre":
    st.header(f"Trade Centre — {ticker}")
    st.warning("PAPER TRADING ONLY — V15 does not connect to a live broker or transmit real orders.")
    st.caption("The order manager is intentionally separated from research signals. Analysis can inform an order proposal, but a user must review and submit the paper order.")

    h=history(ticker,"1mo")
    if h.empty:
        st.error("A current reference price could not be loaded.")
    else:
        ref=float(h["Close"].iloc[-1])
        c1,c2,c3=st.columns(3)
        metric_box(c1,"Price",f"${ref:,.3f}")
        metric_box(c2,"Paper cash",f"${paper_cash_balance():,.2f}")
        pos=paper_positions_df()
        held=float(pos.loc[pos["ticker"]==ticker,"quantity"].iloc[0]) if (not pos.empty and ticker in pos["ticker"].values) else 0
        metric_box(c3,"Paper shares held",f"{held:,.0f}")

        with st.form("paper_order_ticket"):
            st.subheader("Paper order ticket")
            a,b,c=st.columns(3)
            side=a.selectbox("Side",["Buy","Sell"])
            order_type=b.selectbox("Order type",["Market","Limit","Stop","Stop Limit"])
            tif=c.selectbox("Time in force",["DAY","GTC"])
            d,e,f=st.columns(3)
            qty=d.number_input("Quantity",min_value=0.0,value=100.0,step=1.0)
            limit=e.number_input("Limit price",min_value=0.0,value=round(ref,3),step=0.01,
                                 disabled=order_type not in {"Limit","Stop Limit"})
            stop=f.number_input("Stop price",min_value=0.0,value=round(ref,3),step=0.01,
                                disabled=order_type not in {"Stop","Stop Limit"})
            notes=st.text_input("Order notes / thesis reference",placeholder="Optional: why this paper trade is being considered")
            gross,sim_cost=estimate_order(side,qty,ref)
            st.info(f"Reference notional: ${gross:,.2f}. Simulator cost estimate: ${sim_cost:,.2f}. V15 fills Market paper orders at the latest loaded close; this is not a live execution quote.")
            preview=st.form_submit_button("Review paper order",type="primary",use_container_width=True)

        if preview:
            st.session_state["paper_preview"]={
                "ticker":ticker,"side":side,"order_type":order_type,"qty":qty,"reference_price":ref,
                "limit_price":limit if order_type in {"Limit","Stop Limit"} else None,
                "stop_price":stop if order_type in {"Stop","Stop Limit"} else None,"tif":tif,"notes":notes
            }

        if "paper_preview" in st.session_state and st.session_state["paper_preview"].get("ticker")==ticker:
            o=st.session_state["paper_preview"]
            st.subheader("Order confirmation")
            st.write(f"**{o['side']} {o['qty']:,.0f} {ticker} — {o['order_type']} — {o['tif']}**")
            st.write(f"Reference price: **${o['reference_price']:,.3f}**")
            x,y=st.columns(2)
            if x.button("Submit PAPER order",type="primary",use_container_width=True):
                ok,msg=submit_paper_order(**o)
                (st.success if ok else st.error)(msg)
                if ok: st.session_state.pop("paper_preview",None); st.rerun()
            if y.button("Discard",use_container_width=True):
                st.session_state.pop("paper_preview",None); st.rerun()

elif page=="Orders":
    st.header("Order Management System")
    st.caption("Audit trail for the V15 paper execution engine. Live broker transmission is disabled.")
    od=paper_orders_df()
    if od.empty:
        st.info("No paper orders yet.")
    else:
        show=od.copy()
        for col in ["reference_price","fill_price","estimated_value"]:
            if col in show: show[col]=show[col].map(lambda x:f"{x:,.3f}" if pd.notna(x) else "")
        st.dataframe(show,use_container_width=True,hide_index=True)
        opens=od[od["status"]=="OPEN"]
        if not opens.empty:
            oid=st.selectbox("Open order to cancel",opens["id"].tolist())
            if st.button("Cancel selected paper order"):
                if cancel_paper_order(oid): st.success("Paper order cancelled."); st.rerun()

elif page=="Paper Portfolio":
    st.header("Paper Portfolio")
    st.caption("Unified portfolio framework for simulated positions. Future broker adapters can reconcile domestic and global accounts into this schema.")
    pos=paper_positions_df(); cash=paper_cash_balance()
    metric_box(st,"Paper cash",f"${cash:,.2f}")
    if pos.empty:
        st.info("No paper positions yet.")
    else:
        rows=[]
        total=cash
        for _,r in pos.iterrows():
            hh=history(r["ticker"],"5d")
            last=float(hh["Close"].iloc[-1]) if not hh.empty else float(r["avg_cost"])
            mv=float(r["quantity"])*last; pnl=(last-float(r["avg_cost"]))*float(r["quantity"])
            total+=mv
            rows.append({"Ticker":r["ticker"],"Quantity":r["quantity"],"Avg cost":r["avg_cost"],
                         "Last":last,"Market value":mv,"Unrealised P&L":pnl})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        metric_box(st,"Paper account value",f"${total:,.2f}")
    with st.expander("Reset simulator"):
        st.write("Deletes all V15 paper orders and positions and restores simulated cash to $100,000.")
        if st.button("Reset paper account"):
            reset_paper_account(); st.success("Paper account reset."); st.rerun()

elif page=="Broker Connections":
    st.header("Broker & Execution Architecture")
    st.warning("LIVE EXECUTION IS DISABLED IN V15.")
    st.write("V15 establishes adapter boundaries without storing brokerage credentials or sending orders. A production connection should use broker-supported authentication, encrypted secrets, explicit account permissions, risk controls and an auditable order lifecycle.")
    st.dataframe(BROKER_ADAPTER_REQUIREMENTS,use_container_width=True,hide_index=True)
    st.subheader("Target routing")
    st.code("""Research / Technical / Quant
        ↓
Order Proposal
        ↓
Risk & Validation
        ↓
User Confirmation
        ↓
Order Manager
   ↙             ↘
AU Broker       Global Broker
Adapter         Adapter
(CHESS/HIN)     (Global/FX)""")
    st.subheader("Production gates before live trading")
    st.markdown("""- Verify the selected Australian partner's current CHESS/HIN and API capabilities.
- Verify the global broker's supported API, instruments, order types, market-data entitlements and FX workflow.
- Add secure OAuth/token or broker-approved authentication; never hard-code credentials.
- Add account-level limits, duplicate-order protection, stale-price protection, market-hours checks and a kill switch.
- Add immutable order/event audit logging and broker reconciliation.
- Obtain legal advice on the exact Australian licensing/authorisation model before offering execution to other users.""")


elif page=="Company Command Centre":
    st.header(f"Company Command Centre — {ticker}")
    st.caption("One-screen research cockpit: price, thesis, fundamentals, technical context, valuation, catalysts, risk and evidence provenance.")
    st.markdown("**Core workflow:** Before I Invest → make the evidence visible. Monitor My Thesis → check whether the reasons for owning the company remain true.")
    q1,q2=st.columns(2)
    q1.info("**BEFORE I INVEST**\n\nWhat do I need to know before committing more capital? Open **Before I Invest** from the sidebar.")
    q2.info("**MONITOR MY THESIS**\n\nAre the reasons I invested still true? Open **Monitor My Thesis** from the sidebar.")
    h=history(ticker,"1y")
    if h.empty:
        st.warning("No price history available.")
    else:
        ms=market_structure(h); conf=confluence_snapshot(h)
        a,b,c,d=st.columns(4)
        metric_box(a,"Price",f"${ms['Price']:,.3f}")
        metric_box(b,"52W high",f"${ms['Period high']:,.3f}")
        metric_box(c,"52W low",f"${ms['Period low']:,.3f}")
        metric_box(d,"Volume",f"{ms['Volume vs 20D']:.2f}× 20D")
        tabs=st.tabs(["Thesis","Company KPIs","Technical","Market Structure","Catalysts","Risks & Evidence"])
        with tabs[0]:
            st.write(st.session_state.get("thesis","Use the sidebar investment thesis as the working hypothesis."))
            st.info("Use Thesis Scorecard to convert narrative beliefs into measurable conditions.")
        with tabs[1]:
            cls=classify_company(ticker)
            kpis=company_kpi_template(ticker,cls.get("sector",""),cls.get("industry",""))
            st.write("**Relevant KPI framework for this company type:**")
            st.write(" • ".join(kpis))
            st.caption("V16 defines the KPI schema. Report extraction should populate reported values only when supported by source documents.")
        with tabs[2]:
            st.dataframe(conf,use_container_width=True,hide_index=True)
            if not conf.empty:
                st.info("Read across different families. Trend + momentum + participation agreement is more informative than counting several correlated momentum indicators.")
        with tabs[3]:
            st.dataframe(pd.DataFrame([ms]).T.rename(columns={0:"Current reading"}),use_container_width=True)
        with tabs[4]:
            con=ws_db(); cats=pd.read_sql_query("SELECT event_date,event,category,status,source FROM catalysts WHERE ticker=? ORDER BY event_date",(ticker,),con); con.close()
            st.dataframe(cats,use_container_width=True,hide_index=True) if not cats.empty else st.info("No catalysts recorded yet. Add them in Catalyst Calendar.")
        with tabs[5]:
            st.write(provenance_badge("Market"),"Price/volume history")
            st.write(provenance_badge("Calculated"),"Technical indicators, market structure and model outputs")
            st.write(provenance_badge("Reported"),"Only use this label for values taken directly from company documents.")
            st.write(provenance_badge("AI"),"Interpretation must remain distinguishable from reported facts.")

elif page=="Before I Invest":
    st.header(f"Before I Invest — {ticker}")
    st.markdown("### What do I need to know before committing more capital?")
    st.caption("Decision Brief combines your stored position, thesis conditions, market structure, technical context, portfolio concentration and trade scenario. It does not issue a buy/sell recommendation.")
    v17_db_upgrade()
    hold=holding_for(ticker)
    with st.expander("Your current position",expanded=(hold["quantity"]==0)):
        a,b=st.columns(2)
        qty=a.number_input("Shares currently owned",min_value=0.0,value=float(hold["quantity"]),step=1.0,key="v17_hold_qty")
        avg=b.number_input("Average cost",min_value=0.0,value=float(hold["avg_cost"]),step=0.01,key="v17_hold_avg")
        if st.button("Save current position",key="v17_save_hold"):
            save_holding(ticker,qty,avg); st.success("Position saved."); st.rerun()

    amount=st.number_input("Amount you are considering investing",min_value=0.0,value=10000.0,step=500.0,key="v17_amount")
    d=decision_brief_data(ticker,amount)
    if not d:
        st.error("Price history could not be loaded, so the Decision Brief cannot calculate a trade scenario.")
    else:
        st.subheader("What requires my attention?")
        for icon,msg in attention_items(ticker): st.write(f"{icon} {msg}")

        st.subheader("Position & proposed investment")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Current price",f"${d['price']:,.3f}")
        c2.metric("Current shares",f"{d['qty0']:,.0f}")
        c3.metric("Average cost",f"${d['avg0']:,.3f}" if d["qty0"] else "—")
        c4.metric("Market value",f"${d['mv0']:,.0f}")
        before=pd.DataFrame([
            {"Measure":"Shares","Before":d["qty0"],"After":d["qty1"]},
            {"Measure":"Average cost","Before":d["avg0"],"After":d["avg1"]},
            {"Measure":"Market value @ reference price","Before":d["mv0"],"After":d["mv1"]},
            {"Measure":"Observed portfolio weight*","Before":d["w0"],"After":d["w1"]},
        ])
        st.dataframe(before,use_container_width=True,hide_index=True)
        st.caption(f"Proposed purchase: {d['add_qty']:,} shares × ${d['price']:,.3f} = ${d['spend']:,.2f}. *Weight uses holdings known to this prototype (saved selected holding + paper positions + paper cash), not your complete external wealth.")

        left,right=st.columns(2)
        with left:
            st.subheader("Thesis evidence")
            t=thesis_table(ticker)
            if t.empty: st.info("No measurable thesis conditions yet. Add them in Thesis Scorecard.")
            else: st.dataframe(t[["metric","current_value","operator","threshold","status","source"]],use_container_width=True,hide_index=True)
            st.subheader("Company KPI checklist")
            cls=classify_company(ticker)
            st.write(" • ".join(company_kpi_template(ticker,cls.get("sector",""),cls.get("industry",""))))
        with right:
            st.subheader("Technical & market context")
            st.dataframe(d["confluence"],use_container_width=True,hide_index=True)
            ms=d["market"]
            st.write(f"20D support: **${ms['20D support']:,.3f}**  |  20D resistance: **${ms['20D resistance']:,.3f}**")
            st.write(f"52-week/period range: **${ms['Period low']:,.3f} – ${ms['Period high']:,.3f}**")

        st.subheader("Catalysts")
        con=ws_db(); cats=pd.read_sql_query("SELECT event_date,event,category,status,source FROM catalysts WHERE ticker=? ORDER BY event_date LIMIT 8",(ticker,),con); con.close()
        st.dataframe(cats,use_container_width=True,hide_index=True) if not cats.empty else st.info("No catalysts stored yet.")

        st.subheader("Trade scenario")
        st.write(f"**Add ${amount:,.0f} → {d['add_qty']:,} shares at the latest loaded reference price.**")
        st.write(f"New holding: **{d['qty1']:,.0f} shares** · New average cost: **${d['avg1']:,.3f}**")
        x,y,z=st.columns(3)
        if x.button("Send scenario to Paper Trade",type="primary",use_container_width=True):
            st.session_state["paper_preview"]={"ticker":ticker,"side":"Buy","order_type":"Market","qty":float(d["add_qty"]),
                "reference_price":d["price"],"limit_price":None,"stop_price":None,"tif":"DAY",
                "notes":"Created from Before I Invest Decision Brief"}
            st.success("Paper-trade scenario prepared. Open Trade Centre to review and explicitly submit it.")
        if y.button("Add price alert",use_container_width=True):
            con=ws_db(); con.execute("INSERT INTO alerts(ticker,metric,operator,threshold,enabled,notes) VALUES(?,?,?,?,1,?)",
                (ticker,"Price","<=",d["price"],"Created from Decision Brief")); con.commit(); con.close(); st.success("Price alert rule saved.")
        if z.button("Record review",use_container_width=True):
            con=ws_db(); con.execute("""INSERT INTO review_log(ticker,reviewed_at,amount,price,shares_before,avg_cost_before,shares_after,avg_cost_after,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",(ticker,datetime.now(timezone.utc).isoformat(),amount,d["price"],d["qty0"],d["avg0"],d["qty1"],d["avg1"],"Before I Invest review"))
            con.commit(); con.close(); st.success("Decision review recorded.")

        st.markdown("---")
        st.caption("Evidence labels: 🟢 company reported · 🔵 exchange/regulatory · 🟣 market data · 🟠 calculated · ⚪ interpretation. V17 never treats an unpopulated KPI as a reported fact.")

elif page=="Monitor My Thesis":
    st.header(f"Monitor My Thesis — {ticker}")
    st.markdown("### Are the reasons I invested still true?")
    st.caption("This monitor compares your current stored thesis conditions with a prior snapshot. It only evaluates evidence you have actually entered or sourced; missing evidence stays missing.")
    v17_db_upgrade()
    t=thesis_table(ticker)
    a,b,c=st.columns(3)
    a.metric("Conditions tracked",str(len(t)))
    a_met=int((t["status"]=="Met").sum()) if not t.empty else 0
    b.metric("Currently met",str(a_met))
    c.metric("Require attention",str(len(t)-a_met))
    if t.empty:
        st.info("No thesis conditions are stored. Add measurable conditions in Thesis Scorecard first.")
    else:
        st.subheader("Current thesis")
        st.dataframe(t[["metric","current_value","operator","threshold","status","source","updated_at"]],use_container_width=True,hide_index=True)
        if st.button("Save current thesis as monitoring baseline",type="primary"):
            n=snapshot_thesis(ticker); st.success(f"Saved {n} thesis conditions as the new baseline.")
        st.subheader("What changed since my last review?")
        changes=thesis_changes(ticker)
        st.dataframe(changes,use_container_width=True,hide_index=True)
        st.info("An increase is not automatically good and a decrease is not automatically bad. Direction must be interpreted in the context of the metric—for example, lower credit losses may be favourable while lower growth may not be.")

    st.subheader("Attention queue")
    for icon,msg in attention_items(ticker): st.write(f"{icon} {msg}")

    st.subheader("Monitoring controls")
    st.write("Use **Catalyst Calendar** for expected events, **Alerts** for stored market/technical thresholds, and **Announcements & Reports** to inspect new company evidence and original documents.")
    st.caption("Background alert delivery is not yet a durable service in this Streamlit prototype; V17 stores the monitoring rules and review baselines.")


elif page=="Thesis Scorecard":
    st.header(f"Investment Thesis Scorecard — {ticker}")
    st.caption("Convert the investment thesis into measurable conditions. Status is descriptive; it is not an investment recommendation.")
    con=ws_db()
    with st.form("thesis_rule"):
        c1,c2,c3,c4=st.columns(4)
        metric=c1.text_input("Metric",placeholder="e.g. US TTV growth")
        operator=c2.selectbox("Condition",[">",">=","<","<="])
        threshold=c3.number_input("Threshold",value=0.0)
        current=c4.number_input("Current reported value",value=0.0)
        source=st.text_input("Evidence/source",placeholder="e.g. FY26 results presentation p. 12")
        add=st.form_submit_button("Add thesis condition")
    if add and metric:
        ok={">":current>threshold,">=":current>=threshold,"<":current<threshold,"<=":current<=threshold}[operator]
        status="Met" if ok else "Watch / Broken"
        con.execute("INSERT INTO thesis_rules(ticker,metric,operator,threshold,current_value,status,source,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                    (ticker,metric,operator,threshold,current,status,source,datetime.now(timezone.utc).isoformat()))
        con.commit(); st.success("Condition added."); st.rerun()
    df=pd.read_sql_query("SELECT id,metric,operator,threshold,current_value,status,source,updated_at FROM thesis_rules WHERE ticker=? ORDER BY id",(ticker,),con)
    con.close()
    st.dataframe(df,use_container_width=True,hide_index=True) if not df.empty else st.info("No measurable thesis conditions yet.")

elif page=="Catalyst Calendar":
    st.header(f"Catalyst Calendar — {ticker}")
    st.caption("Track company events, results, AGMs, dividends, index events, macro releases and your own thesis checkpoints.")
    con=ws_db()
    with st.form("cat_form"):
        a,b,c=st.columns(3)
        event_date=a.date_input("Date")
        category=b.selectbox("Category",["Results","AGM","Dividend","Guidance","Capital","Index","Macro","Other"])
        status=c.selectbox("Status",["Expected","Confirmed","Completed"])
        event=st.text_input("Catalyst / event")
        source=st.text_input("Source / evidence")
        submit=st.form_submit_button("Add catalyst")
    if submit and event:
        con.execute("INSERT INTO catalysts(ticker,event_date,event,category,source,status) VALUES(?,?,?,?,?,?)",
                    (ticker,str(event_date),event,category,source,status)); con.commit(); st.success("Catalyst added."); st.rerun()
    cats=pd.read_sql_query("SELECT id,event_date,event,category,status,source FROM catalysts WHERE ticker=? ORDER BY event_date",(ticker,),con); con.close()
    st.dataframe(cats,use_container_width=True,hide_index=True) if not cats.empty else st.info("No catalysts recorded.")

elif page=="Strategy Builder":
    st.header(f"No-Code Strategy Builder — {ticker}")
    st.caption("Build transparent technical rules, test their current state, then use Backtesting/Paper Trading before considering any live workflow.")
    h=history(ticker,"2y")
    metrics=["Price","SMA20","SMA50","SMA200","RSI","ADX","ROC","VolumeRatio"]
    n=st.slider("Number of rules",1,6,3)
    rules=[]
    for i in range(n):
        a,b,c,d=st.columns(4)
        metric=a.selectbox(f"Metric {i+1}",metrics,key=f"sm{i}")
        op=b.selectbox("Operator",[">","<",">=","<="],key=f"so{i}")
        compare_type=c.selectbox("Compare with",["Value","Indicator"],key=f"ct{i}")
        if compare_type=="Indicator":
            rhs=d.selectbox("Indicator",metrics,key=f"si{i}")
            rules.append({"metric":metric,"operator":{">":"gt","<":"lt",">=":"gte","<=":"lte"}[op],"compare_metric":rhs})
        else:
            val=d.number_input("Value",value=0.0,key=f"sv{i}")
            rules.append({"metric":metric,"operator":{">":"gt","<":"lt",">=":"gte","<=":"lte"}[op],"compare_metric":None,"value":val})
    if not h.empty:
        results=strategy_eval(h,rules)
        rdf=pd.DataFrame([{"Rule":f"{r['metric']} {r['operator']} {r.get('compare_metric') or r.get('value')}",
                           "Current":r["lhs"],"Comparison":r["rhs"],"Pass":r["passed"]} for r in results])
        st.dataframe(rdf,use_container_width=True,hide_index=True)
        st.info(f"Current setup satisfies {sum(r['passed'] for r in results)} of {len(results)} rules. This is a rule-state check, not a forecast.")
    name=st.text_input("Strategy name",value=f"{ticker} strategy")
    if st.button("Save strategy"):
        con=ws_db(); con.execute("INSERT INTO strategy_rules(name,ticker,rule_json,created_at) VALUES(?,?,?,?)",
                                 (name,ticker,json.dumps(rules),datetime.now(timezone.utc).isoformat())); con.commit(); con.close(); st.success("Strategy saved.")

elif page=="Risk Centre":
    st.header(f"Risk & Position Sizing Centre — {ticker}")
    h=history(ticker,"1y")
    if h.empty: st.warning("No price history available.")
    else:
        ti=technical_indicators(h); px=float(h["Close"].iloc[-1]); atr=float(ti["ATR"].iloc[-1])
        a,b,c=st.columns(3)
        account=a.number_input("Portfolio value",min_value=0.0,value=max(paper_cash_balance(),100000.0),step=1000.0)
        risk_pct=b.number_input("Maximum risk per trade (%)",min_value=0.1,max_value=10.0,value=1.0,step=0.1)
        atr_mult=c.number_input("ATR stop multiple",min_value=0.5,max_value=10.0,value=2.0,step=0.5)
        stop=max(0,px-atr*atr_mult); risk_per_share=max(px-stop,0.000001); risk_dollars=account*risk_pct/100
        qty=int(risk_dollars/risk_per_share); position=qty*px
        r1,r2,r3,r4=st.columns(4)
        r1.metric("ATR",f"${atr:.3f}"); r2.metric("Illustrative stop",f"${stop:.3f}")
        r3.metric("Risk-sized shares",f"{qty:,}"); r4.metric("Position value",f"${position:,.0f}")
        st.caption("Illustrative risk sizing only. ATR-based stops can gap through their level and do not cap losses.")
        pr,stats=portfolio_risk_snapshot()
        if not pr.empty:
            st.subheader("Existing paper portfolio concentration")
            st.dataframe(pr,use_container_width=True,hide_index=True)
            st.write(f"Largest paper position weight: **{stats['Largest position']*100:.1f}%**")

elif page=="Portfolio Intelligence":
    st.header("Portfolio Intelligence")
    pr,stats=portfolio_risk_snapshot()
    if pr.empty:
        st.info("Create paper positions to populate portfolio intelligence.")
    else:
        a,b,c=st.columns(3)
        a.metric("Invested value",f"${stats['Invested']:,.0f}")
        b.metric("Largest position",f"{stats['Largest position']*100:.1f}%")
        c.metric("Weighted volatility",f"{stats['Weighted volatility']*100:.1f}%")
        st.dataframe(pr,use_container_width=True,hide_index=True)
        st.subheader("Concentration")
        fig=go.Figure(go.Pie(labels=pr["Ticker"],values=pr["Market value"],hole=.45))
        st.plotly_chart(fig,use_container_width=True)
        st.caption("V16 portfolio analytics use paper positions and historical market data. Tax, dividends, FX attribution and broker cash reconciliation require richer transaction data.")

elif page=="Alerts":
    st.header(f"Research Alerts — {ticker}")
    st.caption("Define monitoring rules now. V16 stores them; scheduled/background evaluation should be connected to a durable worker before relying on notifications.")
    con=ws_db()
    with st.form("alert_form"):
        a,b,c=st.columns(3)
        metric=a.selectbox("Metric",["Price","RSI","VolumeRatio","SMA50","SMA200","ADX"])
        op=b.selectbox("Condition",[">","<",">=","<="])
        threshold=c.number_input("Threshold",value=0.0)
        notes=st.text_input("Alert note")
        submit=st.form_submit_button("Add alert")
    if submit:
        con.execute("INSERT INTO alerts(ticker,metric,operator,threshold,enabled,notes) VALUES(?,?,?,?,1,?)",(ticker,metric,op,threshold,notes))
        con.commit(); st.success("Alert rule saved."); st.rerun()
    adf=pd.read_sql_query("SELECT id,metric,operator,threshold,enabled,notes FROM alerts WHERE ticker=? ORDER BY id",(ticker,),con); con.close()
    st.dataframe(adf,use_container_width=True,hide_index=True) if not adf.empty else st.info("No alert rules saved.")

elif page=="Workspace Settings":
    st.header("Workspace Customisation")
    st.caption("Choose a working style and the information that should dominate your company workflow.")
    con=ws_db(); row=con.execute("SELECT preset,default_period,default_benchmark,widgets FROM user_layout WHERE id=1").fetchone()
    preset=st.selectbox("Workspace preset",["Investor","Swing Trader","Technical Trader","Portfolio Manager"],index=["Investor","Swing Trader","Technical Trader","Portfolio Manager"].index(row[0] if row else "Investor"))
    period=st.selectbox("Default timeframe",["6mo","1y","2y","5y"],index=["6mo","1y","2y","5y"].index(row[1] if row and row[1] in ["6mo","1y","2y","5y"] else "1y"))
    widgets=st.multiselect("Command Centre modules",["Price","Thesis","Fundamentals","Technical","Valuation","Catalysts","Risks","Latest announcement","Portfolio"],
                           default=(row[3].split(",") if row and row[3] else ["Price","Thesis","Fundamentals","Technical"]))
    if st.button("Save workspace"):
        con.execute("""INSERT INTO user_layout(id,preset,default_period,default_benchmark,widgets) VALUES(1,?,?,?,?)
                       ON CONFLICT(id) DO UPDATE SET preset=excluded.preset,default_period=excluded.default_period,
                       default_benchmark=excluded.default_benchmark,widgets=excluded.widgets""",
                    (preset,period,"Auto",",".join(widgets))); con.commit(); st.success("Workspace saved.")
    con.close()
    st.info("Streamlit does not provide native drag-and-drop dashboard layout persistence. V16 implements saved presets/module selection; a custom frontend/component would be the next step for true draggable cards.")


elif page=="Quant":
    st.header("Quant")
    ret=close.pct_change().dropna(); curve=(1+ret).cumprod(); dd=curve/curve.cummax()-1
    cs=st.columns(4); metric_box(cs[0], "Annualised volatility",f"{ret.std()*np.sqrt(252)*100:.1f}%"); metric_box(cs[1], "Max drawdown",f"{dd.min()*100:.1f}%")
    sh=ret.mean()/ret.std()*np.sqrt(252) if ret.std() else np.nan; metric_box(cs[2], "Sharpe (0% RF)","—" if pd.isna(sh) else f"{sh:.2f}")
    metric_box(cs[3], "12M momentum","—" if len(close)<253 else f"{change(close,252)*100:.1f}%")
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
            metric_box(cs[0], "Annualised return",f"{a['annualised_return']*100:.1f}%"); metric_box(cs[1], "Volatility",f"{a['annualised_volatility']*100:.1f}%"); metric_box(cs[2], "Max drawdown",f"{a['max_drawdown']*100:.1f}%"); metric_box(cs[3], "HHI",f"{concentration(w):.3f}")
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
    metric_box(c1, "Twelve Data API","Connected" if td_key else "Not configured")
    metric_box(c2, "ASX prototype feed","Yahoo/yfinance")
    metric_box(c3, "Provider architecture","Active")
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
