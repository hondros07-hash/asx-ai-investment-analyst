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

st.set_page_config(page_title="Chrímata", page_icon="🏛️", layout="wide")


st.markdown("""
<style>
.chrimata-parthenon{width:100%;overflow:hidden;border-radius:16px;margin-bottom:10px;background:#0b2f66;}
.chrimata-parthenon img{display:block;width:100%;height:auto;max-height:260px;object-fit:cover;}
</style>
""",unsafe_allow_html=True)

st.markdown("""
<style>
/* V19.8.2 — Chrímata terminal landing page */
body, .stApp {font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}
.block-container{max-width:1540px!important;padding-top:.35rem!important;}
.chrimata-terminal-hero{position:relative;width:100%;height:142px;overflow:hidden;border-radius:0 0 2px 2px;margin:0 0 10px;background:#082b59;box-shadow:0 2px 10px rgba(15,23,42,.14)}
.chrimata-terminal-hero img{width:100%;height:100%;object-fit:cover;object-position:center 46%;filter:saturate(.92) contrast(1.03)}
.chrimata-terminal-hero:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,30,63,.92) 0%,rgba(4,30,63,.50) 31%,rgba(4,30,63,.08) 58%,rgba(4,30,63,.62) 100%)}
.chrimata-brand{position:absolute;z-index:2;left:28px;top:27px;color:white}.chrimata-brand-title{font-family:Georgia,serif;font-size:31px;letter-spacing:.035em;text-transform:uppercase;line-height:1}.chrimata-brand-sub{font-family:Georgia,serif;font-size:15px;margin-top:9px;opacity:.94}.chrimata-quote{position:absolute;z-index:2;right:30px;top:28px;width:300px;text-align:center;color:#fff;font-family:Georgia,serif;font-style:italic;font-size:19px;line-height:1.2}.chrimata-quote small{display:block;font-family:Inter,sans-serif;font-style:normal;font-size:9px;letter-spacing:.16em;margin-top:8px;opacity:.72}
.chrimata-market-title{display:flex;align-items:center;gap:12px;margin:5px 0 0}.chrimata-market-flag{font-size:27px}.chrimata-market-name{font-size:27px;font-weight:800;letter-spacing:-.035em;color:#13213b}.chrimata-market-note{font-size:12px;color:#718096;margin:0 0 10px 42px}
/* turn the home market radio into compact terminal tabs */
div[data-testid="stRadio"] > label{display:none!important}div[data-testid="stRadio"] div[role="radiogroup"]{gap:7px!important;flex-wrap:wrap!important;margin:2px 0 7px!important}div[data-testid="stRadio"] div[role="radiogroup"] label{background:#fff;border:1px solid #dbe4f0;border-radius:7px;padding:7px 12px!important;box-shadow:0 1px 2px rgba(15,23,42,.03)}div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:#edf5ff;border-color:#2b78e4;color:#0b63ce!important}div[data-testid="stRadio"] div[role="radiogroup"] p{font-size:.82rem!important;font-weight:700!important}
/* tighter dashboard density */
div[data-testid="stMetric"]{border-radius:8px!important;padding:10px 13px!important;box-shadow:none!important;border:1px solid #dce5ef!important}div[data-testid="stMetricValue"]{font-size:1.65rem!important}div[data-testid="stMetricDelta"]{font-size:.83rem!important}.stDataFrame{font-size:.82rem}.chrimata-section-rule{height:1px;background:#dbe4ee;margin:5px 0 9px}.chrimata-terminal-footer{margin-top:16px;padding:10px 2px;border-top:1px solid #dbe4ee;color:#8290a3;font-size:11px;display:flex;justify-content:space-between}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#062f59 0%,#0b4778 62%,#062d52 100%)!important}.stApp h2{margin-top:.45rem!important;margin-bottom:.45rem!important}.stApp h3{margin-top:.35rem!important;margin-bottom:.35rem!important}
</style>
""",unsafe_allow_html=True)


st.markdown("""
<style>
/* V19.8.3 — precision terminal shell: tuned to the approved Chrímata visual specification */
header[data-testid="stHeader"]{height:0!important;min-height:0!important;background:transparent!important}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{visibility:hidden!important;height:0!important}
[data-testid="stSidebar"]{width:214px!important;min-width:214px!important;max-width:214px!important;border-right:1px solid #0d4774!important}
[data-testid="stSidebar"] > div:first-child{width:214px!important;padding-top:.35rem!important}
[data-testid="stSidebar"] .block-container{padding:.55rem .72rem 1rem!important}
[data-testid="stSidebar"] h1{font-size:1.25rem!important;margin:.2rem 0 .45rem!important;color:white!important}
[data-testid="stSidebar"] h3{font-size:.78rem!important;color:white!important}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label{font-size:.72rem!important}
[data-testid="stSidebar"] div[role="radiogroup"]{gap:1px!important}
[data-testid="stSidebar"] div[role="radiogroup"] label{padding:.42rem .52rem!important;border-radius:6px!important;color:#f8fbff!important}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:#1766aa!important}
[data-testid="stSidebar"] div[role="radiogroup"] p{font-size:.73rem!important;font-weight:650!important}
[data-testid="stSidebar"] details{border:1px solid rgba(255,255,255,.14)!important;border-radius:7px!important;background:rgba(255,255,255,.035)!important}
[data-testid="stSidebar"] details summary{font-size:.72rem!important;color:#fff!important;padding:.4rem!important}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{font-size:.72rem!important}
.stApp > .main{margin-left:0!important}
.main .block-container{max-width:none!important;width:100%!important;padding:.05rem .75rem 1.2rem!important}
.chrimata-terminal-hero{height:108px!important;margin:0 -.75rem 6px!important;width:calc(100% + 1.5rem)!important;border-radius:0!important;box-shadow:none!important}
.chrimata-brand{left:24px!important;top:17px!important}.chrimata-brand-title{font-size:28px!important}.chrimata-brand-sub{font-size:13px!important;margin-top:6px!important}
.chrimata-quote{right:26px!important;top:18px!important;font-size:17px!important;width:270px!important}
.chrimata-market-title{margin:1px 0 0!important}.chrimata-market-name{font-size:22px!important}.chrimata-market-flag{font-size:23px!important}.chrimata-market-note{font-size:10px!important;margin:0 0 5px 35px!important}
div[data-testid="stHorizontalBlock"]{gap:.48rem!important}
[data-testid="stTextInput"]{margin-bottom:0!important}
[data-testid="stTextInput"] input{height:35px!important;min-height:35px!important;border-radius:6px!important;font-size:.78rem!important}
div[data-testid="stRadio"] div[role="radiogroup"]{gap:4px!important;margin:0 0 4px!important;flex-wrap:nowrap!important}
div[data-testid="stRadio"] div[role="radiogroup"] label{padding:5px 9px!important;border-radius:6px!important;min-height:35px!important;display:flex!important;align-items:center!important}
div[data-testid="stRadio"] div[role="radiogroup"] p{font-size:.72rem!important;white-space:nowrap!important}
div[data-testid="stMetric"]{min-height:76px!important;padding:7px 10px!important;border-radius:6px!important;background:#fff!important}
div[data-testid="stMetricLabel"] p{font-size:.72rem!important;color:#60738b!important}
div[data-testid="stMetricValue"]{font-size:1.30rem!important;line-height:1.05!important}
div[data-testid="stMetricDelta"]{font-size:.69rem!important}
.stApp h2{font-size:1.15rem!important;margin:.18rem 0 .3rem!important}.stApp h3{font-size:.82rem!important;margin:.18rem 0 .25rem!important;color:#143f88!important}
[data-testid="stDataFrame"]{border:1px solid #e1e8f0!important;border-radius:6px!important;overflow:hidden!important}
[data-testid="stDataFrame"] *{font-size:10.5px!important}
[data-testid="stArrowVegaLiteChart"],[data-testid="stVegaLiteChart"]{border:1px solid #e1e8f0!important;border-radius:6px!important;padding:3px!important}
[data-testid="stAlert"]{padding:.45rem .55rem!important;font-size:.7rem!important}
.chrimata-section-rule{margin:3px 0 5px!important}.chrimata-terminal-footer{margin-top:7px!important;padding:6px 1px!important;font-size:9px!important}
@media(max-width:1100px){[data-testid="stSidebar"]{width:190px!important;min-width:190px!important}.chrimata-quote{display:none!important}div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important}}
</style>
""",unsafe_allow_html=True)

