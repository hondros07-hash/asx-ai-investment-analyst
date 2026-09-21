import streamlit as st
import streamlit.components.v1 as components
from zoneinfo import ZoneInfo
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import re
import html
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
from global_dividends import upcoming_dividends
from corporate_actions_calendar import corporate_actions_calendar

import sqlite3
import uuid
from datetime import datetime, timezone

import json
import base64
from pathlib import Path

st.set_page_config(page_title="Chrímata - Market Investment Analyst", page_icon="🏛️", layout="wide")


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


# V19.8.7 — aligned fixed terminal shell. Sidebar and main canvas use explicit desktop columns.
st.markdown(r"""
<style>
html,body,.stApp,[data-testid="stAppViewContainer"]{margin:0!important;padding:0!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none!important;height:0!important;}
[data-testid="stAppViewContainer"]>.main{padding-top:0!important;}
.main{margin-left:214px!important;width:calc(100vw - 214px)!important;max-width:calc(100vw - 214px)!important;}
.main .block-container{max-width:none!important;width:100%!important;padding:115px .72rem 1rem!important;margin:0!important;box-sizing:border-box!important;}

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
 .main{margin-left:190px!important;width:calc(100vw - 190px)!important;max-width:calc(100vw - 190px)!important;}
 .main div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important;}
}
</style>
""", unsafe_allow_html=True)

# V20.0.0 — structural landing-page rebuild. This final layer intentionally overrides legacy V19 shell offsets.
st.markdown(r"""
<style>
:root{--chr-sidebar:214px;--chr-banner:108px;--chr-blue:#0b63ce;--chr-navy:#06355f;}
html,body,.stApp,[data-testid="stAppViewContainer"]{margin:0!important;padding:0!important;background:#f7faff!important;}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu{display:none!important;height:0!important;}
/* Main canvas stays viewport-wide, while its CONTENT reserves the sidebar column. This avoids Streamlit DOM-version margin quirks. */
.main,[data-testid="stAppViewContainer"]>.main,section.main{margin-left:0!important;width:100vw!important;max-width:100vw!important;padding:0!important;}
.main .block-container,[data-testid="stAppViewContainer"]>.main .block-container,section.main .block-container{
  max-width:none!important;width:100%!important;margin:0!important;box-sizing:border-box!important;
  padding:calc(var(--chr-banner) + 8px) 14px 18px calc(var(--chr-sidebar) + 14px)!important;
}
/* Exact supplied banner: no generated text overlay, no cover crop, no gradient. */
.chrimata-terminal-hero.chrimata-exact-hero{position:fixed!important;left:0!important;top:0!important;right:0!important;width:100vw!important;height:var(--chr-banner)!important;margin:0!important;z-index:1000000!important;overflow:hidden!important;background:#062f59!important;}
.chrimata-terminal-hero.chrimata-exact-hero:after{display:none!important;content:none!important;}
.chrimata-terminal-hero.chrimata-exact-hero img{display:block!important;width:100%!important;height:100%!important;object-fit:fill!important;object-position:center!important;filter:none!important;}
.chrimata-terminal-hero .chrimata-brand,.chrimata-terminal-hero .chrimata-quote{display:none!important;}
.chrimata-banner-fallback{display:flex!important;align-items:center!important;gap:18px!important;padding:0 24px!important;color:#fff!important;}
.chrimata-banner-fallback b{font-family:Georgia,serif;font-size:30px}.chrimata-banner-fallback span{font-size:13px}
/* Sidebar owns the left rail below the banner and can never cover reserved content. */
[data-testid="stSidebar"]{position:fixed!important;left:0!important;top:var(--chr-banner)!important;bottom:0!important;height:calc(100vh - var(--chr-banner))!important;width:var(--chr-sidebar)!important;min-width:var(--chr-sidebar)!important;max-width:var(--chr-sidebar)!important;transform:none!important;visibility:visible!important;display:block!important;background:linear-gradient(180deg,#063b68 0%,#07365f 56%,#052b4e 100%)!important;border-right:1px solid #0a4c7e!important;z-index:999998!important;}
[data-testid="stSidebar"]>div:first-child{width:100%!important;height:100%!important;padding:0!important;overflow-y:auto!important;}
[data-testid="stSidebar"] .block-container{padding:12px 10px 16px!important;}
/* Pull landing controls directly under the banner. */
.main div[data-testid="stHorizontalBlock"]{gap:8px!important;}
.main [data-testid="stTextInput"]{margin:0!important}.main [data-testid="stTextInput"] input{height:40px!important;min-height:40px!important;border:1px solid #d5e0ed!important;background:#fff!important;}
.main div[data-testid="stRadio"]{margin:0!important}.main div[data-testid="stRadio"] div[role="radiogroup"]{gap:6px!important;margin:0!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"] label{min-height:40px!important;padding:7px 12px!important;border-radius:6px!important;}
.chrimata-market-title{margin:5px 0 0!important;display:flex!important;align-items:center!important;gap:7px!important}.chrimata-market-name{font-size:23px!important;color:#10264b!important;font-weight:800!important}.chrimata-market-note{margin:0 0 8px 34px!important;color:#6b7f9b!important;}
/* Clean terminal cards close to the approved concept. */
.main div[data-testid="stMetric"]{min-height:92px!important;padding:10px 13px!important;border:1px solid #d7e2ee!important;border-radius:7px!important;background:#fff!important;box-shadow:0 1px 2px rgba(15,45,80,.04)!important;}
.main div[data-testid="stMetricValue"]{font-size:1.38rem!important;font-weight:750!important;color:#10264b!important}.main div[data-testid="stMetricLabel"] p{font-size:.76rem!important;font-weight:700!important;color:#536a86!important}.main div[data-testid="stMetricDelta"]{font-size:.72rem!important;}
.main h2{color:#10264b!important}.main h3{color:#123e78!important;font-weight:750!important;}
.main [data-testid="stDataFrame"]{background:#fff!important;border:1px solid #dbe5ef!important;border-radius:7px!important;}
.main [data-testid="stPlotlyChart"],.main [data-testid="stArrowVegaLiteChart"]{background:#fff!important;border:1px solid #dbe5ef!important;border-radius:7px!important;padding:4px!important;}
.chrimata-terminal-footer{margin-left:0!important;}
/* Prevent legacy sidebar/search elements from visually floating over the home canvas. */
[data-testid="stSidebarCollapsedControl"],button[data-testid="stSidebarCollapseButton"]{display:none!important;}
@media(max-width:1100px){:root{--chr-sidebar:196px}.main .block-container,[data-testid="stAppViewContainer"]>.main .block-container,section.main .block-container{padding-left:calc(var(--chr-sidebar) + 10px)!important}.main div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important;}}
@media(max-width:760px){:root{--chr-sidebar:0px;--chr-banner:74px}[data-testid="stSidebar"]{display:none!important}.main .block-container,[data-testid="stAppViewContainer"]>.main .block-container,section.main .block-container{padding:82px 8px 14px!important}.chrimata-terminal-hero.chrimata-exact-hero{height:74px!important}.main div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important;}}
</style>
""", unsafe_allow_html=True)

# V20.1.0 — definitive desktop shell geometry + reference landing canvas.
st.markdown(r"""
<style>
:root{--chr-sidebar:228px;--chr-banner:108px;}
/* Streamlit's current main node must physically start AFTER the fixed sidebar.
   Previous builds only padded the inner block, so column children could still paint underneath the rail. */
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > section.main,
section[data-testid="stMain"],
.stMain{
  position:relative!important;
  margin-left:var(--chr-sidebar)!important;
  width:calc(100vw - var(--chr-sidebar))!important;
  max-width:calc(100vw - var(--chr-sidebar))!important;
  min-width:0!important;
  padding:0!important;
  overflow-x:hidden!important;
  box-sizing:border-box!important;
}
.main .block-container,
section.main .block-container,
[data-testid="stMainBlockContainer"],
.stMainBlockContainer{
  width:100%!important;max-width:none!important;min-width:0!important;
  margin:0!important;padding:calc(var(--chr-banner) + 12px) 12px 18px!important;
  box-sizing:border-box!important;overflow:visible!important;
}
[data-testid="stSidebar"]{width:var(--chr-sidebar)!important;min-width:var(--chr-sidebar)!important;max-width:var(--chr-sidebar)!important;}
[data-testid="stSidebar"]>div:first-child{width:var(--chr-sidebar)!important;}
/* Home dashboard density and card proportions from the approved reference. */
.chrimata-home-intro{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin:5px 1px 8px}
.chrimata-home-title{font-size:23px;font-weight:800;line-height:1.1;color:#10264b}
.chrimata-home-meta{font-size:11px;color:#7185a0;margin-top:4px}
.chrimata-home-quote{font:italic 15px Georgia,serif;color:#36577e;text-align:right;padding:4px 8px 0 0;white-space:nowrap}
.main div[data-testid="stMetric"]{min-height:98px!important;padding:10px 13px!important;overflow:hidden!important}
.main div[data-testid="stMetricValue"]{font-size:1.48rem!important}
.main [data-testid="stHorizontalBlock"]{align-items:stretch!important;min-width:0!important}
.main [data-testid="column"]{min-width:0!important;overflow:hidden!important}
.main h3{font-size:.93rem!important;margin:.38rem 0 .3rem!important;color:#183e72!important}
.main [data-testid="stDataFrame"]{font-size:.76rem!important}
.main [data-testid="stPlotlyChart"],.main [data-testid="stArrowVegaLiteChart"]{overflow:hidden!important}
@media(max-width:1100px){:root{--chr-sidebar:196px}.chrimata-home-quote{display:none!important}}
@media(max-width:760px){:root{--chr-sidebar:0px;--chr-banner:74px}[data-testid="stAppViewContainer"] > .main,[data-testid="stAppViewContainer"] > section.main,section[data-testid="stMain"],.stMain{margin-left:0!important;width:100vw!important;max-width:100vw!important}.main .block-container,section.main .block-container,[data-testid="stMainBlockContainer"],.stMainBlockContainer{padding:82px 8px 14px!important}}
</style>
""", unsafe_allow_html=True)

# V20.3.0 — reference landing-page geometry. Header/sidebar stay locked; main canvas begins directly beneath banner.
st.markdown(r"""
<style>
:root{--chr-sidebar:228px;--chr-banner:108px;}
/* The fixed banner already occupies the top 108px visually. Do not reserve it a second time in Streamlit's block. */
.main .block-container,section.main .block-container,[data-testid="stMainBlockContainer"],.stMainBlockContainer{
  padding:10px 14px 14px!important;
  margin:0!important;width:100%!important;max-width:none!important;box-sizing:border-box!important;
}
/* Main surface begins at the right edge of the sidebar and directly below the persistent banner. */
[data-testid="stAppViewContainer"] > .main,[data-testid="stAppViewContainer"] > section.main,section[data-testid="stMain"],.stMain{
  position:fixed!important;left:var(--chr-sidebar)!important;right:0!important;top:var(--chr-banner)!important;bottom:0!important;
  margin:0!important;width:auto!important;max-width:none!important;min-width:0!important;overflow-y:auto!important;overflow-x:hidden!important;
  background:#f7faff!important;
}
/* Reference terminal density */
.main div[data-testid="stHorizontalBlock"]{gap:8px!important;margin:0!important;}
.main [data-testid="stTextInput"] input{height:38px!important;min-height:38px!important;border-radius:5px!important;font-size:12px!important;}
.main .stButton button{height:38px!important;min-height:38px!important;border-radius:5px!important;font-size:12px!important;font-weight:700!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"]{gap:5px!important;flex-wrap:nowrap!important;}
.main div[data-testid="stRadio"] div[role="radiogroup"] label{height:38px!important;min-height:38px!important;padding:5px 9px!important;border-radius:5px!important;font-size:11px!important;white-space:nowrap!important;}
.chrimata-home-intro{margin:6px 0 8px!important;min-height:48px!important;align-items:center!important;}
.chrimata-home-title{font-size:22px!important;line-height:1.05!important;}
.chrimata-home-meta{font-size:10px!important;margin-top:3px!important;}
.chrimata-home-quote{font-size:13px!important;padding-right:4px!important;}
.main div[data-testid="stMetric"]{min-height:86px!important;height:86px!important;padding:8px 11px!important;border-radius:5px!important;}
.main div[data-testid="stMetricLabel"] p{font-size:12px!important;font-weight:700!important;color:#17345d!important;}
.main div[data-testid="stMetricValue"]{font-size:1.42rem!important;line-height:1.05!important;color:#0b2348!important;}
.main div[data-testid="stMetricDelta"]{font-size:11px!important;}
.main h3{font-size:14px!important;line-height:1.1!important;margin:7px 0 5px!important;color:#0d3266!important;}
.main [data-testid="stDataFrame"]{border-radius:5px!important;font-size:11px!important;}
.main [data-testid="stArrowVegaLiteChart"],.main [data-testid="stPlotlyChart"]{border-radius:5px!important;padding:2px!important;}
.main hr{margin:5px 0!important;}
.chrimata-section-rule{margin:6px 0!important;}
.chrimata-terminal-footer{margin-top:6px!important;padding:5px 0!important;}
/* Keep all home content inside the available canvas. */
.main [data-testid="column"]{min-width:0!important;overflow:hidden!important;}
@media(max-width:1100px){:root{--chr-sidebar:196px}.chrimata-home-quote{display:none!important}.main div[data-testid="stRadio"] div[role="radiogroup"]{flex-wrap:wrap!important;}}
@media(max-width:760px){:root{--chr-sidebar:0px;--chr-banner:74px}[data-testid="stSidebar"]{display:none!important}[data-testid="stAppViewContainer"] > .main,[data-testid="stAppViewContainer"] > section.main,section[data-testid="stMain"],.stMain{left:0!important;top:var(--chr-banner)!important}.main .block-container,section.main .block-container,[data-testid="stMainBlockContainer"],.stMainBlockContainer{padding:8px!important}}
</style>
""",unsafe_allow_html=True)

st.markdown(r"""
<style>
div[data-testid="stElementContainer"]:has(.chrimata-exact-hero){height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:visible!important}
[data-testid="stAppViewContainer"]>.main,section[data-testid="stMain"],.stMain{background:#f5f8fc!important}.main .block-container,section.main .block-container,[data-testid="stMainBlockContainer"],.stMainBlockContainer{padding:10px 12px 12px!important}
.chr-home-v2020{font-family:Inter,Arial,sans-serif;color:#10264b;margin-top:4px}.chr-home-v2020 *{box-sizing:border-box}.chr-overview-head{display:flex;justify-content:space-between;align-items:center;padding:6px 2px 8px}.chr-overview-title{font-size:24px;font-weight:800}.chr-overview-title span{font-size:27px}.chr-overview-meta{font-size:11px;color:#6b7f9b;margin-top:2px}.chr-overview-quote{font:italic 15px Georgia,serif;color:#315276;text-align:right}.chr-overview-quote small{display:block;font:10px Arial,sans-serif;margin-top:2px}
.chr-metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}.chr-card,.chr-panel{background:#fff;border:1px solid #d8e3ef;border-radius:6px;box-shadow:0 1px 2px rgba(20,50,80,.03)}.chr-metric{height:108px;padding:10px 12px;overflow:hidden}.chr-metric-name{font-size:14px;font-weight:800}.chr-metric-name span{font-weight:500;color:#6982a3;margin-left:8px}.chr-metric-row{display:flex;align-items:baseline;gap:12px;margin-top:4px}.chr-metric-row strong{font-size:24px;line-height:1}.chr-metric-row em{font-size:12px;font-style:normal;font-weight:700}.chr-spark{height:43px;margin-top:3px}.chr-spark svg{width:100%;height:100%}
.chr-grid-main{display:grid;grid-template-columns:1.55fr .92fr 1.05fr;gap:8px;margin-top:8px}.chr-grid-mid{display:grid;grid-template-columns:1fr 1fr .82fr 1fr;gap:8px;margin-top:8px}.chr-grid-bottom{display:grid;grid-template-columns:1.1fr 1.15fr .95fr;gap:8px;margin-top:8px}.chr-panel{overflow:hidden}.chr-panel>header{height:34px;padding:8px 10px;font-size:14px;font-weight:800;border-bottom:1px solid #e5edf5;display:flex;justify-content:space-between}.chr-panel>header span{font-size:10px;font-weight:600;color:#5d7594}.chr-panel>footer{font-size:10px;color:#0874df;text-align:right;padding:5px 10px;background:#f8fbff}.chr-chart-panel{min-height:270px}.chr-bigchart{height:235px;padding:12px 12px 5px;position:relative;background:repeating-linear-gradient(0deg,#fff,#fff 44px,#e9eff6 45px),repeating-linear-gradient(90deg,transparent,transparent 78px,#e9eff6 79px)}.chr-bigchart svg{width:100%;height:100%}.chr-bigchart>strong{position:absolute;right:12px;top:50%;font-size:13px;color:#0aa968}.chr-sectors{padding:7px 9px}.chr-sector-row{display:grid;grid-template-columns:105px 1fr 55px;align-items:center;gap:7px;height:21px;font-size:10px}.chr-sector-row>span{text-align:right;color:#1475d1}.chr-sector-row i{height:11px;background:#f2f5f9;position:relative}.chr-sector-row i b{display:block;height:100%}.chr-sector-row i b.up{background:#12b76a}.chr-sector-row i b.down{background:#ef4444}.chr-sector-row em{font-style:normal;text-align:right}.pos{color:#0aa968!important}.neg{color:#ef4444!important}
.chr-table{width:100%;border-collapse:collapse;font-size:10px}.chr-table th{background:#eef4fa;text-align:left;padding:4px 6px;color:#17365d}.chr-table td{padding:4px 6px;border-bottom:1px solid #eef2f6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:145px}.chr-table tbody tr:nth-child(even){background:#f8fbfe}.chr-empty{padding:18px 10px;color:#71839a;font-size:11px}.chr-gauge{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:7px;padding:10px 8px 6px;text-align:center}.arc{width:120px;height:70px;border-radius:120px 120px 0 0;border:12px solid #14b86f;border-right-color:#ef4444;border-top-color:#f4bd22;position:relative;border-bottom:0;margin:0 auto}.needle{position:absolute;width:2px;height:45px;background:#777;left:48px;bottom:0;transform-origin:bottom center}.arc b{position:absolute;left:50%;bottom:-4px;transform:translateX(-50%);font-size:20px;min-width:54px;text-align:center}.vol-state{font-size:12px;font-weight:800;text-align:center;line-height:1.2}.vol-state.low{color:#10a765}.vol-state.normal{color:#d79c00}.vol-state.high{color:#e33}.vol-state.unavailable{color:#71839a}.gleg{display:flex;flex-direction:row;align-items:center;justify-content:center;flex-wrap:wrap;font-size:10px;gap:5px 12px;text-align:center}.gleg .low{color:#10a765}.gleg .normal{color:#d79c00}.gleg .high{color:#e33}.chr-note{font-size:9px;color:#667b94;margin:2px 12px 8px;text-align:center;line-height:1.35}
html,body,.stApp,[data-testid="stAppViewContainer"],section[data-testid="stMain"],.stMain{background:#f5f8fc!important}.stApp{transition:none!important}

/* V20.3.0 — remove the residual Streamlit slot below the fixed banner. */
div[data-testid="stElementContainer"]:has(.chrimata-exact-hero),
div.element-container:has(.chrimata-exact-hero),
div[data-testid="stVerticalBlock"] > div:has(.chrimata-exact-hero){height:0!important;min-height:0!important;max-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;}
.chr-country-row{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:6px;margin:0;}
.chr-country-row .stButton button{background:#fff!important;color:#10264b!important;border:1px solid #d7e2ef!important;box-shadow:none!important;font-size:11px!important;font-weight:700!important;padding:0 8px!important;}
.chr-country-row .stButton button:hover{border-color:#1687ff!important;color:#0874df!important;}
.chr-market-status{font-weight:700;color:#315276}.chr-market-status.open{color:#0a9d62}.chr-market-status.closed{color:#b45309}
@media(max-width:1200px){.chr-metrics{grid-template-columns:repeat(3,1fr)}.chr-grid-main{grid-template-columns:1fr 1fr}.chr-grid-main .chr-chart-panel{grid-column:1/-1}.chr-grid-mid{grid-template-columns:1fr 1fr}.chr-grid-bottom{grid-template-columns:1fr 1fr}.chr-overview-quote{display:none}}
</style>
""",unsafe_allow_html=True)

st.markdown(r"""
<style>
/* V20.3.0 — approved reference alignment */
:root{--chr-sidebar:228px;--chr-banner:108px;}
/* Make the banner host consume zero document height; the image itself stays fixed. */
.chrimata-terminal-hero.chrimata-exact-hero{
  position:static!important;left:auto!important;right:auto!important;top:auto!important;
  width:0!important;height:0!important;min-height:0!important;max-height:0!important;
  margin:0!important;padding:0!important;overflow:visible!important;background:transparent!important;
}
.chrimata-terminal-hero.chrimata-exact-hero img{
  position:fixed!important;left:0!important;top:0!important;width:100vw!important;height:var(--chr-banner)!important;
  display:block!important;object-fit:fill!important;object-position:center!important;z-index:1000000!important;
}
div[data-testid="stElementContainer"]:has(.chrimata-exact-hero),
div.element-container:has(.chrimata-exact-hero),
div[data-testid="stMarkdownContainer"]:has(.chrimata-exact-hero){height:0!important;min-height:0!important;max-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;}
/* Main canvas starts immediately below the banner. */
[data-testid="stAppViewContainer"] > .main,[data-testid="stAppViewContainer"] > section.main,section[data-testid="stMain"],.stMain{
  top:var(--chr-banner)!important;left:var(--chr-sidebar)!important;right:0!important;bottom:0!important;
}
.main .block-container,section.main .block-container,[data-testid="stMainBlockContainer"],.stMainBlockContainer{
  padding:10px 12px 14px!important;margin:0!important;
}
/* Reference-style country controls: white cards with a real flag tile at left. */
.main [data-testid="stHorizontalBlock"]:has(button[key^="country_"]) {gap:6px!important;}
.main button[kind="secondary"]{background:#fff!important;color:#10264b!important;}
/* Country buttons specifically */
.main div[data-testid="stColumn"]:has(button[key^="country_"]) button{
  background:#fff!important;color:#10264b!important;border:1px solid #d7e2ef!important;
  box-shadow:none!important;height:38px!important;min-height:38px!important;border-radius:5px!important;
  font-size:11px!important;font-weight:700!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
}
.main div[data-testid="stColumn"]:has(button[key^="country_"]) button[kind="primary"]{
  background:#fff!important;color:#0874df!important;border:2px solid #1687ff!important;
}
/* Use CSS-drawn flag tiles so Windows font rendering cannot turn emoji into AU/US/GB text. */
.main div[data-testid="stColumn"]:has(button[key="country_Australia_v2021"]) button::before{content:"🇦🇺";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
.main div[data-testid="stColumn"]:has(button[key="country_United States_v2021"]) button::before{content:"🇺🇸";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
.main div[data-testid="stColumn"]:has(button[key="country_United Kingdom_v2021"]) button::before{content:"🇬🇧";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
.main div[data-testid="stColumn"]:has(button[key="country_Japan_v2021"]) button::before{content:"🇯🇵";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
.main div[data-testid="stColumn"]:has(button[key="country_Hong Kong_v2021"]) button::before{content:"🇭🇰";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
.main div[data-testid="stColumn"]:has(button[key="country_Canada_v2021"]) button::before{content:"🇨🇦";font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;margin-right:6px;}
/* Hide the textual regional-indicator prefix in labels by rendering names without emoji in Python. */
.chr-overview-title{display:flex!important;align-items:center!important;gap:8px!important;}
.chr-overview-title .chr-flag{font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:28px!important;line-height:1!important;}
.chr-home-v2020{margin-top:0!important;}
.chr-overview-head{padding-top:4px!important;}
</style>
""",unsafe_allow_html=True)