st.markdown("""
<style>
/* V18.2.1 — text metric cards: allow long labels such as Financial Services to fit */
.mia-text-metric-value {
    font-size: clamp(1.15rem, 1.65vw, 1.65rem) !important;
    line-height: 1.15 !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: normal !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown('''
<style>
/* V18.0.3: prevent quote cards from hiding prices with ellipses */
[data-testid="stMetricValue"] {
    font-size: clamp(1.30rem, 1.85vw, 2.15rem) !important;
    line-height: 1.12 !important;
    min-width: 0 !important;
}
[data-testid="stMetricValue"] > div {
    overflow: visible !important;
    text-overflow: clip !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: normal !important;
    min-width: 0 !important;
}
[data-testid="stMetricDelta"] {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
[data-testid="stMetric"] {
    min-width: 0 !important;
}
[data-testid="stMetric"] label,
[data-testid="stMetricLabel"] {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
}
</style>
''', unsafe_allow_html=True)
st.markdown("""
<style>
:root{
 --mia-blue:#2457D6; --mia-blue2:#173B91; --mia-ink:#0F172A; --mia-muted:#64748B;
 --mia-line:#E2E8F0; --mia-soft:#F8FAFC; --mia-card:#FFFFFF; --mia-green:#067647;
}
.stApp{background:linear-gradient(180deg,#F8FAFC 0,#FFFFFF 240px);color:var(--mia-ink);}
.block-container{max-width:1500px;padding-top:1.35rem;padding-bottom:4rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#153B96 0%,#2457D6 58%,#173B91 100%);border-right:0;}
[data-testid="stSidebar"] *{color:#fff!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{
 color:#0F172A!important;background:#fff!important;border-radius:10px!important;}
[data-testid="stSidebar"] [role="radiogroup"] label{
 padding:.48rem .58rem;border-radius:9px;margin:.08rem 0;transition:.15s ease;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.12);}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.18);}
h1{font-size:2rem!important;letter-spacing:-.035em;color:#0F172A!important;}
h2{font-size:1.35rem!important;letter-spacing:-.02em;color:#172554!important;}
h3{font-size:1.05rem!important;color:#1E3A8A!important;}
div[data-testid="stMetric"]{
 background:rgba(255,255,255,.96);border:1px solid var(--mia-line);border-top:0;
 border-radius:14px;padding:14px 16px;box-shadow:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(15,23,42,.035);}
div[data-testid="stMetric"]:hover{border-color:#BFDBFE;box-shadow:0 8px 28px rgba(37,87,214,.08);}
[data-testid="stMetricLabel"]{color:#64748B!important;font-weight:650!important;}
.stButton>button{background:#2457D6;color:#fff;border:1px solid #2457D6;border-radius:10px;font-weight:650;min-height:2.55rem;}
.stButton>button:hover{background:#173B91;color:#fff;border-color:#173B91;box-shadow:0 5px 14px rgba(36,87,214,.18);}
.stDownloadButton>button{border-radius:10px;}
[data-baseweb="tab-list"]{gap:.35rem;border-bottom:1px solid #E2E8F0;}
button[data-baseweb="tab"]{border-radius:9px 9px 0 0;padding-left:1rem;padding-right:1rem;}
[data-baseweb="tab-highlight"]{background:#2457D6!important;}
[data-testid="stDataFrame"]{border:1px solid #E2E8F0;border-radius:12px;overflow:hidden;}
[data-testid="stExpander"]{border:1px solid #E2E8F0!important;border-radius:12px!important;background:#fff;}
[data-testid="stAlert"]{border-radius:12px;}
a{color:#2457D6;}
.mia-shell-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;padding:2px 0 16px;border-bottom:1px solid #E2E8F0;margin-bottom:18px;}
.mia-eyebrow{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:#2457D6;}
.mia-shell-title{font-size:1.62rem;line-height:1.1;font-weight:800;letter-spacing:-.035em;color:#0F172A;margin-top:4px;}
.mia-shell-sub{font-size:.88rem;color:#64748B;margin-top:5px;}
.mia-live{display:inline-flex;align-items:center;gap:7px;border:1px solid #DCE7FF;background:#F4F7FF;border-radius:999px;padding:6px 10px;font-size:.76rem;font-weight:700;color:#2457D6;}
.mia-dot{width:7px;height:7px;border-radius:50%;background:#16A34A;display:inline-block;}
.mia-hero{background:linear-gradient(135deg,#0F2E75,#2457D6);border-radius:18px;padding:22px 24px;color:#fff;margin:2px 0 18px;box-shadow:0 14px 35px rgba(23,59,145,.18);}
.mia-hero-kicker{font-size:.72rem;text-transform:uppercase;letter-spacing:.12em;font-weight:800;opacity:.76;}
.mia-hero-title{font-size:1.65rem;font-weight:800;letter-spacing:-.025em;margin-top:5px;}
.mia-hero-sub{font-size:.9rem;opacity:.82;margin-top:5px;}
.mia-section-label{font-size:.72rem;text-transform:uppercase;letter-spacing:.10em;font-weight:800;color:#64748B;margin:8px 0 2px;}
.company-logo-fallback{width:78px;height:78px;border:1px solid #D9E2FF;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.35rem;font-weight:800;color:#2747A8;background:#F7F9FF;}
.range-row{display:flex;align-items:center;gap:12px;font-size:.92rem;color:#334155;}
.range-track{position:relative;height:10px;background:#E5E7EB;border-radius:99px;flex:1;overflow:visible;}
.range-fill{height:10px;background:#2457D6;border-radius:99px;}
.range-dot{position:absolute;top:50%;width:16px;height:16px;background:#0F172A;border:3px solid white;border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 0 1px #94A3B8;}
@media(max-width:900px){.block-container{padding-left:1rem;padding-right:1rem}.mia-shell-head{align-items:flex-start;flex-direction:column}.mia-hero{padding:18px}}
</style>
""", unsafe_allow_html=True)


# V19.8.5 — robust fixed terminal shell. This deliberately avoids negative offsets.
st.markdown(r"""
<style>
html,body,.stApp,[data-testid="stAppViewContainer"]{margin:0!important;padding:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none!important;height:0!important;}
[data-testid="stAppViewContainer"]>.main{padding-top:0!important;}
.main .block-container{max-width:none!important;width:100%!important;padding:115px .72rem 1rem!important;margin:0!important;}

/* The hero is fixed to the viewport, so it truly spans above BOTH main and sidebar. */
.chrimata-terminal-hero{position:fixed!important;left:0!important;right:0!important;top:0!important;width:100vw!important;height:108px!important;margin:0!important;border-radius:0!important;overflow:hidden!important;background:#062f59!important;box-shadow:none!important;z-index:1000000!important;}
.chrimata-terminal-hero img{display:block!important;width:100%!important;height:108px!important;object-fit:cover!important;object-position:center 47%!important;}
.chrimata-terminal-hero:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(4,30,63,.91) 0%,rgba(4,30,63,.46) 29%,rgba(4,30,63,.06) 61%,rgba(4,30,63,.60) 100%)!important;}
.chrimata-brand{position:absolute!important;z-index:2!important;left:28px!important;top:17px!important;color:white!important}.chrimata-brand-title{font-size:29px!important;line-height:1!important}.chrimata-brand-sub{font-size:13px!important;margin-top:6px!important}.chrimata-quote{position:absolute!important;z-index:2!important;right:32px!important;top:18px!important;font-size:17px!important;width:285px!important;color:white!important}

/* Keep Streamlit sidebar permanently visible below the banner on desktop. */
[data-testid="stSidebar"]{display:block!important;visibility:visible!important;opacity:1!important;transform:none!important;position:fixed!important;left:0!important;top:108px!important;bottom:0!important;height:calc(100vh - 108px)!important;width:214px!important;min-width:214px!important;max-width:214px!important;background:linear-gradient(180deg,#06355f 0%,#073c69 55%,#052e55 100%)!important;border-right:1px solid #0c4b78!important;z-index:999998!important;}
[data-testid="stSidebar"]>div:first-child{display:block!important;width:214px!important;height:100%!important;padding-top:0!important;overflow-y:auto!important;}
[data-testid="stSidebar"] .block-container{padding:.48rem .62rem .8rem!important;}
[data-testid="stSidebarCollapsedControl"],button[data-testid="stSidebarCollapseButton"]{display:none!important;}
[data-testid="stSidebar"] h1{font-size:1.05rem!important;margin:.12rem 0 .35rem!important;color:#fff!important;}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] span{color:#f8fbff!important;}
[data-testid="stSidebar"] div[role="radiogroup"]{display:flex!important;flex-direction:column!important;gap:2px!important;margin:0!important;}
[data-testid="stSidebar"] div[role="radiogroup"] label{background:transparent!important;border:0!important;box-shadow:none!important;border-radius:5px!important;min-height:32px!important;padding:.34rem .45rem!important;color:#fff!important;}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:#1269b5!important;color:#fff!important;}
[data-testid="stSidebar"] div[role="radiogroup"] p{font-size:.71rem!important;font-weight:650!important;color:#fff!important;white-space:normal!important;}
[data-testid="stSidebar"] div[role="radiogroup"] label>div:first-child{display:none!important;}
[data-testid="stSidebar"] details{background:rgba(255,255,255,.04)!important;border:1px solid rgba(255,255,255,.12)!important;}
[data-testid="stSidebar"] input,[data-testid="stSidebar"] textarea{background:#fff!important;color:#0f172a!important;}

/* Main market controls and terminal density. */
.main div[data-testid="stRadio"] div[role="radiogroup"]{display:flex!important;flex-direction:row!important;gap:5px!important;flex-wrap:nowrap!important;margin:0 0 4px!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"] label{background:#fff!important;border:1px solid #dbe4f0!important;border-radius:6px!important;box-shadow:none!important;min-height:35px!important;padding:5px 10px!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked){background:#edf5ff!important;border-color:#1675e5!important;color:#0b63ce!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"] p{font-size:.71rem!important;font-weight:700!important;white-space:nowrap!important;}
.main div[data-testid="stHorizontalBlock"]{gap:.46rem!important;}
.main [data-testid="stTextInput"] input{height:35px!important;min-height:35px!important;border-radius:6px!important;font-size:.76rem!important;}
.main div[data-testid="stMetric"]{min-height:76px!important;padding:7px 10px!important;border:1px solid #dce5ef!important;border-radius:6px!important;box-shadow:none!important;background:#fff!important;}
.main div[data-testid="stMetricValue"]{font-size:1.28rem!important;line-height:1.05!important}.main div[data-testid="stMetricDelta"]{font-size:.68rem!important}.main div[data-testid="stMetricLabel"] p{font-size:.71rem!important;color:#60738b!important;}
.main h2{font-size:1.15rem!important;margin:.18rem 0 .3rem!important}.main h3{font-size:.81rem!important;margin:.16rem 0 .24rem!important;color:#143f88!important;}
.main [data-testid="stDataFrame"]{border:1px solid #e1e8f0!important;border-radius:6px!important;overflow:hidden!important}.main [data-testid="stDataFrame"] *{font-size:10.3px!important;}
.chrimata-market-title{margin:1px 0 0!important}.chrimata-market-name{font-size:22px!important}.chrimata-market-flag{font-size:23px!important}.chrimata-market-note{font-size:10px!important;margin:0 0 5px 35px!important;}

@media(max-width:900px){
 .chrimata-quote{display:none!important;}
 [data-testid="stSidebar"]{width:190px!important;min-width:190px!important;max-width:190px!important;}
 [data-testid="stSidebar"]>div:first-child{width:190px!important;}
 .main div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important;}
}
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
st.markdown("""
<style>
.mia-identity-card{
  min-height:92px;
  height:100%;
  box-sizing:border-box;
  padding:14px 17px;
  background:#fff;
  border:1px solid #E2E8F0;
  border-radius:14px;
  box-shadow:0 1px 2px rgba(15,23,42,.04),0 8px 24px rgba(15,23,42,.035);
  overflow:hidden;
}
.mia-identity-label{
  color:#64748B;
  font-size:.86rem;
  font-weight:500;
  line-height:1.2;
  margin-bottom:7px;
}
.mia-identity-value{
  color:#0F172A;
  font-size:clamp(1.05rem,1.55vw,1.65rem);
  font-weight:400;
  line-height:1.15;
  white-space:normal;
  overflow-wrap:anywhere;
  word-break:normal;
  max-width:100%;
}
@media(max-width:1100px){
  .mia-identity-value{font-size:1.05rem;}
}
</style>
""",unsafe_allow_html=True)

def metric_box(target, label, value, delta=None, **kwargs):
    """Render a Streamlit metric card with contextual hover help."""
    help_text = METRIC_HELP.get(label)
    if help_text and "help" not in kwargs:
        kwargs["help"] = help_text
    return target.metric(label, value, delta=delta, **kwargs)

def text_metric_box(target, label, value, delta=None, **kwargs):
    """Metric card for categorical/text values."""
    value = "—" if value is None or str(value).strip() == "" else str(value)
    return metric_box(target, label, value, delta=delta, **kwargs)

def identity_text_card(target, label, value):
    """Responsive categorical card that wraps long industry/sector names inside its box."""
    import html
    value="—" if value is None or str(value).strip()=="" else str(value)
    help_text=METRIC_HELP.get(label,"")
    target.markdown(
        f"""<div class="mia-identity-card" title="{html.escape(help_text,quote=True)}">
          <div class="mia-identity-label">{html.escape(str(label))}</div>
          <div class="mia-identity-value">{html.escape(value)}</div>
        </div>""", unsafe_allow_html=True)


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



def classify_company(ticker):
    """Best-effort company classification used by KPI templates.

    Returns a stable dictionary even when the market-data provider does not
    supply sector/industry metadata. This prevents Command Centre rendering
    from failing merely because classification data is unavailable.
    """
    sector=""
    industry=""
    name=ticker
    try:
        t=yf.Ticker(ticker)
        info=getattr(t, "info", {}) or {}
        sector=str(info.get("sector") or "")
        industry=str(info.get("industry") or "")
        name=str(info.get("longName") or info.get("shortName") or ticker)
    except Exception:
        pass
    return {"ticker":ticker, "name":name, "sector":sector, "industry":industry}


def safe_company_classification(ticker):
    """Always return a usable company classification dictionary."""
    result={"ticker":str(ticker), "name":str(ticker), "sector":"", "industry":""}
    try:
        # Reuse any existing classifier if it exists and succeeds.
        fn=globals().get("classify_company")
        if callable(fn):
            x=fn(ticker) or {}
            if isinstance(x,dict):
                result.update({k:str(x.get(k) or result.get(k,"")) for k in result})
                return result
    except Exception:
        pass
    try:
        # Optional metadata enrichment only; failure must never break a page.
        if "yf" in globals():
            info=getattr(yf.Ticker(ticker),"info",{}) or {}
            result["name"]=str(info.get("longName") or info.get("shortName") or ticker)
            result["sector"]=str(info.get("sector") or "")
            result["industry"]=str(info.get("industry") or "")
    except Exception:
        pass
    return result

# ---------------- V16 Institutional Workstation ----------------
WORKSPACE_DB="workstation.db"

def ws_db():
    con=sqlite3.connect(WORKSPACE_DB, timeout=10)
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
    try:
        name=(company_name(ticker) if 'company_name' in globals() else ticker)
    except Exception:
        name=ticker
    text=f"{ticker} {name} {sector} {industry}".lower()
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




def display_price(value, ticker="", decimals=None):
    """Compact price formatting that fits metric cards without truncation."""
    try:
        x=float(value)
    except Exception:
        return "—"
    if not np.isfinite(x):
        return "—"
    if decimals is None:
        # Keep cents readable for ordinary equities; retain precision for penny stocks.
        decimals = 3 if abs(x) < 10 else 2
    return f"${x:,.{decimals}f}"


def compact_number(value, prefix="", suffix=""):
    try: x=float(value)
    except Exception: return "—"
    if not np.isfinite(x): return "—"
    ax=abs(x)
    if ax>=1e12: body=f"{x/1e12:.2f}T"
    elif ax>=1e9: body=f"{x/1e9:.2f}B"
    elif ax>=1e6: body=f"{x/1e6:.2f}M"
    elif ax>=1e3: body=f"{x/1e3:.1f}K"
    else: body=f"{x:,.0f}"
    return f"{prefix}{body}{suffix}"


def company_logo_candidates(ticker, meta, size=256):
    """Several independent brand-icon candidates for stronger global coverage."""
    from urllib.parse import urlparse, quote
    meta=meta if isinstance(meta,dict) else {}
    urls=[]
    direct=str(meta.get("logo_url") or meta.get("logoUrl") or "").strip()
    if direct.startswith("http"):
        urls.append(direct)
    website=str(meta.get("website") or "").strip()
    domain=""
    if website.startswith("http"):
        try:
            domain=urlparse(website).netloc.lower().split(":")[0]
            if domain.startswith("www."): domain=domain[4:]
        except Exception:
            domain=""
    if domain:
        urls.extend([
            f"https://www.google.com/s2/favicons?domain={quote(domain)}&sz={int(size)}",
            f"https://icons.duckduckgo.com/ip3/{quote(domain)}.ico",
            f"https://{domain}/favicon.ico",
            f"https://logo.clearbit.com/{quote(domain)}?size={int(size)}",
        ])
    return list(dict.fromkeys([u for u in urls if u]))

def company_logo_url(meta, size=256, ticker=""):
    c=company_logo_candidates(ticker,meta,size)
    return c[0] if c else ""

def company_logo_html(ticker, meta, name, size=78):
    """Try each real logo source in the browser, then fall back to company initials."""
    import html
    candidates=company_logo_candidates(ticker,meta,max(128,size*2))
    initials="".join([x[0] for x in str(name).split()[:2] if x])[:2].upper() or str(ticker)[:2].upper()
    if not candidates:
        return '<div class="company-logo-fallback">'+html.escape(initials)+'</div>'
    src=html.escape(candidates[0],quote=True)
    rest=html.escape("|".join(candidates[1:]),quote=True)
    return (
        '<div class="mia-logo-wrap">'
        '<img src="'+src+'" width="'+str(int(size))+'" height="'+str(int(size))+'" '
        'style="object-fit:contain;border-radius:14px;background:white;padding:5px;border:1px solid #E2E8F0;" '
        'data-fallbacks="'+rest+'" '
        'onerror="var a=this.dataset.fallbacks?this.dataset.fallbacks.split(\'|\'):[];'
        'if(a.length){this.src=a.shift();this.dataset.fallbacks=a.join(\'|\');}'
        'else{this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\';}">'
        '<div class="company-logo-fallback" style="display:none">'+html.escape(initials)+'</div></div>'
    )

def company_snapshot_header(ticker, meta, h, classification_data=None):
    # Reusable security identity + market snapshot.
    if h is None or h.empty: return
    meta=meta if isinstance(meta,dict) else {}
    cls=classification_data or {}
    name=meta.get("longName") or meta.get("shortName") or cls.get("name") or ticker
    sector=meta.get("sector") or cls.get("sector") or "Sector unavailable"
    industry=meta.get("industry") or cls.get("industry") or ""
    market=detect_market(ticker,meta)
    exchange=market.get("exchange") or meta.get("exchange") or "—"
    currency=market.get("currency") or meta.get("currency") or ""
    price=float(h["Close"].iloc[-1])
    prev=float(h["Close"].iloc[-2]) if len(h)>1 else np.nan
    chg=price-prev if np.isfinite(prev) else np.nan
    pct=chg/prev if np.isfinite(prev) and prev else np.nan
    hi=float(h["High"].max()); lo=float(h["Low"].min())
    yr=float(h["Close"].iloc[-1]/h["Close"].iloc[0]-1) if len(h)>1 else np.nan
    vol=float(h["Volume"].iloc[-1]) if "Volume" in h and pd.notna(h["Volume"].iloc[-1]) else meta.get("regularMarketVolume")
    mcap=meta.get("marketCap")
    shares=meta.get("sharesOutstanding") or meta.get("impliedSharesOutstanding")
    pe=meta.get("trailingPE")
    div=meta.get("dividendYield")
    if div is not None:
        try:
            div=float(div)
            if abs(div)>1: div=div/100.0
        except Exception: div=None
    logo=company_logo_url(meta, size=256, ticker=ticker)
    initials="".join([x[0] for x in str(name).split()[:2] if x])[:2].upper() or str(ticker)[:2]

    top=st.container(border=True)
    with top:
        left,right=st.columns([4.6,1.4])
        with left:
            ident_logo,ident_text=st.columns([0.55,5.45],vertical_alignment="center")
            with ident_logo:
                st.markdown(company_logo_html(ticker,meta,name,78),unsafe_allow_html=True)
            with ident_text:
                st.markdown(f"### {name} ({str(ticker).replace('.AX','')})")
                subtitle=f"{ticker} · {exchange} · {sector}"
                st.caption(subtitle + (f" · {industry}" if industry and industry!=sector else ""))
        with right:
            b1,b2=st.columns([3,1])
            if b1.button("＋ Add to Watchlist",key=f"header_watch_{ticker}",use_container_width=True):
                watch_add(ticker,""); st.toast(f"{ticker} added to Watchlist")
            if b2.button("🔔",key=f"header_alert_{ticker}",help="Use Alerts to set a monitoring trigger.",use_container_width=True):
                st.session_state["header_alert_requested"]=ticker; st.toast("Use the Alerts workspace to set the trigger condition.")

        st.caption(f"Market data: Yahoo/yfinance fallback · not exchange-grade real-time · currency {currency or '—'}")
        price_col,m1,m2,m3,m4,m5=st.columns([1.65,1,1,1,1.15,1])
        delta="—" if pd.isna(chg) else f"{chg:+.3f} ({pct:+.2%})"
        price_col.metric("Price",display_price(price,ticker),delta)
        m1.metric("Volume",compact_number(vol)); m2.metric("Market cap",compact_number(mcap,prefix="$"))
        m3.metric("P/E ratio","—" if pe is None or pd.isna(pe) else f"{float(pe):.2f}")
        m4.metric("Dividend yield","—" if div is None or pd.isna(div) else f"{div:.2%}")
        m5.metric("1Y return","—" if pd.isna(yr) else f"{yr:+.2%}")

        st.markdown("**52-week range**")
        pos=50.0 if hi<=lo else max(0.0,min(100.0,(price-lo)/(hi-lo)*100))
        range_html=f'<div class="range-row"><span>{display_price(lo,ticker)}</span><div class="range-track"><div class="range-fill" style="width:{pos:.2f}%"></div><div class="range-dot" style="left:{pos:.2f}%"></div></div><span>{display_price(hi,ticker)}</span></div>'
        st.markdown(range_html,unsafe_allow_html=True)
        st.caption(f"Current price is {pos:.0f}% of the way from the 52-week low to the 52-week high.")

        k1,k2,k3,k4=st.columns(4)
        k1.metric("Ordinary shares",compact_number(shares)); text_metric_box(k2,"Sector",sector); text_metric_box(k3,"Exchange",exchange)
        try: stamp_text=pd.Timestamp(h.index[-1]).strftime("%d %b %Y")
        except Exception: stamp_text="Latest loaded session"
        k4.metric("Latest session",stamp_text)


# ---------------- V18.2 Forecast + Analyst Consensus ----------------
FORECAST_HORIZONS={"1 Month":21,"3 Months":63,"6 Months":126,"12 Months":252}


def _forecast_price_series(df):
    if df is None or len(df)==0 or "Close" not in df:return pd.Series(dtype=float)
    x=df["Close"]
    if isinstance(x,pd.DataFrame):
        x=x.iloc[:,0]
    return pd.to_numeric(x,errors="coerce").replace([np.inf,-np.inf],np.nan).dropna()

def _forecast_features(px):
    """Lagged, price-only features available at forecast origin; no look-ahead inputs."""
    r=px.pct_change()
    f=pd.DataFrame(index=px.index)
    for n in [5,21,63,126,252]:
        f[f"ret_{n}"]=px.pct_change(n)
    f["vol_21"]=r.rolling(21).std()*np.sqrt(252)
    f["vol_63"]=r.rolling(63).std()*np.sqrt(252)
    f["ma_20_gap"]=px/px.rolling(20).mean()-1
    f["ma_50_gap"]=px/px.rolling(50).mean()-1
    f["ma_200_gap"]=px/px.rolling(200).mean()-1
    f["drawdown_252"]=px/px.rolling(252).max()-1
    return f.replace([np.inf,-np.inf],np.nan)

def _ridge_fit_predict(X,y,x0,alpha=10.0):
    """Small deterministic ridge model with training-only standardisation."""
    X=np.asarray(X,dtype=float); y=np.asarray(y,dtype=float); x0=np.asarray(x0,dtype=float)
    mu=np.nanmean(X,axis=0); sd=np.nanstd(X,axis=0); sd=np.where(sd<1e-10,1.0,sd)
    Xs=(X-mu)/sd; x=(x0-mu)/sd
    X1=np.column_stack([np.ones(len(Xs)),Xs])
    reg=np.eye(X1.shape[1])*alpha; reg[0,0]=0
    beta=np.linalg.pinv(X1.T@X1+reg)@(X1.T@y)
    return float(np.r_[1.0,x]@beta)

def _regime_label(px):
    if len(px)<200:return "Insufficient history"
    p=float(px.iloc[-1]); m50=float(px.rolling(50).mean().iloc[-1]); m200=float(px.rolling(200).mean().iloc[-1])
    v=float(px.pct_change().tail(21).std()*np.sqrt(252))
    histv=px.pct_change().rolling(21).std().dropna()*np.sqrt(252)
    highvol=(len(histv)>40 and v>histv.quantile(.70))
    trend="Uptrend" if p>m50>m200 else "Downtrend" if p<m50<m200 else "Mixed trend"
    return f"{trend} / {'High' if highvol else 'Normal'} volatility"

def _walk_forward_horizon(px,h,min_train=252,step=21):
    """Expanding-window out-of-sample test. Every prediction uses only data available at that date."""
    feat=_forecast_features(px)
    target=px.shift(-h)/px-1
    valid=pd.concat([feat,target.rename("y")],axis=1).dropna()
    if len(valid)<min_train+20:return pd.DataFrame()
    rows=[]
    start=min_train
    for i in range(start,len(valid),step):
        train=valid.iloc[:i]
        test=valid.iloc[i]
        if i>=len(valid):break
        X=train[feat.columns].values; y=train["y"].values
        x0=test[feat.columns].values
        try:
            ridge=_ridge_fit_predict(X,y,x0)
            # Momentum model is deliberately simple and independently auditable.
            mom=float(np.nanmean([test.get("ret_21",np.nan),test.get("ret_63",np.nan),test.get("ret_126",np.nan)]))
            # Historical base rate/median from training outcomes.
            hist=float(np.nanmedian(y))
            ensemble=float(np.nanmean([ridge,mom,hist]))
            actual=float(test["y"])
            rows.append({"Date":valid.index[i],"Actual":actual,"Ridge":ridge,"Momentum":mom,
                         "Historical":hist,"Ensemble":ensemble})
        except Exception:
            continue
    return pd.DataFrame(rows)

def _forecast_diagnostics(bt):
    if bt is None or bt.empty:return {"n":0,"mae":np.nan,"rmse":np.nan,"direction":np.nan,"corr":np.nan}
    a=pd.to_numeric(bt["Actual"],errors="coerce"); p=pd.to_numeric(bt["Ensemble"],errors="coerce")
    ok=a.notna()&p.notna(); a=a[ok]; p=p[ok]
    if len(a)==0:return {"n":0,"mae":np.nan,"rmse":np.nan,"direction":np.nan,"corr":np.nan}
    return {"n":len(a),"mae":float(np.mean(np.abs(a-p))),
            "rmse":float(np.sqrt(np.mean((a-p)**2))),
            "direction":float(np.mean((a>0)==(p>0))),
            "corr":float(a.corr(p)) if len(a)>2 else np.nan}

def _calibration_table(bt,bins=5):
    """Empirical calibration diagnostic; displayed as diagnostic, never promoted to a future probability."""
    if bt is None or len(bt)<20:return pd.DataFrame()
    x=bt.copy()
    # Convert ensemble scores to percentile ranks learned from the backtest sample.
    x["score_pct"]=x["Ensemble"].rank(pct=True)
    try:x["bucket"]=pd.qcut(x["score_pct"],q=min(bins,len(x)//5),duplicates="drop")
    except Exception:return pd.DataFrame()
    out=x.groupby("bucket",observed=True).agg(
        Observations=("Actual","size"),
        Mean_model_score=("Ensemble","mean"),
        Realised_mean_return=("Actual","mean"),
        Realised_positive_frequency=("Actual",lambda z:float((z>0).mean()))
    ).reset_index()
    out["Score bucket"]=out["bucket"].astype(str)
    return out.drop(columns=["bucket"])

def advanced_forecast_snapshot(df):
    """Walk-forward tested multi-model research forecast for 1M/3M/6M/12M."""
    px=_forecast_price_series(df)
    cols=["Horizon","Days","Current price","Ensemble expected return","Estimated price",
          "Historical 20%","Historical 80%","Backtest N","MAE","RMSE","Direction accuracy",
          "Return correlation","Regime","Status"]
    if len(px)<300:return pd.DataFrame(columns=cols),{}
    current=float(px.iloc[-1]); feat=_forecast_features(px).dropna()
    if feat.empty:return pd.DataFrame(columns=cols),{}
    x0=feat.iloc[-1]
    rows=[]; backtests={}
    for label,h in FORECAST_HORIZONS.items():
        target=px.shift(-h)/px-1
        train=pd.concat([_forecast_features(px),target.rename("y")],axis=1).dropna()
        # Exclude last h rows where outcome is not known at current origin.
        train=train.loc[train.index<=px.index[-min(h+1,len(px))]]
        if len(train)<150:
            rows.append([label,h,current,np.nan,np.nan,np.nan,np.nan,0,np.nan,np.nan,np.nan,np.nan,_regime_label(px),"Insufficient history"])
            continue
        try:
            ridge=_ridge_fit_predict(train.drop(columns=["y"]).values,train["y"].values,x0.values)
            mom=float(np.nanmean([x0.get("ret_21",np.nan),x0.get("ret_63",np.nan),x0.get("ret_126",np.nan)]))
            hist=float(np.nanmedian(train["y"].values))
            pred=float(np.nanmean([ridge,mom,hist]))
            vals=train["y"].to_numpy(float)
            lo=float(np.nanquantile(vals,.20)); hi=float(np.nanquantile(vals,.80))
            bt=_walk_forward_horizon(px,h); backtests[label]=bt
            d=_forecast_diagnostics(bt)
            status="Research model" if d["n"]>=12 else "Limited validation"
            rows.append([label,h,current,pred,current*(1+pred),current*(1+lo),current*(1+hi),
                         d["n"],d["mae"],d["rmse"],d["direction"],d["corr"],_regime_label(px),status])
        except Exception:
            rows.append([label,h,current,np.nan,np.nan,np.nan,np.nan,0,np.nan,np.nan,np.nan,np.nan,_regime_label(px),"Model unavailable"])
    return pd.DataFrame(rows,columns=cols),backtests

def render_advanced_forecasting(ticker,h):
    st.header(f"Advanced Forecasting — {ticker}")
    st.caption("Walk-forward tested ensemble research. Outputs are model estimates, not price promises or investment recommendations.")
    fc,bts=advanced_forecast_snapshot(h)
    if fc.empty:
        st.info("At least roughly 300 trading sessions are required for the advanced model.")
        return
    show=fc.copy()
    for c in ["Current price","Estimated price","Historical 20%","Historical 80%"]:
        show[c]=show[c].map(lambda x:"—" if pd.isna(x) else display_price(x,ticker))
    for c in ["Ensemble expected return","MAE","RMSE","Direction accuracy","Return correlation"]:
        show[c]=show[c].map(lambda x:"—" if pd.isna(x) else (f"{x:.2f}" if c=="Return correlation" else f"{x:.1%}"))
    st.dataframe(show,use_container_width=True,hide_index=True)
    st.caption("Ensemble = ridge regression + momentum model + historical median. Features are lagged price/volatility/trend observations available at the forecast origin.")

    horizon=st.selectbox("Validation horizon",list(FORECAST_HORIZONS.keys()),key="adv_fc_horizon")
    bt=bts.get(horizon,pd.DataFrame())
    st.subheader("Walk-forward validation")
    if bt is None or bt.empty:
        st.info("Not enough out-of-sample observations for this horizon.")
    else:
        d=_forecast_diagnostics(bt)
        c=st.columns(4)
        metric_box(c[0],"Out-of-sample tests",str(d["n"]))
        metric_box(c[1],"MAE",f"{d['mae']:.1%}" if pd.notna(d["mae"]) else "—")
        metric_box(c[2],"Direction accuracy",f"{d['direction']:.1%}" if pd.notna(d["direction"]) else "—")
        metric_box(c[3],"Return correlation",f"{d['corr']:.2f}" if pd.notna(d["corr"]) else "—")
        chart=bt[["Actual","Ensemble"]].copy()
        st.line_chart(chart)
        with st.expander("Out-of-sample predictions"):
            st.dataframe(bt,use_container_width=True,hide_index=True)

        st.subheader("Calibration diagnostic")
        cal=_calibration_table(bt)
        if cal.empty:
            st.info("There are too few out-of-sample observations to show a useful calibration diagnostic.")
        else:
            st.dataframe(cal.style.format({
                "Mean_model_score":"{:+.1%}","Realised_mean_return":"{:+.1%}",
                "Realised_positive_frequency":"{:.1%}"},na_rep="—"),use_container_width=True,hide_index=True)
            st.warning("Realised positive frequency is a historical out-of-sample diagnostic. V19.4 does NOT label it as a calibrated future probability.")

    st.subheader("Model architecture")
    st.write("Ridge model: lagged 1W/1M/3M/6M/12M returns, 21D/63D volatility, moving-average gaps and trailing drawdown.")
    st.write("Momentum model: independent recent-return signal.")
    st.write("Historical model: median known forward return at the forecast horizon.")
    st.write("Validation: expanding-window walk-forward tests; each test prediction uses only information available at that test date.")
    st.write("Regime context: trend relative to 50D/200D averages plus current volatility relative to its own history.")
    st.info("Fundamental/report and analyst data remain displayed as separate evidence in V19.4 rather than being forced into the price model without reliable point-in-time historical datasets. This avoids look-ahead bias.")

def research_forecast(df):
    """Transparent historical-distribution forecast; research only, not a recommendation."""
    cols=["Horizon","Days","Current price","Median forecast","Low case (20%)","High case (80%)",
          "Median return","Positive-return frequency","Sample size","Method"]
    try:
        px=pd.to_numeric(df["Close"],errors="coerce").dropna()
        if len(px)<80: return pd.DataFrame(columns=cols)
        current=float(px.iloc[-1])
        rows=[]
        for label,h in FORECAST_HORIZONS.items():
            # Non-overlapping-ish rolling horizon outcomes sampled every 5 sessions to reduce duplication.
            fwd=(px.shift(-h)/px-1).dropna().iloc[::5]
            if len(fwd)<12:
                rows.append([label,h,current,np.nan,np.nan,np.nan,np.nan,np.nan,len(fwd),"Insufficient history"])
                continue
            # Weight recent observations more, while remaining entirely historical and auditable.
            vals=fwd.to_numpy(dtype=float)
            n=len(vals)
            weights=np.linspace(0.5,1.5,n); weights=weights/weights.sum()
            # Deterministic weighted quantile helper.
            order=np.argsort(vals); sv=vals[order]; sw=weights[order]; cw=np.cumsum(sw)
            def wq(q): return float(np.interp(q,cw,sv))
            med=wq(.50); lo=wq(.20); hi=wq(.80)
            pos=float(weights[vals>0].sum())
            rows.append([label,h,current,current*(1+med),current*(1+lo),current*(1+hi),
                         med,pos,n,"Recency-weighted historical horizon returns"])
        return pd.DataFrame(rows,columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def analyst_consensus_snapshot(ticker):
    """Best-effort Yahoo/yfinance analyst consensus. This reports analysts' views, not the app's rating."""
    out={"label":"Unavailable","strongBuy":0,"buy":0,"hold":0,"sell":0,"strongSell":0,
         "analysts":0,"target_low":np.nan,"target_mean":np.nan,"target_median":np.nan,
         "target_high":np.nan,"source":"Yahoo Finance via yfinance"}
    try:
        t=yf.Ticker(ticker)
        rec=t.get_recommendations()
        if rec is None or len(rec)==0:
            rec=getattr(t,"recommendations_summary",None)
        if rec is not None and len(rec):
            r=rec.iloc[0]
            for k in ["strongBuy","buy","hold","sell","strongSell"]:
                try: out[k]=int(float(r.get(k,0) or 0))
                except Exception: out[k]=0
            total=sum(out[k] for k in ["strongBuy","buy","hold","sell","strongSell"])
            out["analysts"]=total
            if total:
                # Consensus is the plurality of published analyst categories; ties are Hold.
                counts={k:out[k] for k in ["strongBuy","buy","hold","sell","strongSell"]}
                mx=max(counts.values()); winners=[k for k,v in counts.items() if v==mx]
                labels={"strongBuy":"Strong Buy","buy":"Buy","hold":"Hold","sell":"Sell","strongSell":"Strong Sell"}
                out["label"]=labels[winners[0]] if len(winners)==1 else "Hold"
        try:
            pt=t.get_analyst_price_targets()
            if isinstance(pt,dict):
                for src_key,dst in [("low","target_low"),("mean","target_mean"),("median","target_median"),("high","target_high")]:
                    v=pt.get(src_key)
                    out[dst]=float(v) if v is not None else np.nan
        except Exception:
            pass
    except Exception:
        pass
    return out

def render_analyst_consensus(ticker,price):
    a=analyst_consensus_snapshot(ticker)
    st.subheader("Analyst consensus")
    st.caption("External analyst consensus reported by Yahoo Finance via yfinance. This is not Chrímata's recommendation.")
    c=st.columns(4)
    metric_box(c[0],"Consensus",a["label"])
    metric_box(c[1],"Analysts",str(a["analysts"]) if a["analysts"] else "—")
    metric_box(c[2],"Mean target","—" if pd.isna(a["target_mean"]) else display_price(a["target_mean"],ticker))
    upside=(a["target_mean"]/price-1) if price and not pd.isna(a["target_mean"]) else np.nan
    metric_box(c[3],"Mean target vs price","—" if pd.isna(upside) else f"{upside*100:+.1f}%")
    dist=pd.DataFrame({
        "Rating":["Strong Buy","Buy","Hold","Sell","Strong Sell"],
        "Analysts":[a["strongBuy"],a["buy"],a["hold"],a["sell"],a["strongSell"]]
    })
    st.dataframe(dist,use_container_width=True,hide_index=True)
    if not all(pd.isna(a[k]) for k in ["target_low","target_mean","target_median","target_high"]):
        st.dataframe(pd.DataFrame([{
            "Low target":"—" if pd.isna(a["target_low"]) else display_price(a["target_low"],ticker),
            "Mean target":"—" if pd.isna(a["target_mean"]) else display_price(a["target_mean"],ticker),
            "Median target":"—" if pd.isna(a["target_median"]) else display_price(a["target_median"],ticker),
            "High target":"—" if pd.isna(a["target_high"]) else display_price(a["target_high"],ticker),
        }]),use_container_width=True,hide_index=True)
    if a["analysts"]==0 and all(pd.isna(a[k]) for k in ["target_low","target_mean","target_median","target_high"]):
        st.info("No analyst consensus or price-target data is available from the current provider for this security.")

def render_forecast_tool(ticker,h):
    st.header("Forecast Research")
    st.caption("1M / 3M / 6M / 12M scenario research based on historical horizon returns. It is not a price promise or investment recommendation.")
    fc=research_forecast(h)
    if fc.empty:
        st.info("Not enough price history is available to calculate forecast scenarios.")
        return
    show=fc.copy()
    for c in ["Current price","Median forecast","Low case (20%)","High case (80%)"]:
        show[c]=show[c].map(lambda x:"—" if pd.isna(x) else display_price(x,ticker))
    for c in ["Median return","Positive-return frequency"]:
        show[c]=show[c].map(lambda x:"—" if pd.isna(x) else f"{x*100:.1f}%")
    st.dataframe(show,use_container_width=True,hide_index=True)
    st.caption("Low/high cases are the 20th/80th percentiles of historical forward returns for the same horizon, with modest recency weighting. Positive-return frequency is historical, not a calibrated probability of the future.")
    # Visual forecast path using horizon medians.
    valid=fc.dropna(subset=["Median forecast"])
    if not valid.empty:
        # Build the month axis from the horizons that actually have a forecast.
        # This avoids unequal-length arrays when one or more horizons are unavailable.
        horizon_months={"1 Month":1,"3 Months":3,"6 Months":6,"12 Months":12}
        current_price=float(fc["Current price"].iloc[0])
        months=[0]
        prices=[current_price]
        for _, row in valid.iterrows():
            month=horizon_months.get(str(row["Horizon"]))
            forecast_price=row["Median forecast"]
            if month is not None and pd.notna(forecast_price):
                months.append(month)
                prices.append(float(forecast_price))
        if len(months)>1 and len(months)==len(prices):
            chart=pd.DataFrame({"Months":months,"Price":prices})
            chart=chart.sort_values("Months").drop_duplicates("Months",keep="last")
            st.line_chart(chart.set_index("Months"))
        else:
            st.info("A forecast path chart is not available for the current data, but the forecast table above remains valid.")

# ---------------- V18 Investment Intelligence Layer ----------------
def v18_db_upgrade():
    v17_db_upgrade()
    con=ws_db()

    # Forward-compatible SQLite migrations. CREATE TABLE IF NOT EXISTS does not
    # add columns to an existing table from an older deployed version.
    def ensure_columns(table, columns):
        try:
            existing={r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()}
            for name, sql_type in columns.items():
                if name not in existing:
                    con.execute(f'ALTER TABLE {table} ADD COLUMN "{name}" {sql_type}')
        except Exception:
            pass

    ensure_columns("catalysts", {
        "ticker":"TEXT","event_date":"TEXT","event":"TEXT","category":"TEXT",
        "status":"TEXT","source":"TEXT"
    })
    ensure_columns("thesis_rules", {
        "ticker":"TEXT","metric":"TEXT","operator":"TEXT","threshold":"REAL",
        "current_value":"REAL","status":"TEXT","source":"TEXT","updated_at":"TEXT"
    })
    ensure_columns("alerts", {
        "ticker":"TEXT","metric":"TEXT","operator":"TEXT","threshold":"REAL",
        "enabled":"INTEGER","notes":"TEXT"
    })
    ensure_columns("kpi_observations", {
        "ticker":"TEXT","metric":"TEXT","period":"TEXT","value":"REAL","unit":"TEXT",
        "source":"TEXT","source_url":"TEXT","evidence_note":"TEXT","observed_at":"TEXT"
    })
    ensure_columns("valuation_profiles", {
        "ticker":"TEXT","fcf":"REAL","shares":"REAL","net_debt":"REAL",
        "bear_growth":"REAL","base_growth":"REAL","bull_growth":"REAL",
        "bear_wacc":"REAL","base_wacc":"REAL","bull_wacc":"REAL",
        "bear_terminal":"REAL","base_terminal":"REAL","bull_terminal":"REAL",
        "updated_at":"TEXT"
    })
    ensure_columns("report_reviews", {
        "ticker":"TEXT","reviewed_at":"TEXT","title":"TEXT","source":"TEXT","notes":"TEXT"
    })
    ensure_columns("portfolio_holdings", {
        "ticker":"TEXT","quantity":"REAL","avg_cost":"REAL","source":"TEXT","updated_at":"TEXT"
    })
    ensure_columns("thesis_snapshots", {
        "ticker":"TEXT","snapshot_at":"TEXT","metric":"TEXT","current_value":"REAL",
        "status":"TEXT","source":"TEXT"
    })
    ensure_columns("review_log", {
        "ticker":"TEXT","reviewed_at":"TEXT","amount":"REAL","price":"REAL",
        "shares_before":"REAL","avg_cost_before":"REAL","shares_after":"REAL",
        "avg_cost_after":"REAL","notes":"TEXT"
    })

    con.execute("""CREATE TABLE IF NOT EXISTS kpi_observations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,metric TEXT,period TEXT,value REAL,
        unit TEXT,source TEXT,source_url TEXT,evidence_note TEXT,observed_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS valuation_profiles(
        ticker TEXT PRIMARY KEY,fcf REAL,shares REAL,net_debt REAL,bear_growth REAL,base_growth REAL,
        bull_growth REAL,bear_wacc REAL,base_wacc REAL,bull_wacc REAL,bear_terminal REAL,
        base_terminal REAL,bull_terminal REAL,updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS report_reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,reviewed_at TEXT,title TEXT,source TEXT,notes TEXT)""")
    con.commit(); con.close()

def kpi_observations(ticker):
    v18_db_upgrade(); con=ws_db()
    cols=["id","metric","period","value","unit","source","source_url","evidence_note","observed_at"]
    try:
        d=pd.read_sql_query("""SELECT id,metric,period,value,unit,source,source_url,evidence_note,observed_at
                               FROM kpi_observations WHERE ticker=? ORDER BY metric,observed_at DESC,id DESC""",
                            con,params=(ticker,))
        return d
    except Exception:
        return pd.DataFrame(columns=cols)
    finally:
        con.close()

def kpi_latest_comparison(ticker):
    d=kpi_observations(ticker)
    if d.empty:return pd.DataFrame(columns=["Metric","Previous","Latest","Unit","Change","Source","Evidence"])
    rows=[]
    for metric,g in d.groupby("metric",sort=False):
        g=g.sort_values(["observed_at","id"],ascending=False)
        latest=g.iloc[0]; prev=g.iloc[1] if len(g)>1 else None
        lv=float(latest["value"]); pv=float(prev["value"]) if prev is not None else np.nan
        ch="New evidence" if pd.isna(pv) else ("↑ Increased" if lv>pv else "↓ Decreased" if lv<pv else "→ Unchanged")
        rows.append({"Metric":metric,"Previous":pv,"Latest":lv,"Unit":latest["unit"] or "",
                     "Change":ch,"Source":latest["source"] or "Manual evidence",
                     "Evidence":latest["evidence_note"] or ""})
    return pd.DataFrame(rows)

def save_kpi_observation(ticker,metric,period,value,unit,source,source_url="",note=""):
    v18_db_upgrade(); con=ws_db()
    con.execute("""INSERT INTO kpi_observations(ticker,metric,period,value,unit,source,source_url,evidence_note,observed_at)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (ticker,metric,period,float(value),unit,source,source_url,note,datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

def valuation_profile(ticker):
    v18_db_upgrade(); con=ws_db()
    row=con.execute("""SELECT fcf,shares,net_debt,bear_growth,base_growth,bull_growth,bear_wacc,base_wacc,bull_wacc,
                      bear_terminal,base_terminal,bull_terminal FROM valuation_profiles WHERE ticker=?""",(ticker,)).fetchone()
    con.close()
    if row:
        keys=["fcf","shares","net_debt","bear_growth","base_growth","bull_growth","bear_wacc","base_wacc","bull_wacc",
              "bear_terminal","base_terminal","bull_terminal"]
        return dict(zip(keys,map(float,row)))
    return {"fcf":100_000_000.0,"shares":1_000_000_000.0,"net_debt":0.0,
            "bear_growth":.04,"base_growth":.10,"bull_growth":.16,
            "bear_wacc":.12,"base_wacc":.10,"bull_wacc":.09,
            "bear_terminal":.02,"base_terminal":.03,"bull_terminal":.035}

def save_valuation_profile(ticker,p):
    v18_db_upgrade(); con=ws_db()
    con.execute("""INSERT INTO valuation_profiles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(ticker) DO UPDATE SET fcf=excluded.fcf,shares=excluded.shares,net_debt=excluded.net_debt,
                   bear_growth=excluded.bear_growth,base_growth=excluded.base_growth,bull_growth=excluded.bull_growth,
                   bear_wacc=excluded.bear_wacc,base_wacc=excluded.base_wacc,bull_wacc=excluded.bull_wacc,
                   bear_terminal=excluded.bear_terminal,base_terminal=excluded.base_terminal,bull_terminal=excluded.bull_terminal,
                   updated_at=excluded.updated_at""",
                (ticker,p["fcf"],p["shares"],p["net_debt"],p["bear_growth"],p["base_growth"],p["bull_growth"],
                 p["bear_wacc"],p["base_wacc"],p["bull_wacc"],p["bear_terminal"],p["base_terminal"],p["bull_terminal"],
                 datetime.now(timezone.utc).isoformat()))
    con.commit(); con.close()

def valuation_snapshot(ticker,price):
    p=valuation_profile(ticker)
    assumptions={"Bear":{"growth":p["bear_growth"],"wacc":p["bear_wacc"],"terminal_growth":p["bear_terminal"]},
                 "Base":{"growth":p["base_growth"],"wacc":p["base_wacc"],"terminal_growth":p["base_terminal"]},
                 "Bull":{"growth":p["bull_growth"],"wacc":p["bull_wacc"],"terminal_growth":p["bull_terminal"]}}
    try:
        v=scenarios(p["fcf"],p["shares"],p["net_debt"],assumptions)
        if "scenario" not in [str(x).lower() for x in v.columns]:
            v=v.reset_index().rename(columns={"index":"Scenario"})
        v["Margin of safety"]=v["value_per_share"].map(lambda x:margin_of_safety(price,x))
        return v
    except Exception:
        return pd.DataFrame()

def reverse_targets(ticker,targets=(3,4,5,6)):
    p=valuation_profile(ticker); rows=[]
    for target in targets:
        try:g=implied_growth(float(target),p["fcf"],p["shares"],p["net_debt"],p["base_wacc"],p["base_terminal"])
        except Exception:g=np.nan
        rows.append({"Target price":float(target),"Implied 5Y FCF growth":g})
    return pd.DataFrame(rows)

def relative_strength_snapshot(ticker,df):
    if df is None or df.empty:return {}
    bench="^AXJO" if ticker.upper().endswith(".AX") else "^GSPC"
    b=history(bench,"1y")
    def ret(x,n):
        return np.nan if x is None or x.empty or len(x)<n+1 else float(x["Close"].iloc[-1]/x["Close"].iloc[-n-1]-1)
    return {"Benchmark":bench,"Stock 3M":ret(df,63),"Benchmark 3M":ret(b,63),
            "Relative 3M":ret(df,63)-ret(b,63) if pd.notna(ret(df,63)) and pd.notna(ret(b,63)) else np.nan,
            "Stock 6M":ret(df,126),"Benchmark 6M":ret(b,126),
            "Relative 6M":ret(df,126)-ret(b,126) if pd.notna(ret(df,126)) and pd.notna(ret(b,126)) else np.nan}

def technical_regime(df,ticker):
    if df is None or df.empty:return {}
    ms=market_structure(df); conf=confluence_snapshot(df)
    states=conf["State"].tolist() if not conf.empty and "State" in conf else []
    pos=sum(x=="Positive" for x in states); neg=sum(x=="Negative" for x in states)
    trend="Improving / constructive" if pos>neg else "Weak / defensive" if neg>pos else "Mixed"
    vol=np.nan
    try: vol=float(df["Close"].pct_change().tail(20).std()*np.sqrt(252))
    except: pass
    rs=relative_strength_snapshot(ticker,df)
    return {"Trend":trend,"Support":ms.get("20D support"),"Resistance":ms.get("20D resistance"),
            "Volume ratio":ms.get("Volume vs 20D"),"Annualised volatility":vol,**rs}


def _mia_num(v):
    try:
        x=float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan

def _mia_component(label, value, score, evidence, source="Market/fundamental provider"):
    return {"Metric":label,"Value":value,"Points":float(max(0,min(100,score))),
            "Evidence":evidence,"Source":source}

def _mia_linear(v, bad, good, reverse=False):
    """Transparent bounded 0-100 linear score. No hidden model weights."""
    v=_mia_num(v)
    if not np.isfinite(v): return np.nan
    if good==bad:return 50.0
    z=(v-bad)/(good-bad)
    z=max(0.0,min(1.0,z))
    out=100*z
    return 100-out if reverse else out

def mia_research_score(ticker,h,meta=None):
    """Explainable research score. Missing evidence stays N/A; it is not a recommendation."""
    if meta is None:
        try: meta=yf.Ticker(ticker).info or {}
        except Exception: meta={}
    meta=meta if isinstance(meta,dict) else {}
    evidence={}
    scores={}
    px=pd.to_numeric(h["Close"],errors="coerce").dropna() if h is not None and not h.empty and "Close" in h else pd.Series(dtype=float)
    price=float(px.iloc[-1]) if not px.empty else np.nan

    # 1. Financial quality
    rows=[]
    pm=_mia_num(meta.get("profitMargins")); om=_mia_num(meta.get("operatingMargins"))
    roe=_mia_num(meta.get("returnOnEquity")); roa=_mia_num(meta.get("returnOnAssets"))
    if np.isfinite(pm): rows.append(_mia_component("Profit margin",f"{pm:.1%}",_mia_linear(pm,-.05,.25),f"Provider-reported profit margin {pm:.1%}."))
    if np.isfinite(om): rows.append(_mia_component("Operating margin",f"{om:.1%}",_mia_linear(om,-.05,.25),f"Provider-reported operating margin {om:.1%}."))
    if np.isfinite(roe): rows.append(_mia_component("Return on equity",f"{roe:.1%}",_mia_linear(roe,-.05,.30),f"Provider-reported ROE {roe:.1%}."))
    if np.isfinite(roa): rows.append(_mia_component("Return on assets",f"{roa:.1%}",_mia_linear(roa,-.03,.15),f"Provider-reported ROA {roa:.1%}."))
    evidence["Financial Quality"]=pd.DataFrame(rows)
    scores["Financial Quality"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=2 else np.nan

    # 2. Growth
    rows=[]
    rg=_mia_num(meta.get("revenueGrowth")); eg=_mia_num(meta.get("earningsGrowth"))
    if np.isfinite(rg): rows.append(_mia_component("Revenue growth",f"{rg:+.1%}",_mia_linear(rg,-.10,.30),f"Provider-reported revenue growth {rg:+.1%}."))
    if np.isfinite(eg): rows.append(_mia_component("Earnings growth",f"{eg:+.1%}",_mia_linear(eg,-.20,.40),f"Provider-reported earnings growth {eg:+.1%}."))
    if len(px)>252:
        r12=float(price/px.iloc[-253]-1)
        rows.append(_mia_component("12M market performance",f"{r12:+.1%}",_mia_linear(r12,-.30,.50),f"Trailing 252-session price return {r12:+.1%}.","Price history"))
    evidence["Growth"]=pd.DataFrame(rows)
    scores["Growth"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=2 else np.nan

    # 3. Valuation — uses observable multiples/yield only; DCF remains a separate user model.
    rows=[]
    pe=_mia_num(meta.get("trailingPE")); fpe=_mia_num(meta.get("forwardPE"))
    ev=_mia_num(meta.get("enterpriseToEbitda")); fcf=_mia_num(meta.get("freeCashflow")); mcap=_mia_num(meta.get("marketCap"))
    if np.isfinite(pe) and pe>0: rows.append(_mia_component("Trailing P/E",f"{pe:.1f}×",_mia_linear(pe,45,10,False),f"Trailing P/E {pe:.1f}×; lower positive multiples receive more points under this generic rule."))
    if np.isfinite(fpe) and fpe>0: rows.append(_mia_component("Forward P/E",f"{fpe:.1f}×",_mia_linear(fpe,40,10,False),f"Forward P/E {fpe:.1f}×; lower positive multiples receive more points under this generic rule."))
    if np.isfinite(ev) and ev>0: rows.append(_mia_component("EV / EBITDA",f"{ev:.1f}×",_mia_linear(ev,30,6,False),f"EV/EBITDA {ev:.1f}×; lower positive multiples receive more points under this generic rule."))
    if np.isfinite(fcf) and np.isfinite(mcap) and mcap>0:
        fy=fcf/mcap
        rows.append(_mia_component("FCF / market cap",f"{fy:.1%}",_mia_linear(fy,-.02,.10),f"Free cash flow divided by market capitalisation is {fy:.1%}."))
    evidence["Valuation"]=pd.DataFrame(rows)
    scores["Valuation"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=2 else np.nan

    # 4. Momentum — price-only, reproducible.
    rows=[]
    for n,label,bad,good in [(21,"1M return",-0.15,0.15),(63,"3M return",-0.25,0.25),(126,"6M return",-0.35,0.40),(252,"12M return",-0.50,0.60)]:
        if len(px)>n:
            r=float(price/px.iloc[-n-1]-1)
            rows.append(_mia_component(label,f"{r:+.1%}",_mia_linear(r,bad,good),f"Trailing {n}-session return {r:+.1%}.","Price history"))
    if len(px)>=200:
        sma50=float(px.tail(50).mean()); sma200=float(px.tail(200).mean())
        gap=price/sma200-1
        rows.append(_mia_component("Price vs 200D",f"{gap:+.1%}",_mia_linear(gap,-.25,.25),f"Price is {gap:+.1%} versus its 200-session average.","Price history"))
        cross=sma50/sma200-1
        rows.append(_mia_component("50D vs 200D",f"{cross:+.1%}",_mia_linear(cross,-.15,.15),f"50-session average is {cross:+.1%} versus 200-session average.","Price history"))
    evidence["Momentum"]=pd.DataFrame(rows)
    scores["Momentum"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=3 else np.nan

    # 5. Balance sheet & risk
    rows=[]
    de=_mia_num(meta.get("debtToEquity")); cr=_mia_num(meta.get("currentRatio")); qr=_mia_num(meta.get("quickRatio"))
    beta=_mia_num(meta.get("beta"))
    if np.isfinite(de): rows.append(_mia_component("Debt / equity",f"{de:.1f}",_mia_linear(de,250,20,False),f"Provider-reported debt/equity {de:.1f}; lower leverage receives more points under this generic rule."))
    if np.isfinite(cr): rows.append(_mia_component("Current ratio",f"{cr:.2f}",_mia_linear(cr,.5,2.0),f"Provider-reported current ratio {cr:.2f}."))
    if np.isfinite(qr): rows.append(_mia_component("Quick ratio",f"{qr:.2f}",_mia_linear(qr,.4,1.5),f"Provider-reported quick ratio {qr:.2f}."))
    if len(px)>63:
        vol=float(px.pct_change().tail(63).std()*np.sqrt(252))
        rows.append(_mia_component("63D annualised volatility",f"{vol:.1%}",_mia_linear(vol,.80,.15,False),f"Annualised volatility from the latest 63 daily returns is {vol:.1%}.","Price history"))
    if np.isfinite(beta): rows.append(_mia_component("Beta",f"{beta:.2f}",_mia_linear(abs(beta-1),1.0,0.0,False),f"Provider beta is {beta:.2f}; this metric rewards proximity to market-like beta, not investment merit."))
    evidence["Balance Sheet & Risk"]=pd.DataFrame(rows)
    scores["Balance Sheet & Risk"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=2 else np.nan

    # 6. Earnings & Thesis Trend — only uses measurable stored/current evidence.
    rows=[]
    try:
        tt=thesis_table(ticker)
    except Exception:
        tt=pd.DataFrame()
    if tt is not None and not tt.empty and "status" in tt:
        total=len(tt); met=int((tt["status"].astype(str)=="Met").sum())
        ratio=met/total if total else np.nan
        if np.isfinite(ratio):
            rows.append(_mia_component("Stored thesis conditions",f"{met}/{total}",ratio*100,
                f"{met} of {total} stored measurable thesis conditions are currently marked Met.","User thesis ledger"))
    if np.isfinite(eg): rows.append(_mia_component("Current earnings growth",f"{eg:+.1%}",_mia_linear(eg,-.20,.40),f"Provider-reported earnings growth {eg:+.1%}."))
    try:
        ae=analyst_evidence(ticker,limit=12)
    except Exception:
        ae=pd.DataFrame()
    if ae is not None and not ae.empty and "Action" in ae:
        acts=ae["Action"].astype(str).str.lower()
        ups=int(acts.str.contains("up|raise|initiated|reiterated").sum())
        downs=int(acts.str.contains("down|lower").sum())
        if ups+downs:
            trend=(ups-downs)/(ups+downs)
            rows.append(_mia_component("Recent analyst actions",f"{ups} positive / {downs} negative",
                _mia_linear(trend,-1,1),f"Directional count from available recent analyst-action records: {ups} positive, {downs} negative.","Analyst action feed"))
    evidence["Earnings & Thesis Trend"]=pd.DataFrame(rows)
    scores["Earnings & Thesis Trend"]=float(np.mean([r["Points"] for r in rows])) if len(rows)>=2 else np.nan

    # Equal-weight available category scores, but require broad coverage.
    available={k:v for k,v in scores.items() if np.isfinite(v)}
    overall=float(np.mean(list(available.values()))) if len(available)>=4 else np.nan
    return {"Overall":overall,"Scores":scores,"Evidence":evidence,"Available":len(available),"Total":len(scores)}

def mia_score_label(score):
    if not np.isfinite(_mia_num(score)):return "N/A"
    if score>=80:return "Very high"
    if score>=65:return "High"
    if score>=50:return "Middle"
    if score>=35:return "Low"
    return "Very low"

def render_mia_research_score(ticker,h,meta=None):
    r=mia_research_score(ticker,h,meta)
    st.subheader("MIA Research Score")
    st.caption("Explainable research scorecard — not a Buy/Sell recommendation. Every category is calculated from visible evidence; insufficient data is shown as N/A.")
    overall=r["Overall"]
    c1,c2,c3=st.columns([1.2,1,2])
    c1.metric("Overall research score",f"{overall:.0f} / 100" if np.isfinite(_mia_num(overall)) else "N/A")
    c2.metric("Evidence coverage",f"{r['Available']} / {r['Total']} categories")
    c3.info("Scores are equal-weighted across available categories only when at least four categories have enough evidence. Generic thresholds are disclosed below and are not sector-specific fair-value rules.")
    cats=list(r["Scores"].keys())
    cols=st.columns(3)
    for j,cat in enumerate(cats):
        sc=r["Scores"][cat]
        with cols[j%3]:
            st.metric(cat,f"{sc:.0f} / 100" if np.isfinite(_mia_num(sc)) else "N/A",
                      mia_score_label(sc) if np.isfinite(_mia_num(sc)) else "Insufficient evidence")
    with st.expander("Show score evidence and calculations",expanded=False):
        for cat in cats:
            st.markdown(f"#### {cat}")
            d=r["Evidence"].get(cat,pd.DataFrame())
            if d is None or d.empty:
                st.caption("N/A — not enough supported inputs to calculate this category.")
            else:
                st.dataframe(d,use_container_width=True,hide_index=True)
        st.markdown("**Methodology:** each input is mapped to a disclosed 0–100 bounded rule, then category inputs are averaged. Categories with insufficient evidence remain N/A. The overall score is the equal-weight average of available category scores only when at least four categories are supported. Valuation thresholds are generic, so the separate valuation/peer tools should be used for sector-specific interpretation.")
    return r

def portfolio_impact(ticker,amount,price):
    hold=holding_for(ticker); qty0=hold["quantity"]; avg0=hold["avg_cost"]
    add=int(float(amount)//price) if price>0 else 0; spend=add*price; qty1=qty0+add
    avg1=((qty0*avg0)+spend)/qty1 if qty1 else 0
    pos=paper_positions_df(); other=0.0
    if not pos.empty:
        for _,r in pos.iterrows():
            if str(r["ticker"])==ticker:continue
            hh=history(str(r["ticker"]),"5d")
            lp=float(hh["Close"].iloc[-1]) if not hh.empty else float(r["avg_cost"])
            other+=float(r["quantity"])*lp
    cash=paper_cash_balance(); mv0=qty0*price; mv1=qty1*price
    d0=mv0+other+cash; d1=mv1+other+max(cash-spend,0)
    return {"qty0":qty0,"avg0":avg0,"mv0":mv0,"add":add,"spend":spend,"qty1":qty1,"avg1":avg1,"mv1":mv1,
            "weight0":mv0/d0 if d0 else np.nan,"weight1":mv1/d1 if d1 else np.nan}

def catalysts_safe(ticker,limit=8):
    v18_db_upgrade()
    cols=["event_date","event","category","status","source"]
    con=ws_db()
    try:
        d=pd.read_sql_query(
            f"""SELECT event_date,event,category,status,source
                FROM catalysts WHERE ticker=? ORDER BY event_date LIMIT {int(limit)}""",
            con, params=(ticker,))
        return d
    except Exception:
        return pd.DataFrame(columns=cols)
    finally:
        con.close()

def latest_announcements_safe(ticker,limit=5):
    try:
        d=announcements(ticker)
        if d is None or d.empty:return pd.DataFrame()
        return d.head(limit)
    except Exception:
        return pd.DataFrame()



def v19_phase4_db_upgrade():
    """Persistent report metadata, extracted evidence and user-confirmed KPI observations."""
    v18_db_upgrade()
    con=ws_db()
    con.execute("""CREATE TABLE IF NOT EXISTS report_intelligence(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,created_at TEXT,title TEXT,period TEXT,
        source TEXT,source_url TEXT,file_name TEXT,document_hash TEXT,summary TEXT,
        raw_text TEXT,confirmed INTEGER DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS report_kpi_candidates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,report_id INTEGER,ticker TEXT,metric TEXT,
        value REAL,unit TEXT,evidence TEXT,page_hint TEXT,confirmed INTEGER DEFAULT 0)""")
    con.execute("""CREATE INDEX IF NOT EXISTS idx_report_intel_ticker ON report_intelligence(ticker,id)""")
    con.execute("""CREATE INDEX IF NOT EXISTS idx_report_kpi_report ON report_kpi_candidates(report_id,id)""")
    con.commit(); con.close()

def report_pages_from_pdf(data,max_pages=80):
    """Extract text page-by-page so evidence can retain a page reference."""
    if not data or data[:4]!=b"%PDF": return []
    try:
        import io, hashlib
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(data))
        return [{"page":i+1,"text":(p.extract_text() or "").strip()} for i,p in enumerate(reader.pages[:max_pages])]
    except Exception:
        return []

def _report_number(text):
    if text is None:return np.nan
    z=str(text).replace(",","").replace("$","").strip()
    mult=1.0
    if z.lower().endswith("bn"): mult=1e9; z=z[:-2]
    elif z.lower().endswith("b"): mult=1e9; z=z[:-1]
    elif z.lower().endswith("m"): mult=1e6; z=z[:-1]
    elif z.lower().endswith("k"): mult=1e3; z=z[:-1]
    try:return float(z)*mult
    except:return np.nan

def extract_report_kpi_candidates(ticker,pages,sector="",industry=""):
    """Conservative deterministic extraction. Candidates require user confirmation."""
    metrics=company_kpi_template(ticker,sector,industry)
    aliases={
      "Transaction / TTV growth":["ttv growth","transaction volume growth","total transaction volume growth"],
      "Revenue growth":["revenue growth","revenue increased","revenue rose"],
      "Revenue margin":["revenue margin"],
      "Credit losses / bad debts":["credit losses","credit loss","bad debts","bad debt"],
      "Cash EBITDA / EBTDA":["cash ebitda","cash ebtda","ebitda"],
      "Operating margin":["operating margin"],
      "Active customers":["active customers","active customer"],
      "Cash generation":["cash generation","operating cash flow","free cash flow"],
      "Earnings growth":["earnings growth","profit growth","net profit growth"],
      "Free cash flow":["free cash flow"],
      "Net debt":["net debt"],
      "Guidance":["guidance"],
    }
    rows=[]; seen=set()
    number=r"([-+]?\$?\d[\d,]*(?:\.\d+)?\s*(?:%|bn|b|m|k)?)"
    for page in pages:
        txt=re.sub(r"\s+"," ",page.get("text",""))
        low=txt.lower()
        for metric in metrics:
            terms=aliases.get(metric,[metric.lower()])
            for term in terms:
                pos=low.find(term)
                if pos<0: continue
                snippet=txt[max(0,pos-130):min(len(txt),pos+260)]
                # Prefer a nearby percentage for growth/margins/losses; otherwise first nearby number.
                matches=re.findall(number,snippet,flags=re.I)
                if not matches: continue
                raw=matches[0].strip()
                val=_report_number(raw.replace("%",""))
                if pd.isna(val): continue
                unit="%" if "%" in raw else ("$" if "$" in raw else "")
                key=(metric,page["page"],round(float(val),6),unit)
                if key in seen: continue
                seen.add(key)
                rows.append({"Metric":metric,"Value":float(val),"Unit":unit,
                             "Page":page["page"],"Evidence":snippet[:500]})
                break
    return pd.DataFrame(rows)

def save_report_intelligence(ticker,title,period,source,source_url,file_name,data,pages,candidates):
    import hashlib
    v19_phase4_db_upgrade()
    raw="\n\n".join(f"[Page {p['page']}] {p['text']}" for p in pages)
    summary=evidence_summary(raw,3500)
    digest=hashlib.sha256(data or raw.encode("utf-8")).hexdigest()
    con=ws_db()
    existing=con.execute("SELECT id FROM report_intelligence WHERE ticker=? AND document_hash=?",
                         (ticker,digest)).fetchone()
    if existing:
        rid=int(existing[0])
    else:
        cur=con.execute("""INSERT INTO report_intelligence
          (ticker,created_at,title,period,source,source_url,file_name,document_hash,summary,raw_text,confirmed)
          VALUES(?,?,?,?,?,?,?,?,?,?,0)""",
          (ticker,datetime.now(timezone.utc).isoformat(),title,period,source,source_url,file_name,digest,summary,raw))
        rid=cur.lastrowid
        for _,r in candidates.iterrows():
            con.execute("""INSERT INTO report_kpi_candidates
              (report_id,ticker,metric,value,unit,evidence,page_hint,confirmed)
              VALUES(?,?,?,?,?,?,?,0)""",
              (rid,ticker,r["Metric"],float(r["Value"]),r["Unit"],r["Evidence"],str(r["Page"])))
    con.commit(); con.close()
    return rid

def report_history(ticker):
    v19_phase4_db_upgrade(); con=ws_db()
    rows=con.execute("""SELECT id,created_at,title,period,source,source_url,file_name,summary
                        FROM report_intelligence WHERE ticker=? ORDER BY id DESC""",(ticker,)).fetchall()
    con.close()
    return pd.DataFrame(rows,columns=["id","created_at","title","period","source","source_url","file_name","summary"])

def report_candidates(report_id):
    v19_phase4_db_upgrade(); con=ws_db()
    rows=con.execute("""SELECT id,metric,value,unit,evidence,page_hint,confirmed
                        FROM report_kpi_candidates WHERE report_id=? ORDER BY id""",(int(report_id),)).fetchall()
    con.close()
    return pd.DataFrame(rows,columns=["id","metric","value","unit","evidence","page","confirmed"])

def confirm_report_candidate(candidate_id,ticker,period,source,source_url):
    v19_phase4_db_upgrade(); con=ws_db()
    row=con.execute("""SELECT metric,value,unit,evidence,page_hint FROM report_kpi_candidates WHERE id=?""",
                    (int(candidate_id),)).fetchone()
    if not row:
        con.close(); return False
    metric,value,unit,evidence,page=row
    con.execute("""INSERT INTO kpi_observations
      (ticker,metric,period,value,unit,source,source_url,evidence_note,observed_at)
      VALUES(?,?,?,?,?,?,?,?,?)""",
      (ticker,metric,period,float(value),unit,source,source_url,
       f"Report Intelligence page {page}: {evidence}",datetime.now(timezone.utc).isoformat()))
    con.execute("UPDATE report_kpi_candidates SET confirmed=1 WHERE id=?",(int(candidate_id),))
    con.commit(); con.close(); return True

def compare_report_kpis(ticker):
    """Compare confirmed company KPI observations by metric; never invent missing periods."""
    d=kpi_observations(ticker)
    if d is None or d.empty:return pd.DataFrame(columns=["Metric","Previous period","Previous","Latest period","Latest","Change"])
    rows=[]
    for metric,g in d.sort_values("observed_at").groupby("metric"):
        if len(g)<2: continue
        a,b=g.iloc[-2],g.iloc[-1]
        change=np.nan if float(a["value"])==0 else float(b["value"])/float(a["value"])-1
        rows.append({"Metric":metric,"Previous period":a["period"],"Previous":a["value"],
                     "Latest period":b["period"],"Latest":b["value"],"Change":change,
                     "Latest source":b["source"]})
    return pd.DataFrame(rows)

def render_report_intelligence(ticker):
    st.header(f"Report Intelligence — {ticker}")
    st.caption("Extract, verify and compare company-reported evidence. Extracted KPI values are candidates until you confirm them.")
    v19_phase4_db_upgrade()
    mode=st.radio("Document source",["Upload company PDF","Latest announcement"],horizontal=True,key="ri_source_mode")
    data=None; source=""; source_url=""; file_name=""; default_title=""
    if mode=="Upload company PDF":
        up=st.file_uploader("Upload annual report, results presentation or trading update",type=["pdf"],key="ri_pdf")
        if up is not None:
            data=up.getvalue(); file_name=up.name; source="Uploaded company document"; default_title=up.name
    else:
        anns=latest_announcements_safe(ticker,20)
        if anns is None or anns.empty:
            st.info("No announcement metadata is currently available.")
        else:
            label_col="Title" if "Title" in anns.columns else anns.columns[0]
            options=list(range(len(anns)))
            pick=st.selectbox("Announcement",options,format_func=lambda i:str(anns.iloc[i][label_col]),key="ri_ann")
            row=anns.iloc[pick]
            source_url=str(row.get("URL","")); default_title=str(row.get(label_col,"Company announcement"))
            source=str(row.get("Source","Company announcement"))
            if st.button("Fetch selected report",key="ri_fetch"):
                data,ctype=fetch_document(source_url)
                if data:
                    st.session_state["ri_fetched"]=(data,source,source_url,default_title)
                else: st.error("The selected document could not be fetched from the source.")
            if "ri_fetched" in st.session_state:
                data,source,source_url,default_title=st.session_state["ri_fetched"]
                file_name=default_title+".pdf"

    if data:
        pages=report_pages_from_pdf(data)
        if not pages:
            st.warning("No machine-readable PDF text was extracted. Scanned/image-only PDFs require OCR, which is not enabled in this Streamlit build.")
        else:
            cls=safe_company_classification(ticker)
            candidates=extract_report_kpi_candidates(ticker,pages,cls.get("sector",""),cls.get("industry",""))
            title=st.text_input("Report title",value=default_title,key="ri_title")
            period=st.text_input("Reporting period",placeholder="e.g. FY26 / H1 FY27",key="ri_period")
            st.subheader("Evidence summary")
            st.write(evidence_summary("\n".join(p["text"] for p in pages),3500))
            st.subheader("Extracted KPI candidates")
            if candidates.empty:
                st.info("No conservative KPI candidates were detected. You can still save the report for review.")
            else:
                st.dataframe(candidates,use_container_width=True,hide_index=True)
                st.caption("These are machine-extracted candidates, not verified facts. Confirm against the cited page/snippet before storing.")
            if st.button("Save report intelligence",type="primary",key="ri_save"):
                if not period.strip():
                    st.error("Enter the reporting period before saving.")
                else:
                    rid=save_report_intelligence(ticker,title,period,source,source_url,file_name,data,pages,candidates)
                    st.session_state["ri_report_id"]=rid
                    st.success(f"Report saved as research record #{rid}.")
                    st.rerun()

    hist=report_history(ticker)
    if not hist.empty:
        st.divider(); st.subheader("Saved reports")
        st.dataframe(hist[["id","created_at","title","period","source","file_name"]],use_container_width=True,hide_index=True)
        rid=st.selectbox("Review saved report",hist["id"].astype(int).tolist(),key="ri_review_id")
        report=hist[hist["id"]==rid].iloc[0]
        st.markdown("**Saved evidence summary**"); st.write(report["summary"])
        cand=report_candidates(rid)
        if not cand.empty:
            st.markdown("**KPI candidates requiring verification**")
            st.dataframe(cand,use_container_width=True,hide_index=True)
            pending=cand[cand["confirmed"]==0]
            if not pending.empty:
                cid=st.selectbox("Candidate to confirm",pending["id"].astype(int).tolist(),
                    format_func=lambda x:f"{pending[pending['id']==x].iloc[0]['metric']} - {pending[pending['id']==x].iloc[0]['value']} {pending[pending['id']==x].iloc[0]['unit']}",
                    key="ri_confirm_candidate")
                if st.button("Confirm this KPI into evidence ledger",key="ri_confirm"):
                    if confirm_report_candidate(cid,ticker,report["period"],report["title"],report["source_url"]):
                        st.success("Verified candidate added to the KPI evidence ledger."); st.rerun()

    comp=compare_report_kpis(ticker)
    st.divider(); st.subheader("What changed between confirmed reports?")
    if comp.empty:
        st.info("At least two confirmed observations for the same KPI are required before a report-to-report comparison can be shown.")
    else:
        st.dataframe(comp.style.format({"Change":"{:+.1%}"},na_rep="—"),use_container_width=True,hide_index=True)
        st.caption("Direction is descriptive. Whether a rise or fall supports the thesis depends on the KPI.")

def v19_phase3_db_upgrade():
    """Durable local snapshots for change detection. Safe forward migration."""
    v18_db_upgrade()
    con=ws_db()
    con.execute("""CREATE TABLE IF NOT EXISTS monitoring_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, captured_at TEXT, price REAL, volume REAL, sma50 REAL, sma200 REAL,
        rsi REAL, analyst_target REAL, analyst_count INTEGER, analyst_label TEXT,
        quant_12m REAL, market_cap REAL, revenue_growth REAL, earnings_growth REAL,
        operating_margin REAL, debt_to_equity REAL, announcement_key TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS monitoring_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT, detected_at TEXT, category TEXT, severity TEXT, headline TEXT,
        old_value TEXT, new_value TEXT, evidence TEXT, acknowledged INTEGER DEFAULT 0)""")
    con.execute("""CREATE INDEX IF NOT EXISTS idx_monitor_snap_ticker_time
                   ON monitoring_snapshots(ticker,captured_at)""")
    con.execute("""CREATE INDEX IF NOT EXISTS idx_monitor_events_ticker_time
                   ON monitoring_events(ticker,detected_at)""")
    con.commit(); con.close()

def _safe_float(v):
    try:
        x=float(v)
        return x if np.isfinite(x) else np.nan
    except Exception:
        return np.nan

def monitoring_snapshot_now(ticker, h=None, meta=None):
    """Build a point-in-time evidence snapshot without inventing unavailable fields."""
    if h is None: h=history(ticker,"2y")
    if meta is None:
        try: meta=yf.Ticker(ticker).info or {}
        except Exception: meta={}
    if h is None or h.empty:
        return {}
    px=pd.to_numeric(h["Close"],errors="coerce").dropna()
    if px.empty: return {}
    price=float(px.iloc[-1])
    ms=market_structure(h)
    ti=technical_indicators(h)
    rsi_now=np.nan
    if ti is not None and not ti.empty and "RSI" in ti:
        rsi_now=_safe_float(ti["RSI"].iloc[-1])
    a=analyst_consensus_snapshot(ticker)
    fc=research_forecast(h)
    q12=np.nan
    if fc is not None and not fc.empty:
        z=fc.loc[fc["Horizon"]=="12 Months","Median forecast"]
        if len(z): q12=_safe_float(z.iloc[0])
    ann=latest_announcements_safe(ticker,1)
    ann_key=""
    if ann is not None and not ann.empty:
        ann_key=" | ".join(str(x) for x in ann.iloc[0].tolist()[:4])
    vol=np.nan
    if "Volume" in h and len(h):
        vol=_safe_float(h["Volume"].iloc[-1])
    return {
        "ticker":ticker,"captured_at":datetime.now(timezone.utc).isoformat(),
        "price":price,"volume":vol,"sma50":_safe_float(ms.get("SMA50")),
        "sma200":_safe_float(ms.get("SMA200")),"rsi":rsi_now,
        "analyst_target":_safe_float(a.get("target_mean")),"analyst_count":int(a.get("analysts") or 0),
        "analyst_label":str(a.get("label") or "Unavailable"),"quant_12m":q12,
        "market_cap":_safe_float(meta.get("marketCap")) if isinstance(meta,dict) else np.nan,
        "revenue_growth":_safe_float(meta.get("revenueGrowth")) if isinstance(meta,dict) else np.nan,
        "earnings_growth":_safe_float(meta.get("earningsGrowth")) if isinstance(meta,dict) else np.nan,
        "operating_margin":_safe_float(meta.get("operatingMargins")) if isinstance(meta,dict) else np.nan,
        "debt_to_equity":_safe_float(meta.get("debtToEquity")) if isinstance(meta,dict) else np.nan,
        "announcement_key":ann_key,
    }

def latest_monitoring_snapshot(ticker):
    v19_phase3_db_upgrade(); con=ws_db()
    row=con.execute("""SELECT ticker,captured_at,price,volume,sma50,sma200,rsi,analyst_target,
                      analyst_count,analyst_label,quant_12m,market_cap,revenue_growth,earnings_growth,
                      operating_margin,debt_to_equity,announcement_key
                      FROM monitoring_snapshots WHERE ticker=? ORDER BY id DESC LIMIT 1""",(ticker,)).fetchone()
    con.close()
    cols=["ticker","captured_at","price","volume","sma50","sma200","rsi","analyst_target",
          "analyst_count","analyst_label","quant_12m","market_cap","revenue_growth","earnings_growth",
          "operating_margin","debt_to_equity","announcement_key"]
    return dict(zip(cols,row)) if row else None

def detect_monitoring_changes(previous,current):
    """Material-change rules. Thresholds are explicit and descriptive."""
    if not previous or not current: return []
    events=[]
    def pct_change(field,category,label,threshold=.05,severity="Info"):
        old=_safe_float(previous.get(field)); new=_safe_float(current.get(field))
        if pd.isna(old) or pd.isna(new) or old==0:return
        ch=new/old-1
        if abs(ch)>=threshold:
            direction="increased" if ch>0 else "decreased"
            events.append({"category":category,"severity":severity,
                "headline":f"{label} {direction} {abs(ch):.1%}",
                "old_value":str(old),"new_value":str(new),
                "evidence":f"Point-in-time comparison; threshold {threshold:.0%}."})
    pct_change("price","Market","Price",.05,"Watch")
    pct_change("analyst_target","Analysts","Analyst mean target",.05,"Watch")
    pct_change("quant_12m","Forecast","Quant 12M scenario",.05,"Info")
    pct_change("revenue_growth","Fundamentals","Revenue growth field",.20,"Watch")
    pct_change("earnings_growth","Fundamentals","Earnings growth field",.20,"Watch")
    pct_change("operating_margin","Fundamentals","Operating margin",.10,"Watch")
    pct_change("debt_to_equity","Balance sheet","Debt-to-equity",.15,"Watch")

    # Technical state crossings are more useful than tiny numeric changes.
    for field,label in [("sma50","50-day average"),("sma200","200-day average")]:
        oldp=_safe_float(previous.get("price")); newp=_safe_float(current.get("price"))
        oldm=_safe_float(previous.get(field)); newm=_safe_float(current.get(field))
        if all(pd.notna(x) for x in [oldp,newp,oldm,newm]):
            was=oldp>=oldm; now=newp>=newm
            if was!=now:
                events.append({"category":"Technical","severity":"Watch",
                    "headline":f"Price crossed {'above' if now else 'below'} the {label}",
                    "old_value":f"{oldp:.4f} vs {oldm:.4f}","new_value":f"{newp:.4f} vs {newm:.4f}",
                    "evidence":"Closing-price state compared with moving average."})

    old_label=str(previous.get("analyst_label") or "")
    new_label=str(current.get("analyst_label") or "")
    if old_label and new_label and old_label!=new_label:
        events.append({"category":"Analysts","severity":"Watch",
            "headline":"Analyst consensus category changed","old_value":old_label,"new_value":new_label,
            "evidence":"Yahoo/yfinance analyst distribution summary."})

    old_ann=str(previous.get("announcement_key") or "")
    new_ann=str(current.get("announcement_key") or "")
    if new_ann and old_ann and new_ann!=old_ann:
        events.append({"category":"Announcement","severity":"New",
            "headline":"A different latest company announcement was detected","old_value":old_ann,
            "new_value":new_ann,"evidence":"Latest announcement identity changed between snapshots."})
    return events

def save_monitoring_snapshot(ticker,h=None,meta=None):
    v19_phase3_db_upgrade()
    current=monitoring_snapshot_now(ticker,h,meta)
    if not current:return 0,[]
    previous=latest_monitoring_snapshot(ticker)
    events=detect_monitoring_changes(previous,current)
    con=ws_db()
    fields=["ticker","captured_at","price","volume","sma50","sma200","rsi","analyst_target",
            "analyst_count","analyst_label","quant_12m","market_cap","revenue_growth","earnings_growth",
            "operating_margin","debt_to_equity","announcement_key"]
    con.execute(f"""INSERT INTO monitoring_snapshots({",".join(fields)})
                    VALUES({",".join(["?"]*len(fields))})""",[current.get(k) for k in fields])
    for e in events:
        con.execute("""INSERT INTO monitoring_events
            (ticker,detected_at,category,severity,headline,old_value,new_value,evidence,acknowledged)
            VALUES(?,?,?,?,?,?,?,?,0)""",
            (ticker,current["captured_at"],e["category"],e["severity"],e["headline"],
             e["old_value"],e["new_value"],e["evidence"]))
    con.commit(); con.close()
    return 1,events

def monitoring_events(ticker=None,limit=100,unacknowledged_only=False):
    v19_phase3_db_upgrade(); con=ws_db()
    sql="""SELECT id,ticker,detected_at,category,severity,headline,old_value,new_value,evidence,acknowledged
           FROM monitoring_events"""
    params=[]
    clauses=[]
    if ticker:
        clauses.append("ticker=?"); params.append(ticker)
    if unacknowledged_only:
        clauses.append("acknowledged=0")
    if clauses: sql+=" WHERE "+" AND ".join(clauses)
    sql+=" ORDER BY id DESC LIMIT ?"; params.append(int(limit))
    rows=con.execute(sql,params).fetchall(); con.close()
    cols=["id","ticker","detected_at","category","severity","headline","old_value","new_value","evidence","acknowledged"]
    return pd.DataFrame(rows,columns=cols)

def acknowledge_monitoring_events(ticker):
    v19_phase3_db_upgrade(); con=ws_db()
    con.execute("UPDATE monitoring_events SET acknowledged=1 WHERE ticker=?",(ticker,))
    con.commit(); con.close()

def render_something_changed(ticker,h=None,meta=None):
    st.subheader("Something Changed")
    st.caption("Point-in-time monitoring compares saved snapshots. It only reports changes observed between snapshots; it is not a background notification service.")
    current=monitoring_snapshot_now(ticker,h,meta)
    previous=latest_monitoring_snapshot(ticker)
    if previous is None:
        st.info("No monitoring baseline exists yet. Save today's snapshot to start change detection.")
    else:
        changes=detect_monitoring_changes(previous,current)
        if changes:
            st.dataframe(pd.DataFrame(changes),use_container_width=True,hide_index=True)
        else:
            st.success("No configured material-change rule is triggered by the current snapshot.")
        st.caption(f"Previous monitoring snapshot: {previous.get('captured_at','—')}")
    c1,c2=st.columns(2)
    if c1.button("Save current monitoring snapshot",type="primary",key=f"save_monitor_{ticker}"):
        n,events=save_monitoring_snapshot(ticker,h,meta)
        st.success(f"Snapshot saved. {len(events)} change event(s) recorded.")
        st.rerun()
    if c2.button("Acknowledge recorded changes",key=f"ack_monitor_{ticker}"):
        acknowledge_monitoring_events(ticker); st.success("Recorded changes acknowledged."); st.rerun()
    ev=monitoring_events(ticker,50,False)
    if not ev.empty:
        st.markdown("**Change history**")
        st.dataframe(ev,use_container_width=True,hide_index=True)

def v18_attention(ticker,amount=0,price=None):
    rows=[]
    t=thesis_table(ticker)
    if not t.empty:
        for _,r in t.iterrows():
            if str(r["status"])!="Met":rows.append({"Priority":"⚠","Item":f"{r['metric']}: {r['status']}","Source":"Thesis"})
    kc=kpi_latest_comparison(ticker)
    for _,r in kc.iterrows():
        if r["Change"]!="→ Unchanged":rows.append({"Priority":"●","Item":f"{r['Metric']}: {r['Change']}","Source":r["Source"]})
    if price and amount:
        pi=portfolio_impact(ticker,amount,price)
        if pd.notna(pi["weight1"]) and pi["weight1"]>=.20:
            rows.append({"Priority":"⚠","Item":f"Known-portfolio concentration would be {pi['weight1']:.1%} after the proposed purchase","Source":"Portfolio calculation"})
    if not rows:rows=[{"Priority":"✓","Item":"No stored thesis/KPI condition currently requires attention","Source":"Stored evidence"}]
    return pd.DataFrame(rows)

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
    # Self-initialise the V17 schema because this helper is called by attention_items()
    # before some V17 pages have explicitly run the database upgrade.
    v17_db_upgrade()
    con=ws_db()
    cols=["id","metric","operator","threshold","current_value","status","source","updated_at"]
    try:
        rows=con.execute(
            "SELECT id,metric,operator,threshold,current_value,status,source,updated_at "
            "FROM thesis_rules WHERE ticker=? ORDER BY id",(ticker,)
        ).fetchall()
        d=pd.DataFrame(rows,columns=cols)
    except Exception:
        d=pd.DataFrame(columns=cols)
    finally:
        con.close()
    return d

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

st.sidebar.title("🏛️ Chrímata")
try:
    _search_key=st.secrets.get("TWELVE_DATA_API_KEY","")
except Exception:
    _search_key=""

with st.sidebar.expander("🔎 Company Search", expanded=False):
    query=st.text_input("Search company or ticker",st.session_state.get("mia_search_query","ZIP"),
        placeholder="Pepsi, PEP, Qantas, QAN, Zip…",
        help="Search by company name or ticker across global listings.",
        label_visibility="collapsed", key="sidebar_company_search")
    st.session_state["mia_search_query"]=query
    matches=search_securities(query,_search_key)
    if not matches.empty:
        _labels=[]; _map={}
        for i,r in matches.head(30).iterrows():
            lab=f"{r.get('Symbol','')}  ·  {r.get('Company','')}  ·  {r.get('Exchange','')}  ·  {r.get('Type','Stock')}"
            _labels.append(lab); _map[lab]=i
        _chosen=st.selectbox("Matching listings",_labels,key="mia_symbol_result")
        _row=matches.loc[_map[_chosen]]
        ticker=resolve_listing(_row["Symbol"],_row.get("Exchange",""),_row.get("Country",""))
        _selected_name=str(_row.get("Company") or identity(ticker))
        try:_selected_meta=yf.Ticker(ticker).info or {}
        except Exception:_selected_meta={}
        st.markdown(company_logo_html(ticker,_selected_meta,_selected_name,42),unsafe_allow_html=True)
        st.markdown(f"**{ticker}** · {_selected_name}")
        st.caption(f"{_row.get('Exchange','')} · {_row.get('Type','Stock')}")
    else:
        ticker=resolve_bare_ticker(query.strip().upper()) if query.strip() else "ZIP.AX"
        st.info("No directory match. Try the company name or exchange ticker.")

with st.sidebar.expander("◇ Investment Thesis", expanded=False):
    thesis=st.text_area("Investment thesis","Revenue and earnings continue growing, margins improve, cash generation strengthens and key operating KPIs remain healthy.",height=105,label_visibility="collapsed")
NAV_GROUPS = {
    "Home": ["Dashboard"],
    "Research": ["Markets","Company Command Centre","Report Intelligence","Before I Invest","Monitor My Thesis"],
    "Portfolio": ["Portfolio"],
    "Trading": ["Trade Centre"],
    "Tools": ["Research Tools"],
    "System": ["Settings"],
}

PRIMARY_NAV = ["Home","Markets","Something Changed","Company Command Centre","Report Intelligence","Advanced Forecasting","Before I Invest",
               "Monitor My Thesis","Portfolio","Trade Centre","Research Tools","Settings"]

st.sidebar.caption(f"Current · {ticker} · {identity(ticker)}")
NAV_ICONS={
    "Home":"⌂","Markets":"◫","Something Changed":"●","Company Command Centre":"▣",
    "Report Intelligence":"▤","Advanced Forecasting":"⌁","Before I Invest":"◇",
    "Monitor My Thesis":"◎","Portfolio":"◈","Trade Centre":"⇄","Research Tools":"⌕","Settings":"⚙"
}
st.sidebar.caption("GLOBAL MARKETS · SMARTER DECISIONS")
primary = st.sidebar.radio("Workspace", PRIMARY_NAV, index=0,
                           format_func=lambda x:f"{NAV_ICONS.get(x,'•')}  {x}")
st.sidebar.markdown("---")

SUBPAGES = {
    "Company Command Centre": ["Overview","Fundamentals","Valuation","Technical","Announcements & Reports","Report Intelligence",
                               "News & Events","Thesis Scorecard","Catalyst Calendar","Quant","Forecasts"],
    "Portfolio": ["Portfolio Overview","Portfolio Intelligence","Risk Centre","Watchlist","Paper Portfolio"],
    "Trade Centre": ["Trade Ticket","Orders","Strategy Builder"],
    "Research Tools": ["Research Report","Investment Committee","Evidence & Thesis","Advanced Forecasting","Model Lab"],
    "Settings": ["Workspace Settings","Data & Production","Broker Connections"],
}

# Map the simplified navigation back to the existing engines. No analytical page is deleted.
if primary == "Home":
    page = "Dashboard"
elif primary in ["Markets","Something Changed","Report Intelligence","Advanced Forecasting","Before I Invest","Monitor My Thesis"]:
    page = primary
elif primary in SUBPAGES:
    sub = st.sidebar.selectbox("Inside this workspace", SUBPAGES[primary])
    PAGE_MAP = {
        ("Company Command Centre","Overview"):"Company Command Centre",
        ("Company Command Centre","Fundamentals"):"Fundamentals",
        ("Company Command Centre","Valuation"):"Valuation",
        ("Company Command Centre","Technical"):"Technical",
        ("Company Command Centre","Announcements & Reports"):"Announcements & Reports",
        ("Company Command Centre","Report Intelligence"):"Report Intelligence",
        ("Company Command Centre","News & Events"):"News & Events",
        ("Company Command Centre","Thesis Scorecard"):"Thesis Scorecard",
        ("Company Command Centre","Catalyst Calendar"):"Catalyst Calendar",
        ("Company Command Centre","Quant"):"Quant",
        ("Company Command Centre","Forecasts"):"Forecasts",
        ("Portfolio","Portfolio Overview"):"Portfolio",
        ("Portfolio","Portfolio Intelligence"):"Portfolio Intelligence",
        ("Portfolio","Risk Centre"):"Risk Centre",
        ("Portfolio","Watchlist"):"Watchlist",
        ("Portfolio","Paper Portfolio"):"Paper Portfolio",
        ("Trade Centre","Trade Ticket"):"Trade Centre",
        ("Trade Centre","Orders"):"Orders",
        ("Trade Centre","Strategy Builder"):"Strategy Builder",
        ("Research Tools","Research Report"):"Research Report",
        ("Research Tools","Investment Committee"):"Investment Committee",
        ("Research Tools","Evidence & Thesis"):"Evidence & Thesis",
        ("Research Tools","Advanced Forecasting"):"Advanced Forecasting",
        ("Research Tools","Model Lab"):"Model Lab",
        ("Settings","Workspace Settings"):"Workspace Settings",
        ("Settings","Data & Production"):"Data & Production",
        ("Settings","Broker Connections"):"Broker Connections",
    }
    page = PAGE_MAP[(primary,sub)]
else:
    page = primary

_PAGE_SUBTITLES={
 "Dashboard":"Market overview and research starting point",
 "Markets":"Discover and compare opportunities across global markets",
 "Something Changed":"Your material-change research inbox",
 "Company Command Centre":"One-company investment research workspace",
 "Report Intelligence":"Extract, verify and compare company-reported evidence",
 "Advanced Forecasting":"Walk-forward tested multi-model forecast research",
 "Before I Invest":"Pre-investment evidence and portfolio-impact review",
 "Monitor My Thesis":"Track whether the reasons for owning remain supported",
 "Portfolio":"Holdings, concentration and portfolio analytics",
 "Trade Centre":"Paper-trade planning and execution workflow",
}
_shell_sub=_PAGE_SUBTITLES.get(page,"Chrímata research workspace")
if page!="Dashboard":
    st.markdown(f"""<div class="mia-shell-head">
<div><div class="mia-eyebrow">Chrímata / {primary}</div>
<div class="mia-shell-title">{page}</div><div class="mia-shell-sub">{_shell_sub}</div></div>
<div class="mia-live"><span class="mia-dot"></span> Research workspace</div>
</div>""",unsafe_allow_html=True)

h=history(ticker); meta=info(ticker)
if h.empty and page!="Dashboard":
    st.error(f"No market data returned for {ticker}. Try another matching listing or enter the exchange ticker directly.")
    st.stop()
if h.empty:
    h=history("^AXJO","1mo")
    meta={}
close=h["Close"] if not h.empty and "Close" in h else pd.Series(dtype=float)
price=float(close.iloc[-1]) if not close.empty else np.nan
name=meta.get("longName") or meta.get("shortName") or ticker
rv=rsi(close); rv=float(rv.iloc[-1]) if len(rv) and pd.notna(rv.iloc[-1]) else np.nan

# Browser-tab branding is intentionally static in V19.8: Chrímata + Parthenon icon.

if page!="Dashboard":
    st.title("Chrímata")
    st.caption("V19.8.5 • Chrímata • Fixed Full-Width Terminal UI")



MARKET_OVERVIEW_CONFIG={
 "Australia":{"flag":"🇦🇺","indices":{"S&P/ASX 200":"^AXJO","All Ordinaries":"^AORD","All Technology":"^AXTX"},"benchmark":"^AXJO","vol":"^AXVI","currency":"AUDUSD=X","universe":["BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","WES.AX","MQG.AX","WOW.AX","TLS.AX","QAN.AX","ZIP.AX","XRO.AX","FMG.AX","RIO.AX","ALL.AX","REA.AX","CAR.AX","JHX.AX","COL.AX"],"sectors":{"Financials":"QFN.AX","Materials":"QRE.AX","Health Care":"QHL.AX","Technology":"ATEC.AX","Resources":"QRE.AX","Property":"VAP.AX"}},
 "United States":{"flag":"🇺🇸","indices":{"S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI"},"benchmark":"^GSPC","vol":"^VIX","currency":"AUDUSD=X","universe":["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V","WMT","XOM","MA","NFLX","COST","AMD","PEP","KO","DIS","CAT"],"sectors":{"Technology":"XLK","Financials":"XLF","Health Care":"XLV","Consumer Discretionary":"XLY","Industrials":"XLI","Energy":"XLE","Materials":"XLB","Utilities":"XLU","Real Estate":"XLRE","Staples":"XLP","Communication":"XLC"}},
 "United Kingdom":{"flag":"🇬🇧","indices":{"FTSE 100":"^FTSE","FTSE 250":"^FTMC","FTSE All-Share":"^FTAS"},"benchmark":"^FTSE","vol":None,"currency":"GBPUSD=X","universe":["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","REL.L","LSEG.L","DGE.L","BARC.L","VOD.L"],"sectors":{}},
 "Japan":{"flag":"🇯🇵","indices":{"Nikkei 225":"^N225","TOPIX":"^TOPX","JPX-Nikkei 400":"^JPXNK400"},"benchmark":"^N225","vol":None,"currency":"JPY=X","universe":["7203.T","6758.T","9984.T","8306.T","6861.T","8035.T","9432.T","7974.T","6501.T","7267.T","6098.T","9983.T"],"sectors":{}},
 "Hong Kong":{"flag":"🇭🇰","indices":{"Hang Seng":"^HSI","Hang Seng China Ent.":"^HSCE","Hang Seng Tech":"^HSTECH"},"benchmark":"^HSI","vol":None,"currency":"HKD=X","universe":["0700.HK","9988.HK","3690.HK","1299.HK","0005.HK","0388.HK","1810.HK","9618.HK","2318.HK","0883.HK","0941.HK","9999.HK"],"sectors":{}},
 "Canada":{"flag":"🇨🇦","indices":{"S&P/TSX Composite":"^GSPTSE","TSX 60":"^TX60","TSX Venture":"^SPCDNX"},"benchmark":"^GSPTSE","vol":None,"currency":"CAD=X","universe":["RY.TO","TD.TO","SHOP.TO","ENB.TO","CNR.TO","BNS.TO","CP.TO","SU.TO","BMO.TO","CNQ.TO","TRI.TO","MFC.TO"],"sectors":{}}
}
GLOBAL_MARKET_TICKERS={"S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI","ASX 200":"^AXJO","Nikkei 225":"^N225","Hang Seng":"^HSI","FTSE 100":"^FTSE","TSX Composite":"^GSPTSE"}
COMMODITY_TICKERS={"Gold":"GC=F","Silver":"SI=F","Brent Crude":"BZ=F","WTI Crude":"CL=F","Copper":"HG=F"}
FX_TICKERS={"AUD / USD":"AUDUSD=X","EUR / USD":"EURUSD=X","GBP / USD":"GBPUSD=X","USD / JPY":"JPY=X","USD / CAD":"CAD=X","USD / HKD":"HKD=X"}

def _ov_close_series(df,ticker=None):
    if df is None or df.empty:return pd.Series(dtype=float)
    try:
        if isinstance(df.columns,pd.MultiIndex):
            if ticker is not None and ("Close",ticker) in df.columns:return pd.to_numeric(df[("Close",ticker)],errors="coerce").dropna()
            c=df["Close"]
            if isinstance(c,pd.DataFrame):c=c.iloc[:,0]
            return pd.to_numeric(c,errors="coerce").dropna()
        return pd.to_numeric(df["Close"],errors="coerce").dropna()
    except Exception:return pd.Series(dtype=float)

@st.cache_data(ttl=300)
def overview_quote(ticker,period="5d"):
    try:
        d=yf.Ticker(ticker).history(period=period,auto_adjust=True)
        c=_ov_close_series(d,ticker)
        if c.empty:return None
        last=float(c.iloc[-1]); prev=float(c.iloc[-2]) if len(c)>1 else np.nan
        return {"last":last,"change":last-prev if np.isfinite(prev) else np.nan,"pct":last/prev-1 if np.isfinite(prev) and prev else np.nan,"series":c}
    except Exception:return None

@st.cache_data(ttl=600)
def overview_batch(tickers):
    rows=[]
    for t in list(tickers):
        q=overview_quote(t,"5d")
        if not q:continue
        try:m=info(t); nm=m.get("shortName") or m.get("longName") or t
        except Exception:nm=t
        rows.append({"Ticker":t,"Company":nm,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
    return pd.DataFrame(rows)

def overview_fmt_price(x):
    return "—" if not np.isfinite(_mia_num(x)) else f"{float(x):,.2f}"

def render_change_table(df,n=8):
    if df is None or df.empty:
        st.caption("No market data returned by the active provider.");return
    d=df.head(n).copy()
    d["Last"]=d["Last"].map(lambda x:f"{x:,.2f}")
    d["Change"]=d["Change"].map(lambda x:f"{x:+,.2f}")
    d["% Chg"]=d["% Chg"].map(lambda x:f"{x:+.2%}")
    st.dataframe(d,use_container_width=True,hide_index=True)

@st.cache_data(ttl=1800)
def overview_calendar(tickers):
    earnings=[]; dividends=[]
    now=pd.Timestamp.now(tz="UTC")
    for t in list(tickers)[:12]:
        try:
            tk=yf.Ticker(t); m=tk.info or {}; nm=m.get("shortName") or t
            cal=tk.calendar
            if isinstance(cal,dict):
                ed=cal.get("Earnings Date") or cal.get("EarningsDate")
                if isinstance(ed,(list,tuple)) and ed:ed=ed[0]
                if ed is not None:
                    dt=pd.to_datetime(ed,utc=True,errors="coerce")
                    if pd.notna(dt) and dt>=now-pd.Timedelta(days=1):earnings.append({"Ticker":t,"Company":nm,"Date":dt.date().isoformat()})
            ex=m.get("exDividendDate")
            if ex:
                dt=pd.to_datetime(ex,unit="s",utc=True,errors="coerce")
                if pd.notna(dt) and dt>=now-pd.Timedelta(days=1):dividends.append({"Ticker":t,"Company":nm,"Ex-Date":dt.date().isoformat(),"Dividend Rate":m.get("dividendRate")})
        except Exception:pass
    return pd.DataFrame(earnings),pd.DataFrame(dividends)

def render_global_market_overview():
    st.markdown("""<div class="chrimata-terminal-hero"><img src="data:image/png;base64,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" alt="Parthenon"><div class="chrimata-brand"><div class="chrimata-brand-title">Chrímata</div><div class="chrimata-brand-sub">Market Investment Analyst · Global Markets. Smarter Decisions.</div></div><div class="chrimata-quote">“Knowledge compounds.”<small>DISCIPLINE &nbsp; | &nbsp; ANALYSIS &nbsp; | &nbsp; OPPORTUNITY</small></div></div>""",unsafe_allow_html=True)
    search_col, market_col = st.columns([1.05,1.55], gap="small")
    with search_col:
        home_q=st.text_input("Global security search",placeholder="Search any company, ETF or index…",label_visibility="collapsed",key="home_global_search")
        if home_q:
            home_matches=search_securities(home_q,_search_key)
            if not home_matches.empty:
                r=home_matches.iloc[0]
                st.caption(f"Top match: {r.get('Symbol','')} · {r.get('Company','')} · {r.get('Exchange','')}")
    with market_col:
        market=st.radio("Market",list(MARKET_OVERVIEW_CONFIG.keys()),horizontal=True,index=0,key="home_market")
    cfg=MARKET_OVERVIEW_CONFIG[market]
    st.markdown(f"<div class='chrimata-market-title'><span class='chrimata-market-flag'>{cfg['flag']}</span><span class='chrimata-market-name'>Market Overview — {market}</span></div><div class='chrimata-market-note'>Latest available provider data · exchange data may be delayed depending on source and market</div>",unsafe_allow_html=True)

    cols=st.columns(len(cfg["indices"])+2)
    index_rows=[]
    for col,(label,t) in zip(cols,cfg["indices"].items()):
        q=overview_quote(t,"5d")
        if q:
            col.metric(label,overview_fmt_price(q["last"]),f"{q['change']:+,.2f} ({q['pct']:+.2%})")
            index_rows.append({"Code":t,"Name":label,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
        else: col.metric(label,"N/A")
    cq=overview_quote(cfg.get("currency"),"5d") if cfg.get("currency") else None
    if cq: cols[-2].metric(cfg.get("currency","FX"),overview_fmt_price(cq["last"]),f"{cq['change']:+,.4f} ({cq['pct']:+.2%})")
    else: cols[-2].metric("FX","N/A")
    gq=overview_quote("GC=F","5d")
    if gq: cols[-1].metric("Gold (USD)",overview_fmt_price(gq["last"]),f"{gq['change']:+,.2f} ({gq['pct']:+.2%})")
    else: cols[-1].metric("Gold (USD)","N/A")

    left,right1,right2=st.columns([1.55,.9,.9],gap="small")
    with left:
        st.subheader(f"{next(iter(cfg['indices']))} Market Chart")
        horizon=st.radio("Chart period",["5d","1mo","3mo","6mo","1y","5y"],horizontal=True,index=1,key="home_chart_period")
        chart=pd.DataFrame()
        for label,t in cfg["indices"].items():
            q=overview_quote(t,horizon)
            if q and not q["series"].empty:
                ser=q["series"]; chart[label]=(ser/ser.iloc[0]-1)*100
        if not chart.empty: st.line_chart(chart,use_container_width=True,height=325)
        else: st.info("No index chart data returned.")
    with right1:
        st.subheader("Sector Performance")
        if cfg["sectors"]:
            sr=[]
            for label,t in cfg["sectors"].items():
                q=overview_quote(t,"5d")
                if q: sr.append({"Sector":label,"% Change":q["pct"]*100})
            if sr: st.bar_chart(pd.DataFrame(sr).sort_values("% Change").set_index("Sector"),horizontal=True,use_container_width=True,height=325)
            else: st.caption("Sector data not returned.")
        else: st.caption("Comparable sector feed not configured for this market.")
    with right2:
        st.subheader("Index Performance")
        if index_rows:
            d=pd.DataFrame(index_rows); d["Last"]=d["Last"].map(lambda x:f"{x:,.2f}"); d["Change"]=d["Change"].map(lambda x:f"{x:+,.2f}"); d["% Chg"]=d["% Chg"].map(lambda x:f"{x:+.2%}")
            st.dataframe(d,use_container_width=True,hide_index=True,height=325)

    movers=overview_batch(tuple(cfg["universe"]))
    if not movers.empty:movers=movers.sort_values("% Chg",ascending=False)
    g,f,w,vcol=st.columns([1,1,.9,.9],gap="small")
    with g:
        st.subheader(f"Top Gainers — {market}")
        render_change_table(movers.head(7) if not movers.empty else movers,7)
    with f:
        st.subheader(f"Biggest Fallers — {market}")
        render_change_table(movers.sort_values("% Chg").head(7) if not movers.empty else movers,7)
    with w:
        st.subheader("Watchlist")
        try: wl=watch_get()
        except Exception: wl=[]
        wt=[]
        if isinstance(wl,pd.DataFrame):
            for c in ["ticker","Ticker","symbol","Symbol"]:
                if c in wl.columns: wt=wl[c].astype(str).tolist();break
        elif isinstance(wl,(list,tuple)): wt=[str(x) for x in wl]
        if wt: render_change_table(overview_batch(tuple(wt)),7)
        else: st.caption("Your saved watchlist is empty.")
    with vcol:
        st.subheader("Volatility & Risk")
        vt=cfg.get("vol")
        vq=overview_quote(vt,"1y") if vt else None
        if vq:
            st.metric(vt, f"{vq['last']:.2f}", f"{vq['change']:+.2f} ({vq['pct']:+.2%})")
            st.line_chart(vq["series"],use_container_width=True,height=190)
            st.caption("Option-implied expected volatility; not a Buy/Sell signal.")
        else: st.caption("Comparable volatility index not configured for this market.")

    st.markdown("<div class='chrimata-section-rule'></div>",unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1,1],gap="small")
    earnings,dividends=overview_calendar(tuple(cfg["universe"]))
    with c1:
        st.subheader(f"Upcoming Dividends — {market}")
        if dividends.empty: st.caption("No upcoming ex-dividend dates returned for the sampled leaders.")
        else: st.dataframe(dividends,use_container_width=True,hide_index=True,height=240)
    with c2:
        st.subheader(f"Upcoming Earnings — {market}")
        if earnings.empty: st.caption("No upcoming earnings dates returned for the sampled leaders.")
        else: st.dataframe(earnings,use_container_width=True,hide_index=True,height=240)
    with c3:
        st.subheader("Global Markets")
        rows=[]
        for label,t in GLOBAL_MARKET_TICKERS.items():
            q=overview_quote(t,"5d")
            if q: rows.append({"Company":label,"Ticker":t,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
        render_change_table(pd.DataFrame(rows),7)

    fx,co,ipo=st.columns(3,gap="small")
    with fx:
        st.subheader("Foreign Exchange")
        rows=[]
        for label,t in FX_TICKERS.items():
            q=overview_quote(t,"5d")
            if q: rows.append({"Company":label,"Ticker":t,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
        render_change_table(pd.DataFrame(rows),7)
    with co:
        st.subheader("Commodities")
        rows=[]
        for label,t in COMMODITY_TICKERS.items():
            q=overview_quote(t,"5d")
            if q: rows.append({"Company":label,"Ticker":t,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
        render_change_table(pd.DataFrame(rows),7)
    with ipo:
        st.subheader("Upcoming IPOs / Listings")
        st.info("A verified cross-market IPO calendar is not configured yet. Chrímata leaves this panel source-empty rather than showing unverified listings.")

    st.markdown("<div class='chrimata-terminal-footer'><span>🏛️ Chrímata · Market Investment Analyst</span><span>V19.8.5 · Fixed Full-Width Terminal UI</span></div>",unsafe_allow_html=True)

def global_yahoo_symbol(symbol, market):
    s=str(symbol).strip().upper()
    suffix={"ASX":".AX","LSE":".L","HKEX":".HK","TSE":".T","TSX":".TO"}.get(market,"")
    if suffix and not s.endswith(suffix):
        if market=="HKEX":
            s=s.zfill(4)
        s+=suffix
    return s

def opportunity_snapshot(symbol, market):
    """Compact, explainable discovery snapshot. Missing provider data stays missing."""
    ys=global_yahoo_symbol(symbol,market)
    h0=history(ys,"2y")
    if h0 is None or h0.empty or "Close" not in h0:
        return None
    px=pd.to_numeric(h0["Close"],errors="coerce").dropna()
    if px.empty: return None
    price=float(px.iloc[-1])
    def ret(n):
        return np.nan if len(px)<=n else float(price/px.iloc[-n-1]-1)
    low=float(px.tail(252).min()) if len(px) else np.nan
    high=float(px.tail(252).max()) if len(px) else np.nan
    pos=(price-low)/(high-low) if pd.notna(low) and pd.notna(high) and high>low else np.nan
    fc=research_forecast(h0)
    fmap={}
    if fc is not None and not fc.empty:
        for _,r in fc.iterrows():
            fmap[str(r["Horizon"])]=r["Median return"]
    return {
        "Company":identity(ys),"Ticker":ys,"Price":price,
        "52W low":low,"52W high":high,"52W position":pos,
        "Actual 1M":ret(21),"Actual 3M":ret(63),"Actual 6M":ret(126),"Actual 12M":ret(252),
        "Model 1M":fmap.get("1 Month",np.nan),"Model 3M":fmap.get("3 Months",np.nan),
        "Model 6M":fmap.get("6 Months",np.nan),"Model 12M":fmap.get("12 Months",np.nan),
    }


def analyst_evidence(ticker, limit=12):
    """Best-effort dated analyst actions. Kept separate from the app's own models."""
    cols=["Date","Firm","Action","From","To"]
    try:
        t=yf.Ticker(ticker)
        d=t.upgrades_downgrades
        if d is None or d.empty:
            return pd.DataFrame(columns=cols)
        d=d.reset_index()
        date_col=next((c for c in d.columns if str(c).lower() in ["gradedate","date","index"]),d.columns[0])
        firm_col=next((c for c in d.columns if str(c).lower() in ["firm","researchfirm"]),None)
        action_col=next((c for c in d.columns if str(c).lower() in ["action","actiontext"]),None)
        from_col=next((c for c in d.columns if str(c).lower() in ["fromgrade","from"]),None)
        to_col=next((c for c in d.columns if str(c).lower() in ["tograde","to"]),None)
        out=pd.DataFrame({
            "Date":d[date_col] if date_col else "—",
            "Firm":d[firm_col] if firm_col else "—",
            "Action":d[action_col] if action_col else "—",
            "From":d[from_col] if from_col else "—",
            "To":d[to_col] if to_col else "—",
        })
        out["Date"]=pd.to_datetime(out["Date"],errors="coerce").dt.strftime("%Y-%m-%d")
        return out.head(limit)
    except Exception:
        return pd.DataFrame(columns=cols)

def forecast_driver_snapshot(ticker, h, meta=None):
    """Explainable observations used to contextualise the statistical forecast."""
    rows=[]
    if h is None or h.empty:
        return pd.DataFrame(columns=["Area","Evidence","Reading","Interpretation"])
    px=pd.to_numeric(h["Close"],errors="coerce").dropna()
    if px.empty:
        return pd.DataFrame(columns=["Area","Evidence","Reading","Interpretation"])
    price=float(px.iloc[-1])
    def add(area,evidence,reading,interpretation):
        rows.append({"Area":area,"Evidence":evidence,"Reading":reading,"Interpretation":interpretation})
    for n,label in [(21,"1M momentum"),(63,"3M momentum"),(126,"6M momentum"),(252,"12M momentum")]:
        if len(px)>n:
            r=float(price/px.iloc[-n-1]-1)
            add("Momentum",label,f"{r:+.1%}","Positive trailing return" if r>0 else "Negative trailing return" if r<0 else "Flat")
    ms=market_structure(h)
    if pd.notna(ms.get("SMA50",np.nan)):
        d=price/ms["SMA50"]-1
        add("Trend","Price vs 50D average",f"{d:+.1%}","Above trend average" if d>0 else "Below trend average")
    if pd.notna(ms.get("SMA200",np.nan)):
        d=price/ms["SMA200"]-1
        add("Trend","Price vs 200D average",f"{d:+.1%}","Above long-term average" if d>0 else "Below long-term average")
    if pd.notna(ms.get("Volume vs 20D",np.nan)):
        vr=ms["Volume vs 20D"]
        add("Participation","Volume vs 20D average",f"{vr:.2f}×","Elevated participation" if vr>=1.5 else "Normal/lower participation")
    if meta is None:
        try: meta=yf.Ticker(ticker).info or {}
        except Exception: meta={}
    for key,label in [("revenueGrowth","Revenue growth"),("earningsGrowth","Earnings growth"),
                      ("profitMargins","Profit margin"),("operatingMargins","Operating margin"),
                      ("debtToEquity","Debt / equity")]:
        v=meta.get(key) if isinstance(meta,dict) else None
        if v is None or pd.isna(v): continue
        if key=="debtToEquity":
            reading=f"{float(v):.1f}"
            interp="Balance-sheet leverage observation"
        else:
            reading=f"{float(v):+.1%}"
            interp="Provider-reported fundamental input"
        add("Fundamentals",label,reading,interp)
    return pd.DataFrame(rows)

def disagreement_snapshot(ticker, price, h):
    """Identify where market, analysts, quant and user DCF differ materially."""
    a=analyst_consensus_snapshot(ticker)
    fc=research_forecast(h)
    q12=np.nan
    if fc is not None and not fc.empty:
        q=fc.loc[fc["Horizon"]=="12 Months","Median forecast"]
        if len(q) and pd.notna(q.iloc[0]): q12=float(q.iloc[0])
    vals=valuation_snapshot(ticker,price)
    base=np.nan
    if vals is not None and not vals.empty:
        sc=next((c for c in vals.columns if str(c).lower()=="scenario"),None)
        vc=next((c for c in vals.columns if str(c).lower()=="value_per_share"),None)
        if sc and vc:
            q=vals[vals[sc].astype(str).str.lower()=="base"]
            if not q.empty:
                base=pd.to_numeric(q[vc],errors="coerce").iloc[0]
    points={"Market":price,"Analysts":a.get("target_mean",np.nan),"Quant 12M":q12,"User DCF":base}
    valid={k:float(v) for k,v in points.items() if v is not None and pd.notna(v) and float(v)>0}
    rows=[]
    for k,v in valid.items():
        if k=="Market": continue
        gap=v/price-1
        rows.append({"Evidence source":k,"Reference value":v,"Difference vs market":gap,
                     "What differs":("Above current market price" if gap>0 else "Below current market price" if gap<0 else "Aligned with market")})
    return pd.DataFrame(rows)

def render_whats_market_missing(ticker, price, h):
    st.subheader("What's the market disagreement?")
    st.caption("This section identifies differences between evidence sources. It does not claim that the market or any model is wrong.")
    d=disagreement_snapshot(ticker,price,h)
    if d.empty:
        st.info("Not enough independent valuation/forecast evidence is available to compare.")
        return
    st.dataframe(d.style.format({"Reference value":"{:,.3f}","Difference vs market":"{:+.1%}"},na_rep="—"),
                 use_container_width=True,hide_index=True)
    biggest=d.loc[d["Difference vs market"].abs().idxmax()]
    st.write(f"The largest currently measurable disagreement is **{biggest['Evidence source']}**, "
             f"which is {biggest['Difference vs market']:+.1%} relative to the current market price. "
             "Open the underlying valuation, analyst evidence and forecast sections to inspect the assumptions behind that difference.")

def render_phase2_company_research(ticker, h, price=None, meta=None, compact=False):
    """Expandable evidence-first research panel used by Markets and Command Centre."""
    if h is None or h.empty:
        st.warning("Historical market data is unavailable for this company.")
        return
    if price is None:
        price=float(pd.to_numeric(h["Close"],errors="coerce").dropna().iloc[-1])
    if meta is None:
        try: meta=yf.Ticker(ticker).info or {}
        except Exception: meta={}
    name=(meta.get("longName") or meta.get("shortName") or identity(ticker)) if isinstance(meta,dict) else identity(ticker)

    st.subheader(f"{name} — Research Intelligence")
    tabs=st.tabs(["Market","Performance & Forecast","Analysts","Forecast Drivers","Market Disagreement","Evidence"])
    with tabs[0]:
        ms=market_structure(h)
        c=st.columns(4)
        metric_box(c[0],"Price",display_price(price,ticker))
        metric_box(c[1],"52W low","—" if pd.isna(ms.get("Period low",np.nan)) else display_price(ms["Period low"],ticker))
        metric_box(c[2],"52W high","—" if pd.isna(ms.get("Period high",np.nan)) else display_price(ms["Period high"],ticker))
        beta=meta.get("beta") if isinstance(meta,dict) else None
        metric_box(c[3],"Beta","—" if beta is None or pd.isna(beta) else f"{float(beta):.2f}")
        c=st.columns(4)
        mc=meta.get("marketCap") if isinstance(meta,dict) else None
        av=meta.get("averageVolume") if isinstance(meta,dict) else None
        dy=meta.get("dividendYield") if isinstance(meta,dict) else None
        vol=pd.to_numeric(h["Close"],errors="coerce").pct_change().tail(252).std()*np.sqrt(252)
        metric_box(c[0],"Market cap","—" if mc is None else compact_number(mc))
        metric_box(c[1],"Average volume","—" if av is None else compact_number(av))
        metric_box(c[2],"Annualised volatility","—" if pd.isna(vol) else f"{vol:.1%}")
        metric_box(c[3],"Dividend yield","—" if dy is None or pd.isna(dy) else f"{float(dy):.2%}")

    with tabs[1]:
        fc=research_forecast(h)
        px=pd.to_numeric(h["Close"],errors="coerce").dropna()
        actual={}
        for n,label in [(21,"1 Month"),(63,"3 Months"),(126,"6 Months"),(252,"12 Months")]:
            actual[label]=np.nan if len(px)<=n else float(px.iloc[-1]/px.iloc[-n-1]-1)
        if fc.empty:
            st.info("Insufficient history for forecast research.")
        else:
            show=fc[["Horizon","Median forecast","Low case (20%)","High case (80%)","Median return","Positive-return frequency","Sample size"]].copy()
            show.insert(1,"Actual trailing return",show["Horizon"].map(actual))
            st.dataframe(show.style.format({
                "Median forecast":"{:,.3f}","Low case (20%)":"{:,.3f}","High case (80%)":"{:,.3f}",
                "Actual trailing return":"{:+.1%}","Median return":"{:+.1%}",
                "Positive-return frequency":"{:.1%}"},na_rep="—"),use_container_width=True,hide_index=True)
            st.caption("Positive-return frequency is a weighted historical frequency, not a calibrated probability of the future.")

    with tabs[2]:
        render_analyst_consensus(ticker,price)
        ev=analyst_evidence(ticker)
        st.markdown("**Recent analyst actions**")
        if ev.empty:
            st.info("No dated analyst upgrade/downgrade evidence was returned by the current provider.")
        else:
            st.dataframe(ev,use_container_width=True,hide_index=True)
            st.caption("Dated analyst actions are provider-supplied external evidence and are separate from Chrímata's models.")

    with tabs[3]:
        drivers=forecast_driver_snapshot(ticker,h,meta)
        if drivers.empty:
            st.info("No explainable forecast context is available.")
        else:
            st.dataframe(drivers,use_container_width=True,hide_index=True)
        st.caption("These are observable context factors, not hidden AI weights. The current forecast itself is based on historical horizon-return distributions.")

    with tabs[4]:
        render_whats_market_missing(ticker,price,h)

    with tabs[5]:
        st.markdown("**Evidence provenance**")
        st.write("Market history: Yahoo Finance/yfinance fallback unless another configured provider supplies the observation.")
        st.write("Analyst consensus/actions: Yahoo Finance via yfinance when available.")
        st.write("Quant forecast: deterministic recency-weighted historical horizon-return distribution calculated inside this app.")
        st.write("DCF: the app's saved valuation assumptions. Review those assumptions before interpreting the output.")
        st.write("Fundamental driver observations: provider-reported fields and should be verified against company filings for material decisions.")

def render_market_vs_model(ticker, price, h):
    st.subheader("Market vs Model")
    st.caption("Compares independent evidence sources. Differences are analytical disagreements, not a recommendation.")
    a=analyst_consensus_snapshot(ticker)
    fc=research_forecast(h)
    f12=np.nan
    if fc is not None and not fc.empty:
        z=fc.loc[fc["Horizon"]=="12 Months","Median forecast"]
        if len(z): f12=float(z.iloc[0]) if pd.notna(z.iloc[0]) else np.nan
    vals=valuation_snapshot(ticker,price)
    base=np.nan
    if vals is not None and not vals.empty:
        scen_col=next((c for c in vals.columns if str(c).lower()=="scenario"),None)
        val_col=next((c for c in vals.columns if str(c).lower()=="value_per_share"),None)
        if scen_col and val_col:
            q=vals[vals[scen_col].astype(str).str.lower()=="base"]
            if not q.empty: base=pd.to_numeric(q[val_col],errors="coerce").iloc[0]
    c=st.columns(4)
    metric_box(c[0],"Market price",display_price(price,ticker))
    metric_box(c[1],"Analyst mean target","—" if pd.isna(a["target_mean"]) else display_price(a["target_mean"],ticker))
    metric_box(c[2],"Quant 12M scenario","—" if pd.isna(f12) else display_price(f12,ticker))
    metric_box(c[3],"User-model base DCF","—" if pd.isna(base) else display_price(base,ticker))
    st.caption("Analyst target = external analyst data. Quant scenario = historical return-distribution model. DCF = saved user assumptions; generic defaults must be replaced before relying on it.")

if page=="Markets":
    st.header("Global Market Opportunity Dashboard")
    with st.expander("🔎 Universal symbol search",expanded=False):
        _uq=st.text_input("Find any company or ticker",placeholder="Pepsi, PEP, Qantas, QAN, Zip, ZIP…",key="market_universal_query")
        if _uq.strip():
            _um=search_securities(_uq,_search_key)
            if _um.empty:
                st.info("No matching listing was returned.")
            else:
                _display=_um.head(20).copy()
                _cols=[c for c in ["Symbol","Company","Exchange","Type","Country","Currency","Source"] if c in _display.columns]
                st.dataframe(_display[_cols],use_container_width=True,hide_index=True)
                _opts=[f"{r.get('Symbol','')} · {r.get('Company','')} · {r.get('Exchange','')}" for _,r in _display.iterrows()]
                _open=st.selectbox("Select listing",_opts,key="market_universal_open")
                if st.button("Set as current company",key="market_use_company"):
                    _rr=_display.iloc[_opts.index(_open)]
                    _tt=resolve_listing(_rr["Symbol"],_rr.get("Exchange",""),_rr.get("Country",""))
                    st.session_state["mia_search_query"]=_tt
                    st.success(f"Current-company search set to {_tt}. The sidebar will use this listing on the next rerun.")
                    st.rerun()

    st.caption("Discover and compare companies across markets. Forecast columns are model research, not promises or recommendations.")

    try:
        td_key=st.secrets.get("TWELVE_DATA_API_KEY","")
    except Exception:
        td_key=""

    market=st.radio("Market",["ASX","NASDAQ","NYSE","LSE","HKEX","TSE","TSX","Commodities"],horizontal=True)
    c1,c2,c3=st.columns([1,1,2])
    page_no=c1.number_input("Catalog page",1,1000,1,1,key="v19_catalog_page")
    page_size=c2.selectbox("Rows per page",[25,50,100,250],index=1,key="v19_page_size")
    search=c3.text_input("Search this market","",key="v19_market_search").strip().lower()

    if market=="Commodities":
        catalog=commodity_catalog(td_key)
    else:
        catalog=td_catalog(td_key,market,int(page_no),int(page_size)) if td_key else fallback_catalog(market)
        if catalog is None or catalog.empty:
            catalog=fallback_catalog(market)

    if catalog is None or catalog.empty:
        st.warning("No catalog data returned for this market.")
    else:
        if search:
            mask=pd.Series(False,index=catalog.index)
            for col in [x for x in ["symbol","name","instrument_name"] if x in catalog.columns]:
                mask=mask | catalog[col].astype(str).str.lower().str.contains(search,regex=False)
            catalog=catalog[mask]

        showcols=[c for c in ["symbol","name","instrument_name","exchange","country","currency","type","category"] if c in catalog.columns]
        st.subheader(f"{market} universe")
        st.dataframe(catalog[showcols] if showcols else catalog,use_container_width=True,hide_index=True,height=300)

        symbols=catalog["symbol"].astype(str).tolist() if "symbol" in catalog.columns else []
        defaults=symbols[:min(6,len(symbols))]
        selected=st.multiselect("Research companies",symbols,default=defaults,
            help="Choose a manageable set. Each company requires historical-data calculations.",key="v19_research_symbols")

        if selected and market!="Commodities":
            if st.button("Scan selected companies for changes",key="v19_phase3_scan"):
                scanned=0; detected=0
                with st.spinner("Comparing selected companies with their last saved monitoring snapshots…"):
                    for _sym in selected[:12]:
                        _ys=global_yahoo_symbol(_sym,market)
                        _h=history(_ys,"2y")
                        try: _m=yf.Ticker(_ys).info or {}
                        except Exception: _m={}
                        _n,_events=save_monitoring_snapshot(_ys,_h,_m)
                        scanned+=_n; detected+=len(_events)
                st.success(f"Scanned {scanned} companies and recorded {detected} material change event(s).")
            if len(selected)>12:
                st.warning("V19 limits deep opportunity research to the first 12 selected companies to reduce provider throttling.")
                selected=selected[:12]
            rows=[]
            with st.spinner("Building opportunity dashboard…"):
                for sym in selected:
                    snap=opportunity_snapshot(sym,market)
                    if snap: rows.append(snap)
            if rows:
                opp=pd.DataFrame(rows)
                st.subheader("Opportunity research")
                fmt={c:"{:+.1%}" for c in ["Actual 1M","Actual 3M","Actual 6M","Actual 12M",
                                           "Model 1M","Model 3M","Model 6M","Model 12M","52W position"]}
                fmt.update({"Price":"{:,.3f}","52W low":"{:,.3f}","52W high":"{:,.3f}"})
                st.dataframe(opp.style.format(fmt,na_rep="—"),use_container_width=True,hide_index=True,height=420)
                st.caption("Actual = realised trailing return. Model = median recency-weighted historical horizon return. 52W position shows where price sits between its trailing 52-week low and high.")

                focus=st.selectbox("Open research preview",opp["Ticker"].tolist(),key="v19_focus_company")
                row=opp.loc[opp["Ticker"]==focus].iloc[0]
                st.subheader(f"{row['Company']} — research preview")
                q1,q2,q3,q4=st.columns(4)
                metric_box(q1,"Price",display_price(row["Price"],focus))
                metric_box(q2,"52W position","—" if pd.isna(row["52W position"]) else f"{row['52W position']:.0%}")
                metric_box(q3,"12M actual","—" if pd.isna(row["Actual 12M"]) else f"{row['Actual 12M']:+.1%}")
                metric_box(q4,"12M model","—" if pd.isna(row["Model 12M"]) else f"{row['Model 12M']:+.1%}")
                with st.expander(f"Deep research — {focus}",expanded=True):
                    fh=history(focus,"2y")
                    try:
                        fm=yf.Ticker(focus).info or {}
                    except Exception:
                        fm={}
                    render_phase2_company_research(focus,fh,float(row["Price"]),fm,compact=True)
                st.info("For portfolio/thesis tools, enter this ticker in the sidebar and open Company Command Centre.")
            else:
                st.warning("No historical data was returned for the selected companies.")
        elif selected:
            st.subheader("Tracked commodity data")
            quotes=live_rows(selected,td_key,None,False)
            st.dataframe(quotes,use_container_width=True,hide_index=True)

elif page=="Advanced Forecasting":
    render_advanced_forecasting(ticker,h)

elif page=="Report Intelligence":
    render_report_intelligence(ticker)

elif page=="Something Changed":
    st.header("Something Changed")
    st.caption("Material changes recorded by your saved point-in-time monitoring snapshots.")
    v19_phase3_db_upgrade()
    all_events=monitoring_events(None,200,False)
    if all_events.empty:
        st.info("No change events have been recorded yet. Use Markets → Scan selected companies for changes, or save snapshots from a Company Command Centre.")
    else:
        c1,c2,c3=st.columns(3)
        c1.metric("Recorded changes",str(len(all_events)))
        c2.metric("Unacknowledged",str(int((all_events["acknowledged"]==0).sum())))
        c3.metric("Companies",str(all_events["ticker"].nunique()))
        category=st.multiselect("Category",sorted(all_events["category"].dropna().unique().tolist()),key="phase3_event_categories")
        show=all_events if not category else all_events[all_events["category"].isin(category)]
        st.dataframe(show,use_container_width=True,hide_index=True,height=520)
        st.caption("Events are descriptive threshold/crossing detections. Review the underlying company evidence before drawing an investment conclusion.")

elif page=="Dashboard":
    render_global_market_overview()

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
    identity_text_card(r1, "Sector",cls["sector"]); identity_text_card(r2, "Industry",cls["industry"])
    identity_text_card(r3, "Market benchmark",bm_name); metric_box(r4, "Price",display_price(price,ticker))

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
    v18_db_upgrade(); vp=valuation_profile(ticker)
    a,b,c=st.columns(3)
    fcf=a.number_input("Starting annual FCF",value=float(vp["fcf"]),step=1_000_000.0,key="v18_val_fcf")
    shares=b.number_input("Shares outstanding",value=float(vp["shares"]),step=1_000_000.0,key="v18_val_shares")
    debt=c.number_input("Net debt (negative = net cash)",value=float(vp["net_debt"]),step=1_000_000.0,key="v18_val_debt")
    st.markdown("#### Scenario assumptions")
    rows=[]
    vals={}
    for label,key in [("Bear","bear"),("Base","base"),("Bull","bull")]:
        c1,c2,c3=st.columns(3)
        vals[f"{key}_growth"]=c1.number_input(f"{label} 5Y FCF growth",value=float(vp[f"{key}_growth"]),format="%.3f",key=f"v18_{key}_g")
        vals[f"{key}_wacc"]=c2.number_input(f"{label} WACC",value=float(vp[f"{key}_wacc"]),format="%.3f",key=f"v18_{key}_w")
        vals[f"{key}_terminal"]=c3.number_input(f"{label} terminal growth",value=float(vp[f"{key}_terminal"]),format="%.3f",key=f"v18_{key}_t")
    profile={"fcf":fcf,"shares":shares,"net_debt":debt,**vals}
    if st.button("Save valuation assumptions",type="primary"):
        save_valuation_profile(ticker,profile); st.success("Valuation assumptions saved."); st.rerun()
    assumptions={"Bear":{"growth":vals["bear_growth"],"wacc":vals["bear_wacc"],"terminal_growth":vals["bear_terminal"]},
                 "Base":{"growth":vals["base_growth"],"wacc":vals["base_wacc"],"terminal_growth":vals["base_terminal"]},
                 "Bull":{"growth":vals["bull_growth"],"wacc":vals["bull_wacc"],"terminal_growth":vals["bull_terminal"]}}
    v=scenarios(fcf,shares,debt,assumptions); v["margin_of_safety"]=v.value_per_share.map(lambda x:margin_of_safety(price,x))
    st.dataframe(v,use_container_width=True,hide_index=True)
    st.subheader("Reverse valuation")
    rt=reverse_targets(ticker)
    rt["Implied 5Y FCF growth"]=rt["Implied 5Y FCF growth"].map(lambda x:"—" if pd.isna(x) else f"{x:.1%}")
    st.dataframe(rt,use_container_width=True,hide_index=True)
    st.caption("Outputs are assumption-sensitive. Store only inputs you can defend; reported company values should be verified against source documents.")

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
        metric_box(c1,"Price",display_price(ref,ticker))
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
    v18_db_upgrade()
    cls=safe_company_classification(ticker)
    h=history(ticker,"1y")
    if h.empty:
        st.warning("No price history available.")
    else:
        price=float(h["Close"].iloc[-1]); hold=holding_for(ticker); tr=technical_regime(h,ticker)
        st.markdown(f"""<div class="mia-hero">
          <div class="mia-hero-kicker">Company Command Centre</div>
          <div class="mia-hero-title">{name} · {ticker}</div>
          <div class="mia-hero-sub">Price {display_price(price,ticker)} · Evidence, valuation, forecasting, thesis and change monitoring in one workspace.</div>
        </div>""",unsafe_allow_html=True)
        company_snapshot_header(ticker, meta, h, cls)
        st.markdown('<div class="mia-section-label">Research scorecard</div>',unsafe_allow_html=True)
        render_mia_research_score(ticker,h,meta)
        st.divider()
        st.markdown('<div class="mia-section-label">Research stack</div>',unsafe_allow_html=True)
        st.subheader("Investment Command Centre")
        render_analyst_consensus(ticker,price)
        st.divider()
        render_forecast_tool(ticker,h)
        st.divider()
        render_market_vs_model(ticker,price,h)
        st.divider()
        render_phase2_company_research(ticker,h,price,meta)
        st.divider()
        render_something_changed(ticker,h,meta)
        st.divider()
        st.subheader("Your position")
        a,b,c,d=st.columns(4)
        a.metric("Shares",f"{hold['quantity']:,.0f}")
        b.metric("Average cost",f"${hold['avg_cost']:,.3f}" if hold["quantity"] else "—")
        c.metric("Market value",f"${hold['quantity']*price:,.0f}")
        pnl=(price-hold["avg_cost"])*hold["quantity"] if hold["quantity"] else 0
        d.metric("Unrealised P&L",f"${pnl:,.0f}" if hold["quantity"] else "—")

        st.subheader("What requires my attention?")
        st.dataframe(v18_attention(ticker,0,price),use_container_width=True,hide_index=True)

        l,r=st.columns(2)
        with l:
            st.subheader("Thesis")
            t=thesis_table(ticker)
            if t.empty: st.info("No measurable thesis conditions yet.")
            else:
                met=int((t["status"]=="Met").sum())
                st.metric("Conditions met",f"{met} / {len(t)}")
                st.dataframe(t[["metric","current_value","operator","threshold","status","source"]],use_container_width=True,hide_index=True)
            st.subheader("What changed since last review?")
            kc=kpi_latest_comparison(ticker)
            if kc.empty: st.info("No KPI observations have been recorded yet. Use Monitor My Thesis → Evidence capture.")
            else: st.dataframe(kc,use_container_width=True,hide_index=True)
        with r:
            st.subheader("Market structure")
            q1,q2=st.columns(2)
            q1.metric("Trend regime",tr.get("Trend","—"))
            q2.metric("Relative strength 3M","—" if pd.isna(tr.get("Relative 3M",np.nan)) else f"{tr['Relative 3M']:+.1%}")
            st.write(f"Support **${tr['Support']:,.3f}** · Resistance **${tr['Resistance']:,.3f}**")
            st.write(f"20D volume **{tr['Volume ratio']:.2f}×** · Annualised volatility **{tr['Annualised volatility']:.1%}**")
            st.caption(f"Relative-strength benchmark: {tr.get('Benchmark','—')}")

            st.subheader("Valuation scenarios")
            vv=valuation_snapshot(ticker,price)
            if vv.empty: st.info("Valuation scenario could not be calculated.")
            else: st.dataframe(vv,use_container_width=True,hide_index=True)

        st.subheader("Latest announcements")
        aa=latest_announcements_safe(ticker,5)
        if aa.empty: st.info("No announcement rows are available from the current announcement provider.")
        else: st.dataframe(aa,use_container_width=True,hide_index=True)

        st.subheader("Catalysts")
        cats=catalysts_safe(ticker,6)
        if not cats.empty:
            st.dataframe(cats,use_container_width=True,hide_index=True)
        else:
            st.info("No catalysts recorded yet.")

        st.markdown("---")
        st.markdown("### Core workflows")
        x,y=st.columns(2)
        x.info("**BEFORE I INVEST**\n\nRun a decision brief that combines position impact, valuation, thesis evidence, market structure and catalysts.")
        y.info("**MONITOR MY THESIS**\n\nCapture company-reported KPI evidence and compare the latest observation with the previous one.")
        st.caption("Evidence discipline: company-reported KPI values are only shown after they have been explicitly captured with a source. The app does not invent missing reported figures.")

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
        st.dataframe(v18_attention(ticker,amount,d["price"]),use_container_width=True,hide_index=True)

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
            cls=safe_company_classification(ticker)
            st.write(" • ".join(company_kpi_template(ticker,cls.get("sector",""),cls.get("industry",""))))
        with right:
            st.subheader("Technical & market context")
            st.dataframe(d["confluence"],use_container_width=True,hide_index=True)
            ms=d["market"]
            st.write(f"20D support: **${ms['20D support']:,.3f}**  |  20D resistance: **${ms['20D resistance']:,.3f}**")
            st.write(f"52-week/period range: **${ms['Period low']:,.3f} – ${ms['Period high']:,.3f}**")

        st.subheader("Valuation & expectations")
        vv=valuation_snapshot(ticker,d["price"])
        if vv.empty: st.info("Valuation scenario could not be calculated.")
        else: st.dataframe(vv,use_container_width=True,hide_index=True)
        rt=reverse_targets(ticker)
        if not rt.empty:
            rt2=rt.copy()
            rt2["Implied 5Y FCF growth"]=rt2["Implied 5Y FCF growth"].map(lambda x:"—" if pd.isna(x) else f"{x:.1%}")
            st.caption("Reverse valuation: approximate FCF growth required by the stored base WACC/terminal-growth assumptions.")
            st.dataframe(rt2,use_container_width=True,hide_index=True)

        st.subheader("Latest KPI evidence")
        kc=kpi_latest_comparison(ticker)
        if not kc.empty:
            st.dataframe(kc,use_container_width=True,hide_index=True)
        else:
            st.info("No company KPI evidence captured yet.")

        st.subheader("Latest announcements")
        aa=latest_announcements_safe(ticker,3)
        if not aa.empty:
            st.dataframe(aa,use_container_width=True,hide_index=True)
        else:
            st.info("No announcement rows available from the current provider.")

        st.subheader("Catalysts")
        cats=catalysts_safe(ticker,8)
        if not cats.empty:
            st.dataframe(cats,use_container_width=True,hide_index=True)
        else:
            st.info("No catalysts stored yet.")

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
    render_something_changed(ticker,h,meta)
    st.divider()
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

    st.subheader("Confirmed report-to-report KPI changes")
    _ri_comp=compare_report_kpis(ticker)
    if _ri_comp.empty:
        st.info("No confirmed report-to-report KPI comparison is available yet. Use Report Intelligence to ingest and verify company reports.")
    else:
        st.dataframe(_ri_comp.style.format({"Change":"{:+.1%}"},na_rep="—"),use_container_width=True,hide_index=True)
    st.subheader("Company KPI evidence")
    cls=safe_company_classification(ticker)
    kpis=company_kpi_template(ticker,cls.get("sector",""),cls.get("industry",""))
    with st.expander("Capture a company-reported KPI observation",expanded=False):
        km=st.selectbox("KPI",kpis,key="v18_kpi_metric")
        kp=st.text_input("Reporting period",placeholder="e.g. FY26 / H1 FY27",key="v18_kpi_period")
        c1,c2=st.columns(2)
        kv=c1.number_input("Reported value",value=0.0,key="v18_kpi_value")
        ku=c2.text_input("Unit",placeholder="%, $m, customers, etc.",key="v18_kpi_unit")
        ks=st.text_input("Source / report title",placeholder="e.g. FY26 Results Presentation",key="v18_kpi_source")
        kurl=st.text_input("Source URL (optional)",key="v18_kpi_url")
        kn=st.text_area("Evidence note",placeholder="Page/section and concise context",key="v18_kpi_note")
        if st.button("Save reported KPI evidence",type="primary",key="v18_save_kpi"):
            if not kp.strip() or not ks.strip():
                st.error("Reporting period and source are required so the value is not presented without provenance.")
            else:
                save_kpi_observation(ticker,km,kp,kv,ku,ks,kurl,kn); st.success("KPI evidence saved."); st.rerun()
    kc=kpi_latest_comparison(ticker)
    if kc.empty: st.info("No company KPI observations recorded yet.")
    else:
        st.subheader("What changed in company KPIs?")
        st.dataframe(kc,use_container_width=True,hide_index=True)

    st.subheader("Attention queue")
    att=v18_attention(ticker)
    st.dataframe(att,use_container_width=True,hide_index=True)

    st.subheader("Monitoring controls")
    st.write("Use **Catalyst Calendar** for expected events, **Alerts** for stored market/technical thresholds, and **Announcements & Reports** to inspect new company evidence and original documents.")
    st.caption("Background alert delivery is not yet a durable service in this Streamlit prototype; V17 stores the monitoring rules and review baselines.")


elif page=="Thesis Scorecard":
    st.header(f"Investment Thesis Scorecard — {ticker}")
    st.caption("Convert the investment thesis into measurable conditions. Status is descriptive; it is not an investment recommendation.")
    # Migrate the retained Streamlit Cloud DB before this page reads it.
    v18_db_upgrade()
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
    thesis_cols=["id","metric","operator","threshold","current_value","status","source","updated_at"]
    try:
        rows=con.execute(
            "SELECT id,metric,operator,threshold,current_value,status,source,updated_at "
            "FROM thesis_rules WHERE ticker=? ORDER BY id",(ticker,)
        ).fetchall()
        df=pd.DataFrame(rows,columns=thesis_cols)
    except Exception as exc:
        df=pd.DataFrame(columns=thesis_cols)
        st.warning(f"Thesis conditions could not be loaded: {exc}")
    finally:
        con.close()
    if not df.empty:
        st.dataframe(df,use_container_width=True,hide_index=True)
    else:
        st.info("No measurable thesis conditions yet.")

elif page=="Catalyst Calendar":
    st.header(f"Catalyst Calendar — {ticker}")
    # Ensure retained Cloud databases have the current catalyst schema.
    v18_db_upgrade()
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
    catalyst_cols=["id","event_date","event","category","status","source"]
    try:
        rows=con.execute(
            "SELECT id,event_date,event,category,status,source "
            "FROM catalysts WHERE ticker=? ORDER BY event_date",(ticker,)
        ).fetchall()
        cats=pd.DataFrame(rows,columns=catalyst_cols)
    except Exception as exc:
        cats=pd.DataFrame(columns=catalyst_cols)
        st.warning(f"Catalysts could not be loaded: {exc}"); con.close()
    if not cats.empty:
        st.dataframe(cats,use_container_width=True,hide_index=True)
    else:
        st.info("No catalysts recorded.")

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
    if not adf.empty:
        st.dataframe(adf,use_container_width=True,hide_index=True)
    else:
        st.info("No alert rules saved.")

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
    render_forecast_tool(ticker,h)
    st.divider()
    render_advanced_forecasting(ticker,h)
    st.divider()
    render_analyst_consensus(ticker,price)

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