st.markdown(r"""
<style>
/* V20.3.0 — exact reference search/country strip */
:root{--chr-sidebar:228px;--chr-banner:108px;}
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > section.main,
section[data-testid="stMain"],.stMain{
  top:var(--chr-banner)!important;
}
.main .block-container,section.main .block-container,
[data-testid="stMainBlockContainer"],.stMainBlockContainer{
  padding-top:8px!important;
}
/* Remove Streamlit's invisible top spacers so the search strip hugs the banner. */
.main .block-container > [data-testid="stVerticalBlock"],
section.main .block-container > [data-testid="stVerticalBlock"]{gap:6px!important;}
.main div[data-testid="stHorizontalBlock"]{margin-top:0!important;margin-bottom:0!important;}
/* Country buttons: white cards, flag at left, dark label. Selected = blue outline/text, never solid blue. */
.main .stButton button,
.main .stButton button[kind="secondary"],
.main .stButton button[kind="primary"]{
  background:#fff!important;
  color:#10264b!important;
  border:1px solid #d6e2ef!important;
  box-shadow:0 1px 2px rgba(20,50,80,.04)!important;
  font-weight:700!important;
}
.main .stButton button[kind="primary"]{
  border:2px solid #1687ff!important;
  color:#0874df!important;
  background:#f8fbff!important;
}
.main .stButton button:hover{background:#f8fbff!important;border-color:#1687ff!important;color:#0874df!important;}
/* Search button remains the one blue action in the strip. */
.main div[data-testid="stColumn"]:nth-child(2) > div .stButton button{
  background:#1687ff!important;color:#fff!important;border-color:#1687ff!important;
}
.chr-overview-head{margin-top:0!important;padding-top:4px!important;}
.chr-overview-title{display:flex!important;align-items:center!important;gap:8px!important;}
.chr-overview-title .chr-flag{font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif!important;font-size:31px!important;line-height:1!important;}
</style>
""",unsafe_allow_html=True)

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

# V20.1.0 — compressed full-height sidebar so all primary navigation fits without scrolling.
try:
    _search_key=st.secrets.get("TWELVE_DATA_API_KEY","")
except Exception:
    _search_key=""
_query_default=st.session_state.get("mia_search_query","ZIP")
ticker=resolve_bare_ticker(str(_query_default).strip().upper()) if str(_query_default).strip() else "ZIP.AX"
# V20.5.4: ticker query params no longer control runtime navigation or selection.
# The active security lives only in session state after initial app startup.

st.markdown(r"""
<style>
:root{--chr-side:220px;--chr-head:108px;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#04345e 0%,#063c69 54%,#032b4d 100%)!important;border-right:1px solid #0b568b!important;}
[data-testid="stSidebar"] .block-container{padding:10px 9px 12px!important;min-height:100%!important;display:flex!important;flex-direction:column!important;}
.chr-nav{display:flex;flex-direction:column;gap:0;width:100%;margin:0;padding:0;}
.chr-nav a,.chr-nav a:visited{text-decoration:none!important;color:#fff!important;}
.chr-nav-item{display:grid;grid-template-columns:32px 1fr;align-items:center;min-height:43px;padding:3px 6px;border-radius:6px;background:transparent;transition:background .12s ease,box-shadow .12s ease;box-sizing:border-box;}
.chr-nav-item:hover{background:rgba(255,255,255,.055);}
.chr-nav-item.active{background:linear-gradient(90deg,#0876df 0%,#0968c7 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.07),0 1px 2px rgba(0,0,0,.08);}
.chr-nav-icon{width:25px;height:25px;display:flex;align-items:center;justify-content:center;color:#fff;line-height:1}.chr-nav-icon svg{width:20px;height:20px;stroke:#fff;stroke-width:1.8;fill:none;stroke-linecap:round;stroke-linejoin:round;}
.chr-nav-copy{display:flex;flex-direction:column;justify-content:center;min-width:0;line-height:1.2;}
.chr-nav-title{font-family:Arial,"Helvetica Neue",sans-serif;font-size:10.7px;font-weight:500;color:#fff;white-space:nowrap;line-height:1.12;letter-spacing:-.01em;}
.chr-nav-sub{font-family:Arial,"Helvetica Neue",sans-serif;font-size:7.5px;font-weight:400;color:#d9ad55;margin-top:1px;white-space:nowrap;line-height:1.1;letter-spacing:-.01em;}
.chr-nav-item.active .chr-nav-sub{color:#f3d58f;}
[data-testid="stSidebar"] details{margin-top:8px!important;background:rgba(255,255,255,.025)!important;border:1px solid rgba(255,255,255,.10)!important;border-radius:6px!important;}
[data-testid="stSidebar"] details summary{font-size:10.5px!important;font-weight:650!important;color:#fff!important;}
[data-testid="stSidebar"] [data-testid="stSelectbox"] label p{font-size:9px!important;text-transform:uppercase!important;letter-spacing:.08em!important;color:#8fbce2!important;}
.chr-side-spacer{height:5px;flex:1 1 auto;min-height:5px;}
.chr-side-wealth{margin:5px 6px 2px;padding:8px 8px;border:1px solid rgba(55,151,221,.30);border-radius:6px;background:rgba(2,32,58,.35);display:grid;grid-template-columns:38px 1fr;gap:7px;align-items:center;color:#fff}
.chr-side-wealth .wealth-pillar{width:36px;height:50px;display:flex;align-items:center;justify-content:center}.chr-side-wealth .wealth-pillar svg{width:34px;height:48px;stroke:#e6bd68;fill:none;stroke-width:1.45;stroke-linecap:round;stroke-linejoin:round}
.chr-side-wealth .wealth-copy{font:9.4px Georgia,serif;letter-spacing:1.45px;line-height:1.65;color:#fff;text-align:center}
.chr-side-version{font-size:8px;color:#d7e8f7;text-align:right;margin:5px 7px 0}
.chr-side-copyright{font:7px Arial,sans-serif;color:#91abc0;text-align:center;margin:5px 4px 0;letter-spacing:.02em}
/* Remove Streamlit footer/bottom chrome that can appear as a white strip. */
footer,[data-testid="stBottom"],[data-testid="stBottomBlockContainer"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;}
/* V20.0.8: compact reference spacing and remove Streamlit sidebar chrome. */

[data-testid="stSidebarHeader"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="headerNoPadding"],
[data-testid="stSidebar"] button[aria-label*="sidebar" i],
[data-testid="stSidebar"] button[title*="sidebar" i]{display:none!important;visibility:hidden!important;width:0!important;height:0!important;min-width:0!important;padding:0!important;margin:0!important;}
[data-testid="stSidebar"] > div:first-child{padding-top:0!important;margin-top:0!important;}
[data-testid="stSidebar"] .block-container{padding-top:0!important;margin-top:0!important;}
[data-testid="stSidebar"] .chr-nav{margin-top:0!important;padding-top:0!important;}
[data-testid="stSidebar"] section,[data-testid="stSidebar"]>div{overflow:hidden!important;}
[data-testid="stSidebar"] details{display:none!important;}
.chr-nav a .chr-nav-title,.chr-nav a:visited .chr-nav-title{color:#ffffff!important;}
.chr-nav a .chr-nav-sub,.chr-nav a:visited .chr-nav-sub{color:#d9ad55!important;font-size:7.5px!important;line-height:1.04!important;margin-top:1px!important;font-weight:400!important;letter-spacing:.01em!important;}
.chr-nav-item.active .chr-nav-sub{color:#f0c86e!important;}
.chr-nav-copy{min-width:0!important;max-width:calc(var(--chr-sidebar) - 46px)!important;overflow:hidden!important;}
.chr-nav-title,.chr-nav-sub{max-width:100%!important;overflow:hidden!important;text-overflow:clip!important;}


/* V20.5.7 Professional Sidebar Restoration — approved compact terminal sidebar. */
[data-testid="stSidebar"] .stButton{margin:0!important;padding:0!important;}
[data-testid="stSidebar"] .stButton>button{width:100%!important;height:48px!important;min-height:48px!important;margin:0 0 1px!important;padding:4px 7px 15px 45px!important;text-align:left!important;justify-content:flex-start!important;white-space:nowrap!important;font-size:11.5px!important;font-weight:600!important;line-height:1.05!important;border-radius:5px!important;box-shadow:none!important;position:relative!important;overflow:visible!important;}
[data-testid="stSidebar"] .stButton>button[kind="secondary"]{background:transparent!important;color:#fff!important;border-color:transparent!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(90deg,#0876df 0%,#0968c7 100%)!important;color:#fff!important;border-color:transparent!important;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)!important;}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(255,255,255,.055)!important;border-color:transparent!important;color:#fff!important;}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{background:linear-gradient(90deg,#0876df 0%,#0968c7 100%)!important;}
[data-testid="stSidebar"] .stButton>button span[data-testid="stIconMaterial"],[data-testid="stSidebar"] .stButton>button [data-testid="stIconMaterial"]{position:absolute!important;left:12px!important;top:12px!important;font-size:23px!important;line-height:23px!important;color:#fff!important;margin:0!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:0!important;}
/* Gold secondary copy from the approved Chrímata sidebar reference. */
.st-key-chr_nav_native_0 button:after{content:"Global Market Overview";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_1 button:after{content:"Find & Analyse Stocks";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_2 button:after{content:"Deep Analysis & Reports";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_3 button:after{content:"Indices, Sectors & Heatmaps";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_4 button:after{content:"Track Your Stocks";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_5 button:after{content:"Performance & Analytics";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_6 button:after{content:"Find Opportunities";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_7 button:after{content:"Price & News Alerts";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_8 button:after{content:"Dividends, Earnings & IPOs";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_9 button:after{content:"Valuation, Forecasts & Scores";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}
.st-key-chr_nav_native_10 button:after{content:"Preferences";position:absolute;left:45px;bottom:7px;color:#e0b45a;font-size:8.2px;font-weight:500;line-height:1;white-space:nowrap;}

/* V20.6.0 — fixed sidebar text column. Streamlit's button-label wrapper can
   center itself independently; pin every title to the same x coordinate as the
   gold subtitle so long/short labels align exactly. */
[data-testid="stSidebar"] .stButton>button p,
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]{position:absolute!important;left:45px!important;top:8px!important;margin:0!important;padding:0!important;width:calc(100% - 52px)!important;max-width:calc(100% - 52px)!important;text-align:left!important;justify-content:flex-start!important;white-space:nowrap!important;}
[data-testid="stSidebar"] .stButton>button p{font-size:11.5px!important;font-weight:600!important;line-height:1.05!important;}

/* V20.6.2 — deterministic sidebar grid.  Streamlit wraps button text in
   multiple flex containers, so pin the complete label wrapper rather than only
   the paragraph. Every white title and gold subtitle now shares x=52px. */
[data-testid="stSidebar"] .stButton>button{
  display:grid!important;grid-template-columns:34px minmax(0,1fr)!important;
  grid-template-rows:1fr!important;align-items:center!important;
  padding:4px 8px 15px 8px!important;text-align:left!important;
}
[data-testid="stSidebar"] .stButton>button span[data-testid="stIconMaterial"],
[data-testid="stSidebar"] .stButton>button [data-testid="stIconMaterial"]{
  position:static!important;grid-column:1!important;grid-row:1!important;
  justify-self:center!important;align-self:center!important;margin:5px 0 0!important;
}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]{
  position:static!important;grid-column:2!important;grid-row:1!important;
  width:100%!important;max-width:100%!important;margin:0!important;padding:0!important;
  display:block!important;text-align:left!important;justify-self:stretch!important;
}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"] p{
  position:static!important;width:100%!important;max-width:100%!important;
  margin:0!important;padding:0!important;text-align:left!important;
}
.st-key-chr_nav_native_0 button:after,.st-key-chr_nav_native_1 button:after,.st-key-chr_nav_native_2 button:after,
.st-key-chr_nav_native_3 button:after,.st-key-chr_nav_native_4 button:after,.st-key-chr_nav_native_5 button:after,
.st-key-chr_nav_native_6 button:after,.st-key-chr_nav_native_7 button:after,.st-key-chr_nav_native_8 button:after,
.st-key-chr_nav_native_9 button:after,.st-key-chr_nav_native_10 button:after{left:42px!important;text-align:left!important;}
/* V20.6.2 — subtitle alignment repair. The grid text column begins at
   8px button padding + 34px icon column = 42px. Gold pseudo-elements now
   use that exact origin, with no inherited transform/margin. */
.st-key-chr_nav_native_0 button:after,.st-key-chr_nav_native_1 button:after,.st-key-chr_nav_native_2 button:after,
.st-key-chr_nav_native_3 button:after,.st-key-chr_nav_native_4 button:after,.st-key-chr_nav_native_5 button:after,
.st-key-chr_nav_native_6 button:after,.st-key-chr_nav_native_7 button:after,.st-key-chr_nav_native_8 button:after,
.st-key-chr_nav_native_9 button:after,.st-key-chr_nav_native_10 button:after{left:42px!important;right:auto!important;margin:0!important;padding:0!important;transform:none!important;text-align:left!important;}


/* V20.6.3 — exact sidebar text alignment fix.
   The pseudo-element is positioned inside Streamlit's text-bearing button wrapper,
   whose origin already matches the white title column.  Previous builds added the
   42px grid offset a second time, visibly pushing every gold subtitle right. */
.st-key-chr_nav_native_0 button:after,.st-key-chr_nav_native_1 button:after,.st-key-chr_nav_native_2 button:after,
.st-key-chr_nav_native_3 button:after,.st-key-chr_nav_native_4 button:after,.st-key-chr_nav_native_5 button:after,
.st-key-chr_nav_native_6 button:after,.st-key-chr_nav_native_7 button:after,.st-key-chr_nav_native_8 button:after,
.st-key-chr_nav_native_9 button:after,.st-key-chr_nav_native_10 button:after{
  left:0!important;right:auto!important;margin-left:0!important;padding-left:0!important;
  transform:none!important;text-align:left!important;
}

/* V20.6.4 — exact shared text origin.
   Both title and subtitle are positioned from the button itself. The button's
   8px left padding + 34px icon track = 42px text origin. */
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"] p{
  grid-column:2!important;position:static!important;left:auto!important;
  margin:0!important;padding:0!important;text-align:left!important;
}
[data-testid="stSidebar"] .stButton>button:after{
  left:42px!important;right:auto!important;margin:0!important;padding:0!important;
  transform:none!important;text-align:left!important;
}

/* V20.6.5 — title/subtitle share one physical text container.
   Do not position the gold copy from the button. Streamlit's text wrapper is
   already the exact white-title origin, so render the subtitle on that wrapper. */
.st-key-chr_nav_native_0 button:after,.st-key-chr_nav_native_1 button:after,.st-key-chr_nav_native_2 button:after,
.st-key-chr_nav_native_3 button:after,.st-key-chr_nav_native_4 button:after,.st-key-chr_nav_native_5 button:after,
.st-key-chr_nav_native_6 button:after,.st-key-chr_nav_native_7 button:after,.st-key-chr_nav_native_8 button:after,
.st-key-chr_nav_native_9 button:after,.st-key-chr_nav_native_10 button:after{content:none!important;display:none!important;}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]{position:relative!important;overflow:visible!important;}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]:after{
  position:absolute!important;left:0!important;top:16px!important;right:auto!important;
  margin:0!important;padding:0!important;transform:none!important;text-align:left!important;
  color:#e0b45a!important;font-size:8.2px!important;font-weight:500!important;line-height:1!important;
  white-space:nowrap!important;display:block!important;
}
.st-key-chr_nav_native_0 button [data-testid="stMarkdownContainer"]:after{content:"Global Market Overview";}
.st-key-chr_nav_native_1 button [data-testid="stMarkdownContainer"]:after{content:"Find & Analyse Stocks";}
.st-key-chr_nav_native_2 button [data-testid="stMarkdownContainer"]:after{content:"Deep Analysis & Reports";}
.st-key-chr_nav_native_3 button [data-testid="stMarkdownContainer"]:after{content:"Indices, Sectors & Heatmaps";}
.st-key-chr_nav_native_4 button [data-testid="stMarkdownContainer"]:after{content:"Track Your Stocks";}
.st-key-chr_nav_native_5 button [data-testid="stMarkdownContainer"]:after{content:"Performance & Analytics";}
.st-key-chr_nav_native_6 button [data-testid="stMarkdownContainer"]:after{content:"Find Opportunities";}
.st-key-chr_nav_native_7 button [data-testid="stMarkdownContainer"]:after{content:"Price & News Alerts";}
.st-key-chr_nav_native_8 button [data-testid="stMarkdownContainer"]:after{content:"Dividends, Earnings & IPOs";}
.st-key-chr_nav_native_9 button [data-testid="stMarkdownContainer"]:after{content:"Valuation, Forecasts & Scores";}
.st-key-chr_nav_native_10 button [data-testid="stMarkdownContainer"]:after{content:"Preferences";}
.st-key-chr_nav_native_0 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_1 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_2 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_3 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_4 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_5 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_6 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_7 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_8 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_9 button[kind="primary"] [data-testid="stMarkdownContainer"]:after,
.st-key-chr_nav_native_10 button[kind="primary"] [data-testid="stMarkdownContainer"]:after{color:#f0c86e!important;}

/* V20.6.6 — Reference Sidebar Restoration.
   This is the final sidebar authority. It mirrors the supplied reference:
   compact rows, a dedicated icon track, and ONE shared title/subtitle origin. */
[data-testid="stSidebar"] .stButton{margin:0!important;padding:0!important;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:0!important;}
[data-testid="stSidebar"] .stButton>button{
  width:100%!important;height:46px!important;min-height:46px!important;
  margin:0 0 1px!important;padding:4px 7px 14px 52px!important;
  position:relative!important;display:block!important;overflow:visible!important;
  text-align:left!important;justify-content:flex-start!important;
  border-radius:5px!important;box-shadow:none!important;
}
[data-testid="stSidebar"] .stButton>button[kind="secondary"]{
  background:transparent!important;color:#fff!important;border-color:transparent!important;
}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:linear-gradient(90deg,#0876df 0%,#0968c7 100%)!important;
  color:#fff!important;border-color:transparent!important;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.07)!important;
}
[data-testid="stSidebar"] .stButton>button span[data-testid="stIconMaterial"],
[data-testid="stSidebar"] .stButton>button [data-testid="stIconMaterial"]{
  position:absolute!important;left:12px!important;top:11px!important;
  width:24px!important;height:24px!important;font-size:22px!important;line-height:24px!important;
  color:#fff!important;margin:0!important;padding:0!important;
}
/* The markdown wrapper is the sole text column for BOTH lines. */
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]{
  position:absolute!important;left:52px!important;top:7px!important;right:auto!important;
  width:calc(100% - 59px)!important;max-width:calc(100% - 59px)!important;
  margin:0!important;padding:0!important;display:block!important;overflow:visible!important;
  text-align:left!important;transform:none!important;
}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"] p{
  position:static!important;display:block!important;width:100%!important;max-width:100%!important;
  margin:0!important;padding:0!important;text-align:left!important;transform:none!important;
  font-family:Arial,"Helvetica Neue",sans-serif!important;font-size:11.2px!important;
  font-weight:600!important;line-height:1.08!important;white-space:nowrap!important;color:#fff!important;
}
/* Disable every legacy button pseudo subtitle; the subtitle is attached to the
   SAME markdown wrapper, so its left edge can never drift from the title. */
.st-key-chr_nav_native_0 button:after,.st-key-chr_nav_native_1 button:after,.st-key-chr_nav_native_2 button:after,
.st-key-chr_nav_native_3 button:after,.st-key-chr_nav_native_4 button:after,.st-key-chr_nav_native_5 button:after,
.st-key-chr_nav_native_6 button:after,.st-key-chr_nav_native_7 button:after,.st-key-chr_nav_native_8 button:after,
.st-key-chr_nav_native_9 button:after,.st-key-chr_nav_native_10 button:after{content:none!important;display:none!important;}
[data-testid="stSidebar"] .stButton>button [data-testid="stMarkdownContainer"]:after{
  position:absolute!important;left:0!important;top:15px!important;right:auto!important;
  margin:0!important;padding:0!important;transform:none!important;text-align:left!important;
  color:#e0b45a!important;font-family:Arial,"Helvetica Neue",sans-serif!important;
  font-size:8.0px!important;font-weight:400!important;line-height:1!important;
  white-space:nowrap!important;display:block!important;
}
.st-key-chr_nav_native_0 button [data-testid="stMarkdownContainer"]:after{content:"Global Market Overview";}
.st-key-chr_nav_native_1 button [data-testid="stMarkdownContainer"]:after{content:"Find & Analyse Stocks";}
.st-key-chr_nav_native_2 button [data-testid="stMarkdownContainer"]:after{content:"Deep Analysis & Reports";}
.st-key-chr_nav_native_3 button [data-testid="stMarkdownContainer"]:after{content:"Indices, Sectors & Heatmaps";}
.st-key-chr_nav_native_4 button [data-testid="stMarkdownContainer"]:after{content:"Track Your Stocks";}
.st-key-chr_nav_native_5 button [data-testid="stMarkdownContainer"]:after{content:"Performance & Analytics";}
.st-key-chr_nav_native_6 button [data-testid="stMarkdownContainer"]:after{content:"Find Opportunities";}
.st-key-chr_nav_native_7 button [data-testid="stMarkdownContainer"]:after{content:"Price & News Alerts";}
.st-key-chr_nav_native_8 button [data-testid="stMarkdownContainer"]:after{content:"Dividends, Earnings & IPOs";}
.st-key-chr_nav_native_9 button [data-testid="stMarkdownContainer"]:after{content:"Valuation, Forecasts & Scores";}
.st-key-chr_nav_native_10 button [data-testid="stMarkdownContainer"]:after{content:"Preferences";}
[data-testid="stSidebar"] .stButton>button[kind="primary"] [data-testid="stMarkdownContainer"]:after{color:#f0c86e!important;}
.chr-side-wealth{margin:7px 6px 2px!important;padding:8px!important;}
.chr-side-version{font-size:8px!important;color:#d7e8f7!important;text-align:right!important;margin:5px 7px 0!important;}

/* V20.5.6 — keep provider/cache execution details out of the product UI. */
[data-testid="stStatusWidget"], [data-testid="stException"] details summary{display:none!important;}
[data-testid="stAppViewContainer"]{transition:opacity .12s ease!important;}
/* V20.5.4 — compact single-row Home search/header alignment. */
.st-key-country_nav_v2027{margin-top:0!important;padding-top:0!important;}
.st-key-country_nav_v2027 [data-testid="stHorizontalBlock"]{align-items:center!important;min-height:44px!important;}
.st-key-country_nav_v2027 .stButton>button{height:44px!important;min-height:44px!important;}
/* The professional search component owns its suggestions; remove extra outer label spacing. */
div[data-testid="stFragment"]{margin-top:0!important;margin-bottom:0!important;padding-top:0!important;}
div[data-testid="stFragment"] iframe{margin-top:0!important;}
</style>
""",unsafe_allow_html=True)

NAV_ITEMS=[
("Home","home","⌂  Home","Global Market Overview"),
("Company Search","search","⌕  Company Search","Find & Analyse Stocks"),
("Company Command Centre","document","▤  Company Command Centre","Deep Analysis & Reports"),
("Markets","chart","▥  Markets","Indices, Sectors & Heatmaps"),
("Watchlist","star","☆  Watchlist","Track Your Stocks"),
("Portfolio","briefcase","▣  Portfolio","Performance & Analytics"),
("Screening","screen","⌕  Screening","Find Opportunities"),
("Alerts","bell","♢  Alerts","Price & News Alerts"),
("Calendar","calendar","▦  Calendar","Dividends, Earnings & IPOs"),
("Research Tools","research","⊕  Research Tools","Valuation, Forecasts & Scores"),
("Settings","settings","⚙  Settings","Preferences")]
_valid_nav={x[0] for x in NAV_ITEMS}
# V20.5.4 — single-router navigation rebuild.
# chr_primary_nav is the ONLY authority for the visible workspace. URL/query
# parameters are deliberately not consulted during reruns, preventing a stale
# ticker or deep-link from forcing the Command Centre back open.
if "chr_router_v2054_ready" not in st.session_state:
    st.session_state["chr_primary_nav"]="Home"
    st.session_state["chr_router_v2054_ready"]=True
primary=st.session_state.get("chr_primary_nav","Home")
if primary not in _valid_nav:
    primary="Home"
    st.session_state["chr_primary_nav"]="Home"

from urllib.parse import quote as _urlquote
def _chr_nav_svg(name):
    icons={
    "home": '<svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V21h13V10.5"/><path d="M9.5 21v-6h5v6"/></svg>',
    "search": '<svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>',
    "document": '<svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 12h6M9 16h6"/></svg>',
    "chart": '<svg viewBox="0 0 24 24"><path d="M4 20V10M9 20V14M14 20V7M19 20V4"/><path d="M3 8l5-4 5 4 7-6"/><path d="M17 2h3v3"/></svg>',
    "star": '<svg viewBox="0 0 24 24"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9z"/></svg>',
    "briefcase": '<svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="1.5"/><path d="M8 7V4h8v3M3 12h18M10 12v2h4v-2"/></svg>',
    "screen": '<svg viewBox="0 0 24 24"><circle cx="10" cy="10" r="6"/><path d="m14.5 14.5 5 5M4 4h12M4 7h8"/></svg>',
    "bell": '<svg viewBox="0 0 24 24"><path d="M6 17h12l-1.5-2.5V10a4.5 4.5 0 0 0-9 0v4.5z"/><path d="M10 20h4"/></svg>',
    "calendar": '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="1.5"/><path d="M7 3v4M17 3v4M3 9h18M7 13h2M11 13h2M15 13h2M7 17h2M11 17h2M15 17h2"/></svg>',
    "research": '<svg viewBox="0 0 24 24"><circle cx="10" cy="10" r="6"/><path d="m14.5 14.5 5 5M10 7v6M7 10h6"/></svg>',
    "settings": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/><circle cx="12" cy="12" r="7"/></svg>'}
    return icons.get(name,icons["home"])
# V20.5.0: use Streamlit's in-app event channel instead of browser URL anchors.
# This avoids a document-level navigation/white flash; only Streamlit rerenders the app body.
st.sidebar.markdown('<nav class="chr-nav chr-nav-native" aria-label="Chrímata navigation">',unsafe_allow_html=True)
for _idx,(_key,_icon,_title,_sub) in enumerate(NAV_ITEMS):
    _active=(_key==primary)
    _material_icons={"home":":material/home:","search":":material/search:","document":":material/description:","chart":":material/monitoring:","star":":material/star_outline:","briefcase":":material/business_center:","screen":":material/filter_alt:","bell":":material/notifications_none:","calendar":":material/calendar_month:","research":":material/query_stats:","settings":":material/settings:"}
    _clean_title=_title.split("  ",1)[-1]
    if st.sidebar.button(_clean_title, key=f"chr_nav_native_{_idx}", use_container_width=True,
                         type="primary" if _active else "secondary", icon=_material_icons.get(_icon)):
        # Page navigation and selected security are intentionally independent.
        # Clicking Home must win immediately, while the last analysed ticker is
        # retained for a later return to Company Command Centre.
        st.session_state["chr_primary_nav"]=_key
        primary=_key
        # Navigation never mutates ticker state and never depends on URL state.
        st.rerun()
st.sidebar.markdown('</nav>',unsafe_allow_html=True)

# V20.5.4: removed the legacy hidden sidebar company selector. It was a second
# security-selection state machine and could silently compete with global search.

# V20.5.4 — active security is independent from page routing.
# It persists when the user returns Home, but can never choose the visible page.
if st.session_state.get("chr_active_ticker"):
    ticker=str(st.session_state["chr_active_ticker"]).strip().upper()
else:
    st.session_state["chr_active_ticker"]=ticker

SUBPAGES={
"Company Command Centre":["Overview","Fundamentals","Valuation","Technical","Announcements & Reports","Report Intelligence","News & Events","Thesis Scorecard","Catalyst Calendar","Quant","Forecasts"],
"Portfolio":["Portfolio Overview","Portfolio Intelligence","Risk Centre","Watchlist","Paper Portfolio"],
"Research Tools":["Research Report","Investment Committee","Evidence & Thesis","Before I Invest","Monitor My Thesis","Something Changed","Report Intelligence","Advanced Forecasting","Model Lab"],
"Settings":["Workspace Settings","Data & Production","Broker Connections"]}


# V20.3.0 — authoritative geometry/nav override. Keep this LAST so legacy Streamlit rules cannot win.
st.markdown(r"""
<style>
:root{--chr-sidebar:228px;--chr-banner:108px;}
/* Main viewport starts immediately below the fixed banner. */
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > section.main,
section[data-testid="stMain"],.stMain{
 position:fixed!important;left:var(--chr-sidebar)!important;right:0!important;top:var(--chr-banner)!important;bottom:0!important;
 margin:0!important;padding:0!important;width:auto!important;max-width:none!important;overflow-y:auto!important;overflow-x:hidden!important;background:#f7faff!important;
}
/* Kill every Streamlit top spacer/padding source. */
[data-testid="stMainBlockContainer"],.stMainBlockContainer,.main .block-container,section.main .block-container{
 position:absolute!important;left:0!important;right:0!important;top:0!important;
 width:100%!important;max-width:none!important;margin:0!important;padding:8px 12px 14px!important;box-sizing:border-box!important;
}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"],
.stMainBlockContainer > [data-testid="stVerticalBlock"]{margin:0!important;padding:0!important;gap:6px!important;}
/* Banner host itself must occupy zero flow height. */
div[data-testid="stElementContainer"]:has(.chrimata-exact-hero),
div[data-testid="stMarkdownContainer"]:has(.chrimata-exact-hero),
div.element-container:has(.chrimata-exact-hero){height:0!important;min-height:0!important;max-height:0!important;margin:0!important;padding:0!important;position:absolute!important;}
/* All country buttons are reference-style white cards. Emoji flags are part of the Python label. */
.main .stButton button[kind="secondary"]{
 background:#fff!important;color:#10264b!important;border:1px solid #d4e0ee!important;box-shadow:0 1px 2px rgba(20,50,80,.05)!important;
 height:40px!important;min-height:40px!important;border-radius:5px!important;font-size:11px!important;font-weight:700!important;white-space:nowrap!important;
}
.main .stButton button[kind="secondary"]:hover{background:#f8fbff!important;color:#0874df!important;border-color:#1687ff!important;}
/* Search remains blue. It is the only primary action in the header strip. */
.main .stButton button[kind="primary"]{background:#1687ff!important;color:#fff!important;border:1px solid #1687ff!important;}
@media(max-width:1100px){:root{--chr-sidebar:196px}.main .stButton button[kind="secondary"]{font-size:10px!important}}
@media(max-width:760px){:root{--chr-sidebar:0px;--chr-banner:74px}[data-testid="stMainBlockContainer"],.stMainBlockContainer,.main .block-container,section.main .block-container{padding:6px 8px 12px!important}}
</style>
""",unsafe_allow_html=True)

# V20.3.0 — final reference-header override. Must remain after all legacy theme CSS.
st.markdown(r"""
<style>
/* Main canvas: exactly below banner, never reserve another banner-height spacer. */
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > section.main,
section[data-testid="stMain"],.stMain{top:108px!important;}
[data-testid="stMainBlockContainer"],.stMainBlockContainer,.main .block-container,section.main .block-container{
 top:0!important;margin-top:0!important;padding-top:8px!important;
}
/* First dashboard row is the search/country strip. No phantom vertical margins. */
.main [data-testid="stVerticalBlock"]{row-gap:6px!important;}
.main [data-testid="stHorizontalBlock"]{margin-top:0!important;margin-bottom:0!important;}
/* Reset every header button to the white reference card. */
.main .stButton>button,
.main button[kind="secondary"],
.main button[kind="primary"]{
 background:#fff!important;color:#10264b!important;border:1px solid #d7e2ef!important;
 box-shadow:0 1px 3px rgba(16,38,75,.06)!important;border-radius:5px!important;
 height:40px!important;min-height:40px!important;font-size:11px!important;font-weight:700!important;
 white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
}
/* The Search action is column 2 of the dashboard's first horizontal row. */
.main [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) .stButton>button{
 background:#1687ff!important;color:#fff!important;border-color:#1687ff!important;font-size:12px!important;
}
.main .stButton>button:hover{background:#f8fbff!important;color:#0874df!important;border-color:#1687ff!important;}
.main [data-testid="stHorizontalBlock"]:first-of-type > [data-testid="stColumn"]:nth-child(2) .stButton>button:hover{background:#0874df!important;color:#fff!important;}
</style>
""",unsafe_allow_html=True)


# V20.3.0 — reference header strip: hard neutralise the remaining phantom 108px flow gap.
st.markdown(r"""
<style>
/* The deployed Streamlit DOM still contributes one legacy 108px top offset.
   Counter it at the actual main block level; the fixed banner itself remains 108px high. */
[data-testid="stMainBlockContainer"], .stMainBlockContainer,
section[data-testid="stMain"] .block-container, .main .block-container{
  transform:translateY(-104px)!important;
  padding-top:6px!important;
}
/* Plain-anchor country navigation: independent of Streamlit button/radio CSS. */
.chr-country-nav{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px;width:100%;margin:0;padding:0;}
.chr-country-link,.chr-country-link:visited{height:40px;display:flex;align-items:center;justify-content:center;gap:7px;box-sizing:border-box;background:#fff;color:#10264b!important;border:1px solid #d7e2ef;border-radius:5px;text-decoration:none!important;font-size:11px;font-weight:700;white-space:nowrap;box-shadow:0 1px 3px rgba(16,38,75,.06);overflow:hidden;}
.chr-country-link:hover{border-color:#1687ff;color:#0874df!important;background:#f8fbff;}
.chr-country-link.active{border:2px solid #1687ff;color:#0874df!important;background:#fff;}
.chr-country-link .chr-flag{font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:18px;line-height:1;}
@media(max-width:1200px){.chr-country-link{font-size:10px;gap:4px}.chr-country-link .chr-flag{font-size:15px}}
@media(max-width:900px){.chr-country-nav{grid-template-columns:repeat(3,minmax(0,1fr));}}
</style>
""",unsafe_allow_html=True)


# V20.3.0 — same-tab country buttons with embedded SVG flags (Windows-safe).
st.markdown(r"""
<style>
/* Country nav is native Streamlit interaction, but visually matches the reference. */
.chr-overview-flag{display:inline-block;width:52px;height:35px;flex:0 0 52px;background-size:100% 100%;background-repeat:no-repeat;background-position:center;border-radius:5px;box-shadow:0 0 0 1px rgba(0,0,0,.10);vertical-align:middle;}
.chr-overview-title{display:flex!important;align-items:center!important;gap:12px!important;}
@media(max-width:900px){.chr-overview-flag{width:42px;height:28px;flex-basis:42px;}}

.st-key-country_nav_v2027 [data-testid="stHorizontalBlock"]{gap:7px!important;}
.st-key-country_nav_v2027 .stButton>button{
  height:40px!important;min-height:40px!important;background:#fff!important;color:#10264b!important;
  border:1px solid #d7e2ef!important;border-radius:5px!important;box-shadow:0 1px 3px rgba(16,38,75,.06)!important;
  font-size:11px!important;font-weight:700!important;white-space:nowrap!important;padding:0 7px!important;
  display:flex!important;align-items:center!important;justify-content:center!important;gap:7px!important;
}
.st-key-country_nav_v2027 .stButton>button[kind="primary"]{background:#fff!important;color:#0874df!important;border:2px solid #1687ff!important;}
.st-key-country_nav_v2027 .stButton>button:hover{background:#f8fbff!important;color:#0874df!important;border-color:#1687ff!important;}
.st-key-country_nav_v2027 .stButton>button:before{content:"";display:inline-block;width:25px;height:17px;flex:0 0 25px;background-size:100% 100%;background-repeat:no-repeat;background-position:center;border-radius:2px;box-shadow:0 0 0 1px rgba(0,0,0,.08);}
/* Australia */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(1) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012469'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='white' stroke-width='5'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='%23C8102E' stroke-width='2'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='white' stroke-width='8'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='%23C8102E' stroke-width='4'/%3E%3Ccircle cx='45' cy='27' r='3' fill='white'/%3E%3Ccircle cx='48' cy='10' r='2' fill='white'/%3E%3C/svg%3E");}
/* United States */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(2) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Cg fill='%23B22234'%3E%3Crect y='0' width='60' height='3.1'/%3E%3Crect y='6.2' width='60' height='3.1'/%3E%3Crect y='12.4' width='60' height='3.1'/%3E%3Crect y='18.6' width='60' height='3.1'/%3E%3Crect y='24.8' width='60' height='3.1'/%3E%3Crect y='31' width='60' height='3.1'/%3E%3Crect y='37.2' width='60' height='2.8'/%3E%3C/g%3E%3Crect width='26' height='21.7' fill='%233C3B6E'/%3E%3Cg fill='white'%3E%3Ccircle cx='5' cy='5' r='1'/%3E%3Ccircle cx='12' cy='5' r='1'/%3E%3Ccircle cx='19' cy='5' r='1'/%3E%3Ccircle cx='8' cy='11' r='1'/%3E%3Ccircle cx='16' cy='11' r='1'/%3E%3Ccircle cx='5' cy='17' r='1'/%3E%3Ccircle cx='12' cy='17' r='1'/%3E%3Ccircle cx='19' cy='17' r='1'/%3E%3C/g%3E%3C/svg%3E");}
/* United Kingdom */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(3) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012169'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='white' stroke-width='8'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='%23C8102E' stroke-width='3'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='white' stroke-width='13'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='%23C8102E' stroke-width='7'/%3E%3C/svg%3E");}
/* Japan */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(4) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Ccircle cx='30' cy='20' r='11' fill='%23BC002D'/%3E%3C/svg%3E");}
/* Hong Kong */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(5) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23DE2910'/%3E%3Cpath d='M30 20c7-12 13-4 5 1 10-2 11 7 1 6 7 7-1 12-5 3-2 10-11 7-6-2-10 4-13-5-3-8-1-7 6-10 2-2 8-1 12 2z' fill='white'/%3E%3C/svg%3E");}
/* Canada */
.st-key-country_nav_v2027 [data-testid="stColumn"]:nth-child(6) button:before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Crect width='14' height='40' fill='%23D80621'/%3E%3Crect x='46' width='14' height='40' fill='%23D80621'/%3E%3Cpath d='M30 7l3 7 5-2-3 6 5 2-7 4 1 7h-8l1-7-7-4 5-2-3-6 5 2z' fill='%23D80621'/%3E%3C/svg%3E");}
@media(max-width:1200px){.st-key-country_nav_v2027 .stButton>button{font-size:10px!important;gap:4px!important}.st-key-country_nav_v2027 .stButton>button:before{width:21px;height:14px;flex-basis:21px}}

.chr-overview-flag.flag-au{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012469'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='white' stroke-width='5'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='%23C8102E' stroke-width='2'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='white' stroke-width='8'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='%23C8102E' stroke-width='4'/%3E%3Ccircle cx='45' cy='27' r='3' fill='white'/%3E%3Ccircle cx='48' cy='10' r='2' fill='white'/%3E%3C/svg%3E");}
.chr-overview-flag.flag-us{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Cg fill='%23B22234'%3E%3Crect y='0' width='60' height='3.1'/%3E%3Crect y='6.2' width='60' height='3.1'/%3E%3Crect y='12.4' width='60' height='3.1'/%3E%3Crect y='18.6' width='60' height='3.1'/%3E%3Crect y='24.8' width='60' height='3.1'/%3E%3Crect y='31' width='60' height='3.1'/%3E%3Crect y='37.2' width='60' height='2.8'/%3E%3C/g%3E%3Crect width='26' height='21.7' fill='%233C3B6E'/%3E%3Cg fill='white'%3E%3Ccircle cx='5' cy='5' r='1'/%3E%3Ccircle cx='12' cy='5' r='1'/%3E%3Ccircle cx='19' cy='5' r='1'/%3E%3Ccircle cx='8' cy='11' r='1'/%3E%3Ccircle cx='16' cy='11' r='1'/%3E%3Ccircle cx='5' cy='17' r='1'/%3E%3Ccircle cx='12' cy='17' r='1'/%3E%3Ccircle cx='19' cy='17' r='1'/%3E%3C/g%3E%3C/svg%3E");}
.chr-overview-flag.flag-gb{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012169'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='white' stroke-width='8'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='%23C8102E' stroke-width='3'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='white' stroke-width='13'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='%23C8102E' stroke-width='7'/%3E%3C/svg%3E");}
.chr-overview-flag.flag-jp{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Ccircle cx='30' cy='20' r='11' fill='%23BC002D'/%3E%3C/svg%3E");}
.chr-overview-flag.flag-hk{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23DE2910'/%3E%3Cpath d='M30 20c7-12 13-4 5 1 10-2 11 7 1 6 7 7-1 12-5 3-2 10-11 7-6-2-10 4-13-5-3-8-1-7 6-10 2-2 8-1 12 2z' fill='white'/%3E%3C/svg%3E");}
.chr-overview-flag.flag-ca{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Crect width='14' height='40' fill='%23D80621'/%3E%3Crect x='46' width='14' height='40' fill='%23D80621'/%3E%3Cpath d='M30 7l3 7 5-2-3 6 5 2-7 4 1 7h-8l1-7-7-4 5-2-3-6 5 2z' fill='%23D80621'/%3E%3C/svg%3E");}</style>
""",unsafe_allow_html=True)

PAGE_MAP={
("Company Command Centre","Overview"):"Company Command Centre",("Company Command Centre","Fundamentals"):"Fundamentals",("Company Command Centre","Valuation"):"Valuation",("Company Command Centre","Technical"):"Technical",("Company Command Centre","Announcements & Reports"):"Announcements & Reports",("Company Command Centre","Report Intelligence"):"Report Intelligence",("Company Command Centre","News & Events"):"News & Events",("Company Command Centre","Thesis Scorecard"):"Thesis Scorecard",("Company Command Centre","Catalyst Calendar"):"Catalyst Calendar",("Company Command Centre","Quant"):"Quant",("Company Command Centre","Forecasts"):"Forecasts",
("Portfolio","Portfolio Overview"):"Portfolio",("Portfolio","Portfolio Intelligence"):"Portfolio Intelligence",("Portfolio","Risk Centre"):"Risk Centre",("Portfolio","Watchlist"):"Watchlist",("Portfolio","Paper Portfolio"):"Paper Portfolio",
("Research Tools","Research Report"):"Research Report",("Research Tools","Investment Committee"):"Investment Committee",("Research Tools","Evidence & Thesis"):"Evidence & Thesis",("Research Tools","Before I Invest"):"Before I Invest",("Research Tools","Monitor My Thesis"):"Monitor My Thesis",("Research Tools","Something Changed"):"Something Changed",("Research Tools","Report Intelligence"):"Report Intelligence",("Research Tools","Advanced Forecasting"):"Advanced Forecasting",("Research Tools","Model Lab"):"Model Lab",
("Settings","Workspace Settings"):"Workspace Settings",("Settings","Data & Production"):"Data & Production",("Settings","Broker Connections"):"Broker Connections"}
if primary=="Home": page="Dashboard"
elif primary=="Company Search": page="Company Search"
elif primary=="Markets": page="Markets"
elif primary=="Watchlist": page="Watchlist"
elif primary=="Screening": page="Markets"
elif primary=="Alerts": page="Something Changed"
elif primary=="Calendar": page="Catalyst Calendar"
elif primary in SUBPAGES:
    sub=st.sidebar.selectbox("Inside this workspace",SUBPAGES[primary],key=f"chr_sub_v209_{primary}"); page=PAGE_MAP[(primary,sub)]
else: page=primary

st.sidebar.markdown("""<div class="chr-side-spacer"></div><div class="chr-side-wealth"><span class="wealth-pillar"><svg viewBox="0 0 48 64" aria-hidden="true"><path d="M8 8h32M11 12h26M14 16h20M14 48h20M11 52h26M8 56h32"/><path d="M16 17v30M22 17v30M26 17v30M32 17v30"/><path d="M10 6h28l-3-3H13zM10 58h28l3 3H7z"/></svg></span><span class="wealth-copy">KNOWLEDGE<br>COMPOUNDS<br>WEALTH</span></div><div class="chr-side-version">v20.7.2.2</div><div class="chr-side-copyright">© 2026 Chrímata. All rights reserved.</div>""",unsafe_allow_html=True)

def render_chrimata_persistent_header():
    # V20.3.0: paint the banner on the app viewport itself. This creates NO Streamlit
    # element in document flow, eliminating the phantom 100+ px spacer below it.
    banner_path=Path(__file__).resolve().parent/"assets"/"chrimata_banner_crisp.jpg"
    try:
        banner_b64=base64.b64encode(banner_path.read_bytes()).decode("ascii")
        st.markdown(f"""<style>
        [data-testid="stAppViewContainer"]::before{{
          content:"";position:fixed;left:0;right:0;top:0;height:108px;z-index:1000000;
          background-image:url(data:image/jpeg;base64,{banner_b64});background-size:100% 108px;background-repeat:no-repeat;background-position:center top;
          pointer-events:none;
        }}
        </style>""",unsafe_allow_html=True)
    except Exception:
        pass

render_chrimata_persistent_header()

_PAGE_SUBTITLES={
 "Dashboard":"Market overview and research starting point",
 "Company Search":"Find and analyse exact listings across global markets",
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
if page not in {"Dashboard","Company Search"}:
    st.markdown(f"""<div class="mia-shell-head">
<div><div class="mia-eyebrow">Chrímata / {primary}</div>
<div class="mia-shell-title">{page}</div><div class="mia-shell-sub">{_shell_sub}</div></div>
<div class="mia-live"><span class="mia-dot"></span> Research workspace</div>
</div>""",unsafe_allow_html=True)

h=history(ticker); meta=info(ticker)
if h.empty and page not in {"Dashboard","Company Search"}:
    st.error(f"No market data returned for {ticker}. Try another matching listing or enter the exchange ticker directly.")
    st.stop()
if h.empty and page!="Company Search":
    h=history("^AXJO","1mo")
    meta={}
close=h["Close"] if not h.empty and "Close" in h else pd.Series(dtype=float)
price=float(close.iloc[-1]) if not close.empty else np.nan
name=meta.get("longName") or meta.get("shortName") or ticker
rv=rsi(close); rv=float(rv.iloc[-1]) if len(rv) and pd.notna(rv.iloc[-1]) else np.nan

# Browser-tab branding is intentionally static in V19.8: Chrímata + Parthenon icon.

if page not in {"Dashboard","Company Search"}:
    st.title("Chrímata")
    st.caption("V20.7.3.1 • Chrímata • Company Search Header & Button Fix")



MARKET_OVERVIEW_CONFIG={
 "Australia":{"flag":"🇦🇺","indices":{"S&P/ASX 200":"^AXJO","All Ordinaries":"^AORD","ASX 50":"^AFLI","ASX 100":"^ATOI","ASX 300":"^AXKO","ASX 20":"^ATLI","All Technology":"^AXTX","ASX 200 Resources":"^AXJR","All Ords Gold (sub)":"^AXGD"},"benchmark":"^AXJO","vol":"^AXVI","currency":"AUDUSD=X","universe":["BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","WES.AX","MQG.AX","WOW.AX","TLS.AX","QAN.AX","ZIP.AX","XRO.AX","FMG.AX","RIO.AX","ALL.AX","REA.AX","CAR.AX","JHX.AX","COL.AX"],"sectors":{"Financials":["^AXFJ","QFN.AX"],"Health Care":["^AXHJ",["CSL.AX","RMD.AX","COH.AX","FPH.AX"]],"Real Estate":["^AXRE","^AXPJ","VAP.AX"],"Industrials":["^AXNJ",["BXB.AX","QAN.AX","QUB.AX","CPU.AX"]],"Telecommunication":["^AXTJ",["TLS.AX","REA.AX","CAR.AX","TPG.AX"]],"Staples":["^AXSJ",["WOW.AX","COL.AX","EDV.AX","TWE.AX"]],"Discretionary":["^AXDJ",["WES.AX","ALL.AX","JBH.AX","HVN.AX"]],"Utilities":["^AXUJ",["APA.AX","AGL.AX","ORG.AX"]],"Materials":["^AXMJ","QRE.AX"],"Information Technology":["^AXIJ","ATEC.AX"],"Energy":["^AXEJ","FUEL.AX"]}},
 "United States":{"flag":"🇺🇸","indices":{"S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI","Nasdaq Composite":"^IXIC","Russell 2000":"^RUT","Russell 1000":"^RUI","S&P 100":"^OEX","S&P MidCap 400":"^MID","NYSE Composite":"^NYA","NYSE Arca Tech 100":"^PSE"},"benchmark":"^GSPC","vol":"^VIX","currency":"AUDUSD=X","universe":["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK-B","JPM","V","WMT","XOM","MA","NFLX","COST","AMD","PEP","KO","DIS","CAT"],"sectors":{"Technology":"XLK","Financials":"XLF","Health Care":"XLV","Consumer Discretionary":"XLY","Industrials":"XLI","Energy":"XLE","Materials":"XLB","Utilities":"XLU","Real Estate":"XLRE","Staples":"XLP","Communication":"XLC"}},
 "United Kingdom":{"flag":"🇬🇧","indices":{"FTSE 100":"^FTSE","FTSE 250":"^FTMC","FTSE All-Share":"^FTAS","FTSE 350":"^FTLC","FTSE SmallCap":"^FTSC","FTSE AIM All-Share":"^FTAI"},"benchmark":"^FTSE","vol":None,"currency":"GBPUSD=X","universe":["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","REL.L","LSEG.L","DGE.L","BARC.L","VOD.L"],"sectors":{}},
 "Japan":{"flag":"🇯🇵","indices":{"Nikkei 225":"^N225","TOPIX":"^TOPX","JPX-Nikkei 400":"^JPXNK400","TOPIX Core 30":"^TPXC30","TOPIX 100":"^TPX100","TOPIX 500":"^TPX500"},"benchmark":"^N225","vol":None,"currency":"JPY=X","universe":["7203.T","6758.T","9984.T","8306.T","6861.T","8035.T","9432.T","7974.T","6501.T","7267.T","6098.T","9983.T"],"sectors":{}},
 "Hong Kong":{"flag":"🇭🇰","indices":{"Hang Seng":"^HSI","Hang Seng China Ent.":"^HSCE","Hang Seng Tech":"^HSTECH","Hang Seng Composite":"^HSCI","Hang Seng China AH Premium":"^HSAHP","Hang Seng Finance":"^HSNF"},"benchmark":"^HSI","vol":None,"currency":"HKD=X","universe":["0700.HK","9988.HK","3690.HK","1299.HK","0005.HK","0388.HK","1810.HK","9618.HK","2318.HK","0883.HK","0941.HK","9999.HK"],"sectors":{}},
 "Canada":{"flag":"🇨🇦","indices":{"S&P/TSX Composite":"^GSPTSE","TSX 60":"^TX60","TSX Venture":"^SPCDNX","S&P/TSX Completion":"^TX40","S&P/TSX SmallCap":"^TX20","S&P/TSX Capped Financials":"^TTFS"},"benchmark":"^GSPTSE","vol":None,"currency":"CAD=X","universe":["RY.TO","TD.TO","SHOP.TO","ENB.TO","CNR.TO","BNS.TO","CP.TO","SU.TO","BMO.TO","CNQ.TO","TRI.TO","MFC.TO"],"sectors":{}}
}
# V20.7.0 — isolated country-aware volatility widget configuration.
# Candidate symbols are tried in order. This configuration is used only by the
# Volatility Index card and cannot alter benchmark/index/sector/chart inputs.
VOLATILITY_INDEX_CONFIG={
 "Australia":{"name":"S&P/ASX 200 VIX","source":"ASX · Australia","symbols":["^AXVI"],"note":"30-day implied volatility derived from S&P/ASX 200 index options."},
 "United States":{"name":"CBOE Volatility Index (VIX)","source":"CBOE · US","symbols":["^VIX"],"note":"S&P 500 options-implied volatility over roughly the next 30 days."},
 "United Kingdom":{"name":"FTSE 100 Volatility Index","source":"UK","symbols":["^VFTSE","VFTSE.L"],"note":"UK equity options-implied volatility benchmark, when available from the configured market-data provider."},
 "Japan":{"name":"Nikkei Stock Average Volatility Index","source":"Japan","symbols":["^JNIV","JNIV"],"note":"Japanese equity options-implied volatility benchmark, when available from the configured market-data provider."},
 "Hong Kong":{"name":"Hang Seng Volatility Index","source":"Hong Kong","symbols":["^VHSI","VHSI.HK"],"note":"Hang Seng options-implied volatility benchmark, when available from the configured market-data provider."},
 "Canada":{"name":"S&P/TSX 60 VIX","source":"Canada","symbols":["^VIXC","VIXC.TO"],"note":"Canadian equity options-implied volatility benchmark, when available from the configured market-data provider."}
}

# V20.6.9 — isolated country-specific Top Gainers coverage.
# Kept separate from MARKET_OVERVIEW_CONFIG[market]["universe"] so expanding
# mover coverage cannot alter sectors, fallers, watchlist, calendars or charts.
TOP_GAINERS_UNIVERSE={
 "Australia":["BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","WES.AX","MQG.AX","WOW.AX","TLS.AX","QAN.AX","ZIP.AX","XRO.AX","FMG.AX","RIO.AX","ALL.AX","REA.AX","CAR.AX","JHX.AX","COL.AX","RMD.AX","COH.AX","FPH.AX","BXB.AX","QUB.AX","CPU.AX","TPG.AX","EDV.AX","TWE.AX","JBH.AX","HVN.AX","APA.AX","AGL.AX","ORG.AX","WDS.AX","STO.AX","MIN.AX","S32.AX","NST.AX","NEM.AX","GMG.AX","SCG.AX","MGR.AX","SUN.AX","IAG.AX","QBE.AX","ASX.AX","SEK.AX","PME.AX","ALU.AX"],
 "United States":["AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","BRK-B","JPM","V","WMT","XOM","MA","NFLX","COST","AMD","PEP","KO","DIS","CAT","AVGO","ORCL","CRM","ADBE","CSCO","INTC","QCOM","TXN","AMAT","MU","IBM","GE","BA","GS","BAC","WFC","MS","CVX","COP","LLY","JNJ","UNH","MRK","ABBV","HD","LOW","NKE","MCD","SBUX"],
 "United Kingdom":["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","REL.L","LSEG.L","DGE.L","BARC.L","VOD.L","BATS.L","GLEN.L","NG.L","RR.L","LLOY.L","AAL.L","ANTO.L","BA.L","CPG.L","EXPN.L","HLMA.L","III.L","IMB.L","LAND.L","MNG.L","PRU.L","SGE.L","SSE.L","STAN.L","TSCO.L","WTB.L"],
 "Japan":["7203.T","6758.T","9984.T","8306.T","6861.T","8035.T","9432.T","7974.T","6501.T","7267.T","6098.T","9983.T","8058.T","8316.T","8411.T","8766.T","6954.T","4063.T","6367.T","4519.T","4502.T","4568.T","7741.T","6902.T","6702.T","8001.T","8002.T","8031.T","2914.T","3382.T"],
 "Hong Kong":["0700.HK","9988.HK","3690.HK","1299.HK","0005.HK","0388.HK","1810.HK","9618.HK","2318.HK","0883.HK","0941.HK","9999.HK","1211.HK","1024.HK","2020.HK","0669.HK","0016.HK","0011.HK","0002.HK","0003.HK","0066.HK","0267.HK","0688.HK","0823.HK","1109.HK","1928.HK","2382.HK","2628.HK","3968.HK","6098.HK"],
 "Canada":["RY.TO","TD.TO","SHOP.TO","ENB.TO","CNR.TO","BNS.TO","CP.TO","SU.TO","BMO.TO","CNQ.TO","TRI.TO","MFC.TO","BCE.TO","T.TO","ABX.TO","WCN.TO","CSU.TO","ATD.TO","NA.TO","CM.TO","POW.TO","GWO.TO","SLF.TO","NTR.TO","WPM.TO","AEM.TO","FNV.TO","IMO.TO","TRP.TO","PPL.TO"]
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

@st.cache_data(ttl=60)
def overview_quote(ticker,period="5d",interval=None):
    """Latest provider quote + chart series. Intraday requests use 5-minute bars.
    Twelve Data is preferred for the headline price when configured; Yahoo remains
    the chart/fallback provider. Missing provider data stays missing.
    """
    try:
        kwargs={"period":period,"auto_adjust":True}
        if interval: kwargs["interval"]=interval
        d=yf.Ticker(ticker).history(**kwargs)
        c=_ov_close_series(d,ticker)
        if c.empty:return None
        last=float(c.iloc[-1]); prev=float(c.iloc[-2]) if len(c)>1 else np.nan
        source="Yahoo/yfinance"
        # Prefer the configured live quote provider without sacrificing chart history.
        try:
            if _search_key:
                tq=twelve_price(ticker,_search_key)
                if getattr(tq,"price",None) is not None:
                    live=float(tq.price)
                    # Preserve the previous close/bar reference for change calculations.
                    last=live; source="Twelve Data"
        except Exception:
            pass
        return {"last":last,"prev":prev,"change":last-prev if np.isfinite(prev) else np.nan,"pct":last/prev-1 if np.isfinite(prev) and prev else np.nan,"series":c,"times":[str(x) for x in c.index],"source":source,"asof":datetime.now(timezone.utc).isoformat()}
    except Exception:return None

@st.cache_data(ttl=60)
def overview_sector_performance(sources, period="5d"):
    """Return sector price performance using the official S&P/ASX sector index first.
    If the active market-data provider cannot resolve that index, fall back to the
    configured ASX proxy or an equal-weight basket of representative ASX shares.
    Values are price returns (dividends excluded) and no synthetic value is invented.
    """
    if isinstance(sources, str):
        sources=[sources]
    for source in (sources or []):
        # Single provider symbol (official sector index preferred).
        if isinstance(source, str):
            q=overview_quote(source,period)
            if q:
                vals=pd.to_numeric(q.get("series",pd.Series(dtype=float)),errors="coerce").dropna()
                if len(vals)>=2 and float(vals.iloc[0])!=0:
                    return {"return":(float(vals.iloc[-1])/float(vals.iloc[0])-1)*100,"source":source}
        # Equal-weight representative ASX basket fallback.
        elif isinstance(source, (list,tuple)):
            rets=[]
            for ticker in source:
                q=overview_quote(str(ticker),period)
                if not q: continue
                vals=pd.to_numeric(q.get("series",pd.Series(dtype=float)),errors="coerce").dropna()
                if len(vals)>=2 and float(vals.iloc[0])!=0:
                    rets.append((float(vals.iloc[-1])/float(vals.iloc[0])-1)*100)
            if rets:
                return {"return":float(np.mean(rets)),"source":"ASX representative basket"}
    return None

@st.cache_data(ttl=60, show_spinner=False)
def overview_batch(tickers):
    rows=[]
    for t in list(tickers):
        q=overview_quote(t,"5d")
        if not q:continue
        try:m=info(t); nm=m.get("shortName") or m.get("longName") or t
        except Exception:nm=t
        rows.append({"Ticker":t,"Company":nm,"Last":q["last"],"Change":q["change"],"% Chg":q["pct"]})
    return pd.DataFrame(rows)

@st.cache_data(ttl=21600, show_spinner=False)
def overview_global_dividends(market, tickers, twelve_data_key="", fmp_key=""):
    # V20.5.9: forward corporate-actions provider hierarchy. Calendar data is
    # cached because declarations change far less frequently than market prices.
    return corporate_actions_calendar(market, tuple(tickers), 120, twelve_data_key, fmp_key)

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

@st.cache_data(ttl=1800, show_spinner=False)
def overview_calendar(tickers):
    """Best-effort upcoming earnings/dividend calendar from the active Yahoo feed.
    Returns only future/current events; unavailable fields remain unavailable rather than invented.
    """
    earnings=[]; dividends=[]
    now=pd.Timestamp.now(tz="UTC")
    for t in list(tickers)[:20]:
        try:
            tk=yf.Ticker(t); m=tk.info or {}; nm=m.get("longName") or m.get("shortName") or t
            # Earnings: prefer the dedicated earnings-date endpoint, then calendar fallback.
            found_earn=False
            try:
                edf=tk.get_earnings_dates(limit=4)
                if edf is not None and not edf.empty:
                    for ed in edf.index:
                        dt=pd.to_datetime(ed,utc=True,errors="coerce")
                        if pd.notna(dt) and dt>=now-pd.Timedelta(days=1):
                            earnings.append({"Ticker":t,"Company":nm,"Date":dt.date().isoformat(),"Type":"Earnings"}); found_earn=True; break
            except Exception: pass
            if not found_earn:
                try:
                    cal=tk.calendar
                    if isinstance(cal,dict):
                        ed=cal.get("Earnings Date") or cal.get("EarningsDate")
                        if isinstance(ed,(list,tuple)) and ed: ed=ed[0]
                        dt=pd.to_datetime(ed,utc=True,errors="coerce")
                        if pd.notna(dt) and dt>=now-pd.Timedelta(days=1): earnings.append({"Ticker":t,"Company":nm,"Date":dt.date().isoformat(),"Type":"Earnings"})
                except Exception: pass
            # Dividend: Yahoo exposes a future ex-dividend timestamp for many securities.
            ex=m.get("exDividendDate")
            if ex:
                dt=pd.to_datetime(ex,unit="s",utc=True,errors="coerce")
                if pd.notna(dt) and dt>=now-pd.Timedelta(days=1):
                    pay=m.get("dividendDate")
                    pdt=pd.to_datetime(pay,unit="s",utc=True,errors="coerce") if pay else pd.NaT
                    dividends.append({"Ticker":t,"Company":nm,"Ex-Date":dt.date().isoformat(),"Pay-Date":pdt.date().isoformat() if pd.notna(pdt) else "—","Dividend Rate":m.get("dividendRate")})
        except Exception: pass
    e=pd.DataFrame(earnings); d=pd.DataFrame(dividends)
    if not e.empty: e=e.drop_duplicates(subset=["Ticker","Date"]).sort_values("Date")
    if not d.empty: d=d.drop_duplicates(subset=["Ticker","Ex-Date"]).sort_values("Ex-Date")
    return e,d

def _chr_svg_line(series, width=420, height=72, stroke="#12b76a", fill="#e8f8ef"):
    try: vals=pd.to_numeric(pd.Series(series),errors="coerce").dropna().astype(float).tolist()
    except Exception: vals=[]
    if len(vals)<2: return ""
    lo,hi=min(vals),max(vals); span=(hi-lo) or 1.0; pts=[]
    for i,v in enumerate(vals):
        x=2+(width-4)*i/(len(vals)-1); y=height-3-(height-8)*(v-lo)/span; pts.append((x,y))
    line=" ".join(f"{x:.1f},{y:.1f}" for x,y in pts); area=f"2,{height-2} "+line+f" {width-2},{height-2}"
    return f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none"><polygon points="{area}" fill="{fill}"/><polyline points="{line}" fill="none" stroke="{stroke}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>'

def _chr_market_session_spec(market):
    return {
        "Australia": ("Australia/Sydney", time(10,0), time(16,0)),
        "United States": ("America/New_York", time(9,30), time(16,0)),
        "United Kingdom": ("Europe/London", time(8,0), time(16,30)),
        "Japan": ("Asia/Tokyo", time(9,0), time(15,30)),
        "Hong Kong": ("Asia/Hong_Kong", time(9,30), time(16,0)),
        "Canada": ("America/Toronto", time(9,30), time(16,0)),
    }.get(market, ("Australia/Sydney", time(10,0), time(16,0)))


def _chr_true_intraday(q, market):
    """Return today's actually elapsed exchange-local bars and full-session geometry metadata."""
    if not q: return q
    try:
        vals=pd.to_numeric(pd.Series(q.get('series',[])),errors='coerce')
        raw_times=list(q.get('times',[]))
        n=min(len(vals),len(raw_times))
        if n < 2: return q
        vals=vals.iloc[:n].reset_index(drop=True)
        idx=pd.to_datetime(raw_times[:n],errors='coerce',utc=True)
        tzname,op,cl=_chr_market_session_spec(market); tz=ZoneInfo(tzname)
        local=idx.tz_convert(tz)
        now=datetime.now(tz)
        # Yahoo can return more than one calendar date around boundaries. Use the latest
        # trading date not in the future, and never plot a timestamp that has not occurred.
        dates=[x.date() for x in local if pd.notna(x) and x <= now]
        if not dates: return q
        trade_date=max(dates)
        open_dt=datetime.combine(trade_date,op,tzinfo=tz); close_dt=datetime.combine(trade_date,cl,tzinfo=tz)
        mask=[]
        for x in local:
            ok=pd.notna(x) and x.date()==trade_date and open_dt <= x <= close_dt
            if trade_date==now.date(): ok=ok and x <= now
            mask.append(ok)
        pos=[i for i,b in enumerate(mask) if b and np.isfinite(_mia_num(vals.iloc[i]))]
        if len(pos)<2: return q
        qq=dict(q)
        qq['series']=[float(vals.iloc[i]) for i in pos]
        qq['times']=[local[i].isoformat() for i in pos]
        qq['session_open']=open_dt.isoformat(); qq['session_close']=close_dt.isoformat()
        qq['latest_bar']=local[pos[-1]].isoformat()
        return qq
    except Exception:
        return q


def _chr_intraday_labels(market):
    tzname,op,cl=_chr_market_session_spec(market)
    base=datetime(2000,1,1,op.hour,op.minute)
    end=datetime(2000,1,1,cl.hour,cl.minute)
    out=[]
    # 7 evenly spaced labels across the actual exchange session.
    for i in range(7):
        d=base+(end-base)*(i/6)
        out.append(d.strftime('%H:%M'))
    return out


def _chr_big_market_svg(series, prev=None, width=760, height=230, stroke="#12b76a", fill="#e8f8ef", times=None, session_open=None, session_close=None):
    """Reference chart; intraday X positions use real exchange timestamps, never redistributed bars."""
    try: vals=pd.to_numeric(pd.Series(series),errors="coerce").dropna().astype(float).tolist()
    except Exception: vals=[]
    if len(vals)<2: return ""
    finite=[v for v in vals if np.isfinite(v)]
    if np.isfinite(_mia_num(prev)): finite.append(float(prev))
    lo0,hi0=min(finite),max(finite); raw=max(hi0-lo0,abs(hi0)*.001,.01)
    pad=raw*.10; lo=lo0-pad; hi=hi0+pad; span=(hi-lo) or 1.0
    left=58; right=4; top=5; bottom=5; pw=width-left-right; ph=height-top-bottom
    xfracs=None
    if times and session_open and session_close:
        try:
            ti=pd.to_datetime(list(times),errors='coerce',utc=True)
            so=pd.Timestamp(session_open); sc=pd.Timestamp(session_close)
            if so.tzinfo is None: so=so.tz_localize('UTC')
            else: so=so.tz_convert('UTC')
            if sc.tzinfo is None: sc=sc.tz_localize('UTC')
            else: sc=sc.tz_convert('UTC')
            denom=max((sc-so).total_seconds(),1)
            xfracs=[min(1,max(0,(x-so).total_seconds()/denom)) for x in ti[:len(vals)]]
            if len(xfracs)!=len(vals): xfracs=None
        except Exception: xfracs=None
    pts=[]
    for i,v in enumerate(vals):
        frac=xfracs[i] if xfracs is not None else i/(len(vals)-1)
        x=left+pw*frac; y=top+ph-(ph*(v-lo)/span); pts.append((x,y))
    line=" ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    # Fill only to the latest actual bar, not to the market close.
    area=f"{pts[0][0]:.1f},{top+ph} "+line+f" {pts[-1][0]:.1f},{top+ph}"
    grid=[]; labels=[]
    for i in range(5):
        frac=i/4; y=top+ph*frac; val=hi-span*frac
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+pw}" y2="{y:.1f}" stroke="#dfe8f2" stroke-width="1"/>')
        labels.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" font-size="12" fill="#27496f" font-family="Arial,Helvetica,sans-serif">{val:,.2f}</text>')
    for i in range(7):
        x=left+pw*i/6; grid.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ph}" stroke="#e7eef6" stroke-width="1"/>')
    prevline=''
    if np.isfinite(_mia_num(prev)):
        py=top+ph-(ph*(float(prev)-lo)/span)
        prevline=f'<line x1="{left}" y1="{py:.1f}" x2="{left+pw}" y2="{py:.1f}" stroke="#ff5c68" stroke-width="1.2" stroke-dasharray="4 3"/>'
    return f'<svg viewBox="0 0 {width} {height}" preserveAspectRatio="none">{"".join(grid)}{"".join(labels)}<polygon points="{area}" fill="{fill}" fill-opacity=".82"/>{prevline}<polyline points="{line}" fill="none" stroke="{stroke}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>'

def _chr_metric_card(label,ticker,q,accent=None,chart_key=None,selected=False,market="Australia"):
    from urllib.parse import quote
    selected_cls=" selected" if selected else ""
    href=f"?market={quote(str(market))}&chart={quote(str(chart_key or ticker))}#investment-command-centre"
    if not q:
        return f'<a class="chr-metric-link" href="{href}" target="_self"><div class="chr-card chr-metric{selected_cls}"><b>{label}</b><strong>N/A</strong></div></a>'
    up=float(q.get("change",0) or 0)>=0; col="#0aa968" if up else "#ef4444"; arrow="▲" if up else "▼"
    spark=_chr_svg_line(q.get("series",[]),300,46,accent or col,"#eaf8f1" if up else "#fff0f0")
    return f'<a class="chr-metric-link" href="{href}" target="_self" title="Show {label} chart"><div class="chr-card chr-metric{selected_cls}"><div class="chr-metric-name">{label} <span>{ticker}</span></div><div class="chr-metric-row"><strong>{q["last"]:,.2f}</strong><em style="color:{col}">{arrow} {q["change"]:+,.2f} ({q["pct"]:+.2%})</em></div><div class="chr-spark">{spark}</div></div></a>'

def _chr_smooth_market_component(market, instruments, selected_key, range_map, sectors, index_table, date_label, time_label, zone_label, market_status, market_is_open, updated_label, panel_asof):
    # V20.4.0 complete ASX sector data engine with official sector indices and fallbacks.
    import json, html as _html
    datasets={}
    for label,ticker,base,accent in instruments:
        per={}
        for rng,(period,interval) in range_map.items():
            q=overview_quote(ticker,period,interval) or base
            if q and rng=='1D':
                q=_chr_true_intraday(q, market)
            if q:
                up=float(q.get('change',0) or 0)>=0
                col='#10b96a' if up else '#ef4444'; fill='#e7f8ef' if up else '#fff0f0'
                # V20.7.4.18.1: derive label Y positions from the exact same value range
                # used by _chr_big_market_svg.  Keep this Pandas-safe: never evaluate
                # a Series as a boolean.
                try:
                    _chart_vals=pd.to_numeric(pd.Series(q.get('series',[])),errors='coerce').dropna().astype(float)
                except Exception:
                    _chart_vals=pd.Series(dtype=float)
                _prev_num=_mia_num(q.get('prev'))
                _last_y_frac=None; _prev_y_frac=None
                if len(_chart_vals)>=2:
                    _finite=_chart_vals[np.isfinite(_chart_vals)].tolist()
                    if np.isfinite(_prev_num): _finite.append(float(_prev_num))
                    if _finite:
                        _lo0,_hi0=min(_finite),max(_finite); _raw=max(_hi0-_lo0,abs(_hi0)*.001,.01)
                        _pad=_raw*.10; _lo=_lo0-_pad; _hi=_hi0+_pad; _span=(_hi-_lo) or 1.0
                        _last_y_frac=max(0.0,min(1.0,1.0-(float(_chart_vals.iloc[-1])-_lo)/_span))
                        if np.isfinite(_prev_num):
                            _prev_y_frac=max(0.0,min(1.0,1.0-(float(_prev_num)-_lo)/_span))
                per[rng]={
                    'label':label,'ticker':ticker,'last':f"{q['last']:,.2f}",
                    'change':f"{q.get('change',0):+,.2f}",'pct':f"{q.get('pct',0):+.2%}",
                    'up':up,'prev':f"{q.get('prev'):,.2f}" if np.isfinite(_prev_num) else '—',
                    'lastY':_last_y_frac,'prevY':_prev_y_frac,
                    'svg':_chr_big_market_svg(q.get('series',[]),q.get('prev'),760,230,col,fill,q.get('times') if rng=='1D' else None,q.get('session_open') if rng=='1D' else None,q.get('session_close') if rng=='1D' else None)
                }
        datasets[ticker]=per
    cards=[]
    for label,ticker,q,accent in instruments:
        if not q: continue
        up=float(q.get('change',0) or 0)>=0; col='#0aa968' if up else '#ef4444'; arrow='▲' if up else '▼'
        spark=_chr_svg_line(q.get('series',[]),300,46,accent or col,'#eaf8f1' if up else '#fff0f0')
        cards.append(f'''<button class="metric {'selected' if ticker==selected_key else ''}" data-key="{_html.escape(ticker)}"><div class="mname">{_html.escape(label)} <span>{_html.escape(ticker)}</span></div><div class="mrow"><strong>{q['last']:,.2f}</strong><em style="color:{col}">{arrow} {q.get('change',0):+,.2f} ({q.get('pct',0):+.2%})</em></div><div class="spark">{spark}</div></button>''')
    # V20.4.0: all 11 ASX sectors use official sector indices first, then provider-safe fallbacks.
    sector_data = sectors if isinstance(sectors, dict) else {'Day': sectors, 'Week': sectors, 'Month': sectors, 'YTD': sectors}
    sector_json=json.dumps({k:[{'name':n,'value':(float(v) if v is not None and np.isfinite(_mia_num(v)) else None)} for n,v in vals] for k,vals in sector_data.items()}).replace('</','<\/')
    flag_class={'Australia':'au','United States':'us','United Kingdom':'gb','Japan':'jp','Hong Kong':'hk','Canada':'ca'}.get(market,'au')
    data=json.dumps(datasets).replace('</','<\\/')
    selected=json.dumps(selected_key)
    status_cls='open' if market_is_open else 'closed'
    _initial=(datasets.get(selected_key,{}) or {}).get('1D') or (next(iter((datasets.get(selected_key,{}) or {}).values()),{}))
    _initial_svg=_initial.get('svg','') if _initial else ''
    _initial_title=((_initial.get('label','')+' Intraday Chart') if _initial else '')
    _initial_last=(_initial.get('last','') if _initial else '')
    _initial_prev=(_initial.get('prev','') if _initial else '')
    _initial_col=('#10b96a' if (_initial or {}).get('up',True) else '#ef4444')
    comp=f'''<div id="smooth"><style>
    *{{box-sizing:border-box}}body{{margin:0;font-family:Arial,Helvetica,sans-serif;color:#0c2747;background:transparent}}.head{{display:flex;justify-content:space-between;align-items:center;margin:0 0 8px}}.title{{font-size:20px;font-weight:800;display:flex;align-items:center;gap:9px}}.hflag{{display:inline-block;width:36px;height:24px;flex:0 0 36px;background-size:100% 100%;background-repeat:no-repeat;border-radius:3px;box-shadow:0 0 0 1px rgba(0,0,0,.10)}}.hflag.au{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012469'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='white' stroke-width='5'/%3E%3Cpath d='M0 0L30 20M30 0L0 20' stroke='%23C8102E' stroke-width='2'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='white' stroke-width='8'/%3E%3Cpath d='M15 0v20M0 10h30' stroke='%23C8102E' stroke-width='4'/%3E%3Ccircle cx='45' cy='27' r='3' fill='white'/%3E%3Ccircle cx='48' cy='10' r='2' fill='white'/%3E%3C/svg%3E")}}.hflag.us{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Cg fill='%23B22234'%3E%3Crect y='0' width='60' height='3.1'/%3E%3Crect y='6.2' width='60' height='3.1'/%3E%3Crect y='12.4' width='60' height='3.1'/%3E%3Crect y='18.6' width='60' height='3.1'/%3E%3Crect y='24.8' width='60' height='3.1'/%3E%3Crect y='31' width='60' height='3.1'/%3E%3Crect y='37.2' width='60' height='2.8'/%3E%3C/g%3E%3Crect width='26' height='21.7' fill='%233C3B6E'/%3E%3Cg fill='white'%3E%3Ccircle cx='5' cy='5' r='1'/%3E%3Ccircle cx='12' cy='5' r='1'/%3E%3Ccircle cx='19' cy='5' r='1'/%3E%3Ccircle cx='8' cy='11' r='1'/%3E%3Ccircle cx='16' cy='11' r='1'/%3E%3Ccircle cx='5' cy='17' r='1'/%3E%3Ccircle cx='12' cy='17' r='1'/%3E%3Ccircle cx='19' cy='17' r='1'/%3E%3C/g%3E%3C/svg%3E")}}.hflag.gb{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23012169'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='white' stroke-width='8'/%3E%3Cpath d='M0 0L60 40M60 0L0 40' stroke='%23C8102E' stroke-width='3'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='white' stroke-width='13'/%3E%3Cpath d='M30 0v40M0 20h60' stroke='%23C8102E' stroke-width='7'/%3E%3C/svg%3E")}}.hflag.jp{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Ccircle cx='30' cy='20' r='11' fill='%23BC002D'/%3E%3C/svg%3E")}}.hflag.hk{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='%23DE2910'/%3E%3Cpath d='M30 20c7-12 13-4 5 1 10-2 11 7 1 6 7 7-1 12-5 3-2 10-11 7-6-2-10 4-13-5-3-8-1-7 6-10 2-2 8-1 12 2z' fill='white'/%3E%3C/svg%3E")}}.hflag.ca{{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40'%3E%3Crect width='60' height='40' fill='white'/%3E%3Crect width='14' height='40' fill='%23D80621'/%3E%3Crect x='46' width='14' height='40' fill='%23D80621'/%3E%3Cpath d='M30 7l3 7 5-2-3 6 5 2-7 4 1 7h-8l1-7-7-4 5-2-3-6 5 2z' fill='%23D80621'/%3E%3C/svg%3E")}}.meta{{font-size:11px;color:#617b9b;margin-top:4px}}.status.open{{color:#08a66a;font-weight:700}}.status.closed{{color:#ef4444;font-weight:700}}.live{{color:#08a66a;font-weight:700}}.quote{{text-align:right;font:italic 13px Georgia,serif;color:#395a82}}.quote small{{display:block;font:700 10px Arial;color:#0d78e8;margin-top:3px}}.metrics{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}}.metric{{appearance:none;text-align:left;background:#fff;border:1px solid #d8e5f2;border-radius:5px;height:104px;padding:8px 11px;cursor:pointer;transition:border-color .18s ease,box-shadow .18s ease,transform .18s ease}}.metric:hover{{transform:translateY(-1px);border-color:#1687ff}}.metric.selected{{border:2px solid #1687ff;box-shadow:0 0 0 2px rgba(22,135,255,.08)}}.mname{{font-size:14px;font-weight:700}}.mname span{{font-size:13px;color:#6780a2}}.mrow{{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:2px}}.mrow strong{{font-size:23px}}.mrow em{{font-size:11px;font-style:normal;font-weight:700}}.spark{{height:38px;margin-top:3px}}.spark svg{{width:100%;height:100%}}.grid{{display:grid;grid-template-columns:1.48fr .86fr 1.10fr;gap:6px;margin-top:6px}}.panel{{height:336px;border:1px solid #d8e5f2;border-radius:5px;background:#fff;overflow:hidden}}.panel header{{height:36px;padding:7px 9px;font-size:14px;font-weight:700;border-bottom:1px solid #e5edf5;display:flex;align-items:center;gap:8px}}.ranges{{margin-left:auto;display:flex;gap:7px}}.ranges button{{border:0;background:#f2f6fb;color:#17365d;font:700 10px Arial;padding:5px 11px;border-radius:4px;cursor:pointer}}.ranges button.active{{background:#087cf0;color:#fff}}.chart{{height:299px;position:relative;overflow:hidden;opacity:1;transition:opacity .16s ease}}.chart.fade{{opacity:.72}}#svg{{position:absolute;left:12px;right:70px;top:10px;bottom:32px;height:auto;min-height:0}}#svg svg{{display:block;width:100%;height:100%}}.last{{position:absolute;right:10px;top:46%;transform:translateY(-50%);font-size:15px;font-weight:800}}.prev{{position:absolute;right:8px;bottom:auto;transform:translateY(-50%);font-size:10px;color:#35547c}}.prev b{{font-size:11px}}.xaxis{{position:absolute;left:70px;right:72px;bottom:8px;display:flex;justify-content:space-between;color:#27496f;font-size:9px;line-height:12px}}.tabs{{display:grid;grid-template-columns:repeat(4,1fr);margin:6px 8px 4px;background:#f1f6fb;border-radius:5px;overflow:hidden;height:30px}}.tabs button{{appearance:none;border:0;border-right:1px solid #dce7f2;background:transparent;color:#17365d;text-align:center;padding:5px 2px;font:500 11px Arial;cursor:pointer}}.tabs button:last-child{{border-right:0}}.tabs button.active{{background:#087cf0;color:#fff;font-weight:700}}.sectors{{padding:3px 8px 5px}}.srow{{display:grid;grid-template-columns:132px 1fr 52px;height:22px;gap:6px;align-items:center;font-size:10px}}.srow i{{height:10px;background:#edf2f7;border-radius:3px;overflow:hidden}}.srow i b{{display:block;height:100%;border-radius:3px}}.srow i .up{{background:#0aa968}}.srow i .down{{background:#ef4444}}.pos{{color:#0aa968}}.neg{{color:#ef4444}}.asof{{font-size:9px;color:#6a80a0;margin-left:auto}}table{{width:100%;border-collapse:collapse;font-size:10px}}th,td{{padding:4px 6px;height:25px;border-bottom:1px solid #e5edf5;text-align:left}}th{{background:#edf3f9}}@media(max-width:900px){{.metrics{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}.panel{{height:auto;min-height:300px}}}}
    </style><div class="head"><div><div class="title"><span class="hflag {flag_class}" aria-label="{_html.escape(market)} flag"></span><span>Market Overview – {_html.escape(market)}</span></div><div class="meta">{_html.escape(date_label)} · <span id="clock">{_html.escape(time_label)}</span> {_html.escape(zone_label)} | <span class="status {status_cls}">{_html.escape(market_status)}</span> · <span class="live">● Live · Data updated {_html.escape(updated_label)}</span></div></div><div class="quote">“The best investments are built on knowledge, not noise.”<small>— CHRÍMATA</small></div></div><div class="metrics">{''.join(cards)}</div><div class="grid"><section class="panel"><header><span id="ctitle">{_html.escape(_initial_title)}</span><span class="ranges">{''.join(f'<button data-range="{r}" class="{"active" if r=="1D" else ""}">{r}</button>' for r in range_map)}</span></header><div class="chart" id="chart"><div id="svg">{_initial_svg}</div><strong class="last" id="last" style="color:{_initial_col}">{_html.escape(_initial_last)}</strong><div class="prev">Prev Close<br><b id="prev">{_html.escape(_initial_prev)}</b></div><div class="xaxis" id="xaxis">{''.join(f'<span>{x}</span>' for x in _chr_intraday_labels(market))}</div></div></section><section class="panel"><header>{'ASX' if market=='Australia' else _html.escape(market)} Sectors <span class="asof">{_html.escape(panel_asof)}</span></header><div class="tabs"><button type="button" data-sector-period="Day" class="active">Day</button><button type="button" data-sector-period="Week">Week</button><button type="button" data-sector-period="Month">Month</button><button type="button" data-sector-period="YTD">YTD</button></div><div class="sectors" id="sectorRows"></div></section><section class="panel"><header>{'ASX' if market=='Australia' else _html.escape(market)} Indices <span class="asof">{_html.escape(panel_asof)}</span></header>{index_table}</section></div><script>
    const root=document.getElementById('smooth'), data={data}; let key={selected}, range='1D';
    const labels={{'1D':{json.dumps(_chr_intraday_labels(market))},'5D':['Mon','Tue','Wed','Thu','Fri'],'1M':['Week 1','Week 2','Week 3','Week 4'],'3M':['Month 1','Month 2','Month 3'],'1Y':['Sep','Nov','Jan','Mar','May','Jul','Sep'],'5Y':['2022','2023','2024','2025','2026']}};
    function draw(animate=true){{const q=(data[key]||{{}})[range]||Object.values(data[key]||{{}})[0];if(!q)return;const c=root.querySelector('#chart');if(animate)c.classList.add('fade');setTimeout(()=>{{root.querySelector('#ctitle').textContent=q.label+' '+(range==='1D'?'Intraday Chart':range+' Chart');const svgBox=root.querySelector('#svg');svgBox.innerHTML=q.svg;const lastEl=root.querySelector('#last'),prevEl=root.querySelector('.prev');lastEl.textContent=q.last;lastEl.style.color=q.up?'#10b96a':'#ef4444';root.querySelector('#prev').textContent=q.prev;const plotTop=svgBox.offsetTop,plotH=svgBox.clientHeight;if(Number.isFinite(q.lastY))lastEl.style.top=(plotTop+plotH*q.lastY)+'px';if(Number.isFinite(q.prevY))prevEl.style.top=(plotTop+plotH*q.prevY)+'px';root.querySelector('#xaxis').innerHTML=(labels[range]||[]).map(x=>'<span>'+x+'</span>').join('');c.classList.remove('fade');}},animate?120:0)}}
    root.querySelectorAll('.metric').forEach(b=>b.addEventListener('click',()=>{{key=b.dataset.key;root.querySelectorAll('.metric').forEach(x=>x.classList.toggle('selected',x===b));draw(true)}}));root.querySelectorAll('[data-range]').forEach(b=>b.addEventListener('click',()=>{{range=b.dataset.range;root.querySelectorAll('[data-range]').forEach(x=>x.classList.toggle('active',x===b));draw(true)}}));draw(false);
    const sectorData={sector_json}; let sectorPeriod='Day';
    function drawSectors(){{const rows=(sectorData[sectorPeriod]||[]).slice().sort((a,b)=>{{const av=(a.value===null?-Infinity:a.value),bv=(b.value===null?-Infinity:b.value);return bv-av;}});const box=root.querySelector('#sectorRows');if(!rows.length){{box.innerHTML='<div class="sector-empty">Sector data unavailable.</div>';return;}}const valid=rows.filter(r=>r.value!==null && Number.isFinite(r.value));const maxAbs=Math.max(...valid.map(r=>Math.abs(r.value)),.01);box.innerHTML=rows.map(r=>{{if(r.value===null || !Number.isFinite(r.value))return '<div class="srow"><span>'+r.name+'</span><i></i><em style="color:#6a80a0">N/A</em></div>';const up=r.value>=0,w=Math.max(3,Math.abs(r.value)/maxAbs*100);return '<div class="srow"><span>'+r.name+'</span><i><b class="'+(up?'up':'down')+'" style="width:'+w.toFixed(0)+'%"></b></i><em class="'+(up?'pos':'neg')+'">'+(up?'+':'')+r.value.toFixed(2)+'%</em></div>';}}).join('');}}
    root.querySelectorAll('[data-sector-period]').forEach(b=>b.addEventListener('click',()=>{{sectorPeriod=b.dataset.sectorPeriod;root.querySelectorAll('[data-sector-period]').forEach(x=>x.classList.toggle('active',x===b));drawSectors();}}));drawSectors();
    const marketTZ={json.dumps({'Australia':'Australia/Sydney','United States':'America/New_York','United Kingdom':'Europe/London','Japan':'Asia/Tokyo','Hong Kong':'Asia/Hong_Kong','Canada':'America/Toronto'}.get(market,'Australia/Sydney'))};
    function tickClock(){{try{{root.querySelector('#clock').textContent=new Intl.DateTimeFormat('en-AU',{{timeZone:marketTZ,hour:'numeric',minute:'2-digit',second:'2-digit',hour12:true}}).format(new Date());}}catch(e){{}}}}
    tickClock();setInterval(tickClock,1000);
    </script></div>'''
    return comp

def _chr_table(rows, headers, fmts=None):
    fmts=fmts or {}; h=''.join(f'<th>{x}</th>' for x in headers); body=[]
    for r in rows:
        cells=[]
        for key in headers:
            v=r.get(key,'')
            if key in fmts:
                try:v=fmts[key](v)
                except Exception:pass
            cls=''
            try:
                if key in ('Change','% Chg'): cls=' class="pos"' if float(r.get(key,0))>=0 else ' class="neg"'
            except Exception:pass
            cells.append(f'<td{cls}>{v}</td>')
        body.append('<tr>'+''.join(cells)+'</tr>')
    return '<table class="chr-table"><thead><tr>'+h+'</tr></thead><tbody>'+''.join(body)+'</tbody></table>'

def _chr_market_clock(market):
    specs={
      "Australia":("Australia/Sydney", time(10,0), time(16,0), "AEST/AEDT"),
      "United States":("America/New_York", time(9,30), time(16,0), "ET"),
      "United Kingdom":("Europe/London", time(8,0), time(16,30), "UK"),
      "Japan":("Asia/Tokyo", time(9,0), time(15,30), "JST"),
      "Hong Kong":("Asia/Hong_Kong", time(9,30), time(16,0), "HKT"),
      "Canada":("America/Toronto", time(9,30), time(16,0), "ET"),
    }
    tzname,op,cl,abbr=specs.get(market,specs["Australia"]); tz=ZoneInfo(tzname); now=datetime.now(tz)
    wd=now.weekday(); open_dt=datetime.combine(now.date(),op,tzinfo=tz); close_dt=datetime.combine(now.date(),cl,tzinfo=tz)
    is_open=wd<5 and open_dt <= now < close_dt
    if is_open: status=f"Market Open · Closes {close_dt.strftime('%-I:%M %p')}"
    else:
        d=now.date()
        if wd<5 and now < open_dt: nxt=open_dt
        else:
            d=d+timedelta(days=1)
            while d.weekday()>=5: d+=timedelta(days=1)
            nxt=datetime.combine(d,op,tzinfo=tz)
        status=f"Market Closed · Opens {nxt.strftime('%a %-I:%M %p')}"
    zone=now.tzname() or abbr
    return now.strftime('%A, %d %B %Y'), now.strftime('%-I:%M:%S %p'), zone, status, is_open


# V20.3.0 — transformed landing canvas must retain its full scrollable height.
st.markdown(r"""
<style>
/* V20.3.0 — live clock + 60-second provider refresh status */
.chr-live-updated{color:#0aa968;font-weight:700;font-size:11px;white-space:nowrap;}
.chr-metric-link{display:block;color:inherit!important;text-decoration:none!important;min-width:0;}
.chr-metric-link .chr-metric{cursor:pointer;transition:border-color .15s ease,box-shadow .15s ease,transform .15s ease;}
.chr-metric-link:hover .chr-metric{border-color:#1687ff;box-shadow:0 2px 8px rgba(22,135,255,.14);transform:translateY(-1px);}
.chr-metric.selected{border:2px solid #1687ff!important;box-shadow:0 0 0 2px rgba(22,135,255,.08);}
.chr-range-links{display:flex;gap:12px;align-items:center;}
.chr-range-links a{color:#5d7594!important;text-decoration:none!important;font-size:10px;font-weight:700;padding:2px 3px;border-radius:3px;}
.chr-range-links a.active{color:#0874df!important;background:#eaf4ff;}

[data-testid="stMainBlockContainer"], .stMainBlockContainer,
section[data-testid="stMain"] .block-container, .main .block-container{
  min-height:calc(100% + 120px)!important;
  padding-bottom:132px!important;
}
/* V20.3.6 reference-match market section */
.chr-metrics{gap:7px!important}.chr-metric{height:122px!important;padding:10px 12px!important}.chr-metric-name{font-size:15px!important}.chr-metric-row strong{font-size:25px!important}.chr-spark{height:48px!important;margin-top:6px!important}
.chr-grid-main{grid-template-columns:1.48fr .86fr 1.10fr!important;gap:7px!important}.chr-panel{border-color:#d5e3f1!important;border-radius:7px!important}.chr-panel>header{height:40px!important;padding:9px 10px!important;font-size:15px!important}.chr-chart-panel{min-height:345px!important}.chr-bigchart{height:302px!important;padding:18px 72px 28px 18px!important}.chr-bigchart>strong{right:12px!important;top:47%!important;font-size:16px!important}.chr-prev-close{position:absolute;right:9px;bottom:46px;font-size:11px;line-height:1.15;color:#35547c}.chr-prev-close b{font-size:12px}.chr-range-links{gap:8px!important}.chr-range-links a{font-size:11px!important;padding:7px 12px!important;background:#f2f6fb;border-radius:5px!important;color:#17365d!important}.chr-range-links a.active{background:#087cf0!important;color:#fff!important}.chr-sectors{padding:7px 9px!important}.chr-sector-row{grid-template-columns:145px 1fr 58px!important;height:24px!important;font-size:11px!important}.chr-table{font-size:11px!important}.chr-table th,.chr-table td{padding:5px 7px!important}
/* V20.4.2 — live market intelligence widgets + stable client-side market section. */
.chr-home-v2020>.chr-overview-head,.chr-home-v2020>.chr-metrics,.chr-home-v2020>.chr-grid-main{display:none!important;}
/* V20.3.6 — pixel-density pass based on the approved market-section reference. */
.chr-home-v2020{font-family:Arial,Helvetica,sans-serif!important}
.chr-metrics{gap:6px!important}
.chr-metric{height:104px!important;padding:8px 11px!important;border-radius:5px!important}
.chr-metric-name{font-size:14px!important;line-height:18px!important}.chr-metric-name span{font-size:13px!important;color:#6780a2!important}
.chr-metric-row{margin-top:2px!important;gap:10px!important}.chr-metric-row strong{font-size:23px!important}.chr-metric-row em{font-size:11px!important}
.chr-spark{height:38px!important;margin-top:3px!important}
.chr-grid-main{grid-template-columns:1.48fr .86fr 1.10fr!important;gap:6px!important;margin-top:6px!important;align-items:stretch!important}
.chr-grid-main>.chr-panel{height:336px!important;min-height:336px!important}
.chr-panel{border-radius:5px!important;border:1px solid #d8e5f2!important;box-shadow:0 1px 2px rgba(20,50,80,.025)!important}
.chr-panel>header{height:36px!important;padding:7px 9px!important;font-size:14px!important;line-height:21px!important}
.chr-chart-panel{min-height:336px!important}.chr-bigchart{height:299px!important;padding:15px 72px 28px 18px!important;background:#fff!important}
.chr-bigchart>strong{right:10px!important;top:48%!important;font-size:15px!important}.chr-prev-close{right:8px!important;bottom:43px!important;font-size:10px!important}.chr-prev-close b{font-size:11px!important}
.chr-range-links{gap:7px!important}.chr-range-links a{font-size:10px!important;padding:5px 11px!important;background:#f2f6fb!important;border-radius:4px!important}.chr-range-links a.active{background:#087cf0!important;color:white!important}
.chr-sectors{padding:4px 8px!important}.chr-sector-row{grid-template-columns:132px 1fr 52px!important;height:22px!important;font-size:10px!important;gap:6px!important}.chr-sector-row i{height:10px!important}
.chr-table{font-size:10px!important}.chr-table th,.chr-table td{padding:4px 6px!important;height:25px!important}.chr-table th{background:#edf3f9!important}
.chr-panel-asof{font-size:9px!important;font-weight:600!important;color:#6a80a0!important;margin-left:auto!important}
.chr-sector-tabs{display:flex;gap:0;margin:-4px 8px 4px;border-radius:4px;overflow:hidden;background:#f1f6fb}.chr-sector-tabs span{flex:1;text-align:center;padding:4px 2px;font-size:9px;color:#17365d;border-right:1px solid #dce7f2}.chr-sector-tabs span:last-child{border-right:0}.chr-sector-tabs .active{background:#087cf0;color:#fff}
.chr-chart-axis{position:absolute;left:18px;right:72px;bottom:8px;display:flex;justify-content:space-between;color:#27496f;font-size:9px;pointer-events:none}

/* V20.5.6 — inline autocomplete search + interactive bottom intelligence widgets */
.chr-grid-bottom>.chr-panel{min-height:290px!important}
.chr-cal-tabs,.chr-global-tabs{padding:8px 9px}
.chr-cal-tabs>input,.chr-global-tabs>input{position:absolute;opacity:0;pointer-events:none}
.chr-cal-tabs>label,.chr-global-tabs>label,.gm-btn{display:inline-block;padding:5px 11px;margin:0 3px 7px 0;border:1px solid #d8e5f2;border-radius:5px;background:#f1f6fb;color:#17365d;font-size:10px;font-weight:700;cursor:pointer}
#cal-earn:checked+label,#cal-ipo:checked+label,.gm-btn.active{background:#087cf0!important;color:#fff!important;border-color:#087cf0!important}.gm-btn{cursor:pointer}
.cal-earn-panel,.cal-ipo-panel,.gm-panel{display:none;margin:0 -9px}
#cal-earn:checked~.cal-earn-panel,#cal-ipo:checked~.cal-ipo-panel{display:block}
#gm-0:checked~.gm-0-panel,#gm-1:checked~.gm-1-panel,#gm-2:checked~.gm-2-panel,#gm-3:checked~.gm-3-panel,#gm-4:checked~.gm-4-panel{display:block}

/* V20.5.6 — inline autocomplete search (no selectbox). */
.chr-autocomplete-label{font-size:10px;font-weight:700;color:#6a80a0;margin:2px 0 3px 2px;text-transform:uppercase;letter-spacing:.04em}
div[data-testid="stFragment"] div[data-testid="stButton"] button[kind="secondary"]{min-height:30px!important;height:auto!important;padding:5px 10px!important;border:1px solid #d8e5f2!important;border-radius:4px!important;background:#fff!important;color:#17365d!important;text-align:left!important;justify-content:flex-start!important;font-size:11px!important;font-weight:500!important;margin:0 0 2px!important}
div[data-testid="stFragment"] div[data-testid="stButton"] button[kind="secondary"]:hover{background:#eef6ff!important;border-color:#087cf0!important;color:#087cf0!important}

/* Prevent the final dashboard row from disappearing behind the viewport/taskbar. */
.chr-home-v2020{padding-bottom:28px!important;margin-bottom:24px!important;}
</style>
""",unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def _professional_security_suggestions(term):
    """Return compact global security labels for the autocomplete component."""
    term=(term or "").strip()
    if len(term)<1:
        return []
    try:
        matches=search_securities(term,_search_key)
    except Exception:
        return []
    if matches is None or matches.empty:
        return []
    labels=[]
    mapping={}
    for _,r in matches.head(8).iterrows():
        sym=str(r.get("Symbol","") or "").strip()
        company=str(r.get("Company","") or "").strip()
        exchange=str(r.get("Exchange","") or "").strip()
        country=str(r.get("Country","") or "Global").strip()
        label=" · ".join(x for x in [sym,company,exchange,country] if x)
        if label and label not in mapping:
            mapping[label]=(sym,exchange,country)
            labels.append(label)
    # Mapping is reconstructed on selection too; keeping only labels makes this cache safe.
    return labels

def _resolve_professional_search_label(label):
    parts=[x.strip() for x in str(label or "").split(" · ")]
    sym=parts[0] if parts else ""
    exchange=parts[-2] if len(parts)>=3 else ""
    country=parts[-1] if len(parts)>=2 else ""
    return resolve_listing(sym,exchange,country) if sym else ""

def _home_live_search_fragment():
    """V20.5.0 professional autocomplete. Suggestions live inside the search control.

    streamlit-searchbox handles keystrokes inside its component, so typing does not
    create a stack of Streamlit buttons or push the market dashboard down the page.
    Only selecting a security commits active-company state.
    """
    try:
        from streamlit_searchbox import st_searchbox
    except Exception:
        st.info("Search component is loading. Refresh once after deployment finishes installing dependencies.")
        return

    selected=st_searchbox(
        _professional_security_suggestions,
        key="chrimata_professional_global_search_v2050",
        placeholder="Search any company, ETF or index (e.g. ZIP, QAN, AAPL, BHP) ...",
        label="",
        clear_on_submit=True,
        rerun_on_update=False,
        # V20.7.4.17.2 — Home Search Border Continuity Fix. Keep the exact
        # V20.7.4.17.1 geometry, but paint the outline INSIDE the visible control.
        # This prevents the component frame from clipping the bottom edge. Scoped
        # only to this Home-page searchbox; country buttons and other inputs remain unchanged.
        style_overrides={
            "searchbox": {
                "control": {
                    "height": "44px",
                    "minHeight": "44px",
                    "backgroundColor": "#ffffff",
                    "border": "0",
                    "borderRadius": "5px",
                    "boxSizing": "border-box",
                    "boxShadow": "inset 0 0 0 1px #d7e2ef",
                },
                "placeholder": {
                    "color": "#66778f",
                },
                "input": {
                    "color": "#10264b",
                },
                "singleValue": {
                    "color": "#10264b",
                },
            }
        },
    )
    if selected:
        resolved=_resolve_professional_search_label(selected)
        if resolved and resolved != st.session_state.get("chr_last_search_commit_v2054"):
            # Search text/suggestions are deliberately separate from the loaded company.
            st.session_state["mia_search_query"]=resolved
            st.session_state["chr_active_ticker"]=resolved
            st.session_state["chr_primary_nav"]="Company Command Centre"
            # Consume each autocomplete selection once; URL state is not used.
            st.session_state["chr_last_search_commit_v2054"]=resolved
            st.rerun()

@st.fragment(run_every="60s")
def render_global_market_overview():
    if "home_market_v2021" not in st.session_state: st.session_state.home_market_v2021="Australia"
    # V20.3.0: query-param navigation uses plain HTML anchors instead of Streamlit
    # buttons. This guarantees the reference white-card appearance and real flags.
    try:
        qp_market=st.query_params.get("market")
        if qp_market in MARKET_OVERVIEW_CONFIG:
            st.session_state.home_market_v2021=qp_market
    except Exception:
        pass
    search_col,market_col=st.columns([1.72,2.28],gap="small")
    with search_col:
        _home_live_search_fragment()
    with market_col:
        names=list(MARKET_OVERVIEW_CONFIG.keys())
        # V20.3.0: native Streamlit buttons keep navigation in the SAME app/tab.
        # Actual flag artwork is injected by CSS below (not Windows emoji), so flags
        # render consistently on Windows/Chrome.
        with st.container(key="country_nav_v2027"):
            nav_cols=st.columns(6,gap="small")
            for i,m in enumerate(names):
                with nav_cols[i]:
                    if st.button(m, key=f"country_v2027_{i}", use_container_width=True,
                                 type="primary" if st.session_state.home_market_v2021==m else "secondary"):
                        st.session_state.home_market_v2021=m
                        try:
                            st.query_params["market"]=m
                        except Exception:
                            pass
                        st.rerun()
    market=st.session_state.home_market_v2021; cfg=MARKET_OVERVIEW_CONFIG[market]
    idx=[]
    for label,t in cfg['indices'].items(): idx.append((label,t,overview_quote(t,'5d')))
    cq=overview_quote(cfg.get('currency'),'5d') if cfg.get('currency') else None; gq=overview_quote('GC=F','5d'); date_label, time_label, zone_label, market_status, market_is_open=_chr_market_clock(market)

    # V20.3.1 — top metric cards drive the large chart below. Query parameters make
    # the interaction reliable in Streamlit without opening a modal or a new tab.
    # V20.3.6 — keep the headline strip intentionally limited to five cards.
    # The broader index universe remains available in the Indices panel below.
    if market == 'Australia':
        primary_index_names = ['S&P/ASX 200', 'All Ordinaries', 'All Technology']
        idx_by_name = {a:(a,b,q,None) for a,b,q in idx}
        instruments = [idx_by_name[n] for n in primary_index_names if n in idx_by_name]
    else:
        # For other countries use the first three configured headline indices.
        instruments = [(a,b,q,None) for a,b,q in idx[:3]]
    if cfg.get('currency'):
        instruments.append(('AUD/USD' if market=='Australia' else cfg.get('currency','FX'),cfg.get('currency',''),cq,'#1687ff'))
    instruments.append(('Gold (USD)','GC=F',gq,'#f5b400'))
    valid_keys=[t for _,t,_,_ in instruments if t]
    try: selected_key=st.query_params.get('chart')
    except Exception: selected_key=None
    if selected_key not in valid_keys: selected_key=valid_keys[0]
    try: selected_range=st.query_params.get('range','1D').upper()
    except Exception: selected_range='1D'
    range_map={'1D':('1d','1m'),'5D':('5d','15m'),'1M':('1mo','60m'),'3M':('3mo','1d'),'1Y':('1y','1d'),'5Y':('5y','1wk')}
    if selected_range not in range_map: selected_range='1D'
    selected_label,selected_t,selected_base,_=next((x for x in instruments if x[1]==selected_key),instruments[0])
    cards=''.join(_chr_metric_card(a,b,q,accent,chart_key=b,selected=(b==selected_key),market=market) for a,b,q,accent in instruments)
    chart_period,chart_interval=range_map[selected_range]
    chart_q=overview_quote(selected_t,chart_period,chart_interval) or selected_base
    chart_up=float((chart_q or {}).get('change',0) or 0)>=0
    chart_col='#10b96a' if chart_up else '#ef4444'
    chart_fill='#e7f8ef' if chart_up else '#fff0f0'
    chart_svg=_chr_big_market_svg(chart_q['series'] if chart_q else [], (chart_q or {}).get('prev'),760,230,chart_col,chart_fill)
    last_txt=f"{chart_q['last']:,.2f}" if chart_q else '—'
    prev_txt=f"{chart_q.get('prev'):,.2f}" if chart_q and np.isfinite(_mia_num(chart_q.get('prev'))) else '—'
    from urllib.parse import quote
    range_links=''.join(f'<a class="{"active" if r==selected_range else ""}" href="?market={quote(str(market))}&chart={quote(str(selected_key))}&range={r}" target="_self">{r}</a>' for r in range_map)
    chart_title=f'{selected_label} {"Intraday Chart" if selected_range=="1D" else selected_range+" Chart"}'
    xlabels = ['10:00','11:00','12:00','13:00','14:00','15:00','16:00'] if selected_range=='1D' else ({'5D':['Mon','Tue','Wed','Thu','Fri'],'1M':['Week 1','Week 2','Week 3','Week 4'],'3M':['Month 1','Month 2','Month 3'],'1Y':['Sep','Nov','Jan','Mar','May','Jul','Sep'],'5Y':['2022','2023','2024','2025','2026']}[selected_range])
    xaxis_html='<div class="chr-chart-axis">'+''.join(f'<span>{x}</span>' for x in xlabels)+'</div>' 
    main_q=idx[0][2]
    intraday_q=chart_q
    # V20.4.0 sector performance: official S&P/ASX sector indices first, then ASX fallbacks.
    # Provider gaps fall back to ASX proxies/representative baskets before N/A.
    sector_names=list(cfg.get('sectors',{}).keys())
    sector_values={p:{name:None for name in sector_names} for p in ('Day','Week','Month','YTD')}
    for label,sources in cfg.get('sectors',{}).items():
        # Day = latest trading-session move. Official S&P/ASX sector index first.
        first_source = sources[0] if isinstance(sources,(list,tuple)) and sources else sources
        qday=overview_quote(first_source,'5d') if isinstance(first_source,str) else None
        if qday and np.isfinite(_mia_num(qday.get('pct'))):
            sector_values['Day'][label]=float(qday['pct'])*100
        else:
            # A 2-day history gives the closest price-return fallback for a basket/proxy.
            d=overview_sector_performance(sources,'5d')
            if d: sector_values['Day'][label]=d['return']
        for pname,period in (('Week','5d'),('Month','1mo'),('YTD','ytd')):
            d=overview_sector_performance(sources,period)
            if d: sector_values[pname][label]=d['return']
    sectors={p:[(name,sector_values[p][name]) for name in sector_names] for p in ('Day','Week','Month','YTD')}
    sector_html=''
    # V20.4.1 — ASX Indices terminal table. Always preserve the complete nine-row
    # reference layout. Yahoo/provider symbols differ from the ASX display codes for
    # several capitalisation indices (AFLI/ATOI/ATLI), so present canonical ASX codes.
    index_rows=[]
    asx_display_codes={
        'S&P/ASX 200':'XJO','All Ordinaries':'XAO','ASX 50':'XFL','ASX 100':'XTO',
        'ASX 300':'XKO','ASX 20':'XTL','All Technology':'XTX',
        'ASX 200 Resources':'XJR','All Ords Gold (sub)':'XGD'
    }
    for label,t,q in idx:
        code=asx_display_codes.get(label,t.replace('^','')) if market=='Australia' else t.replace('^','')
        index_rows.append({
            'Code':code,'Name':label,
            'Last':q['last'] if q else '—',
            'Change':q['change'] if q else '—',
            '% Chg':q['pct'] if q else '—'
        })
    index_table=_chr_table(index_rows,['Code','Name','Last','Change','% Chg'],{
        'Last':lambda x:f'{x:,.2f}' if isinstance(x,(int,float,np.integer,np.floating)) else str(x),
        'Change':lambda x:f'{x:+,.2f}' if isinstance(x,(int,float,np.integer,np.floating)) else str(x),
        '% Chg':lambda x:f'{x:+.2%}' if isinstance(x,(int,float,np.integer,np.floating)) else str(x)
    })
    # V20.4.2 — genuine movers: gainers are positive-only and fallers negative-only.
    # Never pad a list with securities moving in the wrong direction.
    # V20.6.9: Top Gainers uses its own broader country universe. This is
    # deliberately isolated so no other dashboard widget changes data inputs.
    gainers_movers=overview_batch(tuple(TOP_GAINERS_UNIVERSE.get(market,cfg['universe'])))
    movers=overview_batch(tuple(cfg['universe'])); gain=[]; fall=[]
    if gainers_movers is not None and not gainers_movers.empty:
        clean=gainers_movers.copy()
        clean['% Chg']=pd.to_numeric(clean['% Chg'],errors='coerce')
        clean=clean.dropna(subset=['% Chg'])
        def _clean_company_name(name,ticker):
            nm=str(name or ticker).strip()
            # Provider names sometimes echo the exchange ticker rather than a company name.
            if nm.upper() in {str(ticker).upper(),str(ticker).split('.')[0].upper()}:
                return str(ticker).split('.')[0]
            for suffix in (' FPO',' CDI 1:1'):
                nm=nm.replace(suffix,'')
            return nm[:28]
        for _,r in clean[clean['% Chg']>0].sort_values('% Chg',ascending=False).head(5).iterrows():
            gain.append({'Code':r['Ticker'].split('.')[0],'Company':_clean_company_name(r['Company'],r['Ticker']),'Last':r['Last'],'% Chg':r['% Chg']})
    # Preserve the pre-V20.6.9 Biggest Fallers input universe unchanged.
    if movers is not None and not movers.empty:
        fall_clean=movers.copy()
        fall_clean['% Chg']=pd.to_numeric(fall_clean['% Chg'],errors='coerce')
        fall_clean=fall_clean.dropna(subset=['% Chg'])
        for _,r in fall_clean[fall_clean['% Chg']<0].sort_values('% Chg',ascending=True).head(5).iterrows():
            fall.append({'Code':r['Ticker'].split('.')[0],'Company':_clean_company_name(r['Company'],r['Ticker']),'Last':r['Last'],'% Chg':r['% Chg']})
    smallfmt={'Last':lambda x:f'${x:,.2f}','% Chg':lambda x:f'{x:+.2%}'}
    gain_t=_chr_table(gain,['Code','Company','Last','% Chg'],smallfmt) if gain else '<div class="chr-empty">No qualifying gainers returned by the active provider.</div>'
    fall_t=_chr_table(fall,['Code','Company','Last','% Chg'],smallfmt) if fall else '<div class="chr-empty">No qualifying fallers returned by the active provider.</div>'
    try: wl=watch_get()
    except Exception: wl=[]
    wt=[]
    if isinstance(wl,pd.DataFrame):
        for c in ['ticker','Ticker','symbol','Symbol']:
            if c in wl.columns: wt=wl[c].astype(str).tolist();break
    elif isinstance(wl,(list,tuple)): wt=[str(x) for x in wl]
    # V20.4.2 — the dashboard reads the same persistent watchlist database as the full Watchlist page.
    # Resolve bare symbols to the selected market before requesting quotes.
    resolved_wt=[]
    for sym in wt[:6]:
        raw=str(sym).strip().upper()
        if not raw: continue
        if any(raw.endswith(x) for x in ('.AX','.L','.HK','.T','.TO')) or raw.startswith('^') or '=' in raw:
            resolved_wt.append(raw)
        else:
            market_code={'Australia':'ASX','United Kingdom':'LSE','Hong Kong':'HKEX','Japan':'TSE','Canada':'TSX'}.get(market,'US')
            resolved_wt.append(global_yahoo_symbol(raw,market_code))
    wdf=overview_batch(tuple(resolved_wt)) if resolved_wt else pd.DataFrame(); wrows=[]
    if wdf is not None and not wdf.empty:
        for _,r in wdf.head(6).iterrows():wrows.append({'Code':r['Ticker'].split('.')[0],'Last':r['Last'],'% Chg':r['% Chg']})
    watch_t=_chr_table(wrows,['Code','Last','% Chg'],smallfmt) if wrows else ('<div class="chr-empty">Your saved watchlist is empty.</div>' if not wt else '<div class="chr-empty">Watchlist saved; live quotes are temporarily unavailable.</div>')
    # V20.7.0 — country-aware volatility widget. This code path is intentionally
    # isolated: it reads only VOLATILITY_INDEX_CONFIG and overview_quote().
    vol_cfg=VOLATILITY_INDEX_CONFIG.get(market,{})
    vv=None; vol_symbol=None
    for _vsym in vol_cfg.get('symbols',[]):
        try:
            _vq=overview_quote(_vsym,'5d')
            _vlast=_mia_num(_vq.get('last')) if _vq else np.nan
            if np.isfinite(_vlast) and float(_vlast)>0:
                vv=float(_vlast); vol_symbol=_vsym; break
        except Exception:
            continue
    needle=(-80 if vv is None else max(-80,min(80,(min(vv,50.0)/50.0*160)-80)))
    vix_text='—' if vv is None else f'{vv:.1f}'
    # V20.7.0 enhanced: simple, market-independent presentation bands.
    # These affect only this widget's display text/colour; the underlying index value is untouched.
    if vv is None:
        vol_state='Unavailable'; vol_state_class='unavailable'
    elif vv < 15:
        vol_state='Low'; vol_state_class='low'
    elif vv <= 30:
        vol_state='Normal'; vol_state_class='normal'
    else:
        vol_state='High'; vol_state_class='high'
    vol_name=vol_cfg.get('name','Volatility Index')
    vol_source=vol_cfg.get('source',market)
    vol_note=vol_cfg.get('note','Market volatility benchmark.')
    if vv is None:
        vol_note=f"{vol_note} Current provider data unavailable — no US VIX substitution is used."
    earnings,_legacy_dividends=overview_calendar(tuple(cfg['universe'])); divrows=[]
    # V20.5.9: Global Corporate Actions Calendar. Use a real forward calendar provider
    # first (Twelve Data; optional FMP), with Yahoo declared events only as fallback.
    try: _td_div_key=st.secrets.get('TWELVE_DATA_API_KEY','')
    except Exception: _td_div_key=''
    try: _fmp_div_key=st.secrets.get('FMP_API_KEY','')
    except Exception: _fmp_div_key=''
    dividends=overview_global_dividends(market, tuple(cfg['universe']), _td_div_key, _fmp_div_key)
    if dividends is not None and not dividends.empty:
        for _,r in dividends.head(8).iterrows():
            amt=r.get('Amount','—'); amt='—' if pd.isna(amt) else f'{float(amt):.4g}'
            divrows.append({'Code':str(r.get('Ticker','')).split('.')[0],'Company':str(r.get('Company',''))[:23],'Ex-Date':r.get('Ex-Date',''),'Pay-Date':r.get('Pay-Date','—'),'Amount':amt})
    div_t=_chr_table(divrows,['Code','Company','Ex-Date','Pay-Date','Amount']) if divrows else '<div class="chr-empty">No confirmed upcoming dividends were returned by the configured calendar providers for this market. Chrímata does not estimate undeclared future dividends.</div>'
    earnrows=[]
    if earnings is not None and not earnings.empty:
        for _,r in earnings.head(5).iterrows(): earnrows.append({'Code':str(r.get('Ticker','')).split('.')[0],'Company':str(r.get('Company',''))[:25],'Date':r.get('Date','')})
    earnings_table=_chr_table(earnrows,['Code','Company','Date']) if earnrows else '<div class="chr-empty">No upcoming earnings dates were returned by the active provider.</div>'
    earn_t='<div class="chr-cal-tabs"><input checked type="radio" name="calmode" id="cal-earn"><label for="cal-earn">Earnings</label><input type="radio" name="calmode" id="cal-ipo"><label for="cal-ipo">IPOs</label><div class="cal-earn-panel">'+earnings_table+'</div><div class="cal-ipo-panel"><div class="chr-empty">IPO calendar feed is not available from the configured market-data provider.</div></div></div>'
    global_groups={
      'US':[('S&P 500','^GSPC'),('Nasdaq 100','^NDX'),('Dow Jones','^DJI')],
      'UK':[('FTSE 100','^FTSE'),('FTSE 250','^FTMC'),('FTSE All-Share','^FTAS')],
      'Japan':[('Nikkei 225','^N225'),('TOPIX','^TOPX'),('JPX-Nikkei 400','^JPXNK400')],
      'HK':[('Hang Seng','^HSI'),('Hang Seng China Ent.','^HSCE'),('Hang Seng Tech','^HSTECH')],
      'Canada':[('TSX Composite','^GSPTSE'),('TSX 60','^TX60'),('TSX Venture','^SPCDNX')]
    }
    gp=[]
    for gi,(gname,items) in enumerate(global_groups.items()):
        rows=[]
        for label,t in items:
            q=overview_quote(t,'5d')
            if q: rows.append({'Name':label,'Last':q['last'],'Change':q['change'],'% Chg':q['pct']})
        tbl=_chr_table(rows,['Name','Last','Change','% Chg'],{'Last':lambda x:f'{x:,.2f}','Change':lambda x:f'{x:+,.2f}','% Chg':lambda x:f'{x:+.2%}'}) if rows else '<div class="chr-empty">Market data temporarily unavailable.</div>'
        gp.append((gname,tbl))
    # V20.7.1 — Interactive Global Markets Widget.
    # CSS-only tabs avoid script execution inside st.markdown and remain fully local
    # to this card: no Streamlit session state, routing or main market state is changed.
    gm_uid='chr-gm-tabs'
    gm_inputs=[]; gm_labels=[]; gm_panels=[]
    for i,(gname,tbl) in enumerate(gp):
        checked=' checked' if i==0 else ''
        gm_inputs.append(f'<input class="gm-radio" type="radio" name="{gm_uid}" id="{gm_uid}-{i}"{checked}>')
        gm_labels.append(f'<label class="gm-tab-label gm-label-{i}" for="{gm_uid}-{i}">{gname}</label>')
        gm_panels.append(f'<div class="gm-panel gm-panel-{i}">{tbl}</div>')
    gm_rules=''.join(
        f'#{gm_uid}-{i}:checked ~ .gm-labels .gm-label-{i}{{background:#eef5ff;color:#0b57d0;border-color:#b9d3ff;font-weight:700;}}'
        f'#{gm_uid}-{i}:checked ~ .gm-panels .gm-panel-{i}{{display:block;}}'
        for i in range(len(gp))
    )
    glob_t=(
        '<div class="chr-global-tabs gm-css-tabs"><style>'
        '.gm-css-tabs .gm-radio{position:absolute;opacity:0;pointer-events:none;}'
        '.gm-css-tabs .gm-labels{display:flex;gap:5px;flex-wrap:wrap;margin:0 0 8px;}'
        '.gm-css-tabs .gm-tab-label{cursor:pointer;padding:4px 9px;border:1px solid #d7e0ea;border-radius:5px;background:#fff;color:#43566d;font-size:10px;line-height:1.2;user-select:none;}'
        '.gm-css-tabs .gm-tab-label:hover{background:#f5f8fc;color:#0b57d0;}'
        '.gm-css-tabs .gm-panel{display:none;}'
        +gm_rules+'</style>'+''.join(gm_inputs)+
        '<div class="gm-labels">'+''.join(gm_labels)+'</div>'
        '<div class="gm-panels">'+''.join(gm_panels)+'</div></div>'
    )
    flag_class={'Australia':'au','United States':'us','United Kingdom':'gb','Japan':'jp','Hong Kong':'hk','Canada':'ca'}.get(market,'au')
    # V20.4.0: no timed Streamlit fragment rerun. The market clock updates client-side so the page remains stationary.
    # Show the latest market-data timestamp separately so users can distinguish the live clock from quote freshness.
    try:
        data_asof = pd.to_datetime((intraday_q or main_q or {}).get('asof'), utc=True).tz_convert(ZoneInfo({'Australia':'Australia/Sydney','United States':'America/New_York','United Kingdom':'Europe/London','Japan':'Asia/Tokyo','Hong Kong':'Asia/Hong_Kong','Canada':'America/Toronto'}.get(market,'Australia/Sydney')))
        updated_label = data_asof.strftime('%-I:%M:%S %p %Z')
    except Exception:
        updated_label = time_label + ' ' + zone_label
    try:
        panel_asof = "At Close " + data_asof.strftime("%d/%m (%Z)") if not market_is_open else "Live · " + data_asof.strftime("%-I:%M %p %Z")
    except Exception:
        panel_asof = "Live" if market_is_open else "At Close"
    smooth_html=_chr_smooth_market_component(market,instruments,selected_key,range_map,sectors,index_table,date_label,time_label,zone_label,market_status,market_is_open,updated_label,panel_asof)
    components.html(smooth_html,height=496,scrolling=False)
    html=f'''<div class="chr-home-v2020"><div class="chr-overview-head"><div><div class="chr-overview-title"><span class="chr-overview-flag flag-{flag_class}" aria-label="{market} flag"></span><span>Market Overview – {market}</span></div><div class="chr-overview-meta">{date_label} &nbsp; · &nbsp; {time_label} {zone_label} &nbsp; | &nbsp; <span class="chr-market-status {'open' if market_is_open else 'closed'}">{market_status}</span> &nbsp; · &nbsp; <span class="chr-live-updated">● Live · Data updated {updated_label}</span></div></div><div class="chr-overview-quote">“The best investments are built on knowledge, not noise.”<small>— CHRÍMATA</small></div></div><div class="chr-metrics">{cards}</div><div class="chr-grid-main"><section class="chr-panel chr-chart-panel"><header>{chart_title} <span class="chr-range-links">{range_links}</span></header><div class="chr-bigchart">{chart_svg}{xaxis_html}<strong style="color:{chart_col}">{last_txt}</strong><div class="chr-prev-close">Prev Close<br><b>{prev_txt}</b></div></div></section><section class="chr-panel"><header>{"ASX" if market=="Australia" else market} Sectors <span class="chr-panel-asof">{panel_asof}</span></header><div class="chr-sector-tabs"><span class="active">Day</span><span>Week</span><span>Month</span><span>YTD</span></div><div class="chr-sectors">{sector_html}</div></section><section class="chr-panel"><header>{"ASX" if market=="Australia" else market} Indices <span class="chr-panel-asof">{panel_asof}</span></header>{index_table}</section></div><div class="chr-grid-mid"><section class="chr-panel"><header>Top Gainers ({market})</header>{gain_t}<footer>View more gainers →</footer></section><section class="chr-panel"><header>Biggest Fallers ({market})</header>{fall_t}<footer>View more fallers →</footer></section><section class="chr-panel"><header>Watchlist <span>My Watchlist</span></header>{watch_t}<footer>Go to Watchlist →</footer></section><section class="chr-panel"><header>{vol_name} <span>{vol_source}</span></header><div class="chr-gauge"><div class="arc"><div class="needle" style="transform:rotate({needle:.0f}deg)"></div><b>{vix_text}</b></div><div class="vol-state {vol_state_class}">{vol_state}</div><div class="gleg"><span class="low">■ Low &lt;15</span><span class="normal">■ Normal 15–30</span><span class="high">■ High &gt;30</span></div></div><p class="chr-note">{vol_note}</p></section></div><div class="chr-grid-bottom"><section class="chr-panel"><header>Upcoming Dividends ({market})</header>{div_t}<footer>View all dividends →</footer></section><section class="chr-panel"><header>Upcoming IPOs / Earnings ({market})</header>{earn_t}<footer>View calendar →</footer></section><section class="chr-panel"><header>Global Markets <span>Live market indices</span></header>{glob_t}<footer>View more global markets →</footer></section></div></div>'''
    st.markdown(html,unsafe_allow_html=True)

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

def _chr_search_exchange_bucket(symbol, exchange, country):
    sym=str(symbol or "").upper(); ex=str(exchange or "").upper(); country=str(country or "")
    if sym.endswith(".AX") or "ASX" in ex: return "ASX"
    if sym.endswith(".L") or "LONDON" in ex or ex=="LSE": return "LSE"
    if sym.endswith(".T") or "TOKYO" in ex or ex in {"TSE","JPX"}: return "TSE"
    if sym.endswith(".HK") or "HONG KONG" in ex or ex in {"HKG","HKEX"}: return "HKEX"
    if sym.endswith(".TO") or "TORONTO" in ex or ex=="TSX": return "TSX"
    if "NASDAQ" in ex or ex in {"NMS","NGM","NCM"}: return "NASDAQ"
    if "NYSE" in ex or ex in {"NYQ","ASE","AMEX"}: return "NYSE"
    if country=="United States": return "US Other"
    return ex or "Other"

def _chr_company_search_page():
    """V20.7.4.7 — exact reference search row + pixel-matched results."""
    st.markdown("""
    <style>
    .v2073-rule{border-top:0!important;margin-top:0!important;padding-top:0!important}
    .v2073-head{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}
    .v2073-title{font-size:30px;font-weight:850;color:#10264b;letter-spacing:-.035em;line-height:1.05}
    .v2073-sub{font-size:14px;color:#65778d;margin-top:5px}.v2073-quote{font-size:14px;font-style:italic;font-weight:650;color:#687b92;padding-top:8px}
    .v2073-hint{font-size:10px;color:#71839a;margin:10px 0 14px 2px}.v2073-label{font-size:10px;font-weight:800;color:#40546d;letter-spacing:.04em;text-transform:uppercase;margin:5px 0 4px}
    .v2073-card{background:#fff;border:1px solid #dbe5f0;border-radius:7px;padding:11px 13px;height:100%;box-shadow:0 1px 2px rgba(15,23,42,.025)}
    .v2073-kicker{font-size:9px;font-weight:850;color:#1d66b2;letter-spacing:.08em;text-transform:uppercase}.v2073-name{font-size:17px;font-weight:850;color:#10264b;margin:2px 0}.v2073-meta{font-size:10px;color:#6d7f95;margin-bottom:7px}
    .v2073-price{font-size:25px;font-weight:850;color:#10264b}.v2073-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 12px;margin-top:7px}.v2073-stat{display:flex;justify-content:space-between;border-top:1px solid #edf1f6;padding:5px 0;font-size:10px}.v2073-stat span{color:#708197}.v2073-stat b{color:#172b4d}
    .v2073-empty{background:#fff;border:1px dashed #cbd8e7;border-radius:7px;padding:24px;text-align:center;color:#6d7f95;margin-top:16px}.v2073-mini{font-size:10px;color:#72849a}.v2073-paneltitle{font-size:12px;font-weight:800;color:#18335c;margin-bottom:5px}
    /* V20.7.4.13.1 — Search Row Recovery & Alignment Fix.
       Scoped only to the Company Search form. No header/toolbar/global rules are changed. */
    [data-testid="stForm"]:has(.st-key-chr_company_search_input_v20747){
        border:0!important;outline:0!important;box-shadow:none!important;
        background:transparent!important;padding:0!important;margin:0!important;
    }
    .st-key-chr_company_search_input_v20747,
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInput"]{
        position:relative!important;margin:0!important;padding:0!important;
    }
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInputRootElement"],
    .st-key-chr_company_search_input_v20747 [data-baseweb="input"]{
        height:58px!important;min-height:58px!important;max-height:58px!important;
        background:#fff!important;background-color:#fff!important;
        border:1px solid #cbd8e6!important;border-radius:10px!important;
        outline:0!important;box-shadow:none!important;box-sizing:border-box!important;
        display:flex!important;align-items:center!important;overflow:hidden!important;
    }
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInputRootElement"]:hover,
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInputRootElement"]:focus-within,
    .st-key-chr_company_search_input_v20747 [data-baseweb="input"]:hover,
    .st-key-chr_company_search_input_v20747 [data-baseweb="input"]:focus-within{
        background:#fff!important;background-color:#fff!important;
        border-color:#cbd8e6!important;outline:0!important;box-shadow:none!important;
    }
    .st-key-chr_company_search_input_v20747 [data-baseweb="base-input"]{
        height:56px!important;min-height:56px!important;max-height:56px!important;
        width:100%!important;background:transparent!important;border:0!important;
        outline:0!important;box-shadow:none!important;display:flex!important;align-items:center!important;
    }
    .st-key-chr_company_search_input_v20747 input[placeholder="Search by company name or ticker..."]{
        height:56px!important;min-height:56px!important;max-height:56px!important;
        width:100%!important;margin:0!important;padding:0 20px 0 58px!important;
        background:transparent!important;border:0!important;outline:0!important;box-shadow:none!important;
        color:#17345c!important;-webkit-text-fill-color:#17345c!important;caret-color:#17345c!important;
        font-size:18px!important;line-height:56px!important;box-sizing:border-box!important;opacity:1!important;
    }
    .st-key-chr_company_search_input_v20747 input[placeholder="Search by company name or ticker..."]::placeholder{
        color:#667b94!important;-webkit-text-fill-color:#667b94!important;opacity:1!important;font-weight:500!important;
    }
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInput"]:before{
        content:""!important;position:absolute!important;z-index:8!important;left:22px!important;top:50%!important;
        width:19px!important;height:19px!important;border:3px solid #0b5bd3!important;border-radius:50%!important;
        transform:translateY(-58%)!important;box-sizing:border-box!important;pointer-events:none!important;
    }
    .st-key-chr_company_search_input_v20747 [data-testid="stTextInput"]:after{
        content:""!important;position:absolute!important;z-index:8!important;left:39px!important;top:50%!important;
        width:11px!important;height:3px!important;background:#0b5bd3!important;border-radius:2px!important;
        transform:translateY(6px) rotate(45deg)!important;transform-origin:left center!important;pointer-events:none!important;
    }
    .st-key-chr_company_search_submit_v20747,
    .st-key-chr_company_search_submit_v20747 [data-testid="stFormSubmitButton"]{
        margin:0!important;padding:0!important;height:58px!important;min-height:58px!important;max-height:58px!important;
    }
    .main .st-key-chr_company_search_submit_v20747 button,
    .st-key-chr_company_search_submit_v20747 button{
        height:58px!important;min-height:58px!important;max-height:58px!important;margin:0!important;padding:0 18px!important;
        border-radius:10px!important;background:#0b5bd3!important;background-color:#0b5bd3!important;
        border:1px solid #0b5bd3!important;color:#fff!important;font-size:18px!important;font-weight:750!important;
        line-height:1!important;box-shadow:none!important;box-sizing:border-box!important;display:flex!important;
        align-items:center!important;justify-content:center!important;
    }
    .main .st-key-chr_company_search_submit_v20747 button:hover,
    .st-key-chr_company_search_submit_v20747 button:hover{
        background:#084fb9!important;background-color:#084fb9!important;border-color:#084fb9!important;color:#fff!important;
    }
    /* V20.7.3.4 toolbar: explicit keyed buttons so theme/accent colours cannot override the reference design. */
    [class*="st-key-chr_mkt_"] button{height:42px!important;border:0!important;border-radius:8px!important;background:#eaf0f7!important;color:#17345c!important;font-size:13px!important;font-weight:750!important;box-shadow:none!important;padding:0 10px!important}
    [class*="st-key-chr_mkt_"] button:hover{background:#e2ebf5!important;color:#0b4f9c!important;border:0!important}
    .st-key-chr_mkt_all button,.st-key-chr_mkt_all button:hover{background:#0b5bd3!important;color:#fff!important}
    .v20734-market-gap{height:14px}
    /* V20.7.4.14 — reference-matched control spacing. */
    [data-testid="stForm"]:has(.st-key-chr_company_search_input_v20747){margin-bottom:0!important;}
    .st-key-chr_clear_company_filters_v20734{margin:0!important;padding:0!important;}
    /* V20.7.3.8 — exact two-line Company Search filter cards. */
    .st-key-chr_sector_filter_v2073,.st-key-chr_cap_filter_v2073,.st-key-chr_exchange_filter_v2073{position:relative!important;background:#fff!important;border:1px solid #cbd8e6!important;border-radius:8px!important;box-shadow:0 1px 3px rgba(15,23,42,.05)!important;padding:7px 12px 7px 13px!important;min-height:64px!important;box-sizing:border-box!important}
    .st-key-chr_sector_filter_v2073>div,.st-key-chr_cap_filter_v2073>div,.st-key-chr_exchange_filter_v2073>div{gap:0!important}
    .st-key-chr_sector_filter_v2073>div>label,.st-key-chr_cap_filter_v2073>div>label,.st-key-chr_exchange_filter_v2073>div>label,.st-key-chr_sector_filter_v2073 [data-testid="stWidgetLabel"],.st-key-chr_cap_filter_v2073 [data-testid="stWidgetLabel"],.st-key-chr_exchange_filter_v2073 [data-testid="stWidgetLabel"]{display:flex!important;visibility:visible!important;height:18px!important;min-height:18px!important;margin:0!important;padding:0!important;align-items:center!important}
    .st-key-chr_sector_filter_v2073 [data-testid="stWidgetLabel"] p,.st-key-chr_cap_filter_v2073 [data-testid="stWidgetLabel"] p,.st-key-chr_exchange_filter_v2073 [data-testid="stWidgetLabel"] p,.st-key-chr_sector_filter_v2073>div>label p,.st-key-chr_cap_filter_v2073>div>label p,.st-key-chr_exchange_filter_v2073>div>label p{color:#687b92!important;font-size:11px!important;line-height:16px!important;font-weight:600!important;margin:0!important;padding:0!important}
    .st-key-chr_sector_filter_v2073:before,.st-key-chr_cap_filter_v2073:before,.st-key-chr_exchange_filter_v2073:before{content:none!important;display:none!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"],.st-key-chr_cap_filter_v2073 [data-baseweb="select"],.st-key-chr_exchange_filter_v2073 [data-baseweb="select"]{height:30px!important;min-height:30px!important;background:transparent!important;border:0!important;border-radius:0!important;box-shadow:none!important;overflow:visible!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"]>div,.st-key-chr_cap_filter_v2073 [data-baseweb="select"]>div,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"]>div{height:30px!important;min-height:30px!important;background:transparent!important;border:0!important;box-shadow:none!important;padding:0!important;align-items:center!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] span,.st-key-chr_cap_filter_v2073 [data-baseweb="select"] span,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"] span{font-size:14px!important;line-height:20px!important;font-weight:650!important;color:#172b4d!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] svg,.st-key-chr_cap_filter_v2073 [data-baseweb="select"] svg,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"] svg{color:#17345c!important}
    /* V20.7.3.10: force the complete BaseWeb select surface white — no grey inner field. */
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"],
    .st-key-chr_cap_filter_v2073 [data-baseweb="select"],
    .st-key-chr_exchange_filter_v2073 [data-baseweb="select"],
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] > div,
    .st-key-chr_cap_filter_v2073 [data-baseweb="select"] > div,
    .st-key-chr_exchange_filter_v2073 [data-baseweb="select"] > div,
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] div,
    .st-key-chr_cap_filter_v2073 [data-baseweb="select"] div,
    .st-key-chr_exchange_filter_v2073 [data-baseweb="select"] div{background-color:#fff!important;background-image:none!important;box-shadow:none!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] input,
    .st-key-chr_cap_filter_v2073 [data-baseweb="select"] input,
    .st-key-chr_exchange_filter_v2073 [data-baseweb="select"] input{background:#fff!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] [role="button"],
    .st-key-chr_cap_filter_v2073 [data-baseweb="select"] [role="button"],
    .st-key-chr_exchange_filter_v2073 [data-baseweb="select"] [role="button"]{background:#fff!important}
    /* V20.7.3.11 — hard reset the native Streamlit/BaseWeb field chrome inside ONLY these three cards. */
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"],
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"],
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"],
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] div[role="combobox"],
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] div[role="combobox"],
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] div[role="combobox"]{
        background:#fff!important;
        background-color:#fff!important;
        background-image:none!important;
        border:0!important;
        outline:0!important;
        box-shadow:none!important;
    }
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
        background:#fff!important;
        border:0!important;
        outline:0!important;
        box-shadow:none!important;
    }
    /* V20.7.3.12 — flatten every rendered layer inside these three select widgets.
       Streamlit/BaseWeb can paint the field on nested generated elements/pseudo-elements,
       so reset the whole select subtree instead of guessing one generated class. */
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"],
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"],
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"]{
        --secondary-background-color:#fff!important;
        background:#fff!important;
    }
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *{
        background-color:transparent!important;
        background-image:none!important;
        box-shadow:none!important;
    }
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] [data-baseweb="select"],
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] [data-baseweb="select"],
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] [data-baseweb="select"],
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] [role="combobox"],
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] [role="combobox"],
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] [role="combobox"]{
        background:transparent!important;
        border:0!important;
        outline:0!important;
        box-shadow:none!important;
    }
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *::before,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *::before,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *::before,
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *::after,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *::after,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *::after{
        background-color:transparent!important;
        background-image:none!important;
        box-shadow:none!important;
    }
    /* V20.7.3.13 — remove the remaining native inner outline/border.
       The ONLY visible outline is the keyed outer card above. */
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *{
        border:0!important;
        border-width:0!important;
        border-color:transparent!important;
        outline:0!important;
        outline-width:0!important;
        outline-color:transparent!important;
        box-shadow:none!important;
    }
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *:hover,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *:hover,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *:hover,
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *:focus,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *:focus,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *:focus,
    .st-key-chr_sector_filter_v2073 [data-testid="stSelectbox"] *:focus-within,
    .st-key-chr_cap_filter_v2073 [data-testid="stSelectbox"] *:focus-within,
    .st-key-chr_exchange_filter_v2073 [data-testid="stSelectbox"] *:focus-within{
        border:0!important;
        outline:0!important;
        box-shadow:none!important;
    }
    .st-key-chr_sector_filter_v2073:hover,.st-key-chr_cap_filter_v2073:hover,.st-key-chr_exchange_filter_v2073:hover{border-color:#9db7d5!important}
    /* V20.7.4.14.1 — exact filter-row height alignment.
       Lock the Clear Filters widget wrapper AND native button to the same
       64px outer height as the three keyed select cards. */
    .st-key-chr_clear_company_filters_v20734{
        height:64px!important;
        min-height:64px!important;
        margin:0!important;
        padding:0!important;
        box-sizing:border-box!important;
        display:flex!important;
        align-items:stretch!important;
    }
    .st-key-chr_clear_company_filters_v20734>div,
    .st-key-chr_clear_company_filters_v20734 [data-testid="stButton"]{
        height:64px!important;
        min-height:64px!important;
        width:100%!important;
        margin:0!important;
        padding:0!important;
        display:flex!important;
        align-items:stretch!important;
    }
    .st-key-chr_clear_company_filters_v20734 button{
        height:64px!important;
        min-height:64px!important;
        width:100%!important;
        margin:0!important;
        padding:0 16px!important;
        box-sizing:border-box!important;
        border:1px solid #72a8ed!important;
        border-radius:8px!important;
        background:#fff!important;
        color:#174f91!important;
        font-size:13px!important;
        font-weight:750!important;
        line-height:1!important;
        box-shadow:0 1px 3px rgba(15,23,42,.03)!important;
        display:flex!important;
        align-items:center!important;
        justify-content:center!important;
    }
    .st-key-chr_clear_company_filters_v20734 button p{margin:0!important;line-height:1!important;}
    .st-key-chr_clear_company_filters_v20734 button:hover{background:#f4f8fd!important;color:#084bb2!important;border-color:#0b5bd3!important}
    /* V20.7.4.14.2 — TRUE filter-row height fix.
       The app-level stFragment secondary-button rule has higher specificity and
       was overriding 14.1 with height:auto. Override that exact selector only
       for Clear Filters so it truly matches the 64px filter cards. */
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734,
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 > div,
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"]{
        height:64px!important;min-height:64px!important;max-height:64px!important;
        margin:0!important;padding:0!important;box-sizing:border-box!important;width:100%!important;
    }
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"] button[kind="secondary"],
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 button{
        height:64px!important;min-height:64px!important;max-height:64px!important;
        margin:0!important;padding:0 16px!important;box-sizing:border-box!important;width:100%!important;
        display:flex!important;align-items:center!important;justify-content:center!important;
        border:1px solid #72a8ed!important;border-radius:8px!important;background:#fff!important;
        color:#174f91!important;font-size:13px!important;font-weight:750!important;line-height:1!important;
        box-shadow:0 1px 3px rgba(15,23,42,.03)!important;
    }
    /* V20.7.4.14.3 — structural filter height correction.
       The three select cards render taller than their nominal min-height because
       Streamlit includes label/select content in the keyed widget block. Match the
       Clear Filters OUTER rendered surface to that measured card height instead of
       repeating the ineffective 64px internal-button rule. */
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734,
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 > div,
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"],
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"] > div{
        height:74px!important;min-height:74px!important;max-height:74px!important;
        margin:0!important;padding:0!important;box-sizing:border-box!important;width:100%!important;
        display:flex!important;align-items:stretch!important;
    }
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"] button[kind="secondary"],
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 button{
        height:74px!important;min-height:74px!important;max-height:74px!important;
        margin:0!important;padding:0 16px!important;box-sizing:border-box!important;width:100%!important;
        align-self:stretch!important;display:flex!important;align-items:center!important;justify-content:center!important;
        border:1px solid #72a8ed!important;border-radius:8px!important;background:#fff!important;
        color:#174f91!important;font-size:13px!important;font-weight:750!important;line-height:1!important;
        box-shadow:0 1px 3px rgba(15,23,42,.03)!important;
    }
    /* V20.7.4.15 — REBUILT FILTER ROW STRUCTURE.
       One authoritative geometry contract for all four controls. */
    .st-key-chr_sector_filter_v2073,
    .st-key-chr_cap_filter_v2073,
    .st-key-chr_exchange_filter_v2073,
    .st-key-chr_clear_company_filters_v20734{
        height:64px!important;min-height:64px!important;max-height:64px!important;
        margin:0!important;box-sizing:border-box!important;
    }
    .st-key-chr_sector_filter_v2073,
    .st-key-chr_cap_filter_v2073,
    .st-key-chr_exchange_filter_v2073{padding:7px 12px 7px 13px!important;}
    .st-key-chr_clear_company_filters_v20734,
    .st-key-chr_clear_company_filters_v20734 > div,
    .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"]{
        height:64px!important;min-height:64px!important;max-height:64px!important;
        margin:0!important;padding:0!important;width:100%!important;box-sizing:border-box!important;
        display:flex!important;align-items:stretch!important;
    }
    .main div[data-testid="stFragment"] .st-key-chr_clear_company_filters_v20734 div[data-testid="stButton"] button[kind="secondary"],
    .main .st-key-chr_clear_company_filters_v20734 button[kind="secondary"],
    .st-key-chr_clear_company_filters_v20734 button{
        height:64px!important;min-height:64px!important;max-height:64px!important;
        margin:0!important;padding:0 16px!important;width:100%!important;box-sizing:border-box!important;
        display:flex!important;align-items:center!important;justify-content:center!important;
        border:1px solid #72a8ed!important;border-radius:8px!important;background:#fff!important;
        color:#174f91!important;font-size:13px!important;font-weight:750!important;line-height:1!important;
        box-shadow:0 1px 3px rgba(15,23,42,.03)!important;text-align:center!important;
    }
    .st-key-chr_clear_company_filters_v20734 button p{margin:0!important;line-height:1!important;}
    /* V20.7.4.15.1 — FILTER BORDER CONTINUITY FIX.
       Paint the dropdown-card border as a final overlay so Streamlit/BaseWeb
       descendants cannot visually cover the bottom edge. Geometry is unchanged. */
    .st-key-chr_sector_filter_v2073,
    .st-key-chr_cap_filter_v2073,
    .st-key-chr_exchange_filter_v2073{
        position:relative!important;
        border-color:transparent!important;
        overflow:visible!important;
    }
    .st-key-chr_sector_filter_v2073::after,
    .st-key-chr_cap_filter_v2073::after,
    .st-key-chr_exchange_filter_v2073::after{
        content:""!important;
        display:block!important;
        position:absolute!important;
        inset:0!important;
        z-index:999!important;
        pointer-events:none!important;
        box-sizing:border-box!important;
        border:1px solid #cbd8e6!important;
        border-radius:8px!important;
        background:transparent!important;
        box-shadow:0 1px 3px rgba(15,23,42,.05)!important;
    }
    /* V20.7.4.16 — REFERENCE-MATCHED FILTER CARDS & HOVER FIX. */
    .st-key-chr_sector_filter_v2073,.st-key-chr_cap_filter_v2073,.st-key-chr_exchange_filter_v2073{height:64px!important;min-height:64px!important;max-height:64px!important;padding:6px 12px 6px 13px!important;background:#fff!important;border:0!important;border-radius:8px!important;box-shadow:none!important;overflow:visible!important;position:relative!important}
    .st-key-chr_sector_filter_v2073::after,.st-key-chr_cap_filter_v2073::after,.st-key-chr_exchange_filter_v2073::after{content:""!important;position:absolute!important;inset:0!important;z-index:20!important;pointer-events:none!important;box-sizing:border-box!important;border:1px solid #cbd8e6!important;border-radius:8px!important;background:transparent!important;box-shadow:0 1px 3px rgba(15,23,42,.04)!important}
    .st-key-chr_sector_filter_v2073:hover::after,.st-key-chr_cap_filter_v2073:hover::after,.st-key-chr_exchange_filter_v2073:hover::after,.st-key-chr_sector_filter_v2073:focus-within::after,.st-key-chr_cap_filter_v2073:focus-within::after,.st-key-chr_exchange_filter_v2073:focus-within::after{border-color:#72a8ed!important;box-shadow:0 0 0 1px rgba(11,91,211,.08)!important}
    .st-key-chr_sector_filter_v2073 [data-testid="stWidgetLabel"],.st-key-chr_cap_filter_v2073 [data-testid="stWidgetLabel"],.st-key-chr_exchange_filter_v2073 [data-testid="stWidgetLabel"]{height:17px!important;min-height:17px!important;margin:0!important;padding:0!important;display:flex!important;align-items:center!important}
    .st-key-chr_sector_filter_v2073 [data-testid="stWidgetLabel"] p,.st-key-chr_cap_filter_v2073 [data-testid="stWidgetLabel"] p,.st-key-chr_exchange_filter_v2073 [data-testid="stWidgetLabel"] p{margin:0!important;padding:0!important;color:#60748d!important;font-size:10.5px!important;line-height:15px!important;font-weight:700!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"],.st-key-chr_cap_filter_v2073 [data-baseweb="select"],.st-key-chr_exchange_filter_v2073 [data-baseweb="select"]{height:33px!important;min-height:33px!important;margin:0!important;padding:0!important;background:transparent!important;border:0!important;outline:0!important;box-shadow:none!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"]>div,.st-key-chr_cap_filter_v2073 [data-baseweb="select"]>div,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"]>div{height:33px!important;min-height:33px!important;padding:0!important;margin:0!important;background:transparent!important;border:0!important;outline:0!important;box-shadow:none!important;display:flex!important;align-items:center!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] span,.st-key-chr_cap_filter_v2073 [data-baseweb="select"] span,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"] span{color:#172b4d!important;font-size:13px!important;line-height:18px!important;font-weight:650!important}
    .st-key-chr_sector_filter_v2073 [data-baseweb="select"] *,.st-key-chr_cap_filter_v2073 [data-baseweb="select"] *,.st-key-chr_exchange_filter_v2073 [data-baseweb="select"] *{border:0!important;outline:0!important;box-shadow:none!important}
    /* V20.7.4 — Search Results widget. Scoped to the Company Search results dataframe only. */
    .v2074-results-head{background:#fff;border:1px solid #dbe5f0;border-bottom:0;border-radius:9px 9px 0 0;padding:12px 16px 10px;margin-top:12px;box-shadow:0 1px 3px rgba(15,23,42,.035)}
    .v2074-results-title{font-size:20px;line-height:1.05;font-weight:850;color:#10264b;letter-spacing:-.02em}
    .v2074-results-sub{font-size:12px;color:#60748d;margin-top:4px}.v2074-results-sub b{color:#18335c}
    .st-key-chr_company_search_results_v2073{border-left:1px solid #dbe5f0!important;border-right:1px solid #dbe5f0!important;border-bottom:1px solid #dbe5f0!important;border-radius:0 0 9px 9px!important;overflow:hidden!important;background:#fff!important;box-shadow:0 1px 3px rgba(15,23,42,.035)!important}
    .st-key-chr_company_search_results_v2073 [data-testid="stDataFrame"]{border:0!important;border-radius:0!important}
    /* V20.7.4.1 — two-widget Search Results + Company Preview layout */
    .v20741-preview{background:#fff;border:1px solid #dbe5f0;border-radius:10px;padding:14px 15px 12px;box-shadow:0 1px 3px rgba(15,23,42,.035);min-height:520px}
    .v20741-company{font-size:18px;font-weight:850;color:#10264b;line-height:1.1}.v20741-meta{font-size:11px;color:#6a7d94;margin-top:3px}
    .v20741-price{font-size:29px;font-weight:900;color:#101820;margin:14px 0 12px}.v20741-up{font-size:16px;color:#159447;font-weight:800}.v20741-down{font-size:16px;color:#cf3c3c;font-weight:800}
    .v20741-stats{margin-top:8px}.v20741-stat{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid #e7edf4;padding:6px 0;font-size:12px}.v20741-stat span{color:#63768e}.v20741-stat b{color:#172b4d;text-align:right}
    .v20741-section{font-size:14px;font-weight:850;color:#10264b;margin:13px 0 8px}.v20741-consensus{display:flex;justify-content:space-between;align-items:center}.v20741-pill{background:#dcf4e7;color:#118348;padding:5px 10px;border-radius:12px;font-size:12px;font-weight:800}
    .v20741-empty{background:#fff;border:1px solid #dbe5f0;border-radius:10px;padding:28px 18px;color:#6a7d94;text-align:center;min-height:520px;display:flex;align-items:center;justify-content:center}
    /* V20.7.4.3 — purpose-built reference-matched results table. */
    .v20743-results-card{background:#fff;border:1px solid #dbe5f0;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(15,23,42,.035);min-height:610px;margin-top:12px}
    .v20743-results-top{padding:15px 18px 13px;border-bottom:1px solid #edf2f7}.v20743-results-title{font-size:22px;line-height:1.05;font-weight:900;color:#10264b;letter-spacing:-.025em}.v20743-results-sub{font-size:12px;color:#60748d;margin-top:5px}.v20743-results-sub b{color:#18335c}
    .v20743-table{width:100%;font-size:11px;color:#172b4d}.v20743-tr{display:grid;grid-template-columns:minmax(150px,1.7fr) minmax(70px,.72fr) minmax(78px,.78fr) minmax(115px,1.18fr) minmax(72px,.78fr) minmax(66px,.66fr) minmax(92px,.92fr);align-items:center;min-height:42px;border-bottom:1px solid #e8eef5}.v20743-th{min-height:38px;background:#eef6ff;color:#204f88;font-weight:850;border-bottom:1px solid #dce8f5}
    .v20743-cell{padding:8px 9px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v20743-num{text-align:right}.v20743-companycell{display:flex;align-items:center;gap:8px;font-weight:800}.v20743-companylink{color:#1261bd!important;text-decoration:none!important;font-weight:850}.v20743-companylink:hover{text-decoration:underline!important}
    .v20743-logo{width:23px;height:23px;object-fit:contain;border-radius:5px;flex:0 0 23px}.v20743-logo-fallback{width:23px;height:23px;border-radius:50%;background:#eef3f8;color:#17345c;display:inline-flex;align-items:center;justify-content:center;font-size:10px;font-weight:900;flex:0 0 23px}.v20743-country{display:flex;align-items:center;gap:6px}.v20743-flag{font-size:16px;line-height:1}.v20743-up{color:#159447;font-weight:850}.v20743-down{color:#d04747;font-weight:850}.v20743-flat{color:#52657d;font-weight:750}
    @media(max-width:1100px){.v20743-table{font-size:10px}.v20743-cell{padding-left:6px;padding-right:6px}.v20743-tr{grid-template-columns:minmax(130px,1.55fr) 68px 72px minmax(100px,1fr) 66px 60px 82px}}
    </style>
    <div class="v2073-rule"><div class="v2073-head"><div><div class="v2073-title">Company Search</div><div class="v2073-sub">Find and analyse stocks across global markets</div></div><div class="v2073-quote">“Better information. Better decisions.”</div></div></div>
    """,unsafe_allow_html=True)

    with st.form("chr_global_company_search_form_v2073", clear_on_submit=False):
        c1,c2=st.columns([5.4,1])
        with c1:
            q=st.text_input("Global company search",value=st.session_state.get("chr_company_search_query",""),placeholder="Search by company name or ticker...",label_visibility="collapsed",key="chr_company_search_input_v20747")
        with c2: submitted=st.form_submit_button("Search",use_container_width=True,type="primary",key="chr_company_search_submit_v20747")
    st.markdown('<div class="v2073-hint">e.g. Apple, AAPL, ZIP, Commonwealth Bank, Coca-Cola...</div>',unsafe_allow_html=True)
    if submitted:
        st.session_state["chr_company_search_query"]=q.strip(); st.session_state.pop("chr_company_search_selected",None)

    markets=["All Markets","Australia","United States","United Kingdom","Japan","Hong Kong","Canada"]
    if "chr_company_market_v20734" not in st.session_state:
        st.session_state["chr_company_market_v20734"]="All Markets"
    country_tab=st.session_state["chr_company_market_v20734"]
    country_map={markets[1]:"Australia",markets[2]:"United States",markets[3]:"United Kingdom",markets[4]:"Japan",markets[5]:"Hong Kong",markets[6]:"Canada"}

    # V20.7.3.4: native keyed buttons reproduce the approved reference reliably,
    # independent of Streamlit's segmented-control/theme accent styling.
    mcols=st.columns([1.05,.92,1.10,1.10,.72,.88,.72,1.35],gap="small")
    mkeys=["all","au","us","uk","jp","hk","ca"]
    for col,label,keypart in zip(mcols[:7],markets,mkeys):
        # Active state gets its own key/class so CSS can paint it Chrímata blue.
        css_key=f"chr_mkt_{keypart}" if label==country_tab else f"chr_mkt_off_{keypart}"
        if col.button(label,key=css_key,use_container_width=True):
            st.session_state["chr_company_market_v20734"]=label
            st.rerun()
    st.markdown('<div class="v20734-market-gap"></div>',unsafe_allow_html=True)

    # V20.7.4.16: reference proportions — three compact filter cards, a deliberate
    # whitespace channel, then Clear Filters at the far right.
    filter_left,filter_spacer,filter_right=st.columns([7.2,0.9,1.3],gap="small",vertical_alignment="top")
    with filter_left:
        f1,f2,f3=st.columns(3,gap="small",vertical_alignment="top")
        sector_filter=f1.selectbox("Sector",["All Sectors","Technology","Financial Services","Healthcare","Consumer Cyclical","Consumer Defensive","Industrials","Energy","Basic Materials","Real Estate","Utilities","Communication Services"],key="chr_sector_filter_v2073")
        cap_filter=f2.selectbox("Market Cap",["All Market Caps","Mega (>$200B)","Large ($10B–$200B)","Mid ($2B–$10B)","Small (<$2B)"],key="chr_cap_filter_v2073")
        exchange_filter=f3.selectbox("Exchange",["All Exchanges","ASX","NASDAQ","NYSE","LSE","HKEX","TSE","TSX"],key="chr_exchange_filter_v2073")
    with filter_right:
        clear_filters=st.button("Clear Filters",key="chr_clear_company_filters_v20734",use_container_width=True)
    if clear_filters:
        st.session_state["chr_company_market_v20734"]=markets[0]
        st.session_state["chr_sector_filter_v2073"]="All Sectors"
        st.session_state["chr_cap_filter_v2073"]="All Market Caps"
        st.session_state["chr_exchange_filter_v2073"]="All Exchanges"
        st.rerun()

    query=st.session_state.get("chr_company_search_query","").strip()
    if not query:
        st.markdown('<div class="v2073-empty"><b>Search global listed companies</b><br>Use the market and listing controls above to find the exact security you want to analyse.</div>',unsafe_allow_html=True)
        return
    try: key=st.secrets.get("TWELVE_DATA_API_KEY","")
    except Exception: key=""
    with st.spinner("Searching global markets..."): results=search_securities(query,key)
    if results is None or results.empty:
        st.warning(f'No listed securities found for "{query}". Try the company name, ticker, or an exchange-qualified ticker.'); return
    results=results.copy(); results["Market"]=[_chr_search_exchange_bucket(s,e,c) for s,e,c in zip(results["Symbol"],results["Exchange"],results["Country"])]
    wanted_country=country_map.get(country_tab)
    if wanted_country: results=results[results["Country"].astype(str).eq(wanted_country)].copy()
    if exchange_filter!="All Exchanges": results=results[results["Market"].astype(str).eq(exchange_filter)].copy()
    if results.empty: st.info("No listings matched the current market filters. Try All Markets / All Exchanges."); return

    rows=[]
    for _,r in results.head(16).iterrows():
        sym=str(r["Symbol"]); resolved=resolve_listing(sym,r.get("Exchange",""),r.get("Country","")); oq=overview_quote(resolved,"5d") or {}
        last=_mia_num(oq.get("last")); chg=_mia_num(oq.get("pct"))
        try: meta=info(resolved) or {}
        except Exception: meta={}
        rows.append({"Company":str(meta.get("shortName") or r.get("Company") or sym),"Ticker":sym,"Exchange":str(r.get("Exchange") or ""),"Market":str(r.get("Market") or ""),"Country":str(r.get("Country") or ""),"Currency":str(meta.get("currency") or r.get("Currency") or ""),"Sector":str(meta.get("sector") or "—"),"Logo":str(meta.get("logo_url") or meta.get("logoUrl") or ""),"Market Cap":_mia_num(meta.get("marketCap")),"Price":None if not np.isfinite(last) else float(last),"Day %":None if not np.isfinite(chg) else float(chg),"_resolved":resolved})
    view=pd.DataFrame(rows)
    if sector_filter!="All Sectors": view=view[view["Sector"].eq(sector_filter)].copy()
    if cap_filter!="All Market Caps":
        mc=pd.to_numeric(view["Market Cap"],errors="coerce")
        if cap_filter.startswith("Mega"): view=view[mc>=2e11]
        elif cap_filter.startswith("Large"): view=view[(mc>=1e10)&(mc<2e11)]
        elif cap_filter.startswith("Mid"): view=view[(mc>=2e9)&(mc<1e10)]
        else: view=view[mc<2e9]
    if view.empty: st.info("Listings were found, but none match the selected Sector / Market Cap filters."); return

    # V20.7.4.3 — custom results widget; avoids Streamlit dataframe chrome.
    flag_map={"United States":"🇺🇸","USA":"🇺🇸","Australia":"🇦🇺","United Kingdom":"🇬🇧","UK":"🇬🇧","Japan":"🇯🇵","Hong Kong":"🇭🇰","Canada":"🇨🇦","Germany":"🇩🇪","Argentina":"🇦🇷","Mexico":"🇲🇽","Poland":"🇵🇱","Taiwan":"🇹🇼"}
    def _v20743_cap(v):
        try:
            x=float(v)
            if not np.isfinite(x): return "—"
            if x>=1e12: return f"US${x/1e12:.2f}T"
            if x>=1e9: return f"US${x/1e9:.1f}B"
            if x>=1e6: return f"US${x/1e6:.1f}M"
            return f"US${x:,.0f}"
        except Exception: return "—"
    try:
        pick_raw=st.query_params.get("chr_pick")
        if isinstance(pick_raw,list): pick_raw=pick_raw[0] if pick_raw else None
        if pick_raw is not None:
            pick_i=int(pick_raw)
            if 0 <= pick_i < len(view):
                st.session_state["chr_company_search_selected"]=view.iloc[pick_i].to_dict()
                recent=st.session_state.setdefault("chr_recent_companies",[])
                item=view.iloc[pick_i]["_resolved"]
                st.session_state["chr_recent_companies"]=[item]+[x for x in recent if x!=item][:4]
    except Exception:
        pass

    q_label=html.escape(query)
    results_col, preview_col = st.columns([1.78,1.0], gap="small")
    with results_col:
        rows_html=[]
        for i,(_,r) in enumerate(view.iterrows()):
            company_txt=html.escape(str(r.get("Company") or r.get("Ticker") or "—")); ticker_txt=html.escape(str(r.get("Ticker") or "—")); exchange_txt=html.escape(str(r.get("Exchange") or "—")); country_raw=str(r.get("Country") or "")
            country_txt=html.escape(country_raw or "—"); flag=flag_map.get(country_raw,"🌐"); price=r.get("Price"); day=r.get("Day %"); cap=r.get("Market Cap"); logo=str(r.get("Logo") or "")
            try: price_txt="—" if not np.isfinite(float(price)) else f"{float(price):,.2f}"
            except Exception: price_txt="—"
            try:
                dv=float(day); day_txt="—" if not np.isfinite(dv) else f"{dv:+.2f}%"; day_cls="v20743-up" if dv>0 else ("v20743-down" if dv<0 else "v20743-flat")
            except Exception: day_txt="—"; day_cls="v20743-flat"
            if logo.startswith("http://") or logo.startswith("https://"):
                logo_html=f'<img class="v20743-logo" src="{html.escape(logo,quote=True)}" alt="">'
            else:
                initial=html.escape((str(r.get("Company") or "?").strip()[:1] or "?").upper()); logo_html=f'<span class="v20743-logo-fallback">{initial}</span>'
            rows_html.append(f'<div class="v20743-tr"><div class="v20743-cell v20743-companycell">{logo_html}<a class="v20743-companylink" href="?chr_pick={i}">{company_txt}</a></div><div class="v20743-cell">{ticker_txt}</div><div class="v20743-cell">{exchange_txt}</div><div class="v20743-cell v20743-country"><span class="v20743-flag">{flag}</span><span>{country_txt}</span></div><div class="v20743-cell v20743-num">{price_txt}</div><div class="v20743-cell v20743-num {day_cls}">{day_txt}</div><div class="v20743-cell v20743-num">{_v20743_cap(cap)}</div></div>')
        plural="s" if len(view)!=1 else ""
        table_html=(f'<div class="v20743-results-card"><div class="v20743-results-top"><div class="v20743-results-title">Search Results</div><div class="v20743-results-sub">Showing results for <b>“{q_label}”</b> ({len(view)} result{plural})</div></div>'
                    + '<div class="v20743-table"><div class="v20743-tr v20743-th"><div class="v20743-cell">Company ◊</div><div class="v20743-cell">Ticker ◊</div><div class="v20743-cell">Exchange</div><div class="v20743-cell">Country</div><div class="v20743-cell v20743-num">Price</div><div class="v20743-cell v20743-num">Day</div><div class="v20743-cell v20743-num">Market Cap</div></div>'
                    + ''.join(rows_html) + '</div></div>')
        st.markdown(table_html,unsafe_allow_html=True)

    selected=st.session_state.get("chr_company_search_selected")
    if not selected and len(view):
        selected=view.iloc[0].to_dict(); st.session_state["chr_company_search_selected"]=selected

    with preview_col:
        if not selected:
            st.markdown('<div class="v20741-empty">Select a result to open the company preview.</div>',unsafe_allow_html=True)
        else:
            resolved=str(selected.get("_resolved") or selected.get("Ticker") or "")
            try: smeta=info(resolved) or {}
            except Exception: smeta={}
            oq=overview_quote(resolved,"1y") or {}; last=_mia_num(oq.get("last")); pct=_mia_num(oq.get("pct")); company=smeta.get("longName") or smeta.get("shortName") or selected.get("Company") or resolved
            currency=smeta.get("currency") or selected.get("Currency") or ""; cap=_mia_num(smeta.get("marketCap")); low=_mia_num(smeta.get("fiftyTwoWeekLow")); high=_mia_num(smeta.get("fiftyTwoWeekHigh")); pe=_mia_num(smeta.get("trailingPE")); dy=_mia_num(smeta.get("dividendYield")); sector=smeta.get("sector") or selected.get("Sector") or "—"; industry=smeta.get("industry") or "—"
            def fm(v):
                if not np.isfinite(v): return "—"
                if abs(v)>=1e12:return f"US${v/1e12:.2f}T"
                if abs(v)>=1e9:return f"US${v/1e9:.2f}B"
                if abs(v)>=1e6:return f"US${v/1e6:.2f}M"
                return f"US${v:,.0f}"
            price_txt="—" if not np.isfinite(last) else f"{last:,.2f}"; delta="—" if not np.isfinite(pct) else f"{pct:+.2f}%"; range_txt="—" if not(np.isfinite(low) and np.isfinite(high)) else f"{low:,.2f} – {high:,.2f}"
            delta_cls="v20741-up" if np.isfinite(pct) and pct>=0 else "v20741-down"
            target=_mia_num(smeta.get("targetMeanPrice")); rec=str(smeta.get("recommendationKey") or "No consensus").replace("_"," ").title(); analysts=smeta.get("numberOfAnalystOpinions"); upside=(target/last-1)*100 if np.isfinite(target) and np.isfinite(last) and last else np.nan
            pe_txt="—" if not np.isfinite(pe) else f"{pe:.1f}"; dy_txt="—" if not np.isfinite(dy) else f"{dy*100:.2f}%"; target_txt="—" if not np.isfinite(target) else f"{target:,.2f}"; upside_txt="" if not np.isfinite(upside) else f" ({upside:+.1f}%)"; analysts_txt="—" if analysts is None else html.escape(str(analysts))
            ex=html.escape(str(selected.get("Exchange",""))); country=html.escape(str(selected.get("Country",""))); ticker_txt=html.escape(str(selected.get("Ticker","")))
            st.markdown(f'<div class="v20741-preview"><div class="v20741-company">{html.escape(str(company))}</div><div class="v20741-meta">{ticker_txt} | {ex} | {country}</div><div class="v20741-price">{price_txt} <span class="{delta_cls}">{delta}</span></div>',unsafe_allow_html=True)
            h1=history(resolved,"1y")
            if h1 is not None and not h1.empty and "Close" in h1.columns:
                fig=go.Figure(go.Scatter(x=h1.index,y=h1["Close"],mode="lines",line={"width":2,"color":"#159447"},fill="tozeroy",fillcolor="rgba(21,148,71,.08)")); fig.update_layout(height=155,margin=dict(l=0,r=0,t=4,b=4),showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)"); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            st.markdown(f'<div class="v20741-stats"><div class="v20741-stat"><span>Market Cap</span><b>{fm(cap)}</b></div><div class="v20741-stat"><span>52 Week Range</span><b>{range_txt}</b></div><div class="v20741-stat"><span>P/E Ratio</span><b>{pe_txt}</b></div><div class="v20741-stat"><span>Dividend Yield</span><b>{dy_txt}</b></div><div class="v20741-stat"><span>Sector</span><b>{html.escape(str(sector))}</b></div><div class="v20741-stat"><span>Industry</span><b>{html.escape(str(industry))}</b></div></div><div class="v20741-consensus"><div class="v20741-section">Analyst Consensus</div><div class="v20741-pill">{html.escape(rec)}</div></div><div class="v20741-stat"><span>Analysts</span><b>{analysts_txt}</b></div><div class="v20741-stat"><span>12M Target</span><b>{target_txt}{upside_txt}</b></div></div>',unsafe_allow_html=True)
            if st.button("Open Company Command Centre  →",type="primary",use_container_width=True,key="chr_search_open_cc_v20741"):
                st.session_state["chr_active_ticker"]=resolved; st.session_state["mia_search_query"]=resolved; st.session_state["chr_primary_nav"]="Company Command Centre"; st.rerun()
            if st.button("☆  Add to Watchlist",use_container_width=True,key="chr_search_watch_v20741"):
                try: watch_add(resolved); st.success(f"{resolved} added to Watchlist.")
                except Exception as exc: st.warning(f"Could not add {resolved} to Watchlist: {exc}")
    st.markdown('<div class="v2073-label">Market Discovery</div>',unsafe_allow_html=True)
    p1,p2,p3=st.columns(3)
    recent=st.session_state.get("chr_recent_companies",[])
    with p1:
        st.markdown('<div class="v2073-paneltitle">Recently Viewed</div>',unsafe_allow_html=True)
        if recent:
            for x in recent[:3]: st.caption(f"• {x}")
        else: st.caption("Your selected companies will appear here.")
    with p2:
        st.markdown('<div class="v2073-paneltitle">Popular Today</div>',unsafe_allow_html=True); st.caption("Market popularity feed requires a configured market-data source. Search remains fully functional without it.")
    with p3:
        st.markdown('<div class="v2073-paneltitle">Biggest Movers (Global)</div>',unsafe_allow_html=True); st.caption("Global movers populate when a live market breadth / movers feed is configured.")


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


elif page=="Company Search":
    _chr_company_search_page()

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


# V20.4.0 stable labelled chart axis alignment.
st.markdown(r"""<style>
.chr-chart-axis{left:76px!important;right:76px!important;bottom:7px!important;font-size:10px!important;font-weight:500!important;}
.chr-bigchart svg{overflow:visible!important;}
.chr-metric-link{cursor:pointer!important;}
</style>""",unsafe_allow_html=True)
