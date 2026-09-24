import streamlit as st
import streamlit.components.v1 as components
from zoneinfo import ZoneInfo
from datetime import datetime, time, timedelta
import pandas as pd
import numpy as np
import re
import html
import html as html_lib
from urllib.parse import urlparse
import yfinance as yf
from news_intelligence_engine import news_intelligence, latest_company_news
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from valuation_lab import scenarios, margin_of_safety
from reverse_dcf import implied_growth
from evidence_engine import evidence_for, thesis_rules, add_thesis_rule
from services.thesis_engine import build_thesis_scorecard, ThesisThresholds
from services.thesis_status_engine import calculate_thesis_status
from services.thesis_template_engine import get_thesis_template, classify_thesis_template
from services.research_score_engine import calculate_research_score
from services.valuation_engine import calculate_dcf_scenarios, provider_inputs as valuation_provider_inputs
from services.technical_engine import calculate_technical_snapshot, core_indicator_frame
from services.valuation_evidence import recover_financial_inputs, bridge_payload
from services.analyst_engine import build_analyst_payload
from services.forecast_engine import build_12m_forecast
from services.macro_to_micro_engine import exposure_map, fetch_close as macro_fetch_close, align_series as macro_align_series, normalize_100 as macro_normalize_100, macro_by_label
from services.security_identity import canonicalize_security, safe_classification, validate_identity, CACHE_TTL
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
from announcement_engine import (announcements, fetch_document, extract_text, evidence_summary, announcement_provenance,
    announcements_global, official_disclosure_gateway, announcement_provenance_global, resolve_announcement_market)
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

@st.cache_data(ttl=21600, show_spinner=False)
def info(t):
    try: return yf.Ticker(t).info
    except: return {}

@st.cache_data(ttl=120, show_spinner=False)
def history_interval(t, period="1y", interval="1d"):
    """Cached interval history used by interactive charts and technical workspaces.
    Prevents a Streamlit navigation rerun from downloading identical bars again.
    """
    try:
        return yf.Ticker(t).history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def history_metadata(t):
    try:
        return yf.Ticker(t).get_history_metadata() or {}
    except Exception:
        return {}

@st.cache_data(ttl=21600, show_spinner=False)
def shares_history(t):
    """Point-in-time share-count fallback from the upstream provider.
    Used only when quote metadata does not expose sharesOutstanding.
    """
    try:
        x=yf.Ticker(t).get_shares_full(start=(pd.Timestamp.utcnow()-pd.Timedelta(days=550)).strftime("%Y-%m-%d"))
        if x is None:
            return pd.Series(dtype=float)
        return pd.to_numeric(x,errors="coerce").dropna()
    except Exception:
        return pd.Series(dtype=float)

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
    # V21.3.20 — core RSI/SMA/MACD/ATR/volume calculations come from one deterministic engine.
    t=core_indicator_frame(x)
    t["EMA 20"]=c.ewm(span=20,adjust=False).mean()
    mid=c.rolling(20).mean(); sd=c.rolling(20).std()
    t["BB Upper"]=mid+2*sd; t["BB Middle"]=mid; t["BB Lower"]=mid-2*sd
    lo14=l.rolling(14).min(); hi14=h.rolling(14).max()
    t["Stoch %K"]=100*(c-lo14)/(hi14-lo14).replace(0,np.nan); t["Stoch %D"]=t["Stoch %K"].rolling(3).mean()
    t["Williams %R"]=-100*(hi14-c)/(hi14-lo14).replace(0,np.nan)
    t["ROC"]=c.pct_change(12)*100; t["Momentum"]=c-c.shift(10)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    # ATR is supplied by services.technical_engine.core_indicator_frame.
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



@st.cache_data(ttl=3600, show_spinner=False)
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


@st.cache_data(ttl=3600, show_spinner=False)
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
            info=info(ticker) or {}
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

def overview_thesis_template(ticker, sector="", industry=""):
    """Return a six-row monitoring template without inventing evidence or status.

    Stored thesis rules always take precedence. These rows are only a starter
    structure for an unconfigured company and therefore remain Pending until
    the user records measurable evidence in Thesis Scorecard.
    """
    try:
        name=(company_name(ticker) if 'company_name' in globals() else ticker)
    except Exception:
        name=ticker
    text=f"{ticker} {name} {sector} {industry}".lower()
    if "zip" in text:
        return [
            "US TTV growth",
            "Cash EBITDA growth",
            "Operating margin improvement",
            "Credit losses / bad debts",
            "NASDAQ listing catalyst",
            "Valuation attractive at current price",
        ]
    base=company_kpi_template(ticker,sector,industry)
    labels=[]
    for x in base:
        x=str(x).strip()
        if x and x not in labels:
            labels.append(x)
        if len(labels)>=6:
            break
    while len(labels)<6:
        labels.append(["Valuation","Balance sheet","Catalyst","Guidance","Cash generation","Risk monitor"][len(labels)%6])
    return labels[:6]

@st.cache_data(ttl=3600, show_spinner=False)
def investment_snapshot_ttm_metrics(ticker):
    """Return TTM metrics with a conservative growth fallback hierarchy.

    Value hierarchy: four-quarter TTM -> provider trailing/latest fallback in caller.
    Growth hierarchy: prior four-quarter TTM -> latest FY vs prior FY -> unavailable.
    The fallback never labels an annual comparison as TTM growth; provenance records
    the exact comparison basis used for every metric.
    """
    out={}
    def _frame(obj, attr):
        try:
            x=getattr(obj,attr)
            return x if isinstance(x,pd.DataFrame) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    def _row(df,names):
        if df is None or df.empty: return None
        idx={str(i).strip().lower():i for i in df.index}
        for n in names:
            key=str(n).strip().lower()
            if key in idx:
                try:
                    ser=pd.to_numeric(df.loc[idx[key]],errors="coerce").dropna()
                    # yfinance normally returns newest first; enforce it when dates are parseable.
                    try:
                        dts=pd.to_datetime(ser.index,errors="coerce")
                        if dts.notna().sum()>=2:
                            ser=ser.iloc[list(np.argsort(dts.view("i8"))[::-1])]
                    except Exception:
                        pass
                    return ser
                except Exception: return None
        return None
    def _sum4(ser,offset=0):
        if ser is None or len(ser)<offset+4: return np.nan
        vals=[float(x) for x in ser.iloc[offset:offset+4]]
        return float(np.sum(vals)) if all(np.isfinite(vals)) else np.nan
    def _annual_growth(ser):
        if ser is None or len(ser)<2: return np.nan
        cur=float(ser.iloc[0]); prev=float(ser.iloc[1])
        return np.nan if not np.isfinite(cur) or not np.isfinite(prev) or prev==0 else cur/abs(prev)-1
    def _metric(qser,aser,derive_note=""):
        cur=_sum4(qser,0)
        prior=_sum4(qser,4)
        growth=np.nan; growth_basis=""; cmp_cur=np.nan; cmp_prior=np.nan
        if np.isfinite(cur) and np.isfinite(prior):
            cmp_cur,cmp_prior=cur,prior
            if prior!=0:
                growth=cur/abs(prior)-1
            growth_basis="TTM vs prior TTM (8 quarterly periods)"
        elif aser is not None and len(aser)>=2:
            try:
                cmp_cur=float(aser.iloc[0]); cmp_prior=float(aser.iloc[1])
            except Exception:
                cmp_cur=cmp_prior=np.nan
            ag=_annual_growth(aser)
            if np.isfinite(ag): growth=ag
            if np.isfinite(cmp_cur) and np.isfinite(cmp_prior):
                growth_basis="Latest FY vs prior FY fallback"
        value_basis="4-quarter TTM" if np.isfinite(cur) else "TTM unavailable from quarterly statements"
        if derive_note:
            value_basis += derive_note
            if growth_basis: growth_basis += derive_note
        return {"value":cur,"growth":growth,"compare_current":cmp_cur,"compare_prior":cmp_prior,"value_basis":value_basis,"growth_basis":growth_basis or "Comparable growth unavailable"}
    try:
        t=yf.Ticker(ticker)
        qinc=_frame(t,"quarterly_income_stmt"); qcf=_frame(t,"quarterly_cashflow")
        ainc=_frame(t,"income_stmt"); acf=_frame(t,"cashflow")
        mapping={
            "Revenue": (qinc,ainc,["Total Revenue","Operating Revenue"]),
            "EBITDA": (qinc,ainc,["EBITDA","Normalized EBITDA"]),
            "Net Income": (qinc,ainc,["Net Income","Net Income Common Stockholders","Net Income Including Noncontrolling Interests"]),
            "EPS": (qinc,ainc,["Diluted EPS","Basic EPS"]),
            "Free Cash Flow": (qcf,acf,["Free Cash Flow"]),
        }
        for label,(qdf,adf,names) in mapping.items():
            out[label]=_metric(_row(qdf,names),_row(adf,names))
        # If provider omits FCF, derive it consistently as OCF + capex (capex is normally negative).
        if not np.isfinite(out["Free Cash Flow"]["value"]):
            qocf=_row(qcf,["Operating Cash Flow","Total Cash From Operating Activities"])
            qcap=_row(qcf,["Capital Expenditure","Capital Expenditures"])
            aocf=_row(acf,["Operating Cash Flow","Total Cash From Operating Activities"])
            acap=_row(acf,["Capital Expenditure","Capital Expenditures"])
            def _combine(a,b):
                if a is None or b is None: return None
                n=min(len(a),len(b))
                if n<=0: return None
                return pd.Series([float(a.iloc[i])+float(b.iloc[i]) for i in range(n)])
            out["Free Cash Flow"]=_metric(_combine(qocf,qcap),_combine(aocf,acap),"; derived as operating cash flow + capex")
    except Exception:
        pass
    return out

@st.cache_data(ttl=3600, show_spinner=False)
def thesis_financial_evidence(ticker):
    """Build a small, cached evidence set from provider statements.

    Uses reported statement rows where available and records the comparison used.
    Missing rows stay missing; callers must not infer a thesis state from absence.
    """
    out={}
    def _frame(obj, attr):
        try:
            x=getattr(obj,attr)
            return x if isinstance(x,pd.DataFrame) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()
    def _series(df,names):
        if df is None or df.empty: return None
        idx={str(i).strip().lower():i for i in df.index}
        for n in names:
            key=str(n).strip().lower()
            if key in idx:
                try: return pd.to_numeric(df.loc[idx[key]],errors="coerce").dropna()
                except Exception: return None
        return None
    def _pair(series):
        if series is None or len(series)<2: return (np.nan,np.nan)
        # yfinance normally supplies newest statement first.
        return (float(series.iloc[0]),float(series.iloc[1]))
    def _growth(cur,prior):
        return np.nan if not np.isfinite(cur) or not np.isfinite(prior) or prior==0 else cur/abs(prior)-1
    try:
        t=yf.Ticker(ticker)
        inc=_frame(t,"income_stmt")
        qinc=_frame(t,"quarterly_income_stmt")
        cf=_frame(t,"cashflow")
        qcf=_frame(t,"quarterly_cashflow")
        bs=_frame(t,"balance_sheet")
        qbs=_frame(t,"quarterly_balance_sheet")
        # Prefer annual comparisons for thesis monitoring; fall back to quarterly.
        for df,period in ((inc,"annual"),(qinc,"quarterly")):
            rev=_series(df,["Total Revenue","Operating Revenue"])
            cur,prior=_pair(rev)
            if np.isfinite(_growth(cur,prior)):
                out["revenue_growth"]={"value":_growth(cur,prior),"current":cur,"prior":prior,"source":f"Provider {period} income statement"}; break
        for df,period in ((inc,"annual"),(qinc,"quarterly")):
            ni=_series(df,["Net Income","Net Income Common Stockholders","Net Income Including Noncontrolling Interests"])
            cur,prior=_pair(ni)
            if np.isfinite(_growth(cur,prior)):
                out["earnings_growth"]={"value":_growth(cur,prior),"current":cur,"prior":prior,"source":f"Provider {period} income statement"}; break
        for df,period in ((inc,"annual"),(qinc,"quarterly")):
            rev=_series(df,["Total Revenue","Operating Revenue"]); op=_series(df,["Operating Income"])
            rc,rp=_pair(rev); oc,oprior=_pair(op)
            if all(np.isfinite(x) for x in [rc,rp,oc,oprior]) and rc and rp:
                out["operating_margin"]={"value":oc/rc,"prior":oprior/rp,"source":f"Provider {period} income statement"}; break
        for df,period in ((cf,"annual"),(qcf,"quarterly")):
            fcf=_series(df,["Free Cash Flow"])
            cur,prior=_pair(fcf)
            if np.isfinite(cur):
                out["free_cash_flow"]={"value":cur,"prior":prior,"growth":_growth(cur,prior),"source":f"Provider {period} cash-flow statement"}; break
            ocf=_series(df,["Operating Cash Flow","Total Cash From Operating Activities"]); capex=_series(df,["Capital Expenditure","Capital Expenditures"])
            oc,oprior=_pair(ocf); cc,cprior=_pair(capex)
            if np.isfinite(oc) and np.isfinite(cc):
                cur=oc+cc; prior=oprior+cprior if np.isfinite(oprior) and np.isfinite(cprior) else np.nan
                out["free_cash_flow"]={"value":cur,"prior":prior,"growth":_growth(cur,prior),"source":f"Provider {period} cash-flow statement"}; break
        for idf,bdf,period in ((inc,bs,"annual"),(qinc,qbs,"quarterly")):
            ni=_series(idf,["Net Income","Net Income Common Stockholders"]); eq=_series(bdf,["Stockholders Equity","Total Stockholder Equity"])
            nc,_=_pair(ni); ec,_=_pair(eq)
            if np.isfinite(nc) and np.isfinite(ec) and ec:
                out["roe"]={"value":nc/ec,"source":f"Provider {period} financial statements"}; break
    except Exception:
        pass
    return out

def deterministic_financial_thesis(ticker):
    """Adapt provider statement evidence into the pure-Python thesis service.

    The service, not AI, performs all growth/margin arithmetic. Missing inputs remain None.
    """
    e=thesis_financial_evidence(ticker) or {}
    rg=e.get("revenue_growth",{}); om=e.get("operating_margin",{}); f=e.get("free_cash_flow",{})
    rc=_mia_num(rg.get("current")); rp=_mia_num(rg.get("prior"))
    mc=_mia_num(om.get("value")); mp=_mia_num(om.get("prior"))
    fc=_mia_num(f.get("value")); fp=_mia_num(f.get("prior"))
    # Recover operating income from reported revenue × reported margin only when both exist.
    oc=rc*mc if np.isfinite(rc) and np.isfinite(mc) else np.nan
    op=rp*mp if np.isfinite(rp) and np.isfinite(mp) else np.nan
    if not (np.isfinite(rc) and np.isfinite(rp)): return None
    raw={"financials":[
        {"year":1,"Revenue":rp,"Operating Income":op if np.isfinite(op) else None,"Free Cash Flow":fp if np.isfinite(fp) else None},
        {"year":2,"Revenue":rc,"Operating Income":oc if np.isfinite(oc) else None,"Free Cash Flow":fc if np.isfinite(fc) else None},
    ]}
    try: return build_thesis_scorecard(raw,ThesisThresholds())
    except Exception: return None

def overview_dynamic_thesis(ticker, sector="", industry="", meta=None, base_value=np.nan, current_price=np.nan):
    """Evaluate a company-specific six-condition thesis from traceable evidence.

    Reported statement comparisons take priority over snapshot metadata. A status is
    only assigned where the evidence supports an explicit rule; otherwise Pending.
    """
    meta=meta or {}; stmt=thesis_financial_evidence(ticker); det=deterministic_financial_thesis(ticker)
    try: name=(company_name(ticker) if 'company_name' in globals() else ticker)
    except Exception: name=ticker
    ident=f"{ticker} {name} {sector} {industry}".lower()
    _adaptive_template=get_thesis_template(ticker,name,sector,industry)
    _template_name=_adaptive_template["template"]
    def num(*keys):
        for k in keys:
            try:
                v=_mia_num(meta.get(k))
                if np.isfinite(v): return float(v)
            except Exception: pass
        return np.nan
    def pending(label,why="Evidence unavailable"):
        return (label,"Pending",why,"")
    def growth_row(label,key,*fallback_keys):
        e=stmt.get(key,{})
        v=_mia_num(e.get("value"))
        src=str(e.get("source") or "")
        if not np.isfinite(v):
            v=num(*fallback_keys)
            src="Market-data provider snapshot" if np.isfinite(v) else ""
        if not np.isfinite(v): return pending(label)
        return (label,"On track" if v>0 else "Watch",f"Growth {v:+.1%}",src)
    def margin_row(label="Operating margin"):
        if det:
            curpct=det.get("metrics",{}).get("Operating_Margin_Pct"); state=det.get("scorecard",{}).get("Operating_Margin_On_Track")
            if curpct is not None:
                return (label,"On track" if state is True else ("Watch" if state is False else "Pending"),f"Current margin {curpct:.2f}% · deterministic Python","Chrímata deterministic thesis engine")
        e=stmt.get("operating_margin",{}); cur=_mia_num(e.get("value")); prior=_mia_num(e.get("prior"))
        if np.isfinite(cur) and np.isfinite(prior):
            delta=cur-prior
            return (label,"On track" if delta>=0 else "Watch",f"{cur:.1%} vs {prior:.1%} prior ({delta:+.1%})",str(e.get("source") or "Provider statements"))
        cur=num("operatingMargins","operatingMargin")
        if np.isfinite(cur): return (label,"Pending",f"Current margin {cur:.1%}; prior comparison unavailable","Market-data provider snapshot")
        return pending(label)
    def fcf_row():
        if det:
            gpct=det.get("metrics",{}).get("Free_Cash_Flow_YoY_Pct"); state=det.get("scorecard",{}).get("Free_Cash_Flow_Growth_On_Track")
            if gpct is not None:
                return ("Free cash flow","On track" if state is True else ("Watch" if state is False else "Pending"),f"YoY {gpct:+.2f}% · deterministic Python","Chrímata deterministic thesis engine")
        e=stmt.get("free_cash_flow",{}); cur=_mia_num(e.get("value")); prior=_mia_num(e.get("prior")); g=_mia_num(e.get("growth"))
        if np.isfinite(cur) and np.isfinite(prior):
            return ("Free cash flow","On track" if cur>0 and (not np.isfinite(g) or g>=0) else "Watch",f"{compact_number(cur)} vs {compact_number(prior)} prior"+(f" ({g:+.1%})" if np.isfinite(g) else ""),str(e.get("source") or "Provider cash-flow statement"))
        cur=num("freeCashflow","freeCashFlow")
        if np.isfinite(cur): return ("Free cash flow","On track" if cur>0 else "Watch",f"Current {compact_number(cur)}","Market-data provider snapshot")
        return pending("Free cash flow")
    def roe_row():
        e=stmt.get("roe",{}); v=_mia_num(e.get("value")); src=str(e.get("source") or "")
        if not np.isfinite(v): v=num("returnOnEquity"); src="Market-data provider snapshot" if np.isfinite(v) else ""
        if not np.isfinite(v): return pending("Return on equity")
        # Positive ROE is evidence of positive return on equity; it is not a claim that ROE is improving.
        return ("Return on equity","On track" if v>0 else "Watch",f"{v:.1%}",src)
    def valuation_row():
        bv=_mia_num(base_value); cp=_mia_num(current_price)
        if not (np.isfinite(bv) and np.isfinite(cp) and cp>0): return pending("Valuation vs base case","Base valuation unavailable")
        gap=bv/cp-1
        return ("Valuation vs base case","On track" if gap>0 else "Watch",f"Base case {gap:+.0%} vs price","Chrímata valuation model")

    if "zip" in ident:
        # ZIP-specific items require ZIP-specific reported evidence. Generic EBITDA is
        # not treated as Cash EBITDA and generic credit fields are not treated as losses.
        rows=[pending("US TTV growth","ZIP-specific TTV evidence not loaded"),
              pending("Cash EBITDA growth","ZIP-specific Cash EBITDA comparison not loaded"),
              margin_row("Operating margin improvement"),
              pending("Credit losses / bad debts","ZIP-specific credit-loss evidence not loaded"),
              pending("NASDAQ listing catalyst","Catalyst evidence not loaded"),valuation_row()]
    elif _template_name=="airline":
        rows=[growth_row("Revenue growth","revenue_growth","revenueGrowth"),margin_row(),fcf_row(),
              pending("Capacity / demand trend","Airline operating KPI evidence not loaded"),
              pending("Fleet / fuel cost discipline","Airline cost KPI evidence not loaded")]
        de=num("debtToEquity")
        rows.append(("Balance-sheet leverage","On track" if de<150 else "Watch",f"Debt/equity {de:.0f}%","Market-data provider snapshot") if np.isfinite(de) else pending("Balance-sheet leverage"))
    elif _template_name=="consumer_brand":
        rows=[growth_row("Revenue growth","revenue_growth","revenueGrowth"),growth_row("Earnings growth","earnings_growth","earningsGrowth","earningsQuarterlyGrowth"),margin_row(),pending("Inventory health","Inventory trend evidence not loaded"),fcf_row(),roe_row()]
    elif _template_name=="bank":
        rows=[pending("Net interest margin","Bank KPI evidence not loaded"),pending("CET1 / capital strength","Bank capital evidence not loaded"),growth_row("Revenue growth","revenue_growth","revenueGrowth"),growth_row("Earnings growth","earnings_growth","earningsGrowth"),pending("Credit losses / bad debts","Bank credit-loss evidence not loaded"),roe_row()]
    elif _template_name=="mining":
        rows=[pending("Production trend","Production KPI evidence not loaded"),pending("Unit costs / AISC","Unit-cost evidence not loaded"),growth_row("Revenue growth","revenue_growth","revenueGrowth"),margin_row(),fcf_row(),pending("Reserves / resource quality","Resource evidence not loaded")]
    elif _template_name=="reit":
        rows=[pending("FFO / AFFO growth","REIT KPI evidence not loaded"),pending("Occupancy","Occupancy evidence not loaded"),pending("WALE / lease quality","Lease evidence not loaded"),fcf_row(),pending("Gearing","REIT gearing evidence not loaded"),pending("Distribution sustainability","Distribution evidence not loaded")]
    elif _template_name=="payments":
        rows=[growth_row("Revenue / transaction growth","revenue_growth","revenueGrowth"),growth_row("Earnings growth","earnings_growth","earningsGrowth","earningsQuarterlyGrowth"),margin_row(),pending("Credit losses / bad debts","Issuer credit-loss KPI evidence not loaded"),fcf_row(),pending("Guidance / catalyst execution","Guidance/catalyst evidence not loaded")]
    elif _template_name=="technology":
        rows=[growth_row("Revenue growth","revenue_growth","revenueGrowth"),growth_row("Earnings growth","earnings_growth","earningsGrowth","earningsQuarterlyGrowth"),margin_row(),fcf_row(),roe_row(),pending("Guidance / product execution","Guidance/product evidence not loaded")]
    else:
        rows=[growth_row("Revenue growth","revenue_growth","revenueGrowth"),growth_row("Earnings growth","earnings_growth","earningsGrowth","earningsQuarterlyGrowth"),margin_row(),fcf_row(),roe_row(),pending("Guidance / catalyst execution","Guidance/catalyst evidence not loaded")]
    return pd.DataFrame(rows[:6],columns=["metric","status","evidence","source"])

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

def _forecast_positive_probability(bt, predicted_return, max_neighbours=30):
    """Empirical probability from the closest out-of-sample model scores.

    This is deliberately withheld when the walk-forward sample is too small. It is
    not an analyst probability and it never uses future observations at forecast origin.
    """
    if bt is None or bt.empty or not np.isfinite(_mia_num(predicted_return)):
        return np.nan,0
    x=bt.copy()
    x["Ensemble"]=pd.to_numeric(x.get("Ensemble"),errors="coerce")
    x["Actual"]=pd.to_numeric(x.get("Actual"),errors="coerce")
    x=x.dropna(subset=["Ensemble","Actual"])
    if len(x)<12:return np.nan,len(x)
    x["distance"]=(x["Ensemble"]-float(predicted_return)).abs()
    n=min(max_neighbours,max(12,len(x)//2))
    near=x.nsmallest(n,"distance")
    return float((near["Actual"]>0).mean()),len(near)

def _forecast_validation_confidence(diag):
    """Conservative validation label from out-of-sample sample size and error evidence."""
    n=int(diag.get("n",0) or 0); direction=_mia_num(diag.get("direction")); mae=_mia_num(diag.get("mae"))
    if n<12:return "Validation limited"
    if n>=30 and np.isfinite(direction) and np.isfinite(mae) and direction>=.60 and mae<=.25:return "Higher validation"
    if n>=20 and np.isfinite(direction) and direction>=.55:return "Moderate validation"
    return "Limited validation"

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

@st.cache_data(ttl=1800, show_spinner=False)
@st.cache_data(ttl=21600, show_spinner=False)
def analyst_consensus_snapshot(ticker,current_price=np.nan):
    """Provider evidence → verified identity/normalization → deterministic target-return payload."""
    out={"label":"Unavailable","strongBuy":0,"buy":0,"hold":0,"sell":0,"strongSell":0,
         "analysts":0,"target":np.nan,"target_low":np.nan,"target_mean":np.nan,"target_median":np.nan,
         "target_high":np.nan,"source":"Yahoo Finance via yfinance","provider_date":"Unavailable","evidence":{}}
    try:
        t=yf.Ticker(ticker); meta=t.info or {}
        counts={}
        try:
            rec=getattr(t,"recommendations_summary",None)
            if rec is None or len(rec)==0: rec=t.get_recommendations()
            if rec is not None and len(rec):
                r=rec.iloc[0]
                counts={k:r.get(k,0) for k in ["strongBuy","buy","hold","sell","strongSell"]}
                for dk in ("period","date","Date"):
                    if dk in r and pd.notna(r.get(dk)): out["provider_date"]=str(r.get(dk)); break
        except Exception: pass
        pt={}
        try:
            raw=t.get_analyst_price_targets()
            if isinstance(raw,dict): pt=raw
        except Exception: pass

        # Selected listing first. No bridge is attempted unless provider explicitly supplies a candidate
        # and the existing conservative issuer verifier approves it.
        bridge={"status":"not_used","verified":False,"reason":"Selected listing analyst evidence used"}
        payload=build_analyst_payload(meta,counts,pt,current_price,ticker,bridge)
        if payload["status"]=="unavailable":
            candidate=_primary_listing_candidate(meta)
            if candidate and candidate!=str(ticker).upper():
                cmeta=_valuation_meta(candidate)
                bridge=bridge_payload(str(ticker).upper(),meta,candidate,cmeta)
                if bridge.get("verified"):
                    ct=yf.Ticker(candidate); ccounts={}; cpt={}
                    try:
                        cr=getattr(ct,"recommendations_summary",None)
                        if cr is None or len(cr)==0: cr=ct.get_recommendations()
                        if cr is not None and len(cr):
                            rr=cr.iloc[0]; ccounts={k:rr.get(k,0) for k in ["strongBuy","buy","hold","sell","strongSell"]}
                    except Exception: pass
                    try:
                        cp=ct.get_analyst_price_targets()
                        if isinstance(cp,dict): cpt=cp
                    except Exception: pass
                    # Do NOT guess ADR/depositary/share equivalence. Only explicit provider ratio fields qualify.
                    ratio=_mia_num(meta.get("shareRatio") or meta.get("depositaryReceiptRatio") or meta.get("adrRatio"))
                    fx=1.0
                    fc=cmeta.get("currency") or cmeta.get("financialCurrency"); lc=meta.get("currency")
                    if fc and lc and str(fc).upper()!=str(lc).upper(): fx=valuation_fx_rate(fc,lc)
                    bridged_meta=dict(cmeta); bridged_meta["currency"]=lc or cmeta.get("currency")
                    payload=build_analyst_payload(bridged_meta,ccounts,cpt,current_price,ticker,bridge,
                                                  fx_rate=fx if np.isfinite(_mia_num(fx)) else None,
                                                  security_ratio=ratio if np.isfinite(ratio) else None)
        out.update({"label":payload["consensus_label"],"analysts":payload["analyst_count"] or 0,
                    "target":payload["target_price"] if payload["target_price"] is not None else np.nan,
                    "target_low":payload["target_low"] if payload["target_low"] is not None else np.nan,
                    "target_mean":payload["target_price"] if payload["target_price"] is not None else np.nan,
                    "target_median":payload["target_median"] if payload["target_median"] is not None else np.nan,
                    "target_high":payload["target_high"] if payload["target_high"] is not None else np.nan,
                    "source":payload["source"],"evidence":payload["evidence"],
                    "percentage_return":payload["percentage_return"] if payload["percentage_return"] is not None else np.nan})
        out.update(payload["recommendation_counts"])
    except Exception as e:
        out["evidence"]={"ai_calculated":False,"error":str(e),"security":ticker}
    return out

def render_analyst_consensus(ticker,price):
    a=analyst_consensus_snapshot(ticker,price)
    st.subheader("Analyst consensus")
    st.caption("Provider-reported analyst evidence. Chrímata calculates only the target-versus-current-price percentage.")
    c=st.columns(4)
    metric_box(c[0],"Consensus",a["label"])
    metric_box(c[1],"Analysts",str(a["analysts"]) if a["analysts"] else "—")
    metric_box(c[2],"Mean target","—" if pd.isna(a["target_mean"]) else display_price(a["target_mean"],ticker))
    upside=_mia_num(a.get("percentage_return"))
    metric_box(c[3],"Mean target vs price","—" if not np.isfinite(upside) else f"{upside*100:+.1f}%")
    dist=pd.DataFrame({"Rating":["Strong Buy","Buy","Hold","Sell","Strong Sell"],
                       "Analysts":[a["strongBuy"],a["buy"],a["hold"],a["sell"],a["strongSell"]]})
    st.dataframe(dist,use_container_width=True,hide_index=True)
    ev=a.get("evidence",{}) or {}
    with st.expander("Provider evidence ⓘ",expanded=False):
        st.write(f"Security: {ev.get('security',ticker)}")
        st.write(f"Consensus: {a.get('label','Unavailable')} · Source: {ev.get('consensus_source','unavailable')}")
        st.write(f"Analyst count: {a.get('analysts') or '—'} · Source: {ev.get('analyst_count_source','unavailable')}")
        st.write(f"Recommendation bucket total: {ev.get('recommendation_bucket_total',0)} (shown separately from target analyst count)")
        st.write(f"Mean target: {'—' if pd.isna(a['target_mean']) else display_price(a['target_mean'],ticker)} · Source: {ev.get('target_source','unavailable')}")
        st.write(f"Target return: {'—' if not np.isfinite(upside) else f'{upside*100:+.1f}%'} · Source: {ev.get('target_return_source','unavailable')}")
        st.write(f"Target/listing currency: {ev.get('target_currency') or '—'} / {ev.get('listing_currency') or '—'}")
        br=ev.get("bridge",{}) or {}; st.write(f"Verified target bridge: {br.get('status','not_used')} · {br.get('target_bridge_status',br.get('reason','—'))}")
        st.write("AI calculated: No")
    if a["analysts"]==0 and all(pd.isna(a[k]) for k in ["target_low","target_mean","target_median","target_high"]):
        st.info("No verified analyst consensus or price-target evidence is available from the current provider for this security.")

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
    con.execute("""CREATE TABLE IF NOT EXISTS valuation_validation_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,snapshot_at TEXT,start_price REAL,
        bear_value REAL,base_value REAL,bull_value REAL,profile_updated_at TEXT,
        assumption_fingerprint TEXT,source TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS forecast_validation_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,ticker TEXT,snapshot_at TEXT,start_price REAL,
        horizon_days INTEGER,predicted_return REAL,target_price REAL,positive_probability REAL,
        validation_n INTEGER,direction_accuracy REAL,mae REAL,model_version TEXT,source TEXT)""")
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

@st.cache_data(ttl=3600, show_spinner=False)
def valuation_fx_rate(a,b):
 a=str(a or "").upper();b=str(b or "").upper()
 if not a or not b or a==b:return 1.0
 for pair,inv in ((f"{a}{b}=X",False),(f"{b}{a}=X",True)):
  try:
   d=yf.Ticker(pair).history(period="5d",interval="1d",auto_adjust=True);v=float(pd.to_numeric(d["Close"],errors="coerce").dropna().iloc[-1])
   if np.isfinite(v) and v>0:return 1/v if inv else v
  except Exception:pass
 return np.nan
@st.cache_data(ttl=21600, show_spinner=False)
def valuation_statement_bundle(ticker):
    """Return the richest available Yahoo statements; quarterly can expose fresher/TTM evidence."""
    try:
        t=yf.Ticker(ticker)
        def richest(*frames):
            valid=[x for x in frames if isinstance(x,pd.DataFrame) and not x.empty]
            return max(valid,key=lambda x:(x.notna().sum().sum(),x.shape[0]*x.shape[1])) if valid else pd.DataFrame()
        return (richest(getattr(t,"quarterly_cashflow",pd.DataFrame()),getattr(t,"cashflow",pd.DataFrame())),
                richest(getattr(t,"quarterly_balance_sheet",pd.DataFrame()),getattr(t,"balance_sheet",pd.DataFrame())),
                richest(getattr(t,"quarterly_financials",pd.DataFrame()),getattr(t,"financials",pd.DataFrame())))
    except Exception:
        return pd.DataFrame(),pd.DataFrame(),pd.DataFrame()

def _primary_listing_candidate(meta):
    """Only provider-explicit primary/underlying symbols are considered. Never guess by stripping suffixes."""
    for k in ("underlyingSymbol","primarySymbol","primaryTicker"):
        v=(meta or {}).get(k)
        if v and str(v).strip(): return str(v).strip().upper()
    return None

@st.cache_data(ttl=21600, show_spinner=False)
def _valuation_meta(ticker):
    try:return yf.Ticker(ticker).info or {}
    except Exception:return {}

@st.cache_data(ttl=3600, show_spinner=False)
def _compact_valuation_blocker(audit, fallback="Evidence required"):
    """Card-safe diagnostic label. Full blocking reason remains on the Valuation diagnostics page."""
    audit=audit if isinstance(audit,dict) else {}
    inputs=audit.get("inputs",{}) if isinstance(audit.get("inputs",{}),dict) else {}
    fcf=inputs.get("fcf",{}) if isinstance(inputs.get("fcf",{}),dict) else {}
    shares=inputs.get("shares",{}) if isinstance(inputs.get("shares",{}),dict) else {}
    if fcf.get("status")=="missing" or not (audit.get("eligibility_checks",{}) or {}).get("positive_fcf",False):
        return "FCF unavailable"
    if shares.get("status")=="missing" or not (audit.get("eligibility_checks",{}) or {}).get("shares_available",False):
        return "Shares unavailable"
    if not (audit.get("eligibility_checks",{}) or {}).get("currency_aligned",False):
        return "FX / currency unavailable"
    blockers=audit.get("blocking_reasons") or []
    if blockers:
        text=str(blockers[0]).strip()
        compact={"Positive Free Cash Flow unavailable":"FCF unavailable",
                 "Shares outstanding unavailable":"Shares unavailable",
                 "Currency pair/FX unavailable":"FX / currency unavailable"}.get(text)
        if compact:return compact
        return (text[:25].rstrip()+"…") if len(text)>26 else text
    return fallback

def valuation_pipeline(ticker,price):
    """Single source of truth for automatic valuation and its live diagnostics."""
    selected_ticker=str(ticker or "").upper().strip()
    meta=_valuation_meta(selected_ticker) if selected_ticker else {}
    cf,bs,inc=valuation_statement_bundle(selected_ticker) if selected_ticker else (pd.DataFrame(),pd.DataFrame(),pd.DataFrame())
    _vmeta=dict(meta or {})
    if not _mia_num(_vmeta.get("sharesOutstanding")) and selected_ticker:
        try:
            _sh=shares_history(selected_ticker)
            if _sh is not None and len(_sh):
                _vmeta["sharesOutstanding"]=float(pd.to_numeric(_sh,errors="coerce").dropna().iloc[-1])
                _vmeta["_shares_source"]="provider_shares_history"
        except Exception: pass
    recovered=recover_financial_inputs(_vmeta,cf,bs,inc)
    if _vmeta.get("_shares_source") and recovered.get("audit",{}).get("inputs",{}).get("shares",{}).get("status")=="verified":
        recovered["audit"]["inputs"]["shares"]["source"]=_vmeta["_shares_source"]

    bridge={"status":"not_used","verified":False,"reason":"Selected listing evidence used","ai_calculated":False}
    if not recovered["audit"].get("complete_for_dcf") and selected_ticker:
        candidate=_primary_listing_candidate(_vmeta)
        if candidate and candidate!=selected_ticker:
            cmeta=_valuation_meta(candidate)
            bridge=bridge_payload(selected_ticker,_vmeta,candidate,cmeta)
            if bridge.get("verified"):
                ccf,cbs,cinc=valuation_statement_bundle(candidate)
                crecovered=recover_financial_inputs(cmeta,ccf,cbs,cinc)
                if crecovered["audit"].get("complete_for_dcf"):
                    crecovered["listing_currency"]=_vmeta.get("currency") or recovered.get("listing_currency")
                    crecovered["audit"]["bridge"]=bridge
                    recovered=crecovered

    fc=recovered.get("financial_currency"); lc=recovered.get("listing_currency")
    fx=1.0
    if fc and lc and str(fc).upper()!=str(lc).upper():
        fx=valuation_fx_rate(fc,lc)
    result=calculate_dcf_scenarios(recovered.get("fcf"),recovered.get("shares"),recovered.get("cash"),recovered.get("debt"),
        current_price=price,sector=recovered.get("sector",""),industry=recovered.get("industry",""),
        financial_currency=fc,listing_currency=lc,
        fx_rate_financial_to_listing=fx if np.isfinite(_mia_num(fx)) else None)

    audit=recovered.get("audit",{})
    audit["selected_ticker"]=selected_ticker
    audit["metadata_received"]=bool(_vmeta)
    audit["statement_rows"]={
        "cash_flow":list(map(str,cf.index[:80])) if isinstance(cf,pd.DataFrame) and not cf.empty else [],
        "balance_sheet":list(map(str,bs.index[:80])) if isinstance(bs,pd.DataFrame) and not bs.empty else [],
        "income_statement":list(map(str,inc.index[:80])) if isinstance(inc,pd.DataFrame) and not inc.empty else [],
    }
    audit["primary_listing_bridge"]=bridge
    audit["fx"]={"status":"not_required" if fc and lc and str(fc).upper()==str(lc).upper() else ("verified" if np.isfinite(_mia_num(fx)) else "missing"),
                 "from":fc,"to":lc,"rate":float(fx) if np.isfinite(_mia_num(fx)) else None,
                 "source":"Yahoo Finance FX" if np.isfinite(_mia_num(fx)) and fx!=1 else None}
    checks={
        "positive_fcf": bool(_mia_num(recovered.get("fcf"))>0) if np.isfinite(_mia_num(recovered.get("fcf"))) else False,
        "shares_available": bool(_mia_num(recovered.get("shares"))>0) if np.isfinite(_mia_num(recovered.get("shares"))) else False,
        "currency_aligned": bool(fc and lc and (str(fc).upper()==str(lc).upper() or np.isfinite(_mia_num(fx))))
    }
    audit["eligibility_checks"]=checks
    blockers=[]
    if not checks["positive_fcf"]: blockers.append("Positive Free Cash Flow unavailable")
    if not checks["shares_available"]: blockers.append("Shares outstanding unavailable")
    if not checks["currency_aligned"]: blockers.append("Currency pair/FX unavailable")
    if result.get("status")!="success" and result.get("reason"): blockers.append(str(result.get("reason")))
    audit["dcf_status"]="READY" if result.get("status")=="success" else "BLOCKED"
    audit["blocking_reasons"]=list(dict.fromkeys(blockers))
    audit["ai_calculated"]=False
    result["audit"]=audit
    result["recovered_inputs"]=recovered
    result["provider_meta"]={k:_vmeta.get(k) for k in ("longName","symbol","currency","financialCurrency","sector","industry")}
    return result

def automatic_valuation_snapshot(meta,price,ticker=None):
    # Compatibility wrapper: all consumers now resolve through the ticker-keyed single-source pipeline.
    selected_ticker=str(ticker or (meta or {}).get("symbol") or "").upper().strip()
    return valuation_pipeline(selected_ticker,float(price) if np.isfinite(_mia_num(price)) else np.nan)

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

def valuation_profile_saved(ticker):
    """True only when this ticker has an explicitly saved valuation profile."""
    v18_db_upgrade(); con=ws_db()
    try:
        row=con.execute("SELECT updated_at FROM valuation_profiles WHERE ticker=?",(ticker,)).fetchone()
        return bool(row and row[0]), (row[0] if row else None)
    finally:
        con.close()

def _valuation_fingerprint(profile):
    import hashlib
    keys=["fcf","shares","net_debt","bear_growth","base_growth","bull_growth","bear_wacc","base_wacc","bull_wacc","bear_terminal","base_terminal","bull_terminal"]
    raw="|".join(f"{k}={float(profile.get(k,0)):.10g}" for k in keys)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def record_valuation_validation_snapshot(ticker,price,vals,force=False):
    """Persist a point-in-time valuation without backfilling history or using future information."""
    saved,updated_at=valuation_profile_saved(ticker)
    if not saved or not np.isfinite(_mia_num(price)) or vals is None or vals.empty:
        return False,"Save company-specific valuation assumptions before validation begins."
    profile=valuation_profile(ticker); fp=_valuation_fingerprint(profile)
    def scen(name):
        try:
            q=vals[vals["Scenario"].astype(str).str.lower()==name.lower()]
            return _mia_num(q["value_per_share"].iloc[0]) if not q.empty else np.nan
        except Exception:return np.nan
    bear,base,bull=scen("Bear"),scen("Base"),scen("Bull")
    if not np.isfinite(base): return False,"Base valuation is unavailable."
    now=datetime.now(timezone.utc); day=now.date().isoformat()
    v18_db_upgrade(); con=ws_db()
    try:
        if not force:
            exists=con.execute("""SELECT 1 FROM valuation_validation_snapshots
                                  WHERE ticker=? AND substr(snapshot_at,1,10)=? AND assumption_fingerprint=? LIMIT 1""",
                               (ticker,day,fp)).fetchone()
            if exists:return False,"Today's snapshot for these assumptions is already stored."
        con.execute("""INSERT INTO valuation_validation_snapshots
            (ticker,snapshot_at,start_price,bear_value,base_value,bull_value,profile_updated_at,assumption_fingerprint,source)
            VALUES(?,?,?,?,?,?,?,?,?)""",
            (ticker,now.isoformat(),float(price),bear,base,bull,updated_at,fp,"Chrímata valuation profile"))
        con.commit(); return True,"Point-in-time valuation snapshot recorded."
    finally:con.close()

def valuation_validation_snapshots(ticker=None):
    v18_db_upgrade(); con=ws_db()
    try:
        if ticker:
            return pd.read_sql_query("SELECT * FROM valuation_validation_snapshots WHERE ticker=? ORDER BY snapshot_at",con,params=(ticker,))
        return pd.read_sql_query("SELECT * FROM valuation_validation_snapshots ORDER BY snapshot_at",con)
    except Exception:
        return pd.DataFrame()
    finally:con.close()

def valuation_validation_results(ticker):
    """Evaluate only snapshots whose future market observations now exist. No look-ahead backfill."""
    snaps=valuation_validation_snapshots(ticker)
    if snaps.empty:return pd.DataFrame()
    hist=history(ticker,"5y")
    if hist is None or hist.empty or "Close" not in hist:return pd.DataFrame()
    hp=pd.DataFrame({"date":pd.to_datetime(hist.index,utc=True,errors="coerce"),"close":pd.to_numeric(hist["Close"],errors="coerce")}).dropna().sort_values("date")
    horizons=[(21,"1M"),(63,"3M"),(126,"6M"),(252,"12M")]; rows=[]
    for _,r in snaps.iterrows():
        dt=pd.to_datetime(r["snapshot_at"],utc=True,errors="coerce")
        after=hp[hp["date"]>=dt.normalize()]
        if after.empty:continue
        # first session on/after snapshot anchors the evaluation; stored start_price remains the decision-time quote.
        for sessions,label in horizons:
            if len(after)<=sessions:continue
            future=float(after.iloc[sessions]["close"]); start=_mia_num(r["start_price"]); base=_mia_num(r["base_value"])
            bear=_mia_num(r["bear_value"]); bull=_mia_num(r["bull_value"])
            if not (np.isfinite(start) and np.isfinite(base) and start>0 and future>0):continue
            predicted=np.sign(base-start); realised=np.sign(future-start)
            direction=(predicted==realised) if predicted!=0 else (abs(future/start-1)<.02)
            lo=min(bear,bull) if np.isfinite(bear) and np.isfinite(bull) else np.nan
            hi=max(bear,bull) if np.isfinite(bear) and np.isfinite(bull) else np.nan
            rows.append({"Snapshot":dt.date().isoformat(),"Horizon":label,"Start Price":start,"Base":base,"Future Price":future,
                         "Base Error %":abs(base/future-1)*100,"Direction Correct":bool(direction),
                         "Future In Bear-Bull Range":bool(lo<=future<=hi) if np.isfinite(lo) else np.nan})
    return pd.DataFrame(rows)

def valuation_validation_summary(ticker):
    r=valuation_validation_results(ticker)
    if r.empty:return {"Observations":0,"Median Error":np.nan,"Direction Accuracy":np.nan,"Range Hit":np.nan}
    return {"Observations":len(r),"Median Error":float(r["Base Error %"].median()),
            "Direction Accuracy":float(r["Direction Correct"].mean()),
            "Range Hit":float(pd.to_numeric(r["Future In Bear-Bull Range"],errors="coerce").mean())}

def record_forecast_validation_snapshot(ticker,start_price,row,bt,force=False):
    """Store one point-in-time 12M model forecast per ticker/day/model version."""
    if row is None:return False,"Forecast unavailable."
    pred=_mia_num(row.get("Ensemble expected return")); target=_mia_num(row.get("Estimated price"))
    if not (np.isfinite(_mia_num(start_price)) and np.isfinite(pred) and np.isfinite(target)):
        return False,"Forecast unavailable."
    diag=_forecast_diagnostics(bt); prob,_pn=_forecast_positive_probability(bt,pred)
    now=datetime.now(timezone.utc); day=now.date().isoformat(); model_version="ChrimataForecast-21.2.76"
    v18_db_upgrade(); con=ws_db()
    try:
        if not force:
            exists=con.execute("SELECT 1 FROM forecast_validation_snapshots WHERE ticker=? AND substr(snapshot_at,1,10)=? AND model_version=? LIMIT 1",(ticker,day,model_version)).fetchone()
            if exists:return False,"Today's forecast snapshot is already stored."
        con.execute("""INSERT INTO forecast_validation_snapshots
            (ticker,snapshot_at,start_price,horizon_days,predicted_return,target_price,positive_probability,validation_n,direction_accuracy,mae,model_version,source)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ticker,now.isoformat(),float(start_price),252,pred,target,prob,int(diag.get("n",0) or 0),_mia_num(diag.get("direction")),_mia_num(diag.get("mae")),model_version,"Chrímata walk-forward ensemble"))
        con.commit();return True,"Forecast validation snapshot recorded."
    finally:con.close()

def forecast_validation_results(ticker):
    v18_db_upgrade(); con=ws_db()
    try:d=pd.read_sql_query("SELECT * FROM forecast_validation_snapshots WHERE ticker=? ORDER BY snapshot_at",con,params=(ticker,))
    except Exception:d=pd.DataFrame()
    finally:con.close()
    if d.empty:return pd.DataFrame()
    hist=history(ticker,"5y")
    if hist is None or hist.empty or "Close" not in hist:return pd.DataFrame()
    hp=pd.DataFrame({"date":pd.to_datetime(hist.index,utc=True,errors="coerce"),"close":pd.to_numeric(hist["Close"],errors="coerce")}).dropna().sort_values("date")
    rows=[]
    for _,r in d.iterrows():
        dt=pd.to_datetime(r["snapshot_at"],utc=True,errors="coerce"); after=hp[hp["date"]>=dt.normalize()]
        h=int(r.get("horizon_days") or 252)
        if len(after)<=h:continue
        future=float(after.iloc[h]["close"]); start=_mia_num(r["start_price"]); target=_mia_num(r["target_price"]); pred=_mia_num(r["predicted_return"]); prob=_mia_num(r["positive_probability"])
        if not (np.isfinite(start) and start>0 and np.isfinite(future)):continue
        realised=future/start-1
        rows.append({"Snapshot":dt.date().isoformat(),"Start Price":start,"Target":target,"Future Price":future,"Predicted Return":pred,"Realised Return":realised,"Target Error %":abs(target/future-1)*100 if np.isfinite(target) else np.nan,"Direction Correct":bool((pred>0)==(realised>0)) if np.isfinite(pred) else np.nan,"Predicted Positive Probability":prob,"Realised Positive":bool(realised>0),"Model Version":r.get("model_version")})
    return pd.DataFrame(rows)

def forecast_validation_summary(ticker):
    r=forecast_validation_results(ticker)
    if r.empty:return {"Observations":0,"Median Target Error":np.nan,"Direction Accuracy":np.nan,"Brier Score":np.nan}
    p=pd.to_numeric(r["Predicted Positive Probability"],errors="coerce"); y=pd.to_numeric(r["Realised Positive"],errors="coerce"); ok=p.notna()&y.notna()
    return {"Observations":len(r),"Median Target Error":float(pd.to_numeric(r["Target Error %"],errors="coerce").median()),"Direction Accuracy":float(pd.to_numeric(r["Direction Correct"],errors="coerce").mean()),"Brier Score":float(np.mean((p[ok]-y[ok])**2)) if ok.any() else np.nan}

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
        try: meta=info(ticker) or {}
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
        try: meta=info(ticker) or {}
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
[data-testid="stBottom"],[data-testid="stBottomBlockContainer"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;}
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
# V21.2.11 — listing-aware Command Centre deep links.
# chr_cc duplicates the current research context in a new tab. chr_compare opens
# the dedicated comparison workspace with the originating listing preloaded.
try:
    _chr_cc_deep=str(st.query_params.get("chr_cc") or "").strip().upper()
    _chr_compare_deep=str(st.query_params.get("chr_compare") or "").strip().upper()
    _chr_deep_sig=(
        f"cc:{_chr_cc_deep}:{str(st.query_params.get('chr_cc_page') or 'Overview')}" if _chr_cc_deep
        else (f"compare:{_chr_compare_deep}" if _chr_compare_deep else "")
    )
    _chr_deep_new=bool(_chr_deep_sig and st.session_state.get("chr_consumed_deep_link_v21221")!=_chr_deep_sig)
    if _chr_cc_deep and _chr_deep_new:
        st.session_state["chr_consumed_deep_link_v21221"]=_chr_deep_sig
        st.session_state["chr_active_ticker"]=_chr_cc_deep
        st.session_state["mia_search_query"]=_chr_cc_deep
        st.session_state["chr_primary_nav"]="Company Command Centre"
        st.session_state["chr_cc_sub_v21001"]=str(st.query_params.get("chr_cc_page") or "Overview")
    elif _chr_compare_deep and _chr_deep_new:
        st.session_state["chr_consumed_deep_link_v21221"]=_chr_deep_sig
        st.session_state["chr_active_ticker"]=_chr_compare_deep
        st.session_state["mia_search_query"]=_chr_compare_deep
        st.session_state["chr_primary_nav"]="Company Command Centre"
    elif st.query_params.get("chr_pick") is not None:
        st.session_state["chr_primary_nav"]="Company Search"
except Exception:
    _chr_cc_deep=""; _chr_compare_deep=""
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
# V20.7.4.19.1 — Navigation State Synchronisation Fix.
# Streamlit button callbacks run before the script body on the interaction rerun.
# Updating the single authoritative route in the callback means the sidebar
# highlight and page router read the SAME state during the SAME render.
_CHR_LEGAL_PAGES={"About","Privacy","Disclaimer","Terms","Data Sources","Contact"}

def _chr_clear_legal_route_v21300():
    st.session_state.pop("chr_legal_page", None)
    try:
        if "chr_legal" in st.query_params:
            del st.query_params["chr_legal"]
    except Exception:
        pass

def _chr_set_legal_route_v21300(target):
    if target in _CHR_LEGAL_PAGES:
        st.session_state["chr_legal_page"]=target

def _chr_set_primary_nav_v2074191(target):
    if target in _valid_nav:
        _chr_clear_legal_route_v21300()
        st.session_state["chr_primary_nav"]=target
        # V21.2.22 — a Command Centre deep-link query is only an entry route.
        # Once the user deliberately chooses another sidebar page, remove the
        # stale deep-link parameters so the next Streamlit rerun cannot force
        # Company Command Centre open again.
        if target != "Company Command Centre":
            try:
                for _qp in ("chr_cc","chr_cc_page","chr_compare"):
                    if _qp in st.query_params:
                        del st.query_params[_qp]
            except Exception:
                pass

# V21.1.1 — integrated Company Command Centre navigation.
_cc_sub_key="chr_cc_sub_v21001"
_cc_items=["Overview","Fundamentals","Valuation","Technical","Announcements & Reports","Report Intelligence","News & Events","Thesis Scorecard","Catalyst Calendar","Quant","Forecasts"]
if st.session_state.get(_cc_sub_key) not in _cc_items:
    st.session_state[_cc_sub_key]="Overview"
@st.cache_data(ttl=600, show_spinner=False)
def overview_news_safe(ticker, limit=5):
    """V21.3.13 — dynamic ticker-driven company news preview."""
    try:
        df,_=latest_company_news(ticker,limit)
        if df is None or df.empty: return pd.DataFrame(columns=["Date","Headline","Source","URL"])
        return df[["Date","Headline","Source","URL"]].head(limit).copy()
    except Exception:
        return pd.DataFrame(columns=["Date","Headline","Source","URL"])

def _chr_set_cc_sub_v2111(target):
    """Deterministic in-app Command Centre navigation (V21.3.07)."""
    if target in _cc_items:
        _chr_clear_legal_route_v21300()
        st.session_state["chr_primary_nav"]="Company Command Centre"
        st.session_state[_cc_sub_key]=target
        # Deep-link query params are entry routes only. Remove them so they can
        # never overwrite a deliberate in-app subpage transition on rerun.
        try:
            for _qp in ("chr_cc","chr_cc_page","chr_compare","chr_pick"):
                if _qp in st.query_params:
                    del st.query_params[_qp]
        except Exception:
            pass

st.sidebar.markdown(r'''<style>
/* V21.1.5 — unified icon + text Command Centre child rows.
   Each child is one positioned button row: icon at 12px, label at 46px.
   This deliberately overrides the older global sidebar rule that absolutely
   positions every button label at 45px. */
[data-testid="stSidebar"] .ccnav-inline-start{height:2px!important;margin:0!important;padding:0!important}
[data-testid="stSidebar"] [class*="st-key-ccinline_"]{margin:0 8px 1px 18px!important;padding:0!important;width:calc(100% - 26px)!important}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton{margin:0!important;padding:0!important;width:100%!important}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button{
  position:relative!important;display:block!important;width:100%!important;
  height:31px!important;min-height:31px!important;margin:0!important;padding:0!important;
  border:0!important;border-radius:5px!important;box-shadow:none!important;
  overflow:hidden!important;text-align:left!important;white-space:nowrap!important;
}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button[kind="secondary"]{background:transparent!important;color:#eef6ff!important}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button[kind="secondary"]:hover{background:rgba(255,255,255,.075)!important;color:#fff!important}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button[kind="primary"]{background:#1687ef!important;color:#fff!important}
/* Icon and label share the SAME button coordinate system. */
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button [data-testid="stIconMaterial"],
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button span[data-testid="stIconMaterial"]{
  position:absolute!important;left:10px!important;top:50%!important;transform:translateY(-50%)!important;
  display:flex!important;align-items:center!important;justify-content:center!important;
  width:24px!important;height:22px!important;margin:0!important;padding:0!important;
  font-size:20px!important;line-height:20px!important;color:#fff!important;
}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button [data-testid="stMarkdownContainer"]{
  position:absolute!important;left:44px!important;right:6px!important;top:50%!important;
  transform:translateY(-50%)!important;width:auto!important;max-width:none!important;
  margin:0!important;padding:0!important;text-align:left!important;overflow:hidden!important;
}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button [data-testid="stMarkdownContainer"] p{
  position:static!important;margin:0!important;padding:0!important;text-align:left!important;
  font-size:11.2px!important;line-height:1!important;font-weight:550!important;
  white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
}
[data-testid="stSidebar"] [class*="st-key-ccinline_"] .stButton>button [data-testid="stMarkdownContainer"]:after{display:none!important;content:none!important}
</style>''',unsafe_allow_html=True)
# V21.1.2 — authoritative sidebar renderer.
# The Command Centre and its children live in ONE Streamlit container placed
# between Company Search and Markets.  This makes DOM/render order explicit
# instead of relying on interleaved root-level sidebar deltas.
_material_icons={"home":":material/home:","search":":material/search:","document":":material/description:","chart":":material/monitoring:","star":":material/star_outline:","briefcase":":material/business_center:","screen":":material/filter_alt:","bell":":material/notifications_none:","calendar":":material/calendar_month:","research":":material/query_stats:","settings":":material/settings:"}

def _chr_render_primary_nav_item_v2112(idx, item):
    _key,_icon,_title,_sub=item
    _active=(_key==primary)
    _clean_title=_title.split("  ",1)[-1]
    st.button(_clean_title,key=f"chr_nav_native_{idx}",use_container_width=True,
              type="primary" if _active else "secondary",
              icon=_material_icons.get(_icon),
              on_click=_chr_set_primary_nav_v2074191,args=(_key,))

def _chr_render_cc_children_v2112():
    # V21.1.3: one compact flat child list. The parent already establishes
    # context, so category labels only consumed space and collided with names.
    _cc_order=[
        ("Overview",":material/dashboard:"),
        ("Fundamentals",":material/account_balance:"),
        ("Valuation",":material/show_chart:"),
        ("Technical",":material/monitoring:"),
        ("Announcements & Reports",":material/article:"),
        ("Report Intelligence",":material/travel_explore:"),
        ("News & Events",":material/newspaper:"),
        ("Thesis Scorecard",":material/fact_check:"),
        ("Catalyst Calendar",":material/calendar_month:"),
        ("Quant",":material/query_stats:"),
        ("Forecasts",":material/layers:"),
    ]
    st.markdown('<div class="ccnav-inline-start"></div>',unsafe_allow_html=True)
    for _cc_i,(_item,_item_icon) in enumerate(_cc_order):
        st.button(_item,key=f"ccinline_{_cc_i}",use_container_width=True,
                  type="primary" if st.session_state[_cc_sub_key]==_item else "secondary",
                  icon=_item_icon,
                  on_click=_chr_set_cc_sub_v2111,args=(_item,))

st.sidebar.markdown('<nav class="chr-nav chr-nav-native" aria-label="Chrímata navigation">',unsafe_allow_html=True)
# Top-level entries that must precede the Command Centre.
with st.sidebar.container():
    _chr_render_primary_nav_item_v2112(0,NAV_ITEMS[0])
    _chr_render_primary_nav_item_v2112(1,NAV_ITEMS[1])

# Authoritative Command Centre block: parent and all 11 children are emitted
# inside the same container, so no later primary item can render between them.
with st.sidebar.container():
    _chr_render_primary_nav_item_v2112(2,NAV_ITEMS[2])
    if primary=="Company Command Centre":
        _chr_render_cc_children_v2112()

# All remaining global navigation follows the complete Command Centre block.
with st.sidebar.container():
    for _idx in range(3,len(NAV_ITEMS)):
        _chr_render_primary_nav_item_v2112(_idx,NAV_ITEMS[_idx])
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
    # V21.1.1 — submenu is rendered inline directly beneath Company Command Centre.
    if primary=="Company Command Centre":
        sub=st.session_state.get(_cc_sub_key,"Overview")
    else:
        sub=st.sidebar.selectbox("Inside this workspace",SUBPAGES[primary],key=f"chr_sub_v209_{primary}")
    page=PAGE_MAP[(primary,sub)]
else: page=primary

# V21.3.00 — unified legal navigation: session state is authoritative.
_chr_legal_page=st.session_state.get("chr_legal_page")
if _chr_legal_page in _CHR_LEGAL_PAGES:
    page=_chr_legal_page

# Comparison is a utility workspace, not a twelfth Command Centre research engine.
try:
    if str(st.query_params.get("chr_compare") or "").strip():
        page="Company Comparison"
except Exception:
    pass

st.sidebar.markdown("""<div class="chr-side-spacer"></div><div class="chr-side-wealth"><span class="wealth-pillar"><svg viewBox="0 0 48 64" aria-hidden="true"><path d="M8 8h32M11 12h26M14 16h20M14 48h20M11 52h26M8 56h32"/><path d="M16 17v30M22 17v30M26 17v30M32 17v30"/><path d="M10 6h28l-3-3H13zM10 58h28l3 3H7z"/></svg></span><span class="wealth-copy">KNOWLEDGE<br>COMPOUNDS<br>WEALTH</span></div><div class="chr-side-copyright">© 2026 Chrímata. All rights reserved.</div>""",unsafe_allow_html=True)

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
if page not in {"Dashboard","Company Search","Company Command Centre"}:
    st.markdown(f"""<div class="mia-shell-head">
<div><div class="mia-eyebrow">Chrímata / {primary}</div>
<div class="mia-shell-title">{page}</div><div class="mia-shell-sub">{_shell_sub}</div></div>
<div class="mia-live"><span class="mia-dot"></span> Research workspace</div>
</div>""",unsafe_allow_html=True)

# V20.7.4.19 — Route-aware data loading. Home and Company Search do not need
# the active company's 5Y history/info just to render their own workspace.
# Skipping these provider calls materially reduces cross-page navigation latency.
if page in {"Dashboard","Company Search"}:
    h=pd.DataFrame(); meta={}
else:
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

if page not in {"Dashboard","Company Search","Company Command Centre"}:
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
    function draw(animate=true){{const q=(data[key]||{{}})[range]||Object.values(data[key]||{{}})[0];if(!q)return;const c=root.querySelector('#chart');if(animate)c.classList.add('fade');setTimeout(()=>{{root.querySelector('#ctitle').textContent=q.label+' '+(range==='1D'?'Intraday Chart':range+' Chart');const svgBox=root.querySelector('#svg');svgBox.innerHTML=q.svg;const lastEl=root.querySelector('#last'),prevEl=root.querySelector('.prev');lastEl.textContent=q.last;lastEl.style.color=q.up?'#10b96a':'#ef4444';root.querySelector('#prev').textContent=q.prev;const plotTop=svgBox.offsetTop,plotH=svgBox.clientHeight;let lastTop=Number.isFinite(q.lastY)?plotTop+plotH*q.lastY:null,prevTop=Number.isFinite(q.prevY)?plotTop+plotH*q.prevY:null;const minGap=34,topLimit=plotTop+14,bottomLimit=plotTop+plotH-14;if(lastTop!==null&&prevTop!==null&&Math.abs(lastTop-prevTop)<minGap){{if(lastTop<=prevTop){{lastTop=Math.max(topLimit,lastTop-minGap/2);prevTop=Math.min(bottomLimit,prevTop+minGap/2);if(prevTop-lastTop<minGap)lastTop=Math.max(topLimit,prevTop-minGap);}}else{{prevTop=Math.max(topLimit,prevTop-minGap/2);lastTop=Math.min(bottomLimit,lastTop+minGap/2);if(lastTop-prevTop<minGap)prevTop=Math.max(topLimit,lastTop-minGap);}}}}if(lastTop!==null)lastEl.style.top=Math.max(topLimit,Math.min(bottomLimit,lastTop))+'px';if(prevTop!==null)prevEl.style.top=Math.max(topLimit,Math.min(bottomLimit,prevTop))+'px';root.querySelector('#xaxis').innerHTML=(labels[range]||[]).map(x=>'<span>'+x+'</span>').join('');c.classList.remove('fade');}},animate?120:0)}}
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
            _parts=[x.strip() for x in str(selected).split(" · ")]
            st.session_state["chr_active_exchange"]=_parts[-2] if len(_parts)>=3 else ""
            st.session_state["chr_active_country"]=_parts[-1] if len(_parts)>=2 else ""
            st.session_state["chr_primary_nav"]="Company Command Centre"
            # Consume each autocomplete selection once; URL state is not used.
            st.session_state["chr_last_search_commit_v2054"]=resolved
            st.rerun()

def _chr_detect_home_market_v21222():
    """Choose a country-level Home market from browser timezone/locale only.

    No GPS, street address, or precise geolocation is requested. The result is only
    a first-visit default; an explicit user market choice remains authoritative.
    """
    tz = ""
    locale = ""
    try:
        tz = str(getattr(st.context, "timezone", "") or "")
    except Exception:
        pass
    try:
        locale = str(getattr(st.context, "locale", "") or "")
    except Exception:
        pass

    tz_map = {
        # Australia
        "Australia/Sydney":"Australia", "Australia/Melbourne":"Australia",
        "Australia/Brisbane":"Australia", "Australia/Adelaide":"Australia",
        "Australia/Perth":"Australia", "Australia/Hobart":"Australia",
        "Australia/Darwin":"Australia", "Australia/Broken_Hill":"Australia",
        # United States
        "America/New_York":"United States", "America/Chicago":"United States",
        "America/Denver":"United States", "America/Los_Angeles":"United States",
        "America/Phoenix":"United States", "America/Anchorage":"United States",
        "Pacific/Honolulu":"United States",
        # Supported international markets
        "Europe/London":"United Kingdom",
        "Asia/Tokyo":"Japan",
        "Asia/Hong_Kong":"Hong Kong",
        "America/Toronto":"Canada", "America/Vancouver":"Canada",
        "America/Edmonton":"Canada", "America/Winnipeg":"Canada",
        "America/Halifax":"Canada", "America/St_Johns":"Canada",
    }
    if tz in tz_map:
        return tz_map[tz]
    # Locale is deliberately a fallback because language/region preference can differ
    # from physical location. Timezone therefore wins whenever it is available.
    region = locale.replace("_", "-").split("-")[-1].upper() if "-" in locale or "_" in locale else ""
    return {"AU":"Australia", "US":"United States", "GB":"United Kingdom",
            "JP":"Japan", "HK":"Hong Kong", "CA":"Canada"}.get(region, "Australia")

@st.fragment(run_every="60s")
def render_global_market_overview():
    # V21.2.22 — Home Market Localisation Engine. Detect once per browser session.
    # Explicit user choices always win after the initial seed.
    if "home_market_v2021" not in st.session_state:
        st.session_state.home_market_v2021=_chr_detect_home_market_v21222()
        st.session_state["chr_home_market_auto_v21222"]=True
    # V20.3.0: query-param navigation uses plain HTML anchors instead of Streamlit
    # buttons. This guarantees the reference white-card appearance and real flags.
    # V20.7.4.19 — session state is authoritative during in-app navigation.
    # Import the URL market only once per browser session (deep-link support), then
    # stop a stale query parameter from overwriting later country-button choices.
    if "chr_home_market_url_seeded_v207419" not in st.session_state:
        try:
            qp_market=st.query_params.get("market")
            if qp_market in MARKET_OVERVIEW_CONFIG:
                st.session_state.home_market_v2021=qp_market
        except Exception:
            pass
        st.session_state["chr_home_market_url_seeded_v207419"]=True
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
                        # V20.7.4.19 — single-pass country switching. The button
                        # interaction already triggered this run, so update local/session
                        # state and continue directly into the selected market render.
                        # Avoid query-param mutation + st.rerun(), which previously caused
                        # extra app executions and the visible white/loading transition.
                        st.session_state.home_market_v2021=m
                        st.session_state["chr_home_market_user_selected_v21222"]=True
                        st.session_state["chr_home_market_auto_v21222"]=False
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
    # V20.7.4.18.8 — Global Markets Isolated HTML Component.
    # All five tables are loaded once; switching happens only inside this iframe.
    gm_buttons=[]; gm_panels=[]
    for i,(gname,tbl) in enumerate(gp):
        gm_buttons.append(f'<button type="button" class="gm-tab" data-index="{i}">{html_lib.escape(gname)}</button>')
        gm_panels.append(f'<div class="gm-panel" data-index="{i}">{tbl}</div>')
    gm_doc='''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;padding:0;background:#fff;font-family:Arial,sans-serif;color:#20364f;overflow:hidden}
.gm-tabs{display:flex;gap:5px;flex-wrap:wrap;margin:0 0 8px}.gm-tab{cursor:pointer;padding:4px 9px;border:1px solid #d7e0ea;border-radius:5px;background:#fff;color:#43566d;font-size:10px;line-height:1.2;font-family:inherit}.gm-tab:hover{background:#f5f8fc;color:#0b57d0}.gm-tab.active{background:#eef5ff;color:#0b57d0;border-color:#b9d3ff;font-weight:700}.gm-panel{display:none}.gm-panel.active{display:block}
table{width:100%;border-collapse:collapse;font-size:11px}th,td{padding:6px 7px;border-bottom:1px solid #edf1f5;text-align:right}th:first-child,td:first-child{text-align:left}th{color:#65778b;font-weight:600;background:#fafbfd}.chr-empty{font-size:11px;color:#718096;padding:12px 2px}
</style></head><body><div class="gm-tabs">'''+''.join(gm_buttons)+'''</div><div class="gm-panels">'''+''.join(gm_panels)+'''</div><script>
(function(){const KEY='chrimata-global-markets-tab-v2074188';const tabs=[...document.querySelectorAll('.gm-tab')];const panels=[...document.querySelectorAll('.gm-panel')];function activate(idx){if(idx<0||idx>=tabs.length)idx=0;tabs.forEach((b,i)=>b.classList.toggle('active',i===idx));panels.forEach((p,i)=>p.classList.toggle('active',i===idx));try{localStorage.setItem(KEY,String(idx));}catch(e){}}let initial=0;try{const saved=parseInt(localStorage.getItem(KEY),10);if(Number.isInteger(saved)&&saved>=0&&saved<tabs.length)initial=saved;}catch(e){}tabs.forEach((b,i)=>b.addEventListener('click',()=>activate(i)));activate(initial);})();
</script></body></html>'''
    glob_t=('<iframe class="chr-gm-iframe" title="Global Markets" style="width:100%;height:190px;border:0;display:block;background:#fff;" srcdoc="'+html_lib.escape(gm_doc, quote=True)+'"></iframe>')
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
        try: meta=info(ticker) or {}
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
        try: meta=info(ticker) or {}
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

def _chr_identity_country(symbol, exchange="", provider_country=""):
    """V20.7.4.21.6.2 — exchange-authoritative listing-country resolver.

    For supported exchanges the trading venue is the source of truth. This
    prevents stale provider metadata (for example NASDAQ + Germany) from
    producing mismatched flag/country identities in the Quick View.
    """
    raw=str(provider_country or "").strip()
    aliases={"USA":"United States","US":"United States","United States of America":"United States","UK":"United Kingdom","GB":"United Kingdom","Great Britain":"United Kingdom","AU":"Australia","CA":"Canada","JP":"Japan","HK":"Hong Kong","CN":"China","TW":"Taiwan","PL":"Poland"}
    known_countries={"United States","Australia","United Kingdom","Japan","Hong Kong","Canada","Germany","Argentina","Mexico","Poland","Taiwan","China"}
    sym=str(symbol or "").upper().strip(); ex=str(exchange or "").upper().strip()

    # Supported trading venues are authoritative over provider country text.
    exchange_map={
        "ASX":"Australia","AUSTRALIAN":"Australia",
        "NASDAQ":"United States","NMS":"United States","NGM":"United States","NCM":"United States",
        "NYSE":"United States","NYQ":"United States","AMEX":"United States","ASE":"United States",
        "LSE":"United Kingdom","LONDON":"United Kingdom",
        "TSE":"Japan","JPX":"Japan","TOKYO":"Japan",
        "HKEX":"Hong Kong","HKG":"Hong Kong","HONG KONG":"Hong Kong",
        "TSX":"Canada","TORONTO":"Canada",
        "SHENZHEN":"China","SHANGHAI":"China","TAIPEI":"Taiwan","TAIWAN":"Taiwan",
        "WSE":"Poland","WARSAW":"Poland","XETRA":"Germany","FRANKFURT":"Germany",
        "BYMA":"Argentina","BMV":"Mexico","DUSSELDORF":"Germany","DÜSSELDORF":"Germany",
        "HAMBURG":"Germany","STUTTGART":"Germany","OTC MARKETS":"United States","OTC":"United States"
    }
    if ex in exchange_map: return exchange_map[ex]
    for token,country in exchange_map.items():
        if token and token in ex: return country

    # If the exchange is vague/missing, use the listing suffix next.
    suffixes=[(".AX","Australia"),(".L","United Kingdom"),(".T","Japan"),(".HK","Hong Kong"),(".TO","Canada"),(".V","Canada"),(".SZ","China"),(".SS","China"),(".TW","Taiwan"),(".TWO","Taiwan"),(".WA","Poland"),(".DE","Germany"),(".F","Germany"),(".MX","Mexico"),(".BA","Argentina")]
    for suf,country in suffixes:
        if sym.endswith(suf): return country

    # Provider metadata is only a final fallback once exchange/suffix identity
    # cannot determine the listing country.
    raw_norm=aliases.get(raw,raw)
    if raw_norm in known_countries:
        return raw_norm
    return ""


def _chr_identity_logo_candidates(symbol, meta, company="", size=96):
    """V20.7.4.21.3 — stronger logo sources; provider/domain first, market-logo CDN fallback."""
    from urllib.parse import quote
    base=company_logo_candidates(symbol,meta,size)
    sym=str(symbol or "").strip()
    # V20.7.4.21.6.8 — global symbol-logo fallbacks. Provider metadata and
    # company website remain first choice, but search results often arrive with
    # no website/logo metadata. Add symbol-aware public logo endpoints before
    # falling back to initials so ASX and other global listings can still show
    # their real company identity.
    if sym:
        clean_sym=sym.upper().strip()
        symbol_logo_candidates=[
            f"https://financialmodelingprep.com/image-stock/{quote(clean_sym)}.png",
            f"https://images.financialmodelingprep.com/symbol/{quote(clean_sym)}.png",
        ]
        for u in symbol_logo_candidates:
            if u not in base: base.append(u)
    # V20.7.4.21.4.3: do not append other speculative symbol-image URLs here.
    # A remote 404 renders as a broken-image icon in Streamlit because event-handler
    # attributes can be sanitised. Prefer verified provider/domain candidates and
    # fall back cleanly to the letter avatar when no reliable logo is known.
    # Known canonical domains cover high-frequency names when provider metadata is thin.
    nm=str(company or "").lower()
    known={
        "qantas airways limited":"qantas.com","qantas airways":"qantas.com","qantas":"qantas.com",
        "zip co limited":"zip.co","zip co ltd":"zip.co","ziprecruiter":"ziprecruiter.com",
        "the coca-cola company":"coca-colacompany.com","coca-cola hbc":"coca-colahellenic.com","coca-cola europacific":"cocacolaep.com",
        "qantas airways":"qantas.com","apple inc":"apple.com","microsoft":"microsoft.com","nvidia":"nvidia.com","amazon":"amazon.com","tesla":"tesla.com","pepsico":"pepsico.com","pepsi co":"pepsico.com",
        "commonwealth bank of australia":"commbank.com.au","commonwealth bank":"commbank.com.au","commbank":"commbank.com.au",
        "anz group holdings":"anz.com.au","australia and new zealand banking group":"anz.com.au","anz":"anz.com.au"
    }
    # V21.2.89 — listing-aware issuer identity. Multiple securities/ADRs/OTC
    # listings can represent the same company and should resolve to one brand domain.
    symbol_domains={
        "QAN.AX":"qantas.com","QUBSF":"qantas.com","QABSY":"qantas.com",
        "CBA.AX":"commbank.com.au","ZIP.AX":"zip.co",
    }
    dom=symbol_domains.get(sym.upper(),"") or next((d for k,d in known.items() if k in nm),"")
    if dom:
        # V21.2.38 — official-brand-first policy. For companies with a verified canonical
        # domain, full corporate wordmarks are placed ahead of provider logoUrl/app icons.
        # This prevents a technically valid square icon from winning before the brand logo.
        official_assets={
            # V21.2.89 — Qantas canonical domain is verified from Qantas' official site.
            # We intentionally use validated domain icons rather than scraping/rehosting a
            # trademark asset; the server-side resolver rejects HTML/invalid image responses.
            "qantas.com":[],
            # V21.2.38 — prefer the full official corporate wordmark, not a provider app/icon tile.
            # Zip's official 2026 AU brand resources continue to use the full ZIP wordmark.
            "zip.co":[
                "https://upload.wikimedia.org/wikipedia/commons/9/9d/Zip_Logo.svg",
                "https://zip.co/nz/wp-content/uploads/2021/08/logo-dark.svg",
            ],
            "coca-colacompany.com":["https://www.coca-colacompany.com/content/dam/corporate/us/en/header-footer/Footer%20Icon.svg"],
        }
        branded=list(official_assets.get(dom,[])) + [
            f"https://logo.clearbit.com/{quote(dom)}?size={max(256,int(size)*2)}",
            f"https://www.google.com/s2/favicons?domain_url=https://{quote(dom)}&sz={max(256,int(size)*2)}",
        ]
        for u in branded:
            if u in base: base.remove(u)
        base = branded + base
    return list(dict.fromkeys(base))

@st.cache_data(ttl=21600, show_spinner=False)
def _chr_resolved_logo_data_uri(symbol, company, candidates):
    """V21.2.38: official-brand-first logo resolution with preserved aspect ratio."""
    import base64, io, urllib.request
    from PIL import Image, ImageOps
    headers={"User-Agent":"Mozilla/5.0 (compatible; Chrimata/21.2.88)","Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"}
    for url in list(candidates or []):
        try:
            req=urllib.request.Request(str(url),headers=headers)
            with urllib.request.urlopen(req,timeout=4) as resp:
                raw=resp.read(2_000_000); ctype=str(resp.headers.get_content_type() or "").lower()
            if not raw: continue
            head=raw[:1024].lstrip().lower()
            if b"<html" in head or b"<!doctype html" in head: continue

            # Convert SVG to a high-resolution PNG before embedding. Browsers/providers
            # can disagree on SVG sizing; rasterising here gives the header one stable asset.
            if ctype=="image/svg+xml" or b"<svg" in head:
                try:
                    import cairosvg
                    raw=cairosvg.svg2png(bytestring=raw,output_width=640,output_height=360)
                except Exception:
                    continue

            try:
                im=Image.open(io.BytesIO(raw))
                im.load()
            except Exception:
                continue
            if im.width < 24 or im.height < 24:
                continue

            # Never resize by forcing width and height independently. Fit the original
            # aspect ratio inside a transparent 640x360 brand canvas instead.
            if im.mode not in ("RGBA","LA"):
                im=im.convert("RGBA")
            else:
                im=im.convert("RGBA")
            fitted=ImageOps.contain(im,(600,320),method=Image.Resampling.LANCZOS)
            canvas=Image.new("RGBA",(640,360),(255,255,255,0))
            x=(640-fitted.width)//2; y=(360-fitted.height)//2
            canvas.alpha_composite(fitted,(x,y))
            out=io.BytesIO(); canvas.save(out,format="PNG",optimize=True)
            return "data:image/png;base64,"+base64.b64encode(out.getvalue()).decode("ascii")
        except Exception:
            continue
    return ""

@st.cache_data(ttl=900, show_spinner=False)
def _chr_search_market_enrichment_v2074214(symbol):
    """Lightweight cached metadata used by Company Search and Quick View."""
    out={}
    try:
        out.update(info(symbol) or {})
    except Exception:
        pass
    try:
        richer=yf.Ticker(symbol).get_info() or {}
        for k,v in richer.items():
            if out.get(k) in (None, "", 0, "—") and v not in (None, "", "—"):
                out[k]=v
    except Exception:
        pass
    try:
        fi=yf.Ticker(symbol).fast_info
        def _fi(name):
            try: return getattr(fi,name)
            except Exception:
                try: return fi.get(name)
                except Exception: return None
        # yfinance fast_info is often available even when the larger .info payload is thin.
        fast_map={
            "marketCap":_fi("market_cap"),
            "currency":_fi("currency"),
            "fiftyTwoWeekLow":_fi("year_low"),
            "fiftyTwoWeekHigh":_fi("year_high"),
            "sharesOutstanding":_fi("shares"),
        }
        for k,v in fast_map.items():
            if out.get(k) in (None,"",0) and v not in (None,""):
                out[k]=v
    except Exception:
        pass
    # V20.8.0 — Global Fundamental Data Enrichment Fix.
    # Derive commonly missing Quick View fundamentals from independent Yahoo
    # fields when the primary info payload is thin. Never fabricate a value.
    try:
        q=overview_quote(symbol,"5d") or {}
        px=_mia_num(q.get("last"))
        mc=_mia_num(out.get("marketCap")); sh=_mia_num(out.get("sharesOutstanding"))
        if not np.isfinite(mc) and np.isfinite(sh) and sh>0 and np.isfinite(px) and px>0:
            out["marketCap"]=float(px*sh)

        # P/E: trailing -> forward -> price / trailing EPS -> price / forward EPS.
        pe=_mia_num(out.get("trailingPE"))
        if not np.isfinite(pe): pe=_mia_num(out.get("forwardPE"))
        if not np.isfinite(pe) and np.isfinite(px) and px>0:
            eps=_mia_num(out.get("trailingEps"))
            if not np.isfinite(eps): eps=_mia_num(out.get("epsTrailingTwelveMonths"))
            if not np.isfinite(eps): eps=_mia_num(out.get("forwardEps"))
            if np.isfinite(eps) and eps>0: out["trailingPE"]=float(px/eps)

        # Dividend yield: provider yield -> annual dividend rate / price ->
        # trailing 12-month cash dividends / current price. A confirmed empty
        # dividend history is represented as 0.0 rather than an unknown dash.
        dy=_mia_num(out.get("dividendYield"))
        if not np.isfinite(dy): dy=_mia_num(out.get("trailingAnnualDividendYield"))
        if not np.isfinite(dy) and np.isfinite(px) and px>0:
            rate=_mia_num(out.get("dividendRate"))
            if not np.isfinite(rate): rate=_mia_num(out.get("trailingAnnualDividendRate"))
            if np.isfinite(rate) and rate>=0:
                out["dividendYield"]=float(rate/px)
            else:
                try:
                    div=yf.Ticker(symbol).get_dividends(period="1y")
                    if div is not None:
                        vals=pd.to_numeric(div,errors="coerce").dropna()
                        out["dividendYield"]=float(vals.sum()/px) if len(vals) else 0.0
                except Exception:
                    pass

        # Newer yfinance exposes stable sector/industry keys even when the
        # display labels are absent. Convert those keys into readable labels.
        def _pretty_key(v):
            v=str(v or "").strip()
            if not v: return ""
            return v.replace("—","-").replace("_","-").replace("-"," ").title()
        if not (out.get("sector") or out.get("sectorDisp")):
            sk=out.get("sectorKey")
            if sk: out["sector"]=_pretty_key(sk)
        if not (out.get("industry") or out.get("industryDisp")):
            ik=out.get("industryKey")
            if ik: out["industry"]=_pretty_key(ik)
    except Exception:
        pass
    return out

def _chr_pick_company_v2074214(payload):
    """Native Streamlit selection: never navigate the browser away from Company Search."""
    item=dict(payload or {})
    st.session_state["chr_company_search_selected"]=item
    # V21.3.04 — persist one canonical listing identity object. This survives
    # Company Search -> Command Centre reruns and is the authoritative input
    # for exchange-specific disclosure routing.
    resolved=str(item.get("_resolved") or item.get("Ticker") or "")
    st.session_state["chr_security_identity"]={
        "ticker": resolved,
        "symbol": str(item.get("Ticker") or resolved),
        "company_name": str(item.get("Company") or ""),
        "exchange": str(item.get("Exchange") or item.get("Market") or ""),
        "market": str(item.get("Market") or item.get("Exchange") or ""),
        "country": str(item.get("Country") or ""),
        "mic": str(item.get("MIC") or item.get("mic") or ""),
        "provider_symbol": resolved,
    }
    st.session_state["chr_primary_nav"]="Company Search"
    if resolved:
        recent=st.session_state.get("chr_recent_companies",[])
        st.session_state["chr_recent_companies"]=[resolved]+[x for x in recent if x!=resolved][:4]

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
    .v20743-results-card{background:#fff;border:1px solid #d8e3ef;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(15,23,42,.04);margin-top:10px;max-width:100%}
    /* V20.7.4.21 — contain Search Results inside the Company Search workflow. */
    .v20743-results-top{padding:13px 18px 11px;border-bottom:1px solid #e1ebf5;background:#fff}.v20743-results-title{font-size:22px;line-height:1.05;font-weight:900;color:#10264b;letter-spacing:-.025em}.v20743-results-sub{font-size:12px;color:#60748d;margin-top:5px}.v20743-results-sub b{color:#17345c;font-weight:850}
    .v20743-table{width:100%;font-size:12px;color:#142b4d;max-height:352px;overflow-y:auto;overflow-x:hidden;scrollbar-gutter:stable}
    .v20743-tr{display:grid;grid-template-columns:minmax(285px,2.25fr) minmax(92px,.72fr) minmax(105px,.82fr) minmax(180px,1.25fr) minmax(105px,.78fr) minmax(92px,.68fr) minmax(135px,.95fr);align-items:center;min-height:47px;border-bottom:1px solid #e3ebf4;background:#fff}.v20743-tr:last-child{border-bottom:0}.v20743-th{min-height:42px;background:#edf6ff;color:#184d87;font-weight:900;border-bottom:1px solid #d5e3f1;position:sticky;top:0;z-index:3}
    .v20743-cell{padding:7px 14px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v20743-num{text-align:right}.v20743-companycell{display:flex;align-items:center;gap:12px;font-weight:850}.v20743-companylink{color:#0863c5!important;text-decoration:none!important;font-weight:900;overflow:hidden;text-overflow:ellipsis}.v20743-companylink:hover{text-decoration:underline!important;color:#004fa8!important}
    .v20743-logo{width:30px;height:30px;object-fit:contain;border-radius:7px;flex:0 0 30px;background:#fff}.v20743-logo-fallback{width:30px;height:30px;border-radius:50%;background:#eef3f8;color:#17345c;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:900;flex:0 0 30px}.v20743-country{display:flex;align-items:center;gap:9px}.v20743-flag{font-family:"Segoe UI Emoji","Noto Color Emoji",sans-serif;font-size:21px;line-height:1}.v20743-up{color:#079447;font-weight:900}.v20743-down{color:#dc3d3d;font-weight:900}.v20743-flat{color:#52657d;font-weight:800}
    @media(max-width:1100px){.v20743-table{font-size:11px}.v20743-cell{padding-left:8px;padding-right:8px}.v20743-tr{grid-template-columns:minmax(205px,1.8fr) 72px 82px minmax(130px,1fr) 82px 66px 98px}.v20743-logo,.v20743-logo-fallback{width:29px;height:29px;flex-basis:29px}}
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
        try: meta=_chr_search_market_enrichment_v2074214(resolved) or {}
        except Exception: meta={}
        rows.append({"Company":str(meta.get("longName") or meta.get("shortName") or r.get("Company") or sym),"Ticker":sym,"Exchange":str(r.get("Exchange") or ""),"Market":str(r.get("Market") or ""),"Country":_chr_identity_country(resolved, r.get("Exchange",""), meta.get("country") or r.get("Country") or ""),"Currency":str(meta.get("currency") or r.get("Currency") or ""),"Sector":str(meta.get("sector") or "—"),"Logo":str(meta.get("logo_url") or meta.get("logoUrl") or ""),"Website":str(meta.get("website") or ""),"Market Cap":_mia_num(meta.get("marketCap")),"Price":None if not np.isfinite(last) else float(last),"Day %":None if not np.isfinite(chg) else float(chg),"_resolved":resolved})
    view=pd.DataFrame(rows)
    # V20.7.4.20 — keep the strongest listing for duplicate search hits.
    # Search providers can return the same security several times with partial
    # exchange metadata; prefer a populated exchange and retain legitimate
    # cross-listed tickers as separate rows.
    if not view.empty:
        view["_exchange_quality"]=view["Exchange"].fillna("").astype(str).str.strip().ne("").astype(int)
        view=view.sort_values(["_exchange_quality"],ascending=False,kind="stable")
        view=view.drop_duplicates(subset=["Ticker","Country"],keep="first").drop(columns=["_exchange_quality"]).reset_index(drop=True)
        # V20.7.4.20.1 — rank recognizable primary listings ahead of thin/secondary hits.
        # Market cap is used only as a relevance signal; no listings are fabricated.
        _q=query.strip().lower()
        view["_name_match"]=view["Company"].fillna("").astype(str).str.lower().map(lambda x: 2 if x==_q else (1 if _q in x else 0))
        view["_cap_rank"]=pd.to_numeric(view["Market Cap"],errors="coerce").fillna(-1)
        view=view.sort_values(["_name_match","_cap_rank"],ascending=[False,False],kind="stable").drop(columns=["_name_match","_cap_rank"]).reset_index(drop=True)
    if sector_filter!="All Sectors": view=view[view["Sector"].eq(sector_filter)].copy()
    if cap_filter!="All Market Caps":
        mc=pd.to_numeric(view["Market Cap"],errors="coerce")
        if cap_filter.startswith("Mega"): view=view[mc>=2e11]
        elif cap_filter.startswith("Large"): view=view[(mc>=1e10)&(mc<2e11)]
        elif cap_filter.startswith("Mid"): view=view[(mc>=2e9)&(mc<1e10)]
        else: view=view[mc<2e9]
    if view.empty: st.info("Listings were found, but none match the selected Sector / Market Cap filters."); return

    # V20.7.4.21 — Dual-Panel Company Search & Market Discovery Dashboard.
    flag_map={"United States":"🇺🇸","USA":"🇺🇸","Australia":"🇦🇺","United Kingdom":"🇬🇧","UK":"🇬🇧","Japan":"🇯🇵","Hong Kong":"🇭🇰","Canada":"🇨🇦","Germany":"🇩🇪","Argentina":"🇦🇷","Mexico":"🇲🇽","Poland":"🇵🇱","Taiwan":"🇹🇼"}
    aliases={"USA":"United States","US":"United States","UK":"United Kingdom","GB":"United Kingdom","AU":"Australia","CA":"Canada","JP":"Japan","HK":"Hong Kong"}
    flag_codes={"United States":"us","Australia":"au","United Kingdom":"gb","Japan":"jp","Hong Kong":"hk","Canada":"ca","Germany":"de","Argentina":"ar","Mexico":"mx","Poland":"pl","Taiwan":"tw","China":"cn"}
    def flag_html(country):
        code=flag_codes.get(country)
        return f'<img class="v421flagimg" src="https://flagcdn.com/w40/{code}.png" alt="{html.escape(country)}">' if code else '<span style="font-size:16px">🌐</span>'
    ex_alias={"NMS":"NASDAQ","NGM":"NASDAQ","NCM":"NASDAQ","NYQ":"NYSE","AUSTRALIAN":"ASX","LONDON":"LSE","JPX":"TSE","TOKYO":"TSE","HKG":"HKEX","HONG KONG":"HKEX","TOR":"TSX","TORONTO":"TSX"}
    prefixes={"USD":"$","AUD":"A$","GBP":"£","JPY":"¥","HKD":"HK$","CAD":"C$","EUR":"€","CNY":"CN¥","TWD":"NT$"}
    def exch(v):
        x=str(v or "—").strip(); return ex_alias.get(x.upper(),x)
    def price(v,c=""):
        try:
            x=float(v); return "—" if not np.isfinite(x) else f"{prefixes.get(str(c).upper(),'')}{x:,.2f}"
        except:return "—"
    def capfmt(v,c="USD"):
        try:
            x=float(v)
            if not np.isfinite(x):return "—"
            p={"USD":"US$","AUD":"A$","GBP":"£","JPY":"¥","HKD":"HK$","CAD":"C$","EUR":"€"}.get(str(c).upper(),"$")
            return f"{p}{x/1e12:.2f}T" if x>=1e12 else (f"{p}{x/1e9:.2f}B" if x>=1e9 else (f"{p}{x/1e6:.1f}M" if x>=1e6 else f"{p}{x:,.0f}"))
        except:return "—"
    selected=st.session_state.get("chr_company_search_selected")
    if not selected or str(selected.get("_resolved","")) not in set(view["_resolved"].astype(str)):
        selected=view.iloc[0].to_dict(); st.session_state["chr_company_search_selected"]=selected
    st.markdown("""<style>
    /* V20.7.4.21.3 — reference-matched dual-panel geometry and dense results table. */
    .v421card{background:#fff;border:1px solid #d8e3ef;border-radius:11px;overflow:hidden;box-shadow:0 1px 4px rgba(15,23,42,.04)}
    .v421results{height:620px;display:flex;flex-direction:column}.v421head{padding:12px 15px 9px;border-bottom:1px solid #e1ebf5;flex:0 0 auto}.v421title{font-size:20px;line-height:1.05;font-weight:900;color:#10264b;letter-spacing:-.02em}.v421sub{font-size:11px;color:#60748d;margin-top:4px}.v421table{height:100%;min-height:0;overflow-y:auto;overflow-x:hidden;scrollbar-gutter:stable}.v421row{display:grid;grid-template-columns:minmax(180px,1.75fr) 68px 76px minmax(112px,1.05fr) 82px 68px 92px;align-items:center;min-height:39px;border-bottom:1px solid #e5edf5;font-size:10.5px;color:#183253}.v421th{position:sticky;top:0;z-index:3;background:#edf6ff;color:#184d87;font-weight:900;min-height:38px}.v421cell{padding:5px 7px;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v421num{text-align:right}.v421co{display:flex;align-items:center;gap:7px;font-weight:850}.v421co a{color:#0863c5;text-decoration:none;font-weight:900;overflow:hidden;text-overflow:ellipsis}.v421logo{width:30px;height:30px;object-fit:contain;border-radius:6px;flex:0 0 30px;background:#fff}.v421av{width:30px!important;height:30px!important;flex-basis:30px!important}.v421av{width:25px;height:25px;border-radius:50%;background:#eef3f8;display:flex;align-items:center;justify-content:center;font-weight:900;flex:0 0 25px}.v421country{display:flex;gap:6px;align-items:center}.v421flagimg{width:22px;height:15px;object-fit:cover;border-radius:2px;box-shadow:0 0 0 1px rgba(15,23,42,.08);flex:0 0 22px}.v421up{color:#079447;font-weight:900}.v421down{color:#dc3d3d;font-weight:900}.v421flat{color:#60748d;font-weight:800}
    .st-key-chr_search_results_panel_v2074211,.st-key-chr_search_quickview_panel_v2074211{height:620px;min-height:620px;max-height:620px;overflow:hidden}
    .chr-native-results-head{display:grid;grid-template-columns:2.75fr .72fr .82fr 1.55fr .9fr .8fr 1fr;align-items:center;min-height:38px;background:#edf6ff;border-bottom:1px solid #e5edf5;color:#184d87;font-size:10.5px;font-weight:900}.chr-native-results-head>div{padding:5px 7px;white-space:nowrap}.chr-native-results-head .n{text-align:right}.chr-native-results-title{padding:12px 15px 9px;border-bottom:1px solid #e1ebf5}.chr-native-results-scroll{height:522px;overflow-y:auto;overflow-x:hidden}.chr-native-result-row{border-bottom:1px solid #e5edf5;min-height:48px;padding:4px 5px}.chr-native-result-row.selected{background:#f5f9ff}.chr-native-result-row [data-testid="stColumn"]{display:flex;align-items:center}.chr-native-result-row .stButton{width:100%}.chr-native-result-row .stButton button{border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important;min-height:30px!important;height:auto!important;color:#0863c5!important;font-size:10.5px!important;font-weight:900!important;justify-content:flex-start!important;text-align:left!important}.chr-native-result-row .stButton button:hover{color:#064f9d!important;background:transparent!important}
    /* V20.7.4.21.4.3 — native selection buttons visually behave like table text. */
    [class*="st-key-chr_pick_native_v20742141_"]{margin:0!important;padding:0!important;min-height:30px!important;}
    [class*="st-key-chr_pick_native_v20742141_"] .stButton{margin:0!important;padding:0!important;}
    [class*="st-key-chr_pick_native_v20742141_"] button{
        background:transparent!important;border:0!important;box-shadow:none!important;
        color:#0863c5!important;padding:0!important;margin:0!important;
        min-height:30px!important;height:30px!important;width:auto!important;
        font-size:10.5px!important;font-weight:900!important;line-height:1.15!important;
        justify-content:flex-start!important;text-align:left!important;border-radius:0!important;
    }
    [class*="st-key-chr_pick_native_v20742141_"] button:hover,
    [class*="st-key-chr_pick_native_v20742141_"] button:focus{background:transparent!important;color:#064f9d!important;border:0!important;box-shadow:none!important;}
    [class*="st-key-chr_pick_native_v20742141_"] button p{font-size:10.5px!important;font-weight:900!important;line-height:1.15!important;margin:0!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;}
    /* V20.7.4.21.4.3 — balanced edge spacing + true vertical centering. */
    .chr-native-results-head>div:first-child{padding-left:18px!important;}
    .chr-native-results-head>div:last-child{padding-right:18px!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stHorizontalBlock"]{min-height:40px!important;padding-left:14px!important;padding-right:14px!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stColumn"]{min-height:40px!important;display:flex!important;align-items:center!important;justify-content:center!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stColumn"]>div{width:100%!important;display:flex!important;align-items:center!important;}
    /* V20.7.4.21.5.1 — compact native rows: remove Streamlit's vertical block
       gaps/padding that were stretching rows and pushing content off-centre. */
    .st-key-chr_search_results_scroll_v20742141{padding-top:0!important;margin-top:0!important;}
    .st-key-chr_search_results_scroll_v20742141 > div{padding-top:0!important;margin-top:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stVerticalBlock"]{gap:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stHorizontalBlock"]{height:52px!important;min-height:52px!important;max-height:52px!important;margin:0!important;padding-top:0!important;padding-bottom:0!important;border-bottom:1px solid #e5edf5!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stColumn"]{height:52px!important;min-height:52px!important;max-height:52px!important;margin:0!important;padding-top:0!important;padding-bottom:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [data-testid="stColumn"]>div{height:52px!important;min-height:52px!important;max-height:52px!important;margin:0!important;padding-top:0!important;padding-bottom:0!important;justify-content:center!important;}
    .st-key-chr_search_results_scroll_v20742141 .chr-native-cell{height:52px!important;min-height:52px!important;max-height:52px!important;line-height:1.2!important;}
    .st-key-chr_search_results_scroll_v20742141 .chr-native-logo,.st-key-chr_search_results_scroll_v20742141 .chr-native-avatar{margin-top:0!important;margin-bottom:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [class*="st-key-chr_pick_native_v20742141_"]{height:52px!important;min-height:52px!important;max-height:52px!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [class*="st-key-chr_pick_native_v20742141_"] .stButton{height:52px!important;min-height:52px!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
    .st-key-chr_search_results_scroll_v20742141 [class*="st-key-chr_pick_native_v20742141_"] button{height:52px!important;min-height:52px!important;max-height:52px!important;display:flex!important;align-items:center!important;margin:0!important;padding:0!important;}
    .st-key-chr_search_results_scroll_v20742141 div[data-testid="stMarkdownContainer"]{margin:0!important;padding:0!important;}
    .st-key-chr_search_results_scroll_v20742141 div[data-testid="stMarkdownContainer"] p{margin:0!important;}
    .st-key-chr_search_results_scroll_v20742141 hr{margin:0!important;}
.chr-native-cell{font-size:10.5px;color:#183253;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0!important;margin:0!important;min-height:30px;display:flex;align-items:center}.chr-native-num{text-align:right;width:100%;justify-content:flex-end}.chr-native-country{display:flex;gap:6px;align-items:center}.chr-native-logo{width:30px;height:30px;object-fit:contain;border-radius:6px;background:#fff;margin-right:6px;vertical-align:middle}.chr-native-avatar{width:30px;height:30px;border-radius:50%;background:#eef3f8;display:inline-flex;align-items:center;justify-content:center;font-weight:900;margin-right:6px}.st-key-chr_search_results_panel_v2074211>div,.st-key-chr_search_quickview_panel_v2074211>div{min-height:0}.st-key-chr_search_results_panel_v2074211{background:#fff;border:1px solid #d8e3ef;border-radius:11px;overflow:hidden!important;box-shadow:0 1px 4px rgba(15,23,42,.04)}.st-key-chr_search_quickview_panel_v2074211{display:flex;flex-direction:column}.st-key-chr_search_quickview_panel_v2074211 .v421card{flex:1 1 auto}.v421q{padding:14px 15px}.v421qtop{display:flex;gap:10px;align-items:center}.v421qlogo{width:42px;height:42px;object-fit:contain;border-radius:7px}.v421qname{font-size:18px;font-weight:900;color:#10264b}.v421meta{font-size:10.5px;color:#71839a;margin-top:3px}.v421qmeta{display:flex;align-items:center;gap:4px}.v421qmeta .v421flagimg{width:18px;height:12px;flex:0 0 18px;margin:0 1px}.v421qprice{font-size:28px;font-weight:900;margin:12px 0;color:#101820}.v421stat{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid #e7edf4;font-size:11.5px}.v421stat span{color:#64778e}.v421stat b{color:#172b4d;text-align:right}.v421cons{display:flex;justify-content:space-between;align-items:center;margin-top:10px}.v421pill{background:#dcf4e7;color:#118348;border-radius:12px;padding:4px 9px;font-size:11px;font-weight:850}.v421mini{background:#fff;border:1px solid #d8e3ef;border-radius:10px;padding:11px 13px;min-height:165px}
/* V20.7.4.21.5 — reference-matched Company Quick View */
.st-key-chr_search_quickview_panel_v2074211{background:#fff;border:1px solid #d8e3ef;border-radius:11px;overflow:hidden!important;box-shadow:0 1px 4px rgba(15,23,42,.04);padding:14px!important}
.st-key-chr_search_quickview_panel_v2074211 [data-testid="stHorizontalBlock"]{align-items:center}
.v421qhero{display:flex;align-items:center;gap:11px;min-width:0}.v421qhero .v421qlogo{width:46px;height:46px;object-fit:contain;border-radius:8px}.v421qhero .v421av{width:46px;height:46px;border-radius:50%;background:#eef3f8;display:inline-flex;align-items:center;justify-content:center;font-weight:900;color:#17365d}.v421qname{font-size:19px!important;line-height:1.12;font-weight:900;color:#10264b}.v421meta{font-size:10.5px;color:#71839a;margin-top:4px}.v421price-line{display:flex;align-items:baseline;gap:14px;margin:10px 0 4px;flex-wrap:wrap}.v421price-main{font-size:31px;line-height:1;font-weight:900;color:#111827}.v421price-change{font-size:15px;font-weight:850}.v421stats{margin-top:4px}.v421stat{font-size:11.5px!important;padding:5px 0!important}.v421section-rule{height:1px;background:#e4ebf3;margin:10px -14px 9px}.v421cons-title{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}.v421cons-title b{font-size:14px;color:#10264b}.v421consbar{height:10px;border-radius:999px;overflow:hidden;display:flex;gap:4px;margin:5px 0 8px}.v421consbar span{display:block;border-radius:999px}.v421consbar .buy{background:#18a05e;flex:6}.v421consbar .hold{background:#f4a621;flex:2}.v421consbar .sell{background:#e53935;flex:1}.v421analyst-note{display:flex;justify-content:space-between;gap:8px;font-size:10.5px;color:#6b7f96;margin-bottom:3px}.v421target{display:flex;justify-content:space-between;align-items:center;font-size:11.5px;margin-top:6px}.v421target span{color:#64778e}.v421target b{color:#159447;font-size:12.5px}.st-key-chr_qv_range_v207421{margin:0!important}.st-key-chr_search_watch_top_v2074215 button{min-height:34px!important;height:34px!important;padding:0 9px!important;font-size:11px!important;color:#0b63c9!important;border-color:#79aef0!important;background:#fff!important}.st-key-chr_search_open_cc_v207421 button{min-height:42px!important}.st-key-chr_search_watch_v207421 button{min-height:40px!important;color:#0b63c9!important;border-color:#79aef0!important;background:#fff!important}.v421mh{display:flex;justify-content:space-between;border-bottom:1px solid #e8eef5;padding-bottom:7px}.v421mh b{font-size:14px;color:#10264b}.v421see{font-size:10.5px;color:#0863c5;font-weight:800}.v421mr{display:grid;grid-template-columns:62px 1fr auto;gap:6px;padding:7px 0;border-bottom:1px solid #edf2f7;font-size:10.5px}.v421mt{font-weight:900;color:#18345b}.v421mn{color:#526981;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.v421footer{display:flex;justify-content:space-between;color:#71839a;font-size:10px;margin:11px 2px}.v421footer b{color:#10264b}
/* V20.7.4.21.6 — reference-matched compact Company Quick View. */
.st-key-chr_search_quickview_panel_v2074211{height:620px!important;min-height:620px!important;max-height:620px!important;padding:12px 14px!important;overflow:hidden!important}
.st-key-chr_search_quickview_panel_v2074211 [data-testid="stVerticalBlock"]{gap:5px!important}
.st-key-chr_search_quickview_panel_v2074211 [data-testid="stHorizontalBlock"]{gap:8px!important}
.st-key-chr_search_quickview_panel_v2074211 div[data-testid="stMarkdownContainer"] p{margin:0!important}
.v421qhero{gap:9px!important}.v421qhero .v421qlogo,.v421qhero .v421av{width:38px!important;height:38px!important}.v421qname{font-size:17px!important}.v421meta{font-size:9.5px!important;margin-top:2px!important}
.v421price-line{margin:4px 0 2px!important;gap:12px!important}.v421price-main{font-size:29px!important}.v421price-change{font-size:14px!important}
.st-key-chr_search_watch_top_v2074215 button{height:31px!important;min-height:31px!important;font-size:10px!important;padding:0 7px!important}
/* V20.7.4.21.6.3 — reference-matched chart range controls.
   Remove the segmented-control rail/dividers and present seven evenly spaced
   text choices. Only the active timeframe receives the compact blue pill. */
.st-key-chr_qv_range_v207421{margin:0 0 3px!important;padding:0!important}
.st-key-chr_qv_range_v207421 [data-testid="stWidgetLabel"],
.st-key-chr_qv_range_v207421 > label{display:none!important}
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"]{width:100%!important;border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important}
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"]>div{display:flex!important;align-items:center!important;justify-content:space-between!important;width:100%!important;gap:8px!important;border:0!important;background:transparent!important;box-shadow:none!important;padding:0!important}
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"] button{flex:1 1 0!important;min-width:0!important;min-height:29px!important;height:29px!important;padding:0 6px!important;margin:0!important;border:0!important;border-radius:5px!important;background:transparent!important;box-shadow:none!important;font-size:10.5px!important;font-weight:800!important;color:#53677f!important}
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"] button+button{border-left:0!important}
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"] button[aria-pressed="true"],
.st-key-chr_qv_range_v207421 [data-testid="stSegmentedControl"] button[data-selected="true"]{background:#0d67d7!important;color:#fff!important}
.st-key-chr_qv_range_v207421 label{border:0!important;background:transparent!important;box-shadow:none!important;min-height:29px!important;height:29px!important;padding:0 6px!important;margin:0!important;border-radius:5px!important;display:flex!important;align-items:center!important;justify-content:center!important;flex:1 1 0!important}
.st-key-chr_qv_range_v207421 label>div:first-child{display:none!important}
.st-key-chr_qv_range_v207421 label p{font-size:10.5px!important;font-weight:800!important;color:#53677f!important;margin:0!important}
.st-key-chr_qv_range_v207421 label:has(input:checked){background:#0d67d7!important;border:0!important;box-shadow:none!important}
.st-key-chr_qv_range_v207421 label:has(input:checked) p{color:#fff!important}
/* V20.7.4.21.6.6 — seven open timeframe buttons, matching the reference. */
[class*="st-key-chr_qv_tf_v20742166_"]{margin:0!important;padding:0!important}
[class*="st-key-chr_qv_tf_v20742166_"] .stButton{margin:0!important;padding:0!important}
[class*="st-key-chr_qv_tf_v20742166_"] button{height:28px!important;min-height:28px!important;padding:0!important;margin:0!important;border:0!important;border-radius:5px!important;background:transparent!important;box-shadow:none!important;color:#53677f!important;font-size:10.5px!important;font-weight:800!important;display:flex!important;align-items:center!important;justify-content:center!important;text-align:center!important;width:100%!important}
[class*="st-key-chr_qv_tf_v20742166_"] button:hover{background:#f3f7fb!important;color:#174f8f!important;border:0!important;box-shadow:none!important}
[class*="st-key-chr_qv_tf_v20742166_"] button p{font-size:10.5px!important;font-weight:800!important;line-height:28px!important;margin:0!important;padding:0!important;color:inherit!important;width:100%!important;text-align:center!important}
.st-key-chr_search_quickview_panel_v2074211 [data-testid="stPlotlyChart"]{height:104px!important;min-height:104px!important;margin:0!important;padding:0!important}
.st-key-chr_search_quickview_panel_v2074211 [data-testid="stPlotlyChart"]>div{height:104px!important;min-height:104px!important}
.v421stats{margin-top:0!important}.v421stat{font-size:10.5px!important;padding:4px 0!important;min-height:23px!important;align-items:center!important}.v421stat b{max-width:62%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.v421section-rule{margin:5px -14px 6px!important}.v421cons-title{margin-bottom:4px!important}.v421cons-title b{font-size:13px!important}.v421pill{padding:3px 8px!important;font-size:10px!important}.v421consbar{height:8px!important;margin:3px 0 4px!important}.v421analyst-note{font-size:9px!important;margin-bottom:0!important}.v421target{font-size:10.5px!important;margin-top:2px!important}.v421target b{font-size:11px!important}
.st-key-chr_search_open_cc_v207421 button{height:36px!important;min-height:36px!important;font-size:11px!important;margin-top:2px!important}.st-key-chr_search_watch_v207421 button{height:34px!important;min-height:34px!important;font-size:11px!important}
    </style>""",unsafe_allow_html=True)
    rows=[]; selres=str(selected.get("_resolved") or selected.get("Ticker") or "")
    for i,(_,r) in enumerate(view.iterrows()):
        cr=aliases.get(str(r.get("Country") or ""),str(r.get("Country") or "")); flag=flag_map.get(cr,"🌐")
        # V20.7.4.21.3 — real company logo first, with multiple browser fallbacks.
        logo_meta={"logo_url":str(r.get("Logo") or ""),"website":str(r.get("Website") or "")}
        candidates=_chr_identity_logo_candidates(str(r.get("_resolved") or r.get("Ticker") or ""),logo_meta,str(r.get("Company") or ""),96)
        initial=html.escape(str(r.get("Company") or "?")[:1].upper())
        resolved_logo=_chr_resolved_logo_data_uri(str(r.get("_resolved") or r.get("Ticker") or ""),str(r.get("Company") or ""),tuple(candidates)) if candidates else ""
        if resolved_logo:
            lh=f'<span style="display:inline-flex;align-items:center"><img class="v421logo" src="{html.escape(resolved_logo,quote=True)}" alt="{html.escape(str(r.get("Company") or "Company"),quote=True)} logo"></span>'
        else:
            lh=f'<span class="v421av">{initial}</span>'
        try:dv=float(r.get("Day %")); dt="—" if not np.isfinite(dv) else f"{dv:+.2f}%"; dc="v421up" if dv>0 else ("v421down" if dv<0 else "v421flat")
        except:dt="—";dc="v421flat"
        bg=' style="background:#f5f9ff"' if str(r.get("_resolved"))==selres else ""
        rows.append(f'<div class="v421row"{bg}><div class="v421cell v421co">{lh}<span>{html.escape(str(r.get("Company") or "—"))}</span></div><div class="v421cell">{html.escape(str(r.get("Ticker") or "—"))}</div><div class="v421cell">{html.escape(exch(r.get("Exchange")))}</div><div class="v421cell v421country">{flag_html(cr)}{html.escape(cr or "—")}</div><div class="v421cell v421num">{price(r.get("Price"),r.get("Currency"))}</div><div class="v421cell v421num {dc}">{dt}</div><div class="v421cell v421num">{capfmt(r.get("Market Cap"),r.get("Currency"))}</div></div>')
    left=f'<div class="v421card v421results"><div class="v421head"><div class="v421title">Search Results</div><div class="v421sub">Showing results for <b>“{html.escape(query)}”</b> ({len(view)} results)</div></div><div class="v421table"><div class="v421row v421th"><div class="v421cell">Company ↕</div><div class="v421cell">Ticker ↕</div><div class="v421cell">Exchange</div><div class="v421cell">Country</div><div class="v421cell v421num">Price</div><div class="v421cell v421num">Day</div><div class="v421cell v421num">Market Cap</div></div>{"".join(rows)}</div></div>'
    resolved=selres
    try:meta=_chr_search_market_enrichment_v2074214(resolved) or {}
    except:meta={}
    oq=overview_quote(resolved,"5d") or {}; last=_mia_num(oq.get("last")); pct=_mia_num(oq.get("pct")); company=meta.get("longName") or meta.get("shortName") or selected.get("Company") or resolved; cur=meta.get("currency") or selected.get("Currency") or ""
    mc=_mia_num(meta.get("marketCap"));
    if not np.isfinite(mc): mc=_mia_num(selected.get("Market Cap"))
    lo=_mia_num(meta.get("fiftyTwoWeekLow")); hi=_mia_num(meta.get("fiftyTwoWeekHigh")); pe=_mia_num(meta.get("trailingPE"));
    if not np.isfinite(pe): pe=_mia_num(meta.get("forwardPE"))
    dy=_mia_num(meta.get("dividendYield"));
    if not np.isfinite(dy): dy=_mia_num(meta.get("trailingAnnualDividendYield"))
    sector=meta.get("sector") or meta.get("sectorDisp") or meta.get("sectorKey") or selected.get("Sector") or "—"; industry=meta.get("industry") or meta.get("industryDisp") or meta.get("industryKey") or selected.get("Industry") or "—"; target=_mia_num(meta.get("targetMeanPrice")); rec=str(meta.get("recommendationKey") or "No consensus").replace("_"," ").title(); upside=(target/last-1)*100 if np.isfinite(target) and np.isfinite(last) and last else np.nan
    qlogo=str(meta.get("logo_url") or meta.get("logoUrl") or selected.get("Logo") or "")
    # V20.7.4.21.6.5 — keep the selected listing identity isolated from the
    # Search Results row loop. Previously the shared `cr` variable was overwritten
    # while rendering rows, so Quick View could inherit the country of the final
    # search result (for example Taiwan listing displayed as United States).
    q_country=_chr_identity_country(resolved, selected.get("Exchange",""), selected.get("Country") or meta.get("country") or "")
    flag=flag_map.get(q_country,"🌐")
    # V20.7.4.21.6.7 — selected-company identity uses the enriched website/logo plus
    # the exact selected Search Results payload. This keeps Quick View on the same
    # logo identity and adds a canonical Commonwealth Bank fallback when metadata is thin.
    qcands=_chr_identity_logo_candidates(resolved,{"logo_url":qlogo,"website":str(meta.get("website") or selected.get("Website") or "")},str(company),96)
    qresolved_logo=_chr_resolved_logo_data_uri(resolved,str(company),tuple(qcands)) if qcands else ""
    if qresolved_logo:
        qlh=f'<img class="v421qlogo" src="{html.escape(qresolved_logo,quote=True)}" alt="{html.escape(str(company),quote=True)} logo">'
    else:
        qlh=f'<span class="v421av">{html.escape(str(company)[:1].upper())}</span>'
    dcls="v421up" if np.isfinite(pct) and pct>0 else ("v421down" if np.isfinite(pct) and pct<0 else "v421flat"); dt="—" if not np.isfinite(pct) else f"{pct:+.2f}%"; rng="—" if not(np.isfinite(lo) and np.isfinite(hi)) else f"{price(lo,cur)} – {price(hi,cur)}"; pet="—" if not np.isfinite(pe) else f"{pe:.1f}"; dyt="—" if not np.isfinite(dy) else f"{(dy if dy>1 else dy*100):.2f}%"; tt="—" if not np.isfinite(target) else price(target,cur)+(f" ({upside:+.1f}%)" if np.isfinite(upside) else "")
    analyst_n=meta.get("numberOfAnalystOpinions"); analyst_txt=(f"{int(analyst_n)} analyst opinions" if isinstance(analyst_n,(int,float)) and analyst_n else "Consensus data where available")
    lc,rc=st.columns([1.82,1],gap="small")
    with lc:
        with st.container(key="chr_search_results_panel_v2074211"):
            # V20.7.4.21.4.3 — do not use an open HTML wrapper around native
            # Streamlit widgets. Each st.markdown call is its own DOM block; the old
            # 620px wrapper consumed the panel and pushed every native result row
            # below the clipped viewport. Keep the card on the keyed container and
            # render the title/header as normal children instead.
            st.markdown(f'<div class="chr-native-results-title"><div class="v421title">Search Results</div><div class="v421sub">Showing results for <b>“{html.escape(query)}”</b> ({len(view)} results)</div></div><div class="chr-native-results-head"><div>Company ↕</div><div>Ticker ↕</div><div>Exchange</div><div>Country</div><div class="n">Price</div><div class="n">Day</div><div class="n">Market Cap</div></div>',unsafe_allow_html=True)
            # A real Streamlit scroll container keeps all native selection buttons
            # visible/clickable while preserving the fixed-height dual-panel layout.
            with st.container(height=520, border=False, key="chr_search_results_scroll_v20742141"):
                for i,(_,r) in enumerate(view.iterrows()):
                    payload=r.to_dict(); rres=str(r.get("_resolved") or r.get("Ticker") or "")
                    c0,c1,c2,c3,c4,c5,c6=st.columns([2.75,.72,.82,1.55,.9,.8,1],gap="small",vertical_alignment="center")
                    cr=_chr_identity_country(rres, r.get("Exchange",""), r.get("Country", ""))
                    logo_meta={"logo_url":str(r.get("Logo") or ""),"website":str(r.get("Website") or "")}
                    candidates=_chr_identity_logo_candidates(rres,logo_meta,str(r.get("Company") or ""),96)
                    with c0:
                        a,b=st.columns([.18,.82],gap="small",vertical_alignment="center")
                        with a:
                            resolved_logo=_chr_resolved_logo_data_uri(rres,str(r.get("Company") or ""),tuple(candidates)) if candidates else ""
                            if resolved_logo:
                                st.markdown(f'<img class="chr-native-logo" src="{html.escape(resolved_logo,quote=True)}" alt="{html.escape(str(r.get("Company") or "Company"),quote=True)} logo">',unsafe_allow_html=True)
                            else:
                                st.markdown(f'<span class="chr-native-avatar">{html.escape(str(r.get("Company") or "?")[:1].upper())}</span>',unsafe_allow_html=True)
                        with b:
                            st.button(str(r.get("Company") or "—"),key=f"chr_pick_native_v20742141_{i}_{rres}",use_container_width=True,on_click=_chr_pick_company_v2074214,args=(payload,))
                    with c1: st.markdown(f'<div class="chr-native-cell">{html.escape(str(r.get("Ticker") or "—"))}</div>',unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="chr-native-cell">{html.escape(exch(r.get("Exchange")))}</div>',unsafe_allow_html=True)
                    with c3: st.markdown(f'<div class="chr-native-cell chr-native-country">{flag_html(cr)}{html.escape(cr or "—")}</div>',unsafe_allow_html=True)
                    with c4: st.markdown(f'<div class="chr-native-cell chr-native-num">{price(r.get("Price"),r.get("Currency"))}</div>',unsafe_allow_html=True)
                    try: dv=float(r.get("Day %")); dt="—" if not np.isfinite(dv) else f"{dv:+.2f}%"; dc="v421up" if dv>0 else ("v421down" if dv<0 else "v421flat")
                    except Exception: dt="—"; dc="v421flat"
                    with c5: st.markdown(f'<div class="chr-native-cell chr-native-num {dc}">{dt}</div>',unsafe_allow_html=True)
                    with c6: st.markdown(f'<div class="chr-native-cell chr-native-num">{capfmt(r.get("Market Cap"),r.get("Currency"))}</div>',unsafe_allow_html=True)
                    # V20.7.4.21.5.1 — no separate divider block here. A separate
                    # Streamlit markdown child adds vertical layout gap and stretches
                    # the table. Row separation is drawn with CSS on the row block.
    with rc:
        with st.container(key="chr_search_quickview_panel_v2074211"):
            qh1,qh2=st.columns([1.65,1],gap="small",vertical_alignment="center")
            with qh1:
                st.markdown(f'<div class="v421qhero">{qlh}<div><div class="v421qname">{html.escape(str(company))}</div><div class="v421meta v421qmeta">{html.escape(str(selected.get("Ticker") or resolved))} | {html.escape(exch(selected.get("Exchange")))} | {flag_html(q_country)} {html.escape(q_country or "—")}</div></div></div>',unsafe_allow_html=True)
            with qh2:
                if st.button("☆  Add to Watchlist",use_container_width=True,key="chr_search_watch_top_v2074215"):
                    try: watch_add(resolved); st.toast(f"{resolved} added to Watchlist.")
                    except Exception as exc: st.warning(f"Could not add {resolved}: {exc}")
            st.markdown(f'<div class="v421price-line"><span class="v421price-main">{price(last,cur)}</span><span class="v421price-change {dcls}">{dt}</span></div>',unsafe_allow_html=True)
            # V20.7.4.21.6.6 — reference-matched timeframe selector.
            # Use seven independent Streamlit buttons instead of segmented_control.
            # This avoids the native segmented rail/dividers entirely while keeping
            # every range interactive and preserving selection across reruns.
            ranges=["1D","1W","1M","3M","6M","1Y","5Y"]
            qv_tf_key="chr_qv_timeframe_v20742166"
            if st.session_state.get(qv_tf_key) not in ranges:
                st.session_state[qv_tf_key]="1D"
            tf=st.session_state[qv_tf_key]
            tf_cols=st.columns(7,gap="small")
            for _tf_i,_tf_label in enumerate(ranges):
                with tf_cols[_tf_i]:
                    if st.button(_tf_label,key=f"chr_qv_tf_v20742166_{_tf_label}",use_container_width=True):
                        if st.session_state.get(qv_tf_key)!=_tf_label:
                            st.session_state[qv_tf_key]=_tf_label
                            st.rerun()
            tf=st.session_state[qv_tf_key]
            st.markdown(f"""<style>
            .st-key-chr_qv_tf_v20742166_{tf} button{{background:#0d67d7!important;color:#fff!important;border:0!important;box-shadow:0 1px 3px rgba(13,103,215,.18)!important}}
            .st-key-chr_qv_tf_v20742166_{tf} button:hover{{background:#0d67d7!important;color:#fff!important}}
            </style>""",unsafe_allow_html=True)
            pm={"1D":("1d","5m"),"1W":("5d","30m"),"1M":("1mo",None),"3M":("3mo",None),"6M":("6mo",None),"1Y":("1y",None),"5Y":("5y",None)}; per,itv=pm[tf]
            try: hd=yf.Ticker(resolved).history(period=per,interval=itv,auto_adjust=True) if itv else history(resolved,per)
            except: hd=pd.DataFrame()
            if hd is not None and not hd.empty and "Close" in hd.columns:
                fig=go.Figure(go.Scatter(x=hd.index,y=hd["Close"],mode="lines",line={"width":2,"color":"#159447"},fill="tozeroy",fillcolor="rgba(21,148,71,.08)")); fig.update_layout(height=104,margin=dict(l=0,r=0,t=1,b=1),showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)"); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            else:
                st.markdown('<div style="height:104px;display:flex;align-items:center;justify-content:center;color:#8191a5;font-size:11px">Chart data unavailable</div>',unsafe_allow_html=True)
            st.markdown(f'<div class="v421stats"><div class="v421stat"><span>Market Cap</span><b>{capfmt(mc,cur)}</b></div><div class="v421stat"><span>52 Week Range</span><b>{rng}</b></div><div class="v421stat"><span>P/E Ratio</span><b>{pet}</b></div><div class="v421stat"><span>Dividend Yield</span><b>{dyt}</b></div><div class="v421stat"><span>Sector</span><b>{html.escape(str(sector))}</b></div><div class="v421stat"><span>Industry</span><b>{html.escape(str(industry))}</b></div></div><div class="v421section-rule"></div><div class="v421cons-title"><b>Analyst Consensus</b><span class="v421pill">{html.escape(rec)}</span></div><div class="v421consbar" aria-label="Consensus indicator"><span class="buy"></span><span class="hold"></span><span class="sell"></span></div><div class="v421analyst-note"><span>{html.escape(analyst_txt)}</span><span>Provider consensus</span></div><div class="v421target"><span>12M Target</span><b>{tt}</b></div>',unsafe_allow_html=True)
            if st.button("Open Company Command Centre  →",type="primary",use_container_width=True,key="chr_search_open_cc_v207421"):
                st.session_state["chr_active_ticker"]=resolved
                st.session_state["mia_search_query"]=resolved
                _active_exchange=str(selected.get("Exchange") or selected.get("Market") or "")
                _active_country=str(q_country or selected.get("Country") or "")
                st.session_state["chr_active_exchange"]=_active_exchange
                st.session_state["chr_active_country"]=_active_country
                st.session_state["chr_security_identity"]={
                    "ticker": resolved, "symbol": str(selected.get("Ticker") or resolved),
                    "company_name": str(selected.get("Company") or ""),
                    "exchange": _active_exchange, "market": str(selected.get("Market") or _active_exchange),
                    "country": _active_country, "mic": str(selected.get("MIC") or selected.get("mic") or ""),
                    "provider_symbol": resolved,
                }
                st.session_state["chr_primary_nav"]="Company Command Centre"
                st.rerun()
            if st.button("☆  Add to Watchlist",use_container_width=True,key="chr_search_watch_v207421"):
                try:watch_add(resolved);st.toast(f"{resolved} added to Watchlist.")
                except Exception as exc:st.warning(f"Could not add {resolved} to Watchlist: {exc}")
    def mini_quotes(items):
        z=[]
        for sym,nm in items:
            try:q=overview_quote(sym,"5d") or {}; z.append((sym,nm,_mia_num(q.get("last")),_mia_num(q.get("pct"))))
            except:z.append((sym,nm,np.nan,np.nan))
        return z
    recents=[]
    for sym in st.session_state.get("chr_recent_companies",[])[:5]:
        try:m=info(sym) or {}; nm=m.get("shortName") or m.get("longName") or sym
        except:nm=sym
        recents.append((sym,nm))
    popular=mini_quotes([("NVDA","NVIDIA Corp"),("TSLA","Tesla Inc"),("AAPL","Apple Inc"),("MSFT","Microsoft Corp"),("AMZN","Amazon.com Inc")]); pool=mini_quotes([("SMCI","Super Micro Computer"),("PLTR","Palantir Technologies"),("NU","Nu Holdings"),("BABA","Alibaba Group"),("ZIP.AX","Zip Co Ltd"),("NVDA","NVIDIA Corp"),("TSLA","Tesla Inc")]); movers=sorted(pool,key=lambda x:abs(x[3]) if np.isfinite(x[3]) else -1,reverse=True)[:5]; recentq=mini_quotes(recents)
    def minicard(title,data,showprice=False):
        rr=[]
        for sym,nm,px,mv in data:
            mt="—" if not np.isfinite(mv) else f"{mv:+.2f}%"; cl="v421up" if np.isfinite(mv) and mv>0 else ("v421down" if np.isfinite(mv) and mv<0 else "v421flat"); right=(f'<span>{px:,.2f}</span><span class="{cl}">{mt}</span>' if showprice and np.isfinite(px) else f'<span class="{cl}">{mt}</span>'); rr.append(f'<div class="v421mr"><span class="v421mt">{html.escape(str(sym))}</span><span class="v421mn">{html.escape(str(nm))}</span>{right}</div>')
        if not rr:rr=['<div style="padding:18px 0;color:#71839a;font-size:11px">Your selected companies will appear here.</div>']
        return f'<div class="v421mini"><div class="v421mh"><b>{title}</b><span class="v421see">See all</span></div>{"".join(rr)}</div>'
    a,b,c=st.columns(3,gap="small")
    with a:st.markdown(minicard("Recently Viewed",recentq,True),unsafe_allow_html=True)
    with b:st.markdown(minicard("Popular Today",popular),unsafe_allow_html=True)
    with c:st.markdown(minicard("Biggest Movers (Global)",movers),unsafe_allow_html=True)
    st.markdown('<div class="v421footer"><span><b>Chrímata</b> &nbsp; v20.7.4.21.6.3 &nbsp; | &nbsp; Global Markets. Smarter Decisions.</span><span>Live data where available. Delays may apply.</span></div>',unsafe_allow_html=True)


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
        _secid=dict(st.session_state.get("chr_security_identity") or {})
        _ann_ticker=str(_secid.get("ticker") or _secid.get("provider_symbol") or ticker)
        _ann_exchange=str(_secid.get("exchange") or _secid.get("market") or st.session_state.get("chr_active_exchange","") or "")
        _ann_country=str(_secid.get("country") or st.session_state.get("chr_active_country","") or "")
        ann,coverage,_ann_identity=official_disclosure_gateway(_ann_ticker,_ann_url,_ann_key,int(ann_limit),exchange=_ann_exchange,country=_ann_country)

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
    _vmeta=info(ticker) or {};_vh=history(ticker,"1y");_vprice=float(pd.to_numeric(_vh["Close"],errors="coerce").dropna().iloc[-1]) if _vh is not None and not _vh.empty else np.nan
    _vauto=valuation_pipeline(ticker,_vprice)
    st.subheader("Deterministic DCF — Bear / Base / Bull")
    st.caption("Five-year FCF DCF using provider-reported FCF, cash, debt and shares. Assumptions are deterministic and visible; AI does not calculate the valuation.")
    if _vauto.get("status")=="success":
        _vrows=[]
        for _vn,_vv in (_vauto.get("scenarios") or {}).items():
            if isinstance(_vv,dict) and np.isfinite(_mia_num(_vv.get("value_per_share"))):
                _va=_vv.get("assumptions") or {};_vrows.append({"Scenario":_vn,"Model value / share":_vv.get("value_per_share"),"Model gap":_vv.get("model_gap"),"FCF growth":_va.get("growth"),"Discount rate":_va.get("discount_rate"),"Terminal growth":_va.get("terminal_growth")})
        st.dataframe(pd.DataFrame(_vrows),use_container_width=True,hide_index=True)
        _vi=valuation_provider_inputs(_vmeta);st.caption(f"Inputs · FCF {compact_number(_vi.get('fcf'),prefix='$')} · Cash {compact_number(_vi.get('cash'),prefix='$')} · Debt {compact_number(_vi.get('debt'),prefix='$')} · Shares {compact_number(_vi.get('shares'))} · Financial currency {_vauto.get('financial_currency') or '—'} · Listing currency {_vauto.get('listing_currency') or '—'} · FX {_vauto.get('fx_rate',1):.4f}")
    else:st.info(_vauto.get("reason","Deterministic DCF unavailable because required verified inputs are missing."))
    st.subheader("Live Valuation Diagnostics")
    _audit=_vauto.get("audit",{}) if isinstance(_vauto,dict) else {}
    _checks=_audit.get("eligibility_checks",{}) or {}
    _d1,_d2,_d3,_d4=st.columns(4)
    _d1.metric("Selected security",_audit.get("selected_ticker") or ticker)
    _d2.metric("Metadata","Received" if _audit.get("metadata_received") else "Missing")
    _d3.metric("DCF status",_audit.get("dcf_status","BLOCKED"))
    _d4.metric("AI calculated","No")
    _arows=[]
    for _ak,_av in (_audit.get("inputs",{}) or {}).items():
        if isinstance(_av,dict):
            _arows.append({"Input":_ak.replace("_"," ").title(),"Status":_av.get("status","—"),
                           "Source":_av.get("source") or "—","Value":_av.get("value"),
                           "Statement row":_av.get("row") or (", ".join([str(x) for x in (_av.get("rows") or [])]) if _av.get("rows") else "—"),
                           "Period":_av.get("period") or (", ".join([str(x) for x in (_av.get("periods") or [])]) if _av.get("periods") else "—")})
    if _arows:st.dataframe(pd.DataFrame(_arows),use_container_width=True,hide_index=True)
    _ec1,_ec2,_ec3=st.columns(3)
    _ec1.metric("Positive FCF","✓" if _checks.get("positive_fcf") else "✕")
    _ec2.metric("Shares available","✓" if _checks.get("shares_available") else "✕")
    _ec3.metric("Currency aligned","✓" if _checks.get("currency_aligned") else "✕")
    _fxa=_audit.get("fx",{}) or {};_br=_audit.get("primary_listing_bridge",{}) or {}
    st.caption(f"Currency: {_fxa.get('from') or '—'} → {_fxa.get('to') or '—'} · FX {_fxa.get('status','—')} · Rate {_fxa.get('rate') if _fxa.get('rate') is not None else '—'}")
    st.caption(f"Primary listing bridge: {_br.get('status','not used')} · {_br.get('reason','—')}")
    _block=_audit.get("blocking_reasons") or []
    if _block: st.error("Blocking reason: "+" · ".join(map(str,_block)))
    if _audit.get("dcf_status")!="READY":
        with st.expander("Provider statement rows received",expanded=False):
            _sr=_audit.get("statement_rows",{}) or {}
            st.write("Cash flow rows:",_sr.get("cash_flow") or ["None received"])
            st.write("Balance sheet rows:",_sr.get("balance_sheet") or ["None received"])
            st.write("Income statement rows:",_sr.get("income_statement") or ["None received"])
    st.divider();st.subheader("Saved / custom scenario assumptions")
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

    st.subheader("Valuation Model Validation")
    st.caption("Forward-only validation: Chrímata stores today's valuation and later compares it with observed market prices. It does not backfill historical 'predictions' using today's assumptions.")
    _saved_profile,_profile_updated=valuation_profile_saved(ticker)
    _vv1,_vv2=st.columns([1,2])
    with _vv1:
        if st.button("Record validation snapshot",use_container_width=True,disabled=not _saved_profile,key=f"v21268_val_snapshot_{ticker}"):
            _ok,_msg=record_valuation_validation_snapshot(ticker,price,v)
            (st.success if _ok else st.info)(_msg)
        if not _saved_profile:
            st.info("Save company-specific valuation assumptions first. Generic defaults are not treated as validated model evidence.")
    _vsum=valuation_validation_summary(ticker)
    with _vv2:
        _m1,_m2,_m3,_m4=st.columns(4)
        _m1.metric("Matured observations",str(_vsum["Observations"]))
        _m2.metric("Median base error","—" if not np.isfinite(_vsum["Median Error"]) else f'{_vsum["Median Error"]:.1f}%')
        _m3.metric("Direction accuracy","—" if not np.isfinite(_vsum["Direction Accuracy"]) else f'{_vsum["Direction Accuracy"]:.0%}')
        _m4.metric("Bear–bull range hit","—" if not np.isfinite(_vsum["Range Hit"]) else f'{_vsum["Range Hit"]:.0%}')
    _vres=valuation_validation_results(ticker)
    if not _vres.empty:
        st.dataframe(_vres.sort_values(["Snapshot","Horizon"],ascending=[False,True]),use_container_width=True,hide_index=True)
    else:
        _snap_count=len(valuation_validation_snapshots(ticker))
        if _snap_count:
            st.info(f"{_snap_count} point-in-time snapshot(s) stored. Results will appear as 1M, 3M, 6M and 12M horizons mature.")
        else:
            st.info("No validation history yet. Record the first point-in-time snapshot to establish the model's track record from this date forward.")

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
    _tech_live=calculate_technical_snapshot(h)
    _tm1,_tm2,_tm3,_tm4=st.columns(4)
    _tm1.metric("Composite",_tech_live.get("technical_status","Pending"))
    _tm2.metric("RSI 14","—" if _tech_live.get("rsi_value") is None else f"{_tech_live.get('rsi_value'):.1f}")
    _tm3.metric("Evidence coverage",f"{_tech_live.get('evidence_coverage',0)}%")
    _tm4.metric("Calculation","Deterministic")
    st.caption(f"{_tech_live.get('description','Insufficient technical evidence')} · AI calculated: No")
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


elif page=="Company Comparison":
    # V21.2.11 — dedicated comparison utility. It deliberately reuses existing
    # provider/history helpers and does not alter any independent research engine.
    st.markdown('<div id="company-comparison"></div>',unsafe_allow_html=True)
    _cmp_a=str(st.query_params.get("chr_compare") or ticker).strip().upper() or ticker
    st.markdown("### Company Comparison")
    st.caption("Compare the selected listing with another company. The originating company remains fixed on the left.")
    _cmp_input=st.text_input("Compare with",value=str(st.session_state.get("chr_compare_input", "")),placeholder="Ticker or company symbol, e.g. SQ, PYPL, QAN.AX",key="chr_compare_input")
    _cmp_b=resolve_bare_ticker(str(_cmp_input).strip().upper()) if str(_cmp_input).strip() else ""

    def _cmp_snapshot(_t):
        _h=history(_t,"1y")
        _m={}
        try: _m=_chr_search_market_enrichment_v2074214(_t) or {}
        except Exception: _m={}
        _nm=_m.get("longName") or _m.get("shortName") or (company_name(_t) if 'company_name' in globals() else _t) or _t
        _px=float(_h["Close"].iloc[-1]) if _h is not None and not _h.empty else np.nan
        _ret=np.nan
        if _h is not None and not _h.empty and len(_h)>21:
            _c=pd.to_numeric(_h["Close"],errors="coerce").dropna(); _ret=float(_c.iloc[-1]/_c.iloc[-22]-1) if len(_c)>21 else np.nan
        return {"ticker":_t,"name":_nm,"price":_px,"marketCap":_mia_num(_m.get("marketCap")),"pe":_mia_num(_m.get("trailingPE")),"beta":_mia_num(_m.get("beta")),"sector":_m.get("sector") or "—","industry":_m.get("industry") or "—","ret1m":_ret}

    _a=_cmp_snapshot(_cmp_a)
    _b=_cmp_snapshot(_cmp_b) if _cmp_b and _cmp_b!=_cmp_a else None
    st.markdown("""<style>.chr-cmp-head{border:1px solid #d9e5f2;border-radius:10px;background:#fff;padding:14px 16px;margin:4px 0 12px}.chr-cmp-name{font-size:18px;font-weight:900;color:#10264b}.chr-cmp-tick{font-size:11px;font-weight:800;color:#1769d2}.chr-cmp-meta{font-size:11px;color:#687f9b;margin-top:4px}</style>""",unsafe_allow_html=True)
    _ca,_cb=st.columns(2)
    with _ca:
        st.markdown(f'<div class="chr-cmp-head"><div class="chr-cmp-name">{html.escape(str(_a["name"]))}</div><div class="chr-cmp-tick">{html.escape(_a["ticker"])}</div><div class="chr-cmp-meta">{html.escape(str(_a["sector"]))} · {html.escape(str(_a["industry"]))}</div></div>',unsafe_allow_html=True)
    with _cb:
        if _b:
            st.markdown(f'<div class="chr-cmp-head"><div class="chr-cmp-name">{html.escape(str(_b["name"]))}</div><div class="chr-cmp-tick">{html.escape(_b["ticker"])}</div><div class="chr-cmp-meta">{html.escape(str(_b["sector"]))} · {html.escape(str(_b["industry"]))}</div></div>',unsafe_allow_html=True)
        else:
            st.info("Enter a second ticker above to begin the comparison.")
    if _b:
        def _money(v,t): return "—" if not np.isfinite(v) else display_price(v,t)
        def _cap(v): return "—" if not np.isfinite(v) else (f"{v/1e9:.2f}B" if v>=1e9 else f"{v/1e6:.2f}M")
        _rows=[
            ("Share price",_money(_a["price"],_a["ticker"]),_money(_b["price"],_b["ticker"])),
            ("Market cap",_cap(_a["marketCap"]),_cap(_b["marketCap"])),
            ("P/E (TTM)","—" if not np.isfinite(_a["pe"]) else f'{_a["pe"]:.1f}×',"—" if not np.isfinite(_b["pe"]) else f'{_b["pe"]:.1f}×'),
            ("Beta","—" if not np.isfinite(_a["beta"]) else f'{_a["beta"]:.2f}',"—" if not np.isfinite(_b["beta"]) else f'{_b["beta"]:.2f}'),
            ("1M performance","—" if not np.isfinite(_a["ret1m"]) else f'{_a["ret1m"]:+.1%}',"—" if not np.isfinite(_b["ret1m"]) else f'{_b["ret1m"]:+.1%}'),
        ]
        st.dataframe(pd.DataFrame(_rows,columns=["Metric",_a["ticker"],_b["ticker"]]),use_container_width=True,hide_index=True)
        st.caption("V21.2.11 comparison is evidence-first. Deeper Fundamentals, Valuation, Technical, Quant and Forecast engine comparisons can be layered onto this workspace without changing those engines.")

elif page=="Company Command Centre":
    # V21.2.91 — Official Announcements & Report Document Engine reference-card polish
    st.markdown("""<style>
    .v21291-ann{position:relative;overflow:hidden}.v21291-ann .v21290-row{grid-template-columns:96px minmax(0,1fr) 104px 42px!important}
    .v21291-ann .v21290-row .pdf{text-align:right}.v21291-pdf{color:#0869e8!important;font-weight:800;text-decoration:none}.v21291-pdf:hover{text-decoration:underline}
    .v21291-na{color:#94a3b8}.v21291-source{position:absolute;left:14px;bottom:7px;font-size:9px;color:#94a3b8;white-space:nowrap;max-width:72%;overflow:hidden;text-overflow:ellipsis}
    .v21291-viewall-link{pointer-events:none}
    .v21304-ann-viewall{position:absolute;right:14px;top:14px;color:#0869e8;font-size:11px;font-weight:800;white-space:nowrap}
    </style>""",unsafe_allow_html=True)
    # V21.2 — AI Company Command Centre Overview Intelligence Rebuild
    # Overview orchestrates the independent research engines; it is not a dependency for them.
    v18_db_upgrade()
    # V21.3.17 — canonical security identity is resolved before price, metadata,
    # financials or news are loaded. Price magnitude is never used to guess identity.
    _preselected=st.session_state.get("chr_company_search_selected") or {}
    _expected_company=str(_preselected.get("Company") or name or "").strip()
    _identity_resolution=canonicalize_security(ticker,_expected_company)
    if _identity_resolution.get("changed"):
        ticker=_identity_resolution["ticker"]
        st.session_state["ticker"]=ticker
    cls=safe_company_classification(ticker)
    h=history(ticker,"1y")
    if h.empty:
        st.warning("No price history available for the selected listing. The other Company Command Centre modules remain available from the sidebar.")
    else:
        price=float(h["Close"].iloc[-1]); hold=holding_for(ticker); tr=technical_regime(h,ticker)
        _ccmeta=dict(meta) if isinstance(meta,dict) else {}
        # V21.2.4 — reuse the listing-aware enrichment path already proven in Company Search.
        # Merge only non-empty provider fields so Overview does not discard a richer selected-listing payload.
        try:
            _ccrich=_chr_search_market_enrichment_v2074214(ticker) or {}
            for _k,_v in _ccrich.items():
                if _v not in (None, "", "—") and (_ccmeta.get(_k) in (None, "", 0, "—") or _k in {"longName","shortName","sector","industry","marketCap","averageVolume","trailingPE","dividendYield","beta","website","logo_url","logoUrl"}):
                    _ccmeta[_k]=_v
        except Exception:
            pass
        # V21.2.9 — preserve the exact selected-listing identity before falling back to a bare symbol.
        _selected_cc=st.session_state.get("chr_company_search_selected") or {}
        _selected_resolved=str(_selected_cc.get("_resolved") or _selected_cc.get("Ticker") or "").upper()
        if _selected_resolved==str(ticker).upper():
            _sel_name=str(_selected_cc.get("Company") or "").strip()
            if _sel_name and _sel_name.upper() not in {str(ticker).upper(),str(ticker).split(".")[0].upper()}:
                _ccmeta.setdefault("longName",_sel_name)
            for _dst,_src in (("sector","Sector"),("industry","Industry"),("website","Website"),("logo_url","Logo"),("country","Country"),("exchange","Exchange")):
                _v=_selected_cc.get(_src)
                if _v not in (None,"","—") and _ccmeta.get(_dst) in (None,"","—"): _ccmeta[_dst]=_v
        _ccname=_ccmeta.get("longName") or _ccmeta.get("shortName") or cls.get("name") or name or ticker
        _invalid_names={str(ticker).upper(), str(ticker).split(".")[0].upper()}
        if not _ccname or str(_ccname).strip().upper() in _invalid_names:
            try:
                _rn=company_name(ticker) if 'company_name' in globals() else None
                if _rn and str(_rn).strip().upper() not in _invalid_names: _ccname=_rn
            except Exception: pass
        # V21.2.15 — always query the exact Yahoo listing once for current identity, logo and market-session metadata.
        # Search quote payloads can expose logoUrl/marketState even when Ticker.info is otherwise complete.
        _quote_probe_ok=False
        try:
            _quotes=getattr(yf.Search(str(ticker),max_results=8),"quotes",[]) or []
            _exact=next((q for q in _quotes if str(q.get("symbol") or "").upper()==str(ticker).upper()),None)
            if _exact:
                _quote_probe_ok=True
                _qn=_exact.get("longname") or _exact.get("shortname")
                if _qn and str(_qn).strip().upper() not in _invalid_names: _ccname=_qn; _ccmeta["longName"]=_qn
                for _k in ("sector","industry","sectorDisp","industryDisp","exchange","exchDisp","quoteType","logoUrl","marketState","quoteSourceName","exchangeDataDelayedBy","regularMarketTime","regularMarketPrice"):
                    _v=_exact.get(_k)
                    if _v not in (None,"","—"):
                        # Session/freshness fields should be current; identity fields only fill gaps.
                        if _k in {"marketState","quoteSourceName","exchangeDataDelayedBy","regularMarketTime","regularMarketPrice","logoUrl"} or _ccmeta.get(_k) in (None,"","—"):
                            _ccmeta[_k]=_v
        except Exception:
            _quote_probe_ok=False
        _ccmarket=detect_market(ticker,_ccmeta); _ccex=_ccmarket.get("exchange") or _ccmeta.get("exchange") or "—"
        _cccountry=_chr_identity_country(ticker,_ccex,_ccmeta.get("country") or "")
        # International-safe classification cascade. Never substitutes a Nike-specific
        # sector/industry for an unrelated company when provider metadata is missing.
        _safe_tags=safe_classification(_ccmeta,cls)
        _ccsector=_safe_tags["sector"]; _ccindustry=_safe_tags["industry"]
        _identity_check=validate_identity(ticker,_expected_company or _ccname,_ccmeta)
        if not _identity_check.get("valid"):
            st.warning(f"Listing identity could not be verified for {ticker}. Price and company metrics may be withheld until the selected listing is confirmed.")
        _ccprev=float(h["Close"].iloc[-2]) if len(h)>1 else np.nan; _ccchg=price-_ccprev if np.isfinite(_ccprev) else np.nan; _ccpct=_ccchg/_ccprev if np.isfinite(_ccprev) and _ccprev else np.nan
        _cclo=_mia_num(_ccmeta.get("fiftyTwoWeekLow")); _cchi=_mia_num(_ccmeta.get("fiftyTwoWeekHigh"))
        if not np.isfinite(_cclo): _cclo=float(h["Low"].min())
        if not np.isfinite(_cchi): _cchi=float(h["High"].max())
        _ccscore=mia_research_score(ticker,h,_ccmeta); _ccanalyst=analyst_consensus_snapshot(ticker,price); _ccfc=research_forecast(h); _ccforecast_hist=history(ticker,"5y"); _ccadvfc,_ccadvbt=advanced_forecast_snapshot(_ccforecast_hist); _ccauto_val=valuation_pipeline(ticker,price)
        _ccthesis=thesis_table(ticker); _ccann=latest_announcements_safe(ticker,5); _cccatalysts=catalysts_safe(ticker,6); _ccattention=v18_attention(ticker,0,price)
        _ccth_met=int((_ccthesis["status"]=="Met").sum()) if _ccthesis is not None and not _ccthesis.empty and "status" in _ccthesis else 0; _ccth_total=len(_ccthesis) if _ccthesis is not None else 0
        # V21.3.22 — deterministic 12M forecast is a dedicated, single-source service.
        _fc12=build_12m_forecast(_ccforecast_hist,current_price=price,security=ticker)
        _ccf12=_mia_num(_fc12.get("forecast_return")); _fc_target=_mia_num(_fc12.get("target_price"))
        _fc_prob=_mia_num(_fc12.get("probability_positive")); _fcaudit=_fc12.get("audit",{}) or {}
        _fc_prob_n=int(_fcaudit.get("probability_calibration_observations",0) or 0)
        _fcd=_fcaudit.get("diagnostics",{}) or {}
        _fc_diag={"n":int(_fcd.get("n",0) or 0),"mae":_mia_num(_fcd.get("mae")),"direction":_mia_num(_fcd.get("direction_accuracy"))}
        _fc_conf=str(_fc12.get("validation_label") or _fcaudit.get("validation_label") or "Validation limited")
        _ccbase=_mia_num(_ccauto_val.get("base_case")) if isinstance(_ccauto_val,dict) else np.nan
        _ccvals=pd.DataFrame([{"scenario":k,"value_per_share":v.get("value_per_share"),"Margin of safety":v.get("model_gap")} for k,v in ((_ccauto_val.get("scenarios") or {}).items() if isinstance(_ccauto_val,dict) else []) if isinstance(v,dict) and np.isfinite(_mia_num(v.get("value_per_share")))])
        _cctarget=_mia_num(_ccanalyst.get("target")); _cctarget=_mia_num(_ccmeta.get("targetMeanPrice")) if not np.isfinite(_cctarget) else _cctarget
        _ccmcap=_mia_num(_ccmeta.get("marketCap")); _ccpe=_mia_num(_ccmeta.get("trailingPE")); _ccdy=_mia_num(_ccmeta.get("dividendYield")); _ccvol=_mia_num(_ccmeta.get("averageVolume")); _ccbeta=_mia_num(_ccmeta.get("beta"))
        # Prefer true provider averages, then derive an observed 60-session average from loaded history.
        if not np.isfinite(_ccvol):
            for _vk in ("averageDailyVolume10Day","averageVolume10days","averageDailyVolume3Month"):
                _vv=_mia_num(_ccmeta.get(_vk))
                if np.isfinite(_vv) and _vv>0: _ccvol=_vv; break
        if not np.isfinite(_ccvol) and "Volume" in h.columns:
            _hv=pd.to_numeric(h["Volume"],errors="coerce").dropna().tail(60)
            if len(_hv): _ccvol=float(_hv.mean())
        # TTM P/E can be reconstructed only from a confirmed trailing EPS; never substitute forward P/E.
        if not np.isfinite(_ccpe):
            _eps=_mia_num(_ccmeta.get("trailingEps")); _eps=_mia_num(_ccmeta.get("epsTrailingTwelveMonths")) if not np.isfinite(_eps) else _eps
            if np.isfinite(_eps) and _eps>0 and price>0: _ccpe=float(price/_eps)
        # If provider beta is absent, estimate a 1Y weekly beta against the listing's broad benchmark.
        if not np.isfinite(_ccbeta):
            try:
                _bench={"Australia":"^AXJO","United States":"^GSPC","United Kingdom":"^FTSE","Canada":"^GSPTSE","Japan":"^N225","Hong Kong":"^HSI"}.get(_chr_identity_country(ticker,_ccmeta.get("exchange") or "",_ccmeta.get("country") or ""))
                if _bench:
                    _bh=history(_bench,"1y")
                    _sr=pd.to_numeric(h["Close"],errors="coerce").resample("W").last().pct_change()
                    _br=pd.to_numeric(_bh["Close"],errors="coerce").resample("W").last().pct_change()
                    _pair=pd.concat([_sr,_br],axis=1).dropna()
                    if len(_pair)>=20 and float(_pair.iloc[:,1].var())>0: _ccbeta=float(_pair.iloc[:,0].cov(_pair.iloc[:,1])/_pair.iloc[:,1].var())
            except Exception: pass
        _ccvolatility=_mia_num(tr.get("Annualised volatility",np.nan)); _close=pd.to_numeric(h["Close"],errors="coerce").dropna(); _ccmom=float(_close.iloc[-1]/_close.iloc[-127]-1) if len(_close)>126 else np.nan

        st.markdown("""<style>
        /* V21.2.8 — safe header spacing + responsive right-edge containment */
        .main .block-container{padding-top:0!important;}
        .v2121-shell{margin-top:-18px!important;background:#fff;border:1px solid #d9e5f2;border-radius:9px 9px 0 0;box-shadow:0 1px 3px rgba(16,38,75,.04);margin:0;overflow:hidden;border-bottom:0}.v2121-top{display:grid;grid-template-columns:minmax(360px,1.15fr) minmax(230px,.75fr) minmax(470px,1.15fr);align-items:center;gap:12px;padding:7px 14px;border-bottom:1px solid #e4edf7;min-height:50px}.v2121-titleline{display:flex;align-items:center;gap:8px}.v2121-cc-icon{width:22px;height:22px;display:inline-flex;flex:0 0 22px}.v2121-cc-icon svg{width:22px;height:22px;stroke:#1559d6;stroke-width:1.9;fill:none;stroke-linecap:round;stroke-linejoin:round}.v2121-cc-title{font-size:19px;font-weight:900;color:#10264b;line-height:1.05}.v2121-cc-sub{font-size:11px;color:#10264b;margin-top:4px;padding-left:30px}.v2121-sep{color:#c4d1df;margin:0 9px}.v2121-motto{text-align:center;font-size:10px;color:#647b97;white-space:nowrap;justify-self:center}.v2123-actions{display:flex;justify-content:flex-end;gap:9px;align-items:center;white-space:nowrap}.v2123-btn,.v2123-btn:link,.v2123-btn:visited,.v2123-btn:hover,.v2123-btn:active{height:34px;border:1px solid #8aa3c2;border-radius:6px;background:#fff;color:#10264b;padding:0 14px;font:800 11px Arial,sans-serif;display:inline-flex;align-items:center;justify-content:center;text-decoration:none!important;box-sizing:border-box}.v2123-btn.primary,.v2123-btn.primary:hover{background:#0969e8;border-color:#0969e8;color:#fff;min-width:145px}.v2121-company{display:grid;grid-template-columns:90fr 235fr 105fr 145fr 110fr 110fr 95fr 105fr 90fr 155fr 105fr;align-items:center;padding:8px 14px;background:#fff;border:1px solid #d9e5f2;border-top:0;border-radius:0 0 9px 9px;box-shadow:0 1px 3px rgba(16,38,75,.04);margin-bottom:7px;overflow:hidden}.v2121-logo{display:flex;align-items:center;justify-content:flex-start;padding-right:12px;min-width:0}.v2121-logo img{width:78px;max-width:78px;height:46px;max-height:46px;object-fit:contain;object-position:center;image-rendering:auto;display:block}.v2121-fallback{width:92px;height:56px;border-radius:9px;background:#eef5ff;color:#1458aa;display:flex;align-items:center;justify-content:center;font-size:23px;font-weight:900}.v2121-ident{padding-right:14px;min-width:0}.v2121-name{font-size:17px;font-weight:900;color:#10264b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v2121-ticker{display:inline-block;background:#edf4ff;color:#10264b;border-radius:6px;padding:4px 8px;margin-left:7px;font-size:11px;font-weight:900;vertical-align:2px}.v2121-meta,.v2121-desc{font-size:10px;color:#55708e;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v2121-desc{font-size:9px;max-width:345px}.v2121-stat{min-height:58px;border-left:1px solid #e1e9f2;padding:3px 10px;display:flex;flex-direction:column;justify-content:center;min-width:0}.v2121-k{font-size:9px;font-weight:800;color:#637b98;white-space:nowrap}.v2121-v{font-size:14px;font-weight:900;color:#10264b;margin-top:3px;white-space:nowrap}.v2121-up{color:#069a4e;font-size:10px;font-weight:900}.v2121-down{color:#d14343;font-size:10px;font-weight:900}.v2121-range{height:4px;border-radius:4px;background:#dce6f1;position:relative;margin-top:7px;width:100%}.v2121-range-dot{position:absolute;top:-3px;width:10px;height:10px;border-radius:50%;background:#0878ed;transform:translateX(-50%)}.v2121-update{padding:3px 8px!important;min-width:0}.v2121-update .v2121-v{font-size:8px;font-weight:700;line-height:1.15;white-space:nowrap;max-width:100%;overflow:visible}.v2121-update .v2121-k{font-size:8.6px}.v2121-live{font-size:8px;font-weight:800;white-space:nowrap;line-height:1.15;padding-left:7px;min-width:0;overflow:visible}.v2121-live.live{color:#078d4c}.v2121-live.delayed{color:#9a6700}.v2121-live.provider{color:#c73a3a}.v2121-live.neutral{color:#667b94}.v2121-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px}.v2121-live.live .v2121-dot{background:#08a45c}.v2121-live.delayed .v2121-dot{background:#d99a00}.v2121-live.provider .v2121-dot{background:#d14343}.v2121-live.neutral .v2121-dot{background:#8093aa}
        .v21-card{background:#fff;border:1px solid #d9e5f2;border-radius:9px;padding:10px 11px;box-shadow:0 1px 3px rgba(16,38,75,.04);min-height:72px}.v21-k{font-size:9px;letter-spacing:.07em;font-weight:900;color:#71849b;text-transform:uppercase}.v21-v{font-size:18px;font-weight:900;color:#10264b;margin-top:4px}.v21-s{font-size:10px;color:#71849b;margin-top:2px}.v21-section{font-size:16px;font-weight:900;color:#10264b;margin:9px 0 7px}.v21-ai{background:linear-gradient(135deg,#092f5f,#0d4f89);border-radius:13px;padding:15px 17px;color:white;min-height:150px}.v21-ai h3{color:white!important;font-size:16px!important}.v21-ai p{font-size:11px;line-height:1.5;color:#eaf3ff}.v21-change{background:#f5f9ff;border:1px solid #cfe1f5;border-left:5px solid #1672d8;border-radius:10px;padding:10px 13px;margin:7px 0 4px}.v21-change-title{font-size:10px;font-weight:900;letter-spacing:.09em;color:#1672d8;text-transform:uppercase}.v21-change-main{font-size:14px;font-weight:800;color:#10264b}.v21-change-sub{font-size:10px;color:#6c8099}.v21-engine{min-height:96px}.v21-engine-name{font-size:10px;font-weight:900;color:#1672d8;text-transform:uppercase}.v21-engine-main{font-size:16px;font-weight:900;color:#10264b}.v21-engine-link{font-size:9px;color:#1672d8;font-weight:800}.v21-risk{border-left:4px solid #d97706;background:#fffaf2}.v21-opp{border-left:4px solid #1687ff;background:#f7fbff}.v21-foot{font-size:9px;color:#7b8ca1}
        </style>""",unsafe_allow_html=True)
        _deltatxt="—" if not np.isfinite(_ccpct) else f"{_ccchg:+.3f} ({_ccpct:+.2%})"; _delta_cls="v2121-up" if np.isfinite(_ccchg) and _ccchg>=0 else "v2121-down"
        _range_pos=50.0 if _cchi<=_cclo else max(0.0,min(100.0,(price-_cclo)/(_cchi-_cclo)*100.0)); _logo_candidates=_chr_identity_logo_candidates(ticker,_ccmeta,_ccname,192); _initials="".join([x[0] for x in str(_ccname).split()[:3] if x])[:3].upper() or str(ticker).split(".")[0][:3].upper()
        # V21.2.35 — resolve every candidate server-side. Browser hot-link/CSP failures
        # can no longer leave a broken-image icon in the Command Centre.
        _resolved_logo=_chr_resolved_logo_data_uri(ticker,_ccname,tuple(_logo_candidates)) if _logo_candidates else ""
        if _resolved_logo:
            _logo_html=f'<img src="{html.escape(_resolved_logo,quote=True)}" alt="{html.escape(str(_ccname),quote=True)} logo">'
        else:
            _logo_html=f'<div class="v2121-fallback">{html.escape(_initials)}</div>'
        _desc=str(_ccmeta.get("tagline") or _ccmeta.get("description") or "").strip()
        if not _desc:
            _summary=str(_ccmeta.get("longBusinessSummary") or "").strip()
            _desc=(_summary.split(". ",1)[0]+("." if _summary and "." in _summary else "")) if _summary else ""
        _desc=(_desc[:112].rstrip()+"…") if len(_desc)>115 else _desc; _currency=str(_ccmeta.get("currency") or "")
        _mcap_txt=compact_number(_ccmcap,prefix=("A$" if _currency=="AUD" else "$")) if np.isfinite(_ccmcap) else "—"; _vol_txt=compact_number(_ccvol) if np.isfinite(_ccvol) else "—"; _pe_txt=f"{_ccpe:.1f}×" if np.isfinite(_ccpe) else "—"; _ccdy_display=(_ccdy/100.0 if np.isfinite(_ccdy) and _ccdy>1 else _ccdy); _dy_txt=f"{_ccdy_display:.2%}" if np.isfinite(_ccdy_display) else "—"; _beta_txt=f"{_ccbeta:.2f}" if np.isfinite(_ccbeta) else "—"; _updated=pd.Timestamp.now(tz="Australia/Melbourne").strftime("%d %b %Y %I:%M%p AEST").replace(" 0"," ")
        # V21.2.5 — surface data freshness honestly. Only call the feed live when the provider explicitly identifies it as real-time/live.
        _quote_type=str(_ccmeta.get("quoteType") or "").strip().lower()
        _market_state=str(_ccmeta.get("marketState") or "").strip().lower()
        if not _market_state:
            try:
                _hm=history_metadata(ticker)
                _market_state=str(_hm.get("marketState") or _hm.get("market_state") or "").strip().lower()
            except Exception:
                pass
        _delay=_mia_num(_ccmeta.get("exchangeDataDelayedBy"))
        _source_name=str(_ccmeta.get("quoteSourceName") or "").strip()
        _explicit_live=bool(_ccmeta.get("isRealtime") is True or _ccmeta.get("realtime") is True or str(_ccmeta.get("dataStatus") or "").strip().lower() in {"live","real-time","realtime"} or "real time" in _source_name.lower() or "realtime" in _source_name.lower())
        _market_open=_market_state in {"regular","open","continuous","trading"}
        _market_closed=_market_state in {"closed","post","postpost","pre","prepre"}
        # V21.2.15 — Yahoo Search often omits marketState. Use the listing's current
        # regular trading-period timestamps from history metadata as the authoritative
        # session fallback. This is exchange-aware and handles US/AU/UK/etc time zones
        # without assuming the user's local clock.
        try:
            _hm2=history_metadata(ticker)
            _ctp=_hm2.get("currentTradingPeriod") or _hm2.get("current_trading_period") or {}
            _reg=_ctp.get("regular") or {}
            _rs=_mia_num(_reg.get("start")); _re=_mia_num(_reg.get("end"))
            _now_epoch=float(pd.Timestamp.now(tz="UTC").timestamp())
            if np.isfinite(_rs) and np.isfinite(_re):
                _market_open=bool(_rs <= _now_epoch < _re)
                if not _market_open and not _market_state:
                    _market_closed=True
        except Exception:
            pass
        if _market_open:
            _data_status="Market open"; _data_status_cls="live"
        elif np.isfinite(_delay) and _delay > 0:
            _mins=int(round(_delay)); _data_status=f"Delayed {_mins}m"; _data_status_cls="delayed"
        elif _explicit_live:
            _data_status="Live data"; _data_status_cls="live"
        elif _market_closed:
            _data_status="Market closed"; _data_status_cls="neutral"
        elif _quote_probe_ok or (h is not None and not h.empty):
            _data_status="Provider data"; _data_status_cls="neutral"
        else:
            _data_status="Provider offline"; _data_status_cls="provider"
        _cc_href=f"?chr_cc={_urlquote(str(ticker))}&chr_cc_page=Overview#investment-command-centre"
        _compare_href=f"?chr_compare={_urlquote(str(ticker))}#company-comparison"
        st.markdown(f"""<div class="v2121-shell"><div class="v2121-top"><div><div class="v2121-titleline"><span class="v2121-cc-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v13"></path><path d="M8.5 6.5 12 3l3.5 3.5"></path><path d="M7 9.5h10"></path><path d="M6 9.5 3.5 14h5L6 9.5Z"></path><path d="M18 9.5 15.5 14h5L18 9.5Z"></path><path d="M9 20h6"></path><path d="M10 16h4v4h-4z"></path></svg></span><div class="v2121-cc-title">Company Command Centre</div></div><div class="v2121-cc-sub"><b>Overview</b><span class="v2121-sep">|</span>{html.escape(str(ticker))} – {html.escape(str(_ccname))}</div></div><div class="v2121-motto">All the evidence. A clearer perspective.</div><div class="v2123-actions"><a class="v2123-btn" href="#watchlist">☆&nbsp; Add to Watchlist</a><a class="v2123-btn" href="{_compare_href}">↗&nbsp; Compare</a><a class="v2123-btn primary" href="{_cc_href}" target="_blank" rel="noopener">Open in new tab&nbsp; →</a></div></div></div>""",unsafe_allow_html=True)
        st.markdown(f"""<div class="v2121-company"><div class="v2121-logo">{_logo_html}</div><div class="v2121-ident"><div class="v2121-name">{html.escape(str(_ccname))}<span class="v2121-ticker">{html.escape(str(ticker))}</span></div><div class="v2121-meta">{html.escape(str(_ccsector))}<span class="v2121-sep">|</span>{html.escape(str(_ccindustry))}</div><div class="v2121-desc">{html.escape(_desc)}</div></div><div class="v2121-stat"><div class="v2121-k">Share Price</div><div class="v2121-v">{display_price(price,ticker)}</div><div class="{_delta_cls}">{html.escape(_deltatxt)}</div></div><div class="v2121-stat"><div class="v2121-k">52 Week Range</div><div class="v2121-v">{display_price(_cclo,ticker)} – {display_price(_cchi,ticker)}</div><div class="v2121-range"><span class="v2121-range-dot" style="left:{_range_pos:.1f}%"></span></div></div><div class="v2121-stat"><div class="v2121-k">Market Cap</div><div class="v2121-v">{html.escape(_mcap_txt)}</div></div><div class="v2121-stat"><div class="v2121-k">Volume (Avg)</div><div class="v2121-v">{html.escape(_vol_txt)}</div></div><div class="v2121-stat"><div class="v2121-k">P/E (TTM)</div><div class="v2121-v">{html.escape(_pe_txt)}</div></div><div class="v2121-stat"><div class="v2121-k">Dividend Yield</div><div class="v2121-v">{html.escape(_dy_txt)}</div></div><div class="v2121-stat"><div class="v2121-k">Beta (5Y)</div><div class="v2121-v">{html.escape(_beta_txt)}</div></div><div class="v2121-stat v2121-update"><div class="v2121-k">Last Updated</div><div class="v2121-v">{html.escape(_updated)}</div></div><div class="v2121-live {_data_status_cls}"><span class="v2121-dot"></span>{html.escape(_data_status)}</div></div>""",unsafe_allow_html=True)

        _change_count=0 if _ccattention is None or _ccattention.empty else len(_ccattention)
        _change_main=("No material monitoring changes are currently flagged from loaded evidence." if _change_count==0 else f"{_change_count} monitoring item"+(" requires" if _change_count==1 else "s require")+" attention from the currently loaded evidence.")
        _change_sub=f"Evidence coverage {_ccscore.get('Available',0)}/{_ccscore.get('Total',6)} · Technical: {tr.get('Trend','—')} · Thesis: "+(f"{_ccth_met}/{_ccth_total} conditions met" if _ccth_total else "not configured")+" · Valuation: "+("loaded" if np.isfinite(_mia_num(_ccbase)) else "evidence gap")
        # V21.2.18 — Overview Evidence Monitor remains removed; Price Chart restyled to reference proportions.
        # The standalone Something Changed research tool remains available elsewhere in Chrímata.

        # V21.2.16 — reference-matched Overview intelligence row: interactive Price Chart,
        # live Thesis Scorecard summary, and evidence-constrained AI Research Brief.
        st.markdown("""<style>
        /* V21.2.43 — true white Price Chart card + isolated volume band. */
        .st-key-v21243_price_card,
        .st-key-v21243_price_card > div,
        .st-key-v21243_price_card [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-v21243_price_card [data-testid="stVerticalBlock"],
        .st-key-v21243_price_card [data-testid="stElementContainer"],
        .st-key-v21243_price_card [data-testid="stPlotlyChart"]{background:#fff!important;background-color:#fff!important;}
        .st-key-v21243_price_card [data-testid="stVerticalBlockBorderWrapper"]{border-color:#fff!important;box-shadow:none!important;}
        .st-key-v21243_price_card{background:#fff!important;border-radius:9px!important;overflow:hidden!important;}
        [data-testid="stVerticalBlockBorderWrapper"]:has(.v21241-overview-card){background:#fff!important;background-color:#fff!important;}
        [data-testid="stVerticalBlockBorderWrapper"]:has(.v21241-overview-card) > div{background:#fff!important;background-color:#fff!important;}
        [data-testid="stVerticalBlockBorderWrapper"]:has(.v21241-overview-card) [data-testid="stVerticalBlock"]{background:#fff!important;background-color:#fff!important;}
        .v21241-overview-card{height:0;margin:0;padding:0;overflow:hidden}
        [data-testid="stVerticalBlockBorderWrapper"]:has(.v21241-overview-card){overflow:hidden!important;}
        [data-testid="stVerticalBlockBorderWrapper"]:has(.v21241-overview-card) [data-testid="stPlotlyChart"]{background:#fff!important;margin-bottom:0!important;}
        .v21216-widget-title{font-size:16px;font-weight:900;color:#10264b;margin:0 0 2px}
        /* V21.2.55 — functional reference Thesis Scorecard: six-row starter template + stored-rule live status. */
        .v21216-thesis-score{font-size:27px;font-weight:900;color:#08a142;line-height:1.05;margin:2px 0 7px}.v21216-thesis-score span{font-size:12px;color:#29476f;font-weight:700;margin-left:3px}
        .v21245-thesis-progress{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:7px;align-items:center;margin:1px 0 8px}.v21245-thesis-track{height:11px;background:#dfe9f4;border-radius:99px;overflow:hidden}.v21245-thesis-fill{height:100%;background:#08a142;border-radius:99px}.v21245-thesis-pct{font-size:11px;font-weight:900;color:#29476f}
        .v21324-thesis-template{font-size:8.5px;font-weight:800;color:#6a819b;margin:-2px 0 4px}.v21254-thesis-list{margin:0;padding:0}
        .v21216-thesis-row{display:grid;grid-template-columns:20px minmax(0,1fr) 62px;align-items:center;gap:7px;border-bottom:1px solid #e5edf6;padding:5px 0;font-size:11px;font-weight:650;color:#26466e;line-height:1.15;min-height:27px;box-sizing:border-box}.v21216-thesis-row:last-child{border-bottom:0}
        .v21216-thesis-icon{width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:900;background:#91a4ba}.v21216-thesis-icon.met{background:#0aa64a}.v21216-thesis-icon.watch{background:#f5a300}.v21216-thesis-status{font-size:10px;font-weight:800;white-space:nowrap;text-align:right}.v21216-thesis-status.met{color:#0aa64a}.v21216-thesis-status.watch{color:#f5a300}.v21216-thesis-status.pending{color:#7890aa}
        .v21245-thesis-empty{font-size:10px;color:#7890aa;padding:12px 0 0;min-height:146px}.st-key-v21255_thesis_card,[class*="st-key-v21255_thesis_card"]{background:#fff!important}.st-key-v21255_thesis_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-v21255_thesis_card [data-testid="stVerticalBlock"],.st-key-v21255_thesis_card [data-testid="stElementContainer"]{background:#fff!important;background-color:#fff!important}.st-key-v21255_thesis_card [data-testid="stVerticalBlockBorderWrapper"]{border-color:#d9e5f2!important;box-shadow:none!important}.st-key-v21255_thesis_card{border-radius:9px!important;overflow:hidden!important}
        [class*="st-key-v21255_thesis_card"] [data-testid="stVerticalBlock"]{gap:0!important;row-gap:0!important}
        [class*="st-key-v21255_thesis_link_"]{margin-top:4px!important;width:100%!important}[class*="st-key-v21255_thesis_link_"] .stButton{display:flex!important;justify-content:flex-end!important;width:100%!important}[class*="st-key-v21255_thesis_link_"] .stButton>button{background:transparent!important;border:0!important;box-shadow:none!important;color:#086ee8!important;font-size:10px!important;font-weight:900!important;padding:0!important;min-height:22px!important;height:22px!important;white-space:nowrap!important;width:auto!important;max-width:none!important;overflow:visible!important;text-overflow:clip!important}[class*="st-key-v21255_thesis_link_"] .stButton>button p{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important}[class*="st-key-v21255_thesis_link_"] .stButton>button:hover{background:transparent!important;color:#005dcc!important;border:0!important}
        .v21216-ai-head{display:flex;gap:10px;align-items:flex-start;margin:0 0 10px 0}.v21216-ai-icon{width:34px;height:34px;flex:0 0 34px;color:#10264b;margin-top:1px}.v21216-ai-icon svg{display:block;width:34px;height:34px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.v21216-ai-copy{min-width:0;flex:1}.v21216-ai-title{display:flex;align-items:center;gap:8px;font-size:16px;line-height:1.1;font-weight:900;color:#10264b;white-space:nowrap}.v21216-beta{display:inline-flex;align-items:center;justify-content:center;background:#0b6ee8;color:#fff;border-radius:4px;font-size:9px;line-height:1;padding:5px 8px;margin:0;vertical-align:0;box-shadow:0 1px 2px rgba(11,110,232,.18)}.v21216-ai-sub{font-size:9.5px;line-height:1.25;color:#567292;font-weight:700;margin-top:4px;white-space:nowrap}.v21216-ai-info{background:#eef6ff;border:1px solid #d9eaff;border-radius:8px;padding:10px 11px;font-size:9.5px;line-height:1.42;color:#315d96;margin:0 0 10px}.v21216-ai-time{text-align:center;color:#748aa4;font-size:9px;line-height:1.2;margin:6px 0 0}
        [class*="st-key-v21257_ai_card"]{background:#fff!important;border-radius:9px!important;overflow:hidden!important}[class*="st-key-v21257_ai_card"] [data-testid="stVerticalBlockBorderWrapper"],[class*="st-key-v21257_ai_card"] [data-testid="stVerticalBlock"],[class*="st-key-v21257_ai_card"] [data-testid="stElementContainer"]{background:#fff!important;background-color:#fff!important}[class*="st-key-v21257_ai_card"] [data-testid="stVerticalBlock"]{gap:0!important;row-gap:0!important}[class*="st-key-v21257_ai_card"] [data-testid="stVerticalBlockBorderWrapper"]{border-color:#d9e5f2!important;box-shadow:none!important}
        [class*="st-key-v21257_generate_ai_"]{margin:0!important;padding:0!important}[class*="st-key-v21257_generate_ai_"] .stButton>button{height:42px!important;min-height:42px!important;border-radius:6px!important;background:#086ee8!important;border:1px solid #086ee8!important;box-shadow:none!important;font-size:11px!important;font-weight:900!important;padding:0 12px!important}[class*="st-key-v21257_generate_ai_"] .stButton>button:hover{background:#075fc8!important;border-color:#075fc8!important}
        [class*="st-key-v21257_brief_view_"]{margin-top:6px!important}[class*="st-key-v21257_brief_view_"] details{border:0!important;background:transparent!important}[class*="st-key-v21257_brief_view_"] summary{font-size:9px!important;color:#086ee8!important;padding:2px 0!important;justify-content:center!important;min-height:20px!important}
        .st-key-v21256_ai_card,[class*="st-key-v21256_ai_card"]{background:#fff!important;border-radius:9px!important;overflow:hidden!important}.st-key-v21256_ai_card [data-testid="stVerticalBlockBorderWrapper"],.st-key-v21256_ai_card [data-testid="stVerticalBlock"],.st-key-v21256_ai_card [data-testid="stElementContainer"]{background:#fff!important;background-color:#fff!important}
        .v21216-link{font-size:10px;font-weight:900;color:#086ee8;text-align:right;margin-top:3px}.v21216-range-note{font-size:9px;color:#7287a1;margin-top:-5px;margin-bottom:2px}
        /* V21.2.52 — compact reference geometry: no dead gaps, readable volume, footer locked inside card. */
        [class*="st-key-v21243_price_card"] [data-testid="stVerticalBlock"]{gap:0!important;row-gap:0!important}
        [class*="st-key-v21243_price_card"] [data-testid="stElementContainer"]{margin:0!important;padding:0!important}
        [class*="st-key-v21243_price_card"] [data-testid="stPlotlyChart"]{margin:0!important;padding:0!important}
        /* V21.3.23.1 — compact dashboard geometry, scoped to Price Chart only. */
        [class*="st-key-v21243_price_card"]{min-width:0!important}
        [class*="st-key-v21243_price_card"] [data-testid="stVerticalBlockBorderWrapper"]{overflow:hidden!important}
        [class*="st-key-v21243_price_card"] [data-testid="stCheckbox"]{margin:0!important}
        [class*="st-key-v21243_price_card"] [data-baseweb="select"]{min-height:34px!important}
        [class*="st-key-v21243_price_card"] [data-baseweb="select"]>div{min-height:34px!important;padding-top:0!important;padding-bottom:0!important}
        .v213231-macro-note{font-size:9.5px;line-height:16px;height:16px;color:#6d7d92;margin:0!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}
        /* V21.3.23.2 — fixed-height macro slot keeps the footer stationary across reruns. */
        .v213232-macro-slot{height:16px;min-height:16px;max-height:16px;overflow:hidden;margin:0!important;padding:0!important}
        /* Reference-style active timeframe: solid Chrímata blue with white text. */
        [class*="st-key-v213171_timeframe_"] button[aria-pressed="true"],
        [class*="st-key-v213171_timeframe_"] button[data-selected="true"]{
            background:#086ee8!important;border-color:#086ee8!important;color:#fff!important;
            box-shadow:0 1px 3px rgba(8,110,232,.24)!important;
        }
        [class*="st-key-v213171_timeframe_"] button[aria-pressed="true"] *,
        [class*="st-key-v213171_timeframe_"] button[data-selected="true"] *{color:#fff!important}
        [class*="st-key-v213171_timeframe_"] button:not([aria-pressed="true"]){background:#fff!important;color:#162a46!important}
        .v213231-macro-note b{color:#4d6480;font-weight:800}
        .v213231-macro-note span{color:#086ee8;font-weight:900;cursor:help}
        [class*="st-key-v213172_technical_"] .stButton>button{
            background:transparent!important;border:0!important;box-shadow:none!important;color:#086ee8!important;
            font-size:10px!important;font-weight:850!important;padding:0 2px!important;margin:0!important;
            min-height:22px!important;height:22px!important;width:auto!important;min-width:0!important;
        }
        [class*="st-key-v213172_technical_"] .stButton>button:hover{background:transparent!important;color:#005dcc!important;border:0!important}
        /* V21.3.23.3 — fixed footer geometry and visible white breathing room. */
        [class*="st-key-v213172_technical_"]{min-height:24px!important;margin:0!important;padding:0!important}
        .v213233-price-bottom-space{height:18px;min-height:18px;width:100%;display:block}
        [class*="st-key-v21243_price_card"] [data-testid="stHorizontalBlock"]{flex-shrink:0!important}
        [class*="st-key-v213171_timeframe_"] [aria-checked="true"],
        [class*="st-key-v213171_timeframe_"] [data-state="on"],
        [class*="st-key-v213171_timeframe_"] [data-state="checked"]{background:#086ee8!important;border-color:#086ee8!important;color:#fff!important}
        [class*="st-key-v213171_timeframe_"] [aria-checked="true"] *,
        [class*="st-key-v213171_timeframe_"] [data-state="on"] *,
        [class*="st-key-v213171_timeframe_"] [data-state="checked"] *{color:#fff!important}
        .v21249-chart-legend{display:flex;align-items:center;gap:12px;height:22px;margin:0!important;padding:0!important;font-size:10px;color:#162a46;line-height:22px;white-space:nowrap;box-sizing:border-box}
        .v21249-chart-legend .lg{display:inline-flex;align-items:center;gap:7px}
        .v21249-chart-legend .line{display:inline-block;width:30px;height:4px;border-radius:0}
        .v21249-chart-legend .sma20{background:#24aee8}.v21249-chart-legend .sma50{background:#ff334f}
        .v21249-chart-legend .volbars{display:inline-flex;align-items:flex-end;gap:2px;width:15px;height:13px}
        .v21249-chart-legend .volbars i{display:block;width:3px;background:#f5a300;border-radius:1px 1px 0 0}.v21249-chart-legend .volbars i:nth-child(1){height:8px}.v21249-chart-legend .volbars i:nth-child(2){height:13px}.v21249-chart-legend .volbars i:nth-child(3){height:10px}.v21249-chart-legend .volbars i:nth-child(4){height:6px}
        [class*="st-key-v21252_technical_"]{margin:0!important;padding:0!important;height:22px!important;display:flex!important;align-items:center!important;justify-content:flex-end!important}
        [class*="st-key-v21252_technical_"] .stButton{display:flex!important;justify-content:flex-end!important;align-items:center!important;width:100%!important;height:22px!important;margin:0!important;padding:0!important}
        [class*="st-key-v21252_technical_"] .stButton>button{background:transparent!important;border:0!important;box-shadow:none!important;color:#086ee8!important;font-size:10px!important;font-weight:900!important;padding:0!important;margin:0!important;min-height:22px!important;height:22px!important;width:auto!important;min-width:max-content!important;white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important}
        [class*="st-key-v21252_technical_"] .stButton>button p{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;margin:0!important;padding:0!important;line-height:22px!important;height:22px!important;display:flex!important;align-items:center!important}
        [class*="st-key-v21252_technical_"] .stButton>button:hover{background:transparent!important;color:#005dcc!important;border:0!important}
        /* V21.2.53 — reference active timeframe styling only. Plotly 6.5.2 marks the
           active/hover update-menu button with #F4FAFF; recolour that state to Chrímata blue. */
        [class*="st-key-v21243_price_card"] g.updatemenu-button:has(rect.updatemenu-item-rect[style*="244, 250, 255"]) rect.updatemenu-item-rect{
            fill:#086ee8!important;stroke:#086ee8!important;
        }
        [class*="st-key-v21243_price_card"] g.updatemenu-button:has(rect.updatemenu-item-rect[style*="244, 250, 255"]) text.updatemenu-item-text{
            fill:#ffffff!important;
        }
        /* V21.2.34 — footer rebuilt inside Plotly so legend + technical link share one compact row */
        .v21218-chart-tabs{display:flex;align-items:center;gap:10px;border-bottom:1px solid #e4edf7;margin:0 0 8px;padding:0 0 7px}
        .v21218-chart-tabs a{color:#557398!important;text-decoration:none!important;font-size:10px;font-weight:800;line-height:1;padding:6px 9px;border-radius:5px;min-width:26px;text-align:center}
        .v21218-chart-tabs a:hover{color:#086ee8!important;background:#f1f7ff}
        .v21218-chart-tabs a.active{background:#086ee8;color:#fff!important;box-shadow:0 1px 3px rgba(8,110,232,.25)}
                </style>""",unsafe_allow_html=True)
        # V21.2.62 — compact Company Intelligence Strip.
        # This is a read-only summary of the evidence already loaded above; it does not
        # trigger additional provider calls, so it preserves the faster Overview navigation.
        _rs=_mia_num(_ccscore.get("Overall"))
        _rs_txt=f"{_rs:.0f} / 100" if np.isfinite(_rs) else "— / 100"
        _rs_label=("High" if np.isfinite(_rs) and _rs>=65 else "Modest" if np.isfinite(_rs) and _rs>=45 else "Low" if np.isfinite(_rs) else "Evidence gap")
        # V21.2.68 — retain the prior distinct Research Score in-session so ordinary
        # Streamlit reruns do not erase the last-review comparison.
        _rs_state_key=f"v21267_research_score_{ticker}"
        _rs_prev_key=f"v21267_research_score_prev_{ticker}"
        if np.isfinite(_rs):
            _rs_seen=st.session_state.get(_rs_state_key)
            if _rs_seen is None:
                st.session_state[_rs_state_key]=float(_rs)
            elif np.isfinite(_mia_num(_rs_seen)) and abs(float(_rs)-float(_rs_seen))>=0.5:
                st.session_state[_rs_prev_key]=float(_rs_seen)
                st.session_state[_rs_state_key]=float(_rs)
        _rs_prev=_mia_num(st.session_state.get(_rs_prev_key))
        _rs_delta=(float(_rs)-float(_rs_prev)) if np.isfinite(_rs) and np.isfinite(_rs_prev) else np.nan
        if np.isfinite(_rs_delta):
            _rs_change=(f"↑ +{_rs_delta:.0f} vs last review" if _rs_delta>0 else f"↓ {_rs_delta:.0f} vs last review" if _rs_delta<0 else "No change vs last review")
        else:
            _rs_change="Baseline established"
        _rs_gauge=max(0.0,min(100.0,float(_rs))) if np.isfinite(_rs) else 0.0
        _rs_dash=round(119.38*(_rs_gauge/100.0),2)
        _rs_angle=np.pi-(np.pi*_rs_gauge/100.0)
        _rs_nx=50 + 27*np.cos(_rs_angle); _rs_ny=50 - 27*np.sin(_rs_angle)
        _rs_gauge_html=f'<div class="v21267-rs-gauge" aria-label="Research score {_rs_txt}"><svg viewBox="0 0 100 58" role="img"><path class="v21267-rs-track" d="M 12 50 A 38 38 0 0 1 88 50"/><path class="v21267-rs-fill" d="M 12 50 A 38 38 0 0 1 88 50" pathLength="100" style="stroke-dasharray:{_rs_gauge:.1f} 100"/><line class="v21267-rs-needle" x1="50" y1="50" x2="{_rs_nx:.2f}" y2="{_rs_ny:.2f}"/><circle class="v21267-rs-hub" cx="50" cy="50" r="3.2"/></svg></div>'
        _val_pct=((_ccbase/price)-1) if np.isfinite(_mia_num(_ccbase)) and price else np.nan
        _val_label=("Below base case" if np.isfinite(_val_pct) and _val_pct>=.10 else "Above base case" if np.isfinite(_val_pct) and _val_pct<=-.10 else "Near base case" if np.isfinite(_val_pct) else "Unavailable")
        # V21.2.69 — connect the Overview Valuation card to the forward validation engine.
        # Confidence is withheld until there is a minimally useful matured sample; no synthetic
        # accuracy score is shown while the model is still establishing its track record.
        try:
            _val_validation=valuation_validation_summary(ticker)
        except Exception:
            _val_validation={"Observations":0,"Median Error":np.nan,"Direction Accuracy":np.nan,"Range Hit":np.nan}
        _val_obs=int(_mia_num(_val_validation.get("Observations"))) if np.isfinite(_mia_num(_val_validation.get("Observations"))) else 0
        _val_err=_mia_num(_val_validation.get("Median Error"))
        _val_dir=_mia_num(_val_validation.get("Direction Accuracy"))
        _val_hit=_mia_num(_val_validation.get("Range Hit"))
        if _val_obs < 8:
            _val_conf="Validation pending"
        else:
            _err_component=max(0.0,min(1.0,1.0-(_val_err/50.0))) if np.isfinite(_val_err) else np.nan
            _parts=[x for x in [_val_dir,_val_hit,_err_component] if np.isfinite(x)]
            _confidence_score=float(np.mean(_parts)) if _parts else np.nan
            _val_conf=("High confidence" if np.isfinite(_confidence_score) and _confidence_score>=.75 else "Moderate confidence" if np.isfinite(_confidence_score) and _confidence_score>=.55 else "Low confidence" if np.isfinite(_confidence_score) else "Validation pending")
        _val_conf_text=f"{_val_conf} · {_val_obs} matured obs" if _val_obs else "Validation pending · no matured observations"
        # V21.3.19.2.1 — initialise valuation audit inputs before any diagnostic reads.
        # This prevents the Overview card from referencing _vinputs before assignment.
        _vaudit=_ccauto_val.get("audit",{}) if isinstance(_ccauto_val,dict) else {}
        _vinputs=_vaudit.get("inputs",{}) if isinstance(_vaudit,dict) else {}
        if not np.isfinite(_val_pct):
            _derived_fcf=isinstance(_vinputs.get("fcf"),dict) and _vinputs.get("fcf",{}).get("status")=="derived"
            if _derived_fcf: _val_conf_text="FCF derived from cash-flow statement · validation pending"
        _vmissing=[k.replace("_"," ").title() for k,v in _vinputs.items() if isinstance(v,dict) and v.get("status")=="missing"]
        _vreason=str(_ccauto_val.get("reason") or "") if isinstance(_ccauto_val,dict) else ""
        _vblock=(_vaudit.get("blocking_reasons") or []) if isinstance(_vaudit,dict) else []
        _val_move=(f"Model gap: {_val_pct:+.0%}" if np.isfinite(_val_pct) else _compact_valuation_blocker(_vaudit,(_vreason[:25]+"…" if len(_vreason)>26 else (_vreason or "Evidence required"))))
        _val_move_cls=("up" if np.isfinite(_val_pct) and _val_pct>=.10 else "down" if np.isfinite(_val_pct) and _val_pct<=-.10 else "neutral")
        # V21.3.20 — compact Technicals card uses the deterministic composite engine,
        # not an RSI-only label. Missing indicators remain Pending and reduce evidence coverage.
        try:
            _tech_payload=calculate_technical_snapshot(h)
        except Exception:
            _tech_payload={"technical_status":"Pending","rsi_value":None,"context":"Insufficient technical evidence","evidence_coverage":0}
        _rsi_strip=_mia_num(_tech_payload.get("rsi_value"))
        _tech_label=str(_tech_payload.get("technical_status") or "Pending")
        _tech_context=str(_tech_payload.get("context") or _tech_payload.get("description") or "Insufficient technical evidence")
        _tech_sub=f"RSI {_rsi_strip:.0f} · {_tech_payload.get('evidence_coverage',0)}% evidence" if np.isfinite(_rsi_strip) else f"RSI — · {_tech_payload.get('evidence_coverage',0)}% evidence"
        _an_label=str(_ccanalyst.get("label") or "Unavailable")
        _an_n=int(_mia_num(_ccanalyst.get("analysts"))) if np.isfinite(_mia_num(_ccanalyst.get("analysts"))) else 0
        _an_target=_mia_num(_ccanalyst.get("target_mean")); _an_target=_cctarget if not np.isfinite(_an_target) else _an_target
        _an_up=(_an_target/price-1) if np.isfinite(_an_target) and price else np.nan
        _an_source=str(_ccanalyst.get("source") or "Provider source unavailable")
        _an_provider_date=str(_ccanalyst.get("provider_date") or "Unavailable")
        _an_low=_mia_num(_ccanalyst.get("target_low")); _an_high=_mia_num(_ccanalyst.get("target_high"))
        _an_dist=" · ".join([f"Strong Buy {_ccanalyst.get('strongBuy',0)}",f"Buy {_ccanalyst.get('buy',0)}",f"Hold {_ccanalyst.get('hold',0)}",f"Sell {_ccanalyst.get('sell',0)}",f"Strong Sell {_ccanalyst.get('strongSell',0)}"])
        _an_range=(f"{display_price(_an_low,ticker)}–{display_price(_an_high,ticker)}" if np.isfinite(_an_low) and np.isfinite(_an_high) else "Unavailable")
        _an_provenance=(f"Source: {_an_source} | Provider date: {_an_provider_date} | Analyst distribution: {_an_dist} | Target range: {_an_range}")
        _fc_target=price*(1+_ccf12) if np.isfinite(_ccf12) and price else np.nan
        # V21.2.80 — Thesis Status Monitoring Engine. Stored user thesis rules take
        # precedence. When none exist, evaluate the six company-aware monitoring
        # conditions from traceable provider/model evidence. Missing evidence stays
        # Pending and can never be silently counted as meeting expectations.
        _th_engine_source="Stored thesis conditions"
        if _ccth_total and _ccthesis is not None and not _ccthesis.empty:
            _th_monitor=_ccthesis.copy()
            _th_statuses=_th_monitor.get("status",pd.Series(dtype=str)).astype(str).str.strip().str.lower()
            _th_total=int(len(_th_monitor))
            _th_met=int(_th_statuses.isin({"met","on track","on_track","pass","passed","true"}).sum())
            _th_watch=int(_th_statuses.isin({"watch","warning","at risk","at_risk","attention","broken","fail","failed","false"}).sum())
            _th_pending=max(0,_th_total-_th_met-_th_watch)
        else:
            _th_engine_source="Chrímata evidence-driven monitoring"
            try:
                _th_monitor=overview_dynamic_thesis(ticker,_ccsector,_ccindustry,_ccmeta,_ccbase,price)
            except Exception:
                _th_monitor=pd.DataFrame(columns=["metric","status","evidence","source"])
            _th_statuses=_th_monitor.get("status",pd.Series(dtype=str)).astype(str).str.strip().str.lower()
            _th_total=int(len(_th_monitor))
            _th_met=int(_th_statuses.isin({"met","on track","on_track","pass","passed","true"}).sum())
            _th_watch=int(_th_statuses.isin({"watch","warning","at risk","at_risk","attention","broken","fail","failed","false"}).sum())
            _th_pending=max(0,_th_total-_th_met-_th_watch)
        # V21.3.23 — the compact card and Thesis Scorecard consume the same condition payload.
        # This aggregator performs no financial calculations; Pending remains unknown, not failure.
        _th_summary=calculate_thesis_status(_th_monitor,expected_total=(_th_total or 6),source=_th_engine_source)
        _th_total=int(_th_summary["total_conditions"]); _th_met=int(_th_summary["on_track_count"])
        _th_watch=int(_th_summary["watch_count"]); _th_pending=int(_th_summary["pending_count"])
        _th_evidenced=int(_th_summary["evaluated_count"]); _th_label=str(_th_summary["status_label"])
        _th_card_cls="amber" if _th_summary["ui_state"]=="watch" else "good"
        _th_sub=f"{_th_met} / {_th_total} conditions on track"
        _th_metric_line=f"{_th_evidenced} evaluated · {_th_pending} awaiting evidence"
        _th_provenance=(f"{_th_engine_source}; {_th_evidenced}/{_th_total} conditions evaluated; "
                        f"{_th_pending} pending; evidence coverage {_th_summary['evidence_coverage']:.0%}; AI calculated: No.")
        # V21.3.18 — deterministic Research Score derived from the same thesis
        # conditions shown by the Thesis Scorecard. Pending is unknown, not failure.
        _rs_conditions={}
        if _th_monitor is not None and not _th_monitor.empty:
            for _ri,_row in _th_monitor.iterrows():
                _rk=str(_row.get("metric") or f"condition_{_ri}")
                _rs_conditions[_rk]=_row.get("status")
        _research_payload=calculate_research_score(_rs_conditions)
        _rs=_research_payload.get("research_score")
        _rs_txt=f"{int(_rs)} / 100" if _rs is not None else "— / 100"
        _rs_label=_research_payload.get("score_label","Insufficient evidence")
        _rs_change=f"{_research_payload.get('evidence_coverage',0)}% evidence coverage"
        _rs_delta=np.nan
        _rs_gauge=max(0.0,min(100.0,float(_rs))) if _rs is not None else 0.0
        _rs_angle=np.pi-(np.pi*_rs_gauge/100.0)
        _rs_nx=50 + 27*np.cos(_rs_angle); _rs_ny=50 - 27*np.sin(_rs_angle)
        _rs_gauge_html=f'<div class="v21267-rs-gauge" aria-label="Research score {_rs_txt}"><svg viewBox="0 0 100 58" role="img"><path class="v21267-rs-track" d="M 12 50 A 38 38 0 0 1 88 50"/><path class="v21267-rs-fill" d="M 12 50 A 38 38 0 0 1 88 50" pathLength="100" style="stroke-dasharray:{_rs_gauge:.1f} 100"/><line class="v21267-rs-needle" x1="50" y1="50" x2="{_rs_nx:.2f}" y2="{_rs_ny:.2f}"/><circle class="v21267-rs-hub" cx="50" cy="50" r="3.2"/></svg></div>'
        def _strip_card(cls,icon,title,value,line1,line2):
            return f'<div class="v21262-strip-card {cls}"><div class="v21262-strip-icon">{icon}</div><div class="v21262-strip-copy"><div class="v21262-strip-title">{html.escape(str(title))}</div><div class="v21262-strip-value">{html.escape(str(value))}</div><div class="v21262-strip-line">{html.escape(str(line1))}</div><div class="v21262-strip-sub">{html.escape(str(line2))}</div></div></div>'
        _research_card=f'<div class="v21262-strip-card good v21273-research-card"><div class="v21273-rs-icon" aria-hidden="true"><svg viewBox="0 0 24 24" role="img"><circle cx="12" cy="12" r="7.2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3.3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 3.2V5M20.8 12H19M12 19v1.8M5 12H3.2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><div class="v21273-rs-title">Research Score</div><div class="v21273-rs-body"><div class="v21273-rs-visual">{_rs_gauge_html}</div><div class="v21273-rs-copy"><div class="v21273-rs-value">{html.escape(_rs_txt)}</div><div class="v21273-rs-label">{html.escape(_rs_label)}</div><div class="v21273-rs-change {'up' if np.isfinite(_rs_delta) and _rs_delta>0 else 'down' if np.isfinite(_rs_delta) and _rs_delta<0 else ''}">{html.escape(_rs_change)}</div></div></div></div>'
        _strip_html=''.join([
            _research_card,
            f'<div class="v21262-strip-card blue v21269-valuation-card"><div class="v21262-strip-icon v21269-val-icon" aria-hidden="true"><svg viewBox="0 0 24 24" role="img"><rect x="6.5" y="5.5" width="11" height="14" rx="1.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 5.5V4.4c0-.8.6-1.4 1.4-1.4h3.2c.8 0 1.4.6 1.4 1.4v1.1" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M9.3 9.2h5.4M9.3 12h5.4M9.3 14.8h2.1" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round"/><circle cx="14.6" cy="15.2" r="1.65" fill="none" stroke="currentColor" stroke-width="1.45"/><path d="M14.6 13.9v2.6M13.7 14.5h1.25c.55 0 .9.28.9.7 0 .44-.35.7-.9.7h-.7" fill="none" stroke="currentColor" stroke-width="1.05" stroke-linecap="round"/></svg></div><div class="v21262-strip-copy v21269-val-copy"><div class="v21262-strip-title">Valuation</div><div class="v21269-val-value">{html.escape(_val_label)}</div><div class="v21269-val-base">{html.escape(f"Base case: {display_price(_ccbase,ticker)}" if np.isfinite(_mia_num(_ccbase)) else "Base case unavailable")}</div><div class="v21269-val-move {_val_move_cls}">{html.escape(_val_move)}</div><div class="v21269-val-confidence">{html.escape(_val_conf_text)}</div></div></div>',
            _strip_card('amber','○','Technicals',_tech_label,_tech_sub,_tech_context),
            f'<div class="v21262-strip-card good v21272-analyst-card" title="{html.escape(_an_provenance, quote=True)}"><div class="v21262-strip-icon v21272-analyst-icon" aria-hidden="true"><svg viewBox="0 0 24 24" role="img" aria-label="Analyst consensus"><path d="M4.5 19V8.5h5V19m-2.5 0V5h5v14m-2.5 0V10.5h5V19m-2.5 0V7h5v12" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M3.5 19.5h15" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg></div><div class="v21262-strip-copy v21272-analyst-copy"><div class="v21262-strip-title">Analyst Consensus</div><div class="v21272-analyst-value">{html.escape(_an_label)}</div><div class="v21272-analyst-count">{html.escape(f"{_an_n} analysts" if _an_n else "Analyst count unavailable")}</div><div class="v21272-analyst-target">{(f"Target: {html.escape(display_price(_an_target,ticker))} <span class=\"{'up' if _an_up >= 0 else 'down'}\">({html.escape(f'{_an_up:+.0%}')})</span>" if np.isfinite(_an_target) and np.isfinite(_an_up) else "Target unavailable")}</div><div class="v21274-analyst-source">Provider evidence ⓘ</div></div></div>',
            f'<div class="v21262-strip-card blue v21276-forecast-card" title="{html.escape((f"Chrímata 12M ensemble · {_fc_diag.get('n',0)} walk-forward tests · Direction accuracy: {_fc_diag.get('direction'):.1%} · MAE: {_fc_diag.get('mae'):.1%}" if _fc_diag.get('n',0) and np.isfinite(_mia_num(_fc_diag.get('direction'))) and np.isfinite(_mia_num(_fc_diag.get('mae'))) else "Chrímata 12M ensemble · validation evidence currently limited"), quote=True)}"><div class="v21262-strip-icon v21276-forecast-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M5 17l5-5 3 3 6-7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 8h4v4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="v21276-forecast-copy"><div class="v21262-strip-title">12M Forecast</div><div class="v21276-forecast-value">{html.escape(f"{_ccf12:+.1%}" if np.isfinite(_ccf12) else "Unavailable")}</div><div class="v21276-forecast-target">{html.escape(f"Target: {display_price(_fc_target,ticker)}" if np.isfinite(_fc_target) else "Model target unavailable")}</div><div class="v21276-forecast-prob">{html.escape(f"Prob. positive return: {_fc_prob:.0%}" if np.isfinite(_fc_prob) else (_fc_conf if np.isfinite(_ccf12) else "Insufficient model evidence"))}</div></div></div>',
            f'<div class="v21262-strip-card {_th_card_cls} v21278-thesis-card" title="{html.escape(_th_provenance,quote=True)}"><div class="v21278-thesis-icon" aria-hidden="true"><svg viewBox="0 0 24 24" role="img"><rect x="6" y="4.5" width="12" height="15" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 4.5V3.6h6v.9M8.7 8.5h6.6M8.7 11.5h6.6M8.7 14.5h6.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></div><div class="v21278-thesis-copy"><div class="v21262-strip-title">Thesis Status</div><div class="v21278-thesis-value">{html.escape(_th_label)}</div><div class="v21278-thesis-watch">{html.escape(_th_sub)}</div><div class="v21278-thesis-metrics">{html.escape(_th_metric_line)}</div></div></div>',
        ])
        st.markdown("""<style>
        .v21262-strip{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin:8px 0 24px}.v21269-valuation-card{align-items:flex-start!important;padding:8px 10px!important;min-width:0!important;overflow:hidden!important}.v21269-val-icon{margin-top:1px}.v21269-val-icon svg{width:20px;height:20px;display:block}.v21269-val-copy{display:flex;flex-direction:column;justify-content:center;min-width:0;max-width:100%;overflow:hidden}.v21269-val-value{font-size:15px;font-weight:900;color:#086ee8;line-height:1.08;margin:3px 0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.v21269-val-base{font-size:9px;font-weight:800;color:#3f5e82;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.v21269-val-move{font-size:10px;font-weight:900;line-height:1.15;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.v21269-val-move.up{color:#079b4a}.v21269-val-move.down{color:#d9363e}.v21269-val-move.neutral{color:#e89a00}.v21269-val-confidence{font-size:7.5px;font-weight:700;color:#7890aa;line-height:1.1;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.v21272-analyst-card{align-items:flex-start!important;padding:8px 9px!important;gap:8px!important}.v21272-analyst-icon{margin-top:0;width:28px!important;height:28px!important;flex:0 0 28px!important}.v21272-analyst-icon svg{width:18px;height:18px;display:block}.v21272-analyst-copy{display:flex;flex-direction:column;justify-content:flex-start;min-width:0;padding-top:0}.v21272-analyst-copy .v21262-strip-title{font-size:10.5px!important;font-weight:800!important;line-height:1.05!important}.v21272-analyst-value{font-size:14px;font-weight:900;color:#10264b;line-height:1.02;margin:4px 0 3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21272-analyst-count{font-size:8.8px;font-weight:800;color:#3f5e82;line-height:1.08;white-space:nowrap}.v21272-analyst-target{font-size:8.8px;font-weight:700;color:#3f5e82;line-height:1.08;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21272-analyst-target .up{color:#079b4a;font-weight:900}.v21272-analyst-target .down{color:#d9363e;font-weight:900}.v21274-analyst-source{font-size:7px;font-weight:700;color:#7890aa;line-height:1;margin-top:4px;white-space:nowrap}.v21276-forecast-card{align-items:center!important;padding:10px 11px!important;gap:11px!important;min-height:92px!important}.v21276-forecast-icon{width:36px!important;height:36px!important;flex:0 0 36px!important;margin-top:0}.v21276-forecast-icon svg{width:23px;height:23px;display:block}.v21276-forecast-copy{display:flex;flex-direction:column;justify-content:center;min-width:0;align-self:stretch;padding:1px 0}.v21276-forecast-copy .v21262-strip-title{font-size:11px!important;font-weight:850!important;line-height:1.08!important}.v21276-forecast-value{font-size:20px;font-weight:900;color:#086ee8;line-height:1;margin:6px 0 5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21276-forecast-target{font-size:9.8px;font-weight:850;color:#3f5e82;line-height:1.12;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21276-forecast-prob{font-size:9px;font-weight:750;color:#5f7895;line-height:1.12;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21278-thesis-card{align-items:center!important;padding:9px 10px!important;gap:9px!important;min-height:92px!important;min-width:0!important;overflow:hidden!important}.v21278-thesis-icon{width:32px;height:32px;flex:0 0 32px;border-radius:7px;display:flex;align-items:center;justify-content:center;background:#e5f7ef;color:#079b4a}.v21278-thesis-card.amber .v21278-thesis-icon{background:#fff1d5;color:#f0a000}.v21278-thesis-icon svg{width:20px;height:20px;display:block}.v21278-thesis-copy{min-width:0;max-width:100%;display:flex;flex-direction:column;justify-content:center;align-self:stretch;overflow:hidden}.v21278-thesis-copy .v21262-strip-title{font-size:10.5px!important;font-weight:800!important;line-height:1.05!important}.v21278-thesis-value{font-size:clamp(13px,1.05vw,17px);font-weight:900;color:#079b4a;line-height:1.08;margin:5px 0 4px;white-space:normal;overflow-wrap:anywhere;word-break:normal;max-width:100%}.v21278-thesis-card.amber .v21278-thesis-value{color:#ee9800}.v21278-thesis-watch{font-size:9px;font-weight:850;color:#3f5e82;line-height:1.15;white-space:normal;overflow-wrap:anywhere;max-width:100%}.v21278-thesis-metrics{font-size:8.5px;font-weight:700;color:#5f7895;line-height:1.15;margin-top:4px;white-space:normal;overflow-wrap:anywhere;max-width:100%}.v21273-research-card{position:relative!important;display:block!important;padding:8px 9px 7px!important;min-height:92px!important}.v21273-rs-icon{position:absolute;left:9px;top:8px;width:30px;height:30px;border-radius:7px;display:flex;align-items:center;justify-content:center;background:#e5f7ef;color:#079b4a}.v21273-rs-icon svg{width:19px;height:19px;display:block}.v21273-rs-title{position:absolute;left:47px;right:7px;top:9px;font-size:10.8px;font-weight:850;color:#45688f;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21273-rs-body{position:absolute;left:8px;right:7px;top:34px;bottom:5px;display:grid;grid-template-columns:72px minmax(0,1fr);gap:7px;align-items:center}.v21273-rs-visual{width:72px;display:flex;align-items:center;justify-content:center}.v21267-rs-gauge{width:70px;height:49px}.v21267-rs-gauge svg{display:block;width:100%;height:100%;overflow:visible}.v21267-rs-track,.v21267-rs-fill{fill:none;stroke-width:10;stroke-linecap:round}.v21267-rs-track{stroke:#cbd8e5}.v21267-rs-fill{stroke:#08a142}.v21267-rs-needle{stroke:#9fb2c5;stroke-width:3;stroke-linecap:round}.v21267-rs-hub{fill:#9fb2c5}.v21273-rs-copy{min-width:0;display:flex;flex-direction:column;justify-content:center;align-self:stretch;padding-top:1px}.v21273-rs-value{font-size:17px;font-weight:900;color:#079b4a;line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21273-rs-label{font-size:10px;font-weight:850;color:#ee9800;line-height:1.12;margin-top:3px}.v21273-rs-change{font-size:9px;font-weight:800;color:#5f7895;line-height:1.12;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21273-rs-change.up{color:#079b4a}.v21273-rs-change.down{color:#d9363e}.v21262-strip-card{min-width:0;min-height:92px;border:1px solid #d7e6f4;border-radius:9px;background:#f8fbff;padding:9px 10px;display:flex;gap:9px;box-sizing:border-box}.v21262-strip-card.good{background:#f4fbf8;border-color:#cfeade}.v21262-strip-card.blue{background:#f3f8ff;border-color:#cfe1f8}.v21262-strip-card.amber{background:#fffaf1;border-color:#f1dfba}.v21262-strip-icon{width:30px;height:30px;flex:0 0 30px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;background:#e7f0fb;color:#086ee8}.v21262-strip-card.good .v21262-strip-icon{background:#e5f7ef;color:#079b4a}.v21262-strip-card.amber .v21262-strip-icon{background:#fff1d5;color:#f0a000}.v21262-strip-copy{min-width:0}.v21262-strip-title{font-size:10px;font-weight:750;color:#45688f;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21262-strip-value{font-size:16px;font-weight:900;color:#10264b;line-height:1.12;margin:3px 0 2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21262-strip-card.good .v21262-strip-value{color:#079b4a}.v21262-strip-card.amber .v21262-strip-value{color:#ee9800}.v21262-strip-line{font-size:9px;font-weight:750;color:#3f5e82;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21262-strip-sub{font-size:8.5px;color:#5f7895;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}@media(max-width:1200px){.v21262-strip{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:760px){.v21262-strip{grid-template-columns:repeat(2,minmax(0,1fr))}}
        </style>""",unsafe_allow_html=True)
        st.markdown(f'<div class="v21262-strip">{_strip_html}</div>',unsafe_allow_html=True)

        _w_chart,_w_thesis,_w_ai=st.columns([1.75,.82,1.05],gap="small")
        # V21.2.39 — compact fixed equal-height Overview widgets.
        # 350px matches the intended Thesis Scorecard reference height while keeping all three cards locked.
        # V22.2.1 — lock the complete Overview intelligence row to one shared card height.
        # All three containers use the same Streamlit height so their top and bottom borders align.
        # V22.2.2 — compact equal-height Overview row.
        # 430px removes the large unused lower area while retaining the full chart footer,
        # six-row thesis scorecard and AI brief controls.
        _overview_widget_height=430
        _price_chart_widget_height=_overview_widget_height
        with _w_chart:
            with st.container(border=True,height=_price_chart_widget_height,key="v21243_price_card"):
                st.markdown('<div class="v21241-overview-card"></div><div class="v21216-widget-title">Price Chart</div>',unsafe_allow_html=True)
                # V21.3.15 — company-profile-aware Macro-to-Micro overlay.
                _macro_exposures=exposure_map(ticker,_ccsector,_ccindustry,str(_ccmeta.get("country") or ""))
                _macro_c1,_macro_c2,_macro_c3=st.columns([0.72,1.45,0.95],gap="small",vertical_alignment="center")
                with _macro_c1:
                    _macro_on=st.checkbox("Macro overlay",value=False,key=f"v21315_macro_on_{ticker}")
                with _macro_c2:
                    _macro_labels=[m.label for m in _macro_exposures]
                    _macro_label=st.selectbox("Macro series",_macro_labels,key=f"v21315_macro_sel_{ticker}",label_visibility="collapsed",disabled=not _macro_on)
                with _macro_c3:
                    _macro_normalized=st.checkbox("Rebase 100",value=False,key=f"v21315_macro_norm_{ticker}",disabled=not _macro_on)
                _macro_choice=macro_by_label(_macro_exposures,_macro_label) if _macro_exposures else None
                # V21.2.20 — client-side timeframe switching. All chart ranges are loaded once,
                # then Plotly switches traces in-browser so the Streamlit page does not reload/flash.
                _tf_options=["1D","1W","1M","3M","6M","1Y","3Y","5Y"]
                # V21.3.17.1 — Streamlit owns the active timeframe so each click
                # rebuilds the chart from the correct historical dataset.
                _tf_key=f"v213171_timeframe_{ticker}"
                if _tf_key not in st.session_state:
                    st.session_state[_tf_key]="1Y"
                _active_tf=st.segmented_control("Chart timeframe",_tf_options,key=_tf_key,label_visibility="collapsed") or "1Y"
                # V21.3.23.3 — force the selected segment to the reference solid-blue state.
                # Streamlit's selected-state attributes vary by release, so target the known segment index too.
                _tf_active_index=_tf_options.index(_active_tf)+1
                st.markdown(
                    f"""<style>
                    [class*=\"st-key-v213171_timeframe_\"] div[role=\"radiogroup\"] > label:nth-child({_tf_active_index}),
                    [class*=\"st-key-v213171_timeframe_\"] div[role=\"radiogroup\"] > button:nth-child({_tf_active_index}),
                    [class*=\"st-key-v213171_timeframe_\"] button:nth-of-type({_tf_active_index}) {{
                        background:#086ee8!important;border-color:#086ee8!important;color:#fff!important;
                    }}
                    [class*=\"st-key-v213171_timeframe_\"] div[role=\"radiogroup\"] > label:nth-child({_tf_active_index}) *,
                    [class*=\"st-key-v213171_timeframe_\"] div[role=\"radiogroup\"] > button:nth-child({_tf_active_index}) *,
                    [class*=\"st-key-v213171_timeframe_\"] button:nth-of-type({_tf_active_index}) * {{color:#fff!important;}}
                    </style>""",unsafe_allow_html=True,
                )
                _tf_spec={
                    "1D":("1d","5m"), "1W":("5d","30m"), "1M":("1mo","1d"),
                    "3M":("3mo","1d"), "6M":("6mo","1d"), "1Y":("1y","1d"),
                    "3Y":("3y","1wk"), "5Y":("5y","1wk"),
                }
                # Fetch a longer calculation window than the visible window. This prevents
                # SMA 20/50 from disappearing on 1M/3M and avoids starting each average from zero history.
                _tf_calc={
                    "1D":("5d","5m"), "1W":("1mo","30m"), "1M":("6mo","1d"),
                    "3M":("1y","1d"), "6M":("1y","1d"), "1Y":("2y","1d"),
                    "3Y":("5y","1wk"), "5Y":("10y","1wk"),
                }
                _chart_sets={}
                _macro_sets={}
                for _opt in _tf_options:
                    _per,_int=_tf_calc[_opt]
                    _calc=history_interval(ticker,_per,_int)
                    if _calc is None or _calc.empty:
                        _calc=h.copy() if _opt=="1Y" else pd.DataFrame()
                    if _calc is not None and not _calc.empty:
                        _calc=_calc.copy()
                        _calc["SMA20"]=_calc["Close"].rolling(20,min_periods=20).mean()
                        _calc["SMA50"]=_calc["Close"].rolling(50,min_periods=50).mean()
                        # Slice only after indicators are calculated so short tabs retain valid SMAs.
                        _vis_per,_=_tf_spec[_opt]
                        _cut_days={"1D":1,"1W":7,"1M":31,"3M":93,"6M":186,"1Y":366,"3Y":1098,"5Y":1830}[_opt]
                        _end_ts=_calc.index.max()
                        _start_ts=_end_ts-pd.Timedelta(days=_cut_days)
                        _hh=_calc.loc[_calc.index>=_start_ts].copy()
                    else:
                        _hh=pd.DataFrame()
                    _chart_sets[_opt]=_hh
                    if _macro_on and _macro_choice is not None:
                        _mp={"1D":"5d","1W":"1mo","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","3Y":"3y","5Y":"5y"}[_opt]
                        _mi="1d" if _opt not in ("3Y","5Y") else "1wk"
                        _macro_sets[_opt]=macro_fetch_close(_macro_choice.ticker,_mp,_mi)
                _fig=go.Figure()
                _trace_groups=[]
                _axis_updates=[]
                for _opt in _tf_options:
                    _hh=_chart_sets[_opt]
                    _idx=[]
                    if _macro_on and _macro_normalized and _hh is not None and not _hh.empty and "Close" in _hh.columns:
                        _stock_norm=pd.to_numeric(_hh["Close"],errors="coerce").dropna()
                        if not _stock_norm.empty and float(_stock_norm.iloc[0]) != 0:
                            _stock_norm=_stock_norm/float(_stock_norm.iloc[0])*100.0
                            _idx.append(len(_fig.data))
                            _fig.add_trace(go.Scatter(x=_stock_norm.index,y=_stock_norm,mode="lines",name=ticker,line=dict(width=2.2),hovertemplate=f"%{{x}}<br>{ticker}: %{{y:.2f}}<extra></extra>",visible=(_opt==_active_tf)))
                        _tickfmt=".1f"
                    elif _hh is not None and not _hh.empty and all(c in _hh.columns for c in ["Open","High","Low","Close"]):
                        _idx.append(len(_fig.data))
                        _fig.add_trace(go.Candlestick(x=_hh.index,open=_hh["Open"],high=_hh["High"],low=_hh["Low"],close=_hh["Close"],name=ticker,showlegend=False,increasing_line_color="#00a66a",decreasing_line_color="#f04444",visible=(_opt==_active_tf)))
                        if "SMA20" in _hh and _hh["SMA20"].notna().any():
                            _idx.append(len(_fig.data)); _fig.add_trace(go.Scatter(x=_hh.index,y=_hh["SMA20"],name="SMA 20",line=dict(width=1.5,color="#24aee8"),connectgaps=False,visible=(_opt==_active_tf)))
                        if "SMA50" in _hh and _hh["SMA50"].notna().any():
                            _idx.append(len(_fig.data)); _fig.add_trace(go.Scatter(x=_hh.index,y=_hh["SMA50"],name="SMA 50",line=dict(width=1.5,color="#ff334f"),connectgaps=False,visible=(_opt==_active_tf)))
                        if "Volume" in _hh.columns:
                            _vv=pd.to_numeric(_hh["Volume"],errors="coerce")
                            if _vv.notna().any():
                                _vc=np.where(pd.to_numeric(_hh["Close"],errors="coerce")>=pd.to_numeric(_hh["Open"],errors="coerce"),"rgba(0,166,106,.42)","rgba(240,68,68,.42)")
                                _idx.append(len(_fig.data)); _fig.add_trace(go.Bar(x=_hh.index,y=_vv,name="Volume",yaxis="y2",marker_color=_vc,visible=(_opt==_active_tf)))
                        _lo=float(pd.to_numeric(_hh["Low"],errors="coerce").min()); _hi=float(pd.to_numeric(_hh["High"],errors="coerce").max())
                        _span=max(_hi-_lo,0.0001)
                        _tickfmt=".3f" if _span<0.20 else (".2f" if _span<1.0 else ".1f")
                    else:
                        _tickfmt=".2f"
                    _trace_groups.append(_idx)
                    _axis_updates.append(_tickfmt)
                # V21.3.17.2 — build one macro overlay from the active window only.
                _macro_available=False
                _macro_status=""
                if _macro_on and _macro_choice is not None:
                    _active_stock=_chart_sets.get(_active_tf)
                    _active_macro=_macro_sets.get(_active_tf)
                    if _active_stock is not None and not _active_stock.empty and _active_macro is not None and not _active_macro.empty:
                        _active_close=pd.to_numeric(_active_stock["Close"],errors="coerce").dropna()
                        _active_aligned=macro_align_series(_active_close,_active_macro)
                        if not _active_aligned.empty:
                            _macro_available=True
                            if _macro_normalized:
                                _active_aligned=macro_normalize_100(_active_aligned)
                                _common_start=_active_aligned.index.min()
                                _stock_common=_active_close.copy()
                                _stock_idx=pd.to_datetime(_stock_common.index)
                                if getattr(_stock_idx,"tz",None) is not None: _stock_idx=_stock_idx.tz_localize(None)
                                _stock_common.index=_stock_idx
                                _stock_common=_stock_common[_stock_common.index>=_common_start]
                                if not _stock_common.empty and float(_stock_common.iloc[0])!=0:
                                    _stock_rebased=_stock_common/float(_stock_common.iloc[0])*100.0
                                    for _trace_i in _trace_groups[_tf_options.index(_active_tf)]:
                                        if getattr(_fig.data[_trace_i],"type","")=="scatter":
                                            _fig.data[_trace_i].x=_stock_rebased.index
                                            _fig.data[_trace_i].y=_stock_rebased.values
                                            _fig.data[_trace_i].name=f"{ticker} (Rebased 100)"
                                            break
                            _fig.add_trace(go.Scatter(x=_active_aligned.index,y=_active_aligned["macro"],mode="lines",name=f"{_macro_choice.label}" + (" (Rebased 100)" if _macro_normalized else ""),yaxis=("y" if _macro_normalized else "y3"),line=dict(width=2,dash="dot"),hovertemplate=f"%{{x}}<br>{_macro_choice.label}: %{{y:.3f}}<extra></extra>",visible=True))
                        else:
                            _macro_status=f"No common {_active_tf} observations were available for {ticker} and {_macro_choice.label}."
                    else:
                        _macro_status=f"{_macro_choice.label} data is unavailable for the selected {_active_tf} window."
                # V21.2.44 — Technical navigation is handled by Streamlit state rather than
                # an href inside Plotly. This avoids the browser-level white flash/reload.
                _fig.update_layout(
                    height=202,margin=dict(l=2,r=34,t=8,b=10),xaxis_rangeslider_visible=False,
                    showlegend=bool(_macro_on and _macro_available),legend=dict(orientation="h",y=1.03,x=0),bargap=0.12,
                    paper_bgcolor="white",plot_bgcolor="white",
                    xaxis=dict(gridcolor="#e8eef6",showgrid=True,autorange=True,domain=[0,1],anchor="y2",ticks="outside",ticklabelposition="outside",automargin=True),
                    yaxis=dict(side="left",gridcolor="#e8eef6",autorange=True,tickformat=(".1f" if (_macro_on and _macro_normalized) else _axis_updates[_tf_options.index(_active_tf)]),ticksuffix="",automargin=True,domain=[0.22,1.0],title=("Rebased performance" if (_macro_on and _macro_normalized) else "Stock price")),
                    yaxis2=dict(side="left",showgrid=False,showticklabels=False,zeroline=False,autorange=True,anchor="x",domain=[0.04,0.18]),
                    yaxis3=dict(side="right",overlaying="y",showgrid=False,zeroline=False,autorange=True,automargin=True,title=(_macro_choice.label if (_macro_on and _macro_choice is not None and not _macro_normalized) else ""),visible=bool(_macro_on and not _macro_normalized and _macro_available)),
                )
                if _active_tf in ("1D","1W"):
                    _fig.update_xaxes(rangebreaks=[dict(bounds=["sat","mon"]),dict(bounds=[16,10],pattern="hour")])
                else:
                    _fig.update_xaxes(rangebreaks=[])
                st.plotly_chart(_fig,use_container_width=True,config={"displayModeBar":False,"responsive":True},key=f"v213171_chart_{ticker}_{_active_tf}_{int(_macro_on)}_{int(_macro_normalized)}")
                # V21.3.23.2 — always reserve one compact provenance line.
                # No expander is inserted into the fixed-height card, so controls cannot push the footer down.
                if _macro_on and _macro_choice is not None:
                    if _macro_available:
                        _macro_note_html=(
                            f'<b>{html.escape(_macro_choice.label)}</b> · {html.escape(_macro_choice.channel)} · '
                            'Yahoo Finance/yfinance · '
                            '<span title="Overlay is contextual only; visual co-movement does not establish causation.">ⓘ</span>'
                        )
                    else:
                        _macro_note_html=f'Macro overlay unavailable · {html.escape(str(_macro_status))}'
                else:
                    _macro_note_html='&nbsp;'
                st.markdown(
                    f'<div class="v213232-macro-slot"><div class="v213231-macro-note">{_macro_note_html}</div></div>',
                    unsafe_allow_html=True,
                )
                # V21.2.50 — x-axis is anchored to the volume band, so date labels render beneath volume.
                # Footer remains one physical row with both sides locked to the same 26px baseline.
                # No negative margins or overlays: both sides share the exact same baseline.
                _foot_legend, _foot_link = st.columns([1.58, 0.92], gap="small", vertical_alignment="center")
                with _foot_legend:
                    st.markdown(
                        '<div class="v21249-chart-legend">'
                        '<span class="lg"><span class="line sma20"></span>SMA 20</span>'
                        '<span class="lg"><span class="line sma50"></span>SMA 50</span>'
                        '<span class="lg"><span class="volbars"><i></i><i></i><i></i><i></i></span>Volume</span>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                with _foot_link:
                    # V21.3.16.1 — Macro Chart Technical Analysis Navigation Fix.
                    # Uses the existing internal Command Centre router so the active
                    # ticker/security identity is preserved without a browser reload.
                    st.button(
                        "View Technical Analysis →",
                        key=f"v213172_technical_{ticker}",
                        type="tertiary",
                        use_container_width=False,
                        on_click=_chr_set_cc_sub_v2111,
                        args=("Technical",),
                    )
                # V21.3.23.3 — intentional white breathing room below the fixed footer.
                st.markdown('<div class="v213233-price-bottom-space"></div>',unsafe_allow_html=True)
        with _w_thesis:
            with st.container(border=True,height=_overview_widget_height,key="v21255_thesis_card"):
                st.markdown('<div class="v21241-overview-card"></div><div class="v21216-widget-title">Thesis Scorecard</div>',unsafe_allow_html=True)
                # V21.2.55 — stored rules drive the score. If none exist, render a real
                # six-row starter monitoring template as Pending instead of an empty card.
                # This matches the reference widget without fabricating evidence.
                _thesis_has_rules=bool(_ccth_total and _ccthesis is not None and not _ccthesis.empty)
                if _thesis_has_rules:
                    _thesis_rows=_ccthesis.head(6).copy()
                    _display_total=len(_thesis_rows)
                    _display_met=int(sum(str(v).strip().lower() in {"met","on track","pass","passed","true"} for v in _thesis_rows.get("status",pd.Series(dtype=str)).tolist()))
                else:
                    # V21.2.58 — company-specific evidence engine. The selected ticker,
                    # sector and industry determine the monitoring conditions. Available
                    # provider/model evidence can move a condition to On track or Watch;
                    # unsupported conditions stay Pending rather than being guessed.
                    _thesis_rows=overview_dynamic_thesis(
                        ticker,_ccsector,_ccindustry,_ccmeta,_ccbase,price
                    )
                    _display_total=len(_thesis_rows)
                    _display_met=int(sum(str(v).strip().lower() in {"met","on track","pass","passed","true"} for v in _thesis_rows.get("status",pd.Series(dtype=str)).tolist()))
                _ratio=(_display_met/max(_display_total,1)) if _display_total else 0.0
                # V21.3.24.1 — do not call a non-existent company_name() helper.
                # Reuse the already-loaded provider/security metadata and fall back safely to ticker.
                _thesis_company_name=str(
                    (_ccmeta or {}).get("longName")
                    or (_ccmeta or {}).get("shortName")
                    or (_ccmeta or {}).get("displayName")
                    or ticker
                )
                _thesis_template_payload=get_thesis_template(ticker,_thesis_company_name,_ccsector,_ccindustry)
                _thesis_template_label=str(_thesis_template_payload.get("template","corporate")).replace("_"," ").title()
                st.markdown(f'<div class="v21324-thesis-template" title="Deterministic business-model classification · AI calculated: No">{html.escape(_thesis_template_label)} thesis · {html.escape(str(ticker))}</div>',unsafe_allow_html=True)
                st.markdown(f'<div class="v21216-thesis-score">{_display_met} / {_display_total} <span>conditions on track</span></div>',unsafe_allow_html=True)
                _pct=int(round(_ratio*100)) if _display_total else 0
                st.markdown(f'<div class="v21245-thesis-progress"><div class="v21245-thesis-track"><div class="v21245-thesis-fill" style="width:{_pct}%"></div></div><div class="v21245-thesis-pct">{_pct}%</div></div>',unsafe_allow_html=True)
                _rows=[]
                for _,_r in _thesis_rows.iterrows():
                    _label=str(_r.get("metric") or _r.get("condition") or _r.get("Item") or "Thesis condition")
                    _raw=str(_r.get("status") or "Pending").strip(); _sl=_raw.lower()
                    _cls="met" if _sl in {"met","on track","pass","passed","true"} else ("watch" if _sl in {"watch","watch / broken","warning","at risk","attention","broken"} else "pending")
                    _icon="✓" if _cls in {"met","pending"} else "●"
                    _display="On track" if _cls=="met" else ("Watch" if _cls=="watch" else "Pending")
                    _evidence=str(_r.get("evidence") or "").strip(); _source=str(_r.get("source") or "").strip()
                    _tip=" · ".join([x for x in [_evidence,_source] if x]) or "No supporting evidence loaded yet"
                    _rows.append(f'<div class="v21216-thesis-row" title="{html.escape(_tip,quote=True)}"><span class="v21216-thesis-icon {_cls}">{_icon}</span><span>{html.escape(_label)}</span><span class="v21216-thesis-status {_cls}">{html.escape(_display)}</span></div>')
                st.markdown('<div class="v21254-thesis-list">'+"".join(_rows)+'</div>',unsafe_allow_html=True)
                st.button("View Thesis Monitor  →",key=f"v21255_thesis_link_{ticker}",type="tertiary",use_container_width=False,on_click=_chr_set_cc_sub_v2111,args=("Thesis Scorecard",))
        # Prepare the evidence packet here so the compact AI widget is functional in the same row.
        _attention_text="No stored thesis/monitoring item currently requires attention."
        if _ccattention is not None and not _ccattention.empty:
            _attention_text="; ".join([str(x) for x in _ccattention.head(3).get("Item",pd.Series(dtype=str)).tolist() if str(x).strip()]) or _attention_text
        _ann_text="No announcement evidence loaded."
        if _ccann is not None and not _ccann.empty: _ann_text="; ".join([str(x) for x in _ccann.head(3).iloc[:,0].tolist()])
        _brief_fallback=(f"WHAT CHANGED\n{_change_main}\n\nFUNDAMENTAL EVIDENCE\nEvidence coverage is {_ccscore.get('Available',0)} of {_ccscore.get('Total',6)} categories. Sector: {_ccsector}; industry: {_ccindustry}.\n\nVALUATION & EXPECTATIONS\n"+(f"Stored base scenario: {display_price(_ccbase,ticker)}. " if np.isfinite(_mia_num(_ccbase)) else "No supported base valuation is currently available. ")+(f"12-month historical forecast scenario: {_ccf12:+.1%}." if np.isfinite(_ccf12) else "12-month forecast evidence is unavailable.")+f"\n\nTECHNICAL / QUANT\nCurrent technical regime: {tr.get('Trend','—')}. "+(f"Annualised volatility: {_ccvolatility:.1%}. " if np.isfinite(_ccvolatility) else "")+(f"Six-month momentum: {_ccmom:+.1%}." if np.isfinite(_ccmom) else "")+f"\n\nTHESIS CONFLICTS & MONITORING\n{_attention_text}\n\nCATALYSTS / ANNOUNCEMENTS\n{_ann_text}\n\nEVIDENCE GAPS\nMissing fields and unavailable engines should be completed before stronger conclusions are drawn.\n\nINVESTIGATE NEXT\nPrioritise official financial reports, measurable thesis conditions, valuation assumptions and upcoming catalysts that can change the evidence state.")
        # V21.2.57 — reference-matched functional AI Research Brief.
        # The compact widget synthesises the evidence already loaded by Chrímata; it never invents missing evidence.
        _ai_key=f"v21256_ai_brief_{ticker}"; _ai_time_key=f"v21256_ai_time_{ticker}"; _ai_source_key=f"v21256_ai_source_{ticker}"
        _thesis_evidence=[]
        if _ccthesis is not None and not _ccthesis.empty:
            for _,_r in _ccthesis.head(10).iterrows():
                _thesis_evidence.append({"condition":str(_r.get("metric") or _r.get("condition") or _r.get("Item") or "Thesis condition"),"status":str(_r.get("status") or "Pending")})
        _evidence={
            "company":{"name":_ccname,"ticker":ticker,"sector":_ccsector,"industry":_ccindustry},
            "market":{"price":price,"day_change_pct":None if not np.isfinite(_ccpct) else float(_ccpct),"annualised_volatility":None if not np.isfinite(_ccvolatility) else float(_ccvolatility),"six_month_momentum":None if not np.isfinite(_ccmom) else float(_ccmom)},
            "fundamentals":{"research_score":_ccscore},
            "valuation":{"base_scenario":None if not np.isfinite(_mia_num(_ccbase)) else float(_ccbase)},
            "technical":tr,
            "forecast":{"twelve_month_return_scenario":None if not np.isfinite(_ccf12) else float(_ccf12)},
            "analyst_evidence":_ccanalyst,
            "thesis":{"met":_ccth_met,"total":_ccth_total,"conditions":_thesis_evidence,"attention":_attention_text},
            "announcements":_ann_text,
        }
        _brief_fallback=(f"EXECUTIVE SUMMARY\n{_ccname} ({ticker}) has {_ccscore.get('Available',0)} of {_ccscore.get('Total',6)} core evidence categories currently loaded. The current technical regime is {tr.get('Trend','—')}. This brief does not make a buy/sell recommendation.\n\nWHAT CHANGED\n{_change_main}\n\nFUNDAMENTALS\nSector: {_ccsector}. Industry: {_ccindustry}. Evidence coverage: {_ccscore.get('Available',0)}/{_ccscore.get('Total',6)}.\n\nVALUATION\n"+(f"Stored base scenario: {display_price(_ccbase,ticker)}." if np.isfinite(_mia_num(_ccbase)) else "No supported base valuation is currently loaded.")+"\n\nTECHNICAL PICTURE\nCurrent trend: "+str(tr.get('Trend','—'))+(f". Annualised volatility: {_ccvolatility:.1%}." if np.isfinite(_ccvolatility) else ". Volatility evidence unavailable.")+(f" Six-month momentum: {_ccmom:+.1%}." if np.isfinite(_ccmom) else "")+"\n\nTHESIS SCORECARD\n"+(f"{_ccth_met}/{_ccth_total} stored conditions are currently on track. " if _ccth_total else "No measured thesis conditions are currently stored. ")+_attention_text+"\n\nCATALYSTS & ANNOUNCEMENTS\n"+_ann_text+"\n\nFORECASTS & ANALYST EVIDENCE\n"+(f"Stored 12-month model scenario: {_ccf12:+.1%}. " if np.isfinite(_ccf12) else "12-month model evidence is unavailable. ")+"Analyst evidence is shown only where supplied by the loaded data source.\n\nEVIDENCE GAPS / INVESTIGATE NEXT\nPrioritise official financial reports, measurable thesis conditions, valuation assumptions and upcoming catalysts where evidence is missing or stale.")
        if _ai_key not in st.session_state: st.session_state[_ai_key]=_brief_fallback
        with _w_ai:
            with st.container(border=True,height=_overview_widget_height,key="v21257_ai_card"):
                st.markdown('''<div class="v21241-overview-card"></div><div class="v21216-ai-head"><div class="v21216-ai-icon" aria-hidden="true"><svg viewBox="0 0 32 32"><path d="M13 4.5a5 5 0 0 0-7.8 4.1A4.7 4.7 0 0 0 4 17.5a4.8 4.8 0 0 0 4.2 6.7A5 5 0 0 0 13 27.5V4.5Z"/><path d="M19 4.5a5 5 0 0 1 7.8 4.1 4.7 4.7 0 0 1 1.2 8.9 4.8 4.8 0 0 1-4.2 6.7 5 5 0 0 1-4.8 3.3V4.5Z"/><path d="M13 9.5c-2.2-.2-3.6 1-3.8 2.8M19 9.5c2.2-.2 3.6 1 3.8 2.8M13 16c-2.4-.2-3.8 1.2-4 3M19 16c2.4-.2 3.8 1.2 4 3M13 22c-1.8-.1-2.8.7-3.2 2M19 22c1.8-.1 2.8.7 3.2 2M16 5v22"/></svg></div><div class="v21216-ai-copy"><div class="v21216-ai-title">AI Research Brief <span class="v21216-beta">BETA</span></div><div class="v21216-ai-sub">Evidence-based analysis. No hype. No recommendations.</div></div></div>''',unsafe_allow_html=True)
                st.markdown('<div class="v21216-ai-info">Get an AI-generated research brief based on all available evidence across fundamentals, valuation, technicals, announcements, news and forecasts. This is not a buy/sell recommendation.</div>',unsafe_allow_html=True)
                if st.button("✦  Generate AI Research Brief",type="primary",use_container_width=True,key=f"v21257_generate_ai_{ticker}"):
                    try:
                        import os
                        from openai import OpenAI
                        # V22.3.1 — secure configuration bridge:
                        # Streamlit Cloud secrets first, then standard server environment variables.
                        try: _secret_key=str(st.secrets.get("OPENAI_API_KEY","") or "").strip()
                        except Exception: _secret_key=""
                        _secret_key=_secret_key or str(os.environ.get("OPENAI_API_KEY","") or "").strip()
                        if not _secret_key:
                            raise RuntimeError("ai_service_not_configured")
                        try: _model=str(st.secrets.get("CHRIMATA_BRIEF_MODEL","") or "").strip()
                        except Exception: _model=""
                        _model=_model or str(os.environ.get("CHRIMATA_BRIEF_MODEL","") or "").strip() or "gpt-5.6-luna"
                        _prompt=("You are Chrímata's evidence-synthesis engine. Use ONLY the JSON evidence supplied below. "
                                 "Create a concise investment research brief with these exact sections: EXECUTIVE SUMMARY; WHAT CHANGED; FUNDAMENTALS; VALUATION; TECHNICAL PICTURE; THESIS SCORECARD; CATALYSTS & ANNOUNCEMENTS; FORECASTS & ANALYST EVIDENCE; RISKS / CONFLICTING EVIDENCE; EVIDENCE GAPS; INVESTIGATE NEXT. "
                                 "Clearly distinguish observed/provider facts from model outputs and interpretation. Never invent figures, events, sources, analyst views, probabilities or catalysts. Say 'unavailable' when evidence is missing. Do not issue buy, sell, hold, or investment recommendations. Keep it decision-useful and company-specific. EVIDENCE JSON: "+json.dumps(_evidence,default=str))
                        _resp=OpenAI(api_key=_secret_key).responses.create(model=_model,input=_prompt)
                        _txt=(getattr(_resp,"output_text","") or "").strip()
                        if not _txt: raise RuntimeError("AI provider returned an empty brief")
                        st.session_state[_ai_key]=_txt
                        st.session_state[_ai_source_key]="AI synthesis"
                    except Exception as _aie:
                        st.session_state[_ai_key]=_brief_fallback
                        st.session_state[_ai_source_key]="Evidence fallback"
                        # Public UI stays clean; detailed configuration/provider errors belong in server logs.
                        _ai_err=str(_aie)
                        try:
                            print(f"[Chrímata AI Research Brief] ticker={ticker} error={_ai_err}")
                        except Exception:
                            pass
                        if _ai_err=="ai_service_not_configured":
                            st.warning("AI Research Brief is not configured on this deployment yet. The evidence-only research brief is available below.")
                        else:
                            st.warning("AI Research Brief is temporarily unavailable. Chrímata generated the evidence-only research brief instead.")
                    st.session_state[_ai_time_key]=pd.Timestamp.now(tz="Australia/Melbourne").strftime("%d %b %Y, %-I:%M%p AEST")
                _last_ai=st.session_state.get(_ai_time_key,"Not generated in this session")
                _source_ai=st.session_state.get(_ai_source_key,"")
                st.markdown(f'<div class="v21216-ai-time">Last generated: {html.escape(str(_last_ai))}'+(f' · {html.escape(_source_ai)}' if _source_ai else '')+'</div>',unsafe_allow_html=True)
                with st.container(key=f"v21257_brief_view_{ticker}"):
                    with st.expander("View current research brief",expanded=False):
                        st.markdown(st.session_state.get(_ai_key,_brief_fallback))

        # V21.2.61 — Company Overview Intelligence Widgets.
        # Reference-matched compact research dashboard; values come only from loaded/provider/stored evidence.
        st.markdown("""<style>
        .v21261-snapshot-heading{font-size:16px;font-weight:950;color:#10264b;margin:2px 0 5px}.v21261-title{font-size:10.5px;font-weight:900;color:#10264b;margin:0 0 5px;display:flex;align-items:center;gap:4px}.v21261-info{display:inline-flex;width:11px;height:11px;border:1px solid #9bb4cf;border-radius:50%;align-items:center;justify-content:center;font-size:7px;color:#6f8cab;font-weight:900}.v21261-card{background:#fff;border:1px solid #d8e5f2;border-radius:7px;padding:6px 8px 27px;min-height:158px;height:158px;box-sizing:border-box;overflow:hidden;position:relative}.v21261-center{text-align:center}.v21261-k{font-size:8px;color:#45688f;font-weight:700}.v21261-v{font-size:16px;line-height:1.02;color:#10264b;font-weight:900;margin:2px 0}.v21261-pos{color:#08a142;font-weight:900}.v21261-neg{color:#e32636;font-weight:900}.v21261-watch{color:#e89a00;font-weight:900}.v21261-muted{color:#7b91aa}.v21261-table{width:100%;border-collapse:collapse;font-size:8.2px;color:#29476f}.v21261-table td{border:1px solid #dfe8f2;padding:4px 5px;height:22px}.v21261-table td:nth-child(2){font-weight:850;color:#10264b}.v21261-table td:nth-child(3){font-weight:900;text-align:right}.v21261-row{display:grid;grid-template-columns:72px minmax(0,1fr) 65px;gap:5px;border-bottom:1px solid #dfe8f2;padding:4px 2px;font-size:8.7px;color:#29476f;line-height:1.2}.v21261-row:last-child{border-bottom:0}.v21261-row b{color:#10264b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21261-r{text-align:right;color:#66809c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21261-risk{background:#fff0f3;border-color:#ffd5dd;min-height:76px;height:auto;padding-bottom:8px}.v21261-opp{background:#eefaf4;border-color:#d3f0df;min-height:76px;height:auto;padding-bottom:8px}.v21261-risk .v21261-title{color:#e32636}.v21261-opp .v21261-title{color:#079447}.v21261-list{font-size:8.7px;line-height:1.25;color:#29476f;display:grid;grid-template-columns:1fr 1fr;gap:5px 8px}.v21261-dot{display:inline-flex;width:14px;height:14px;border-radius:50%;align-items:center;justify-content:center;color:#fff;font-size:9px;font-weight:900;margin-right:4px}.v21261-risk .v21261-dot{background:#ef3340}.v21261-opp .v21261-dot{background:#0aa04f}.v21261-val-grid{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;margin-top:1px}.v21261-val-grid>div{border-right:1px solid #e3ebf4}.v21261-val-grid>div:last-child{border-right:0}.v21261-val-lbl{font-size:8px;font-weight:900}.v21261-val-num{font-size:10px;font-weight:900;color:#10264b;margin:1px 0}.v21261-range{height:8px;background:#dce7f2;border-radius:10px;position:relative;margin:9px 8px 4px}.v21261-range i{position:absolute;top:-4px;width:6px;height:16px;border-radius:4px;background:#086ee8}.v21261-range .bear{left:0;background:#ffb000}.v21261-range .base{left:50%}.v21261-range .bull{right:0;background:#a9bfd5}.v21261-range-labels{display:flex;justify-content:space-between;font-size:7.5px;color:#527298}.v21261-spark{height:39px;margin:3px 2px}.v21261-spark svg{width:100%;height:100%}.v21281-fc{padding:6px 8px 27px}.v21281-fc-body{padding:1px 7px 0;text-align:left}.v21281-fc .v21261-k{font-size:8.5px}.v21281-fc-target{font-size:17px;line-height:1.05;color:#10264b;font-weight:950;margin:2px 0}.v21281-fc-return{font-size:12px;line-height:1.05;font-weight:950;margin:1px 0 2px}.v21281-fc .v21261-spark{height:49px;margin:2px 0 2px}.v21281-fc-prob{font-size:8.5px;color:#29476f;font-weight:750;margin-top:1px}.v21261-analyst-grid{display:grid;grid-template-columns:1fr 1.1fr;gap:7px}.v21261-analyst-dist{font-size:7.8px;color:#29476f}.v21261-analyst-dist div{display:flex;justify-content:space-between;margin:3px 0}.v21261-adot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:5px}.v21282-analyst{padding:6px 8px 27px}.v21282-analyst-grid{display:grid;grid-template-columns:.92fr 1.08fr;gap:10px;align-items:start}.v21282-analyst-left{display:flex;flex-direction:column;min-width:0}.v21282-analyst-status{font-size:17px;line-height:1.02;font-weight:950;margin:5px 0 2px}.v21282-analyst-count{font-size:8.5px;color:#527298;font-weight:750}.v21282-analyst-target{margin-top:20px}.v21282-analyst-target-label{font-size:8.5px;color:#45688f;font-weight:800}.v21282-analyst-target-value{font-size:17px;line-height:1.05;color:#10264b;font-weight:950;margin-top:2px}.v21282-analyst-dist{font-size:8.3px;color:#29476f;padding-top:2px}.v21282-analyst-dist div{display:grid;grid-template-columns:1fr 18px;align-items:center;gap:4px;margin:5px 0}.v21282-analyst-dist b{text-align:right;color:#10264b}.v21282-analyst-dist span{white-space:nowrap}.v21282-analyst-dist .v21261-adot{width:8px;height:8px;margin-right:6px}.v21283-metrics{padding:6px 8px 27px}.v21283-metrics .v21261-table{font-size:8.1px}.v21283-metrics .v21261-table td{height:20px;padding:3px 5px}.v21283-metrics .v21261-table td:nth-child(1){width:46%;color:#45688f}.v21283-metrics .v21261-table td:nth-child(2){width:34%;font-weight:900;color:#10264b}.v21283-metrics .v21261-table td:nth-child(3){width:20%;font-weight:950;text-align:right}.v21283-growth-pos{color:#08a142}.v21283-growth-neg{color:#e32636}.v21283-growth-na{color:#8aa0b8}
.v21286-market{padding:7px 8px 27px;min-height:158px;height:158px}.v21286-market .v21261-title{font-size:10.5px;margin-bottom:2px}.v21261-market-range{margin:0 1px 2px}.v21286-range-row{display:grid;grid-template-columns:21px minmax(0,1fr);gap:6px;align-items:center}.v21286-range-badge{width:19px;height:19px;border-radius:50%;background:#ffad00;color:#fff;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:950}.v21286-range-main{min-width:0}.v21286-range-main .v21261-k{font-size:8.2px;font-weight:850;margin-bottom:0}.v21261-market-track{height:6px;border-radius:8px;background:#dce7f2;position:relative;margin:4px 3px 3px}.v21261-market-now{position:absolute;top:-3px;width:7px;height:12px;border-radius:5px;background:#1638a7;transform:translateX(-50%)}.v21261-market-low{display:none}.v21261-market-high{position:absolute;right:0;top:-2px;width:6px;height:10px;border-radius:4px;background:#ff284d}.v21261-market-labels{position:relative;height:10px;font-size:7px;color:#7890aa}.v21261-market-labels span{position:absolute;top:0;white-space:nowrap}.v21261-market-labels span:first-child{left:0}.v21261-market-labels span:nth-child(2){left:clamp(19%,var(--mp-pos,50%),79%);transform:translateX(-50%);font-weight:900;color:#45688f}.v21261-market-labels span:last-child{right:0}.v21286-range-position{font-size:8px;color:#10264b;font-weight:900;margin:1px 0 3px 27px}.v21286-market .v21261-table{font-size:7.9px;margin-top:2px}.v21286-market .v21261-table td{height:15px;padding:1px 5px}.v21286-market .v21261-table td:first-child{color:#45688f}.v21286-market .v21261-table td:last-child{text-align:right;font-weight:900;color:#10264b}.v21290-card{background:#fff;border:1px solid #d8e5f2;border-radius:8px;padding:7px 9px 28px;min-height:158px;height:158px;box-sizing:border-box;overflow:hidden;position:relative}.v21290-title{font-size:10.5px;font-weight:950;color:#10264b;margin:0 0 5px;display:flex;align-items:center;gap:5px}.v21290-icon{color:#086ee8;font-size:11px}.v21290-attn .v21290-icon{color:#ef3340}.v21290-row{display:grid;grid-template-columns:68px minmax(0,1fr) 64px 28px;gap:5px;align-items:center;border-bottom:1px solid #dfe8f2;padding:4px 1px;font-size:8.4px;color:#45688f;line-height:1.15}.v21290-row:last-child{border-bottom:0}.v21290-row .main{color:#29476f;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21290-row .meta{text-align:right;color:#66809c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21290-row .pdf{text-align:right;color:#086ee8;font-weight:900}.v21290-news .v21290-row{grid-template-columns:68px minmax(0,1fr) 70px}.v21290-cat .v21290-row{grid-template-columns:68px minmax(0,1fr) 18px}.v21290-cat .status{text-align:center;font-weight:950;font-size:12px;color:#7e9ab7}.v21290-cat .done{color:#0aa04f}.v21290-attn{padding-bottom:8px}.v21290-attn-item{display:grid;grid-template-columns:20px minmax(0,1fr) 48px;gap:5px;align-items:start;border-bottom:1px solid #edf1f5;padding:4px 0}.v21290-attn-item:last-child{border-bottom:0}.v21290-rank{width:17px;height:17px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#829bb4;color:#fff;font-size:8px;font-weight:950}.v21290-attn-item:nth-child(1) .v21290-rank{background:#ff2949}.v21290-attn-item:nth-child(2) .v21290-rank{background:#ffae00}.v21290-attn-main{font-size:8.3px;color:#10264b;font-weight:900;line-height:1.15}.v21290-attn-sub{font-size:7.5px;color:#6b8198;font-weight:600;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21290-pill{font-size:7px;font-weight:900;border-radius:5px;padding:3px 4px;text-align:center;background:#e7f2ff;color:#0874e8}.v21290-pill.watch{background:#fff2d6;color:#e89a00}.v21290-bottom{background:#fff;border:1px solid #d8e5f2;border-radius:8px;padding:7px 11px;min-height:72px;height:72px;box-sizing:border-box;overflow:hidden}.v21290-bottom-title{font-size:10.5px;font-weight:950;color:#086ee8;margin-bottom:5px;display:flex;align-items:center;gap:5px}.v21290-stats{display:grid;grid-template-columns:repeat(4,1fr)}.v21290-stat{padding:0 9px;border-right:1px solid #dfe8f2}.v21290-stat:first-child{padding-left:0}.v21290-stat:last-child{border-right:0}.v21290-stat .k{font-size:7.5px;color:#67809c;font-weight:700}.v21290-stat .v{font-size:10px;color:#10264b;font-weight:900;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21290-scenario{font-size:8.8px;color:#45688f;line-height:1.3;padding-right:6px}.v21290-source{font-size:7px;color:#7a90a7;margin-top:3px}.v21290-empty{font-size:8.3px;color:#6b8198;padding:7px 2px}.v21290-viewall{position:absolute;right:8px;top:5px;font-size:8px;color:#086ee8;font-weight:900}.v21261-bottom{background:#fff;border:1px solid #d8e5f2;border-radius:8px;padding:9px 12px;min-height:94px;box-sizing:border-box}.v21261-bottom-title{font-size:13px;font-weight:900;color:#086ee8;margin-bottom:7px}.v21261-stats{display:grid;grid-template-columns:repeat(4,1fr)}.v21261-stat{padding:0 9px;border-right:1px solid #dfe8f2}.v21261-stat:last-child{border-right:0}.v21261-stat .k{font-size:8px;color:#67809c;font-weight:700}.v21261-stat .v{font-size:12px;color:#10264b;font-weight:900;margin-top:2px}.v21261-scenario{font-size:9.3px;color:#29476f;line-height:1.4}.v21261-quote{display:flex;align-items:center;justify-content:center;text-align:center;font-size:10px;color:#1e5ca9;font-style:italic;font-weight:800;height:72px}[class*="st-key-v21261_nav_"]{margin-top:-27px!important;position:relative!important;z-index:3!important;border-top:1px solid #e2ebf4!important;background:#fff!important}[class*="st-key-v21261_nav_"] .stButton{display:flex!important;justify-content:flex-end!important}[class*="st-key-v21261_nav_"] .stButton>button{width:auto!important;font-size:8.5px!important;font-weight:850!important;min-height:24px!important;height:24px!important;padding:0 5px!important;border:0!important;border-radius:0!important;background:#fff!important;color:#086ee8!important;box-shadow:none!important}
        </style>""",unsafe_allow_html=True)

        def _ov_fmt(v,prefix=""):
            x=_mia_num(v)
            return "—" if not np.isfinite(x) else compact_number(x,prefix=prefix)
        def _ov_rowdate(v):
            try: return pd.to_datetime(v).strftime("%d %b %Y")
            except Exception: return str(v)[:14] if str(v).strip() else "—"
        def _ov_records(df,limit=5):
            if df is None or df.empty:return []
            out=[]
            for _,r in df.head(limit).iterrows():
                vals=[str(x) for x in r.tolist() if pd.notna(x) and str(x).strip() not in ("","nan","None")]
                if vals:out.append(vals)
            return out

        _cur="A$" if str(_currency).upper()=="AUD" else ("£" if str(_currency).upper()=="GBP" else "$" )
        _valup=(_ccbase/price-1) if np.isfinite(_mia_num(_ccbase)) and price else np.nan
        _bear=_bull=np.nan
        if _ccvals is not None and not _ccvals.empty and "scenario" in _ccvals.columns and "value_per_share" in _ccvals.columns:
            for _nm,_dest in [("bear","bear"),("bull","bull")]:
                _q=_ccvals[_ccvals["scenario"].astype(str).str.lower()==_nm]
                if not _q.empty:
                    if _nm=="bear":_bear=_mia_num(_q.iloc[0]["value_per_share"])
                    else:_bull=_mia_num(_q.iloc[0]["value_per_share"])
        # V21.2.81 — one canonical 12M forecast object across the intelligence strip and Investment Snapshot.
        # The advanced walk-forward ensemble above is the source of truth for return, target and calibrated positive-return probability.
        _f_target=_fc_target if np.isfinite(_mia_num(_fc_target)) else np.nan
        _f_prob=_fc_prob if np.isfinite(_mia_num(_fc_prob)) else np.nan
        _at=_mia_num(_ccanalyst.get("target_mean")); _at=_cctarget if not np.isfinite(_at) else _at
        _aup=_mia_num(_ccanalyst.get("percentage_return"))
        _rev=_mia_num(_ccmeta.get("totalRevenue")); _ebitda=_mia_num(_ccmeta.get("ebitda")); _ni=_mia_num(_ccmeta.get("netIncomeToCommon")); _eps=_mia_num(_ccmeta.get("trailingEps")); _fcf=_mia_num(_ccmeta.get("freeCashflow"))
        # V21.2.89 — provenance-first market-position fields. Short interest is preferably % of shares outstanding;
        # short % of float is only a labelled fallback because the denominators are not interchangeable.
        _shares=_mia_num(_ccmeta.get("sharesOutstanding")); _short=_mia_num(_ccmeta.get("sharesPercentSharesOut")); _mp_short_basis="provider sharesPercentSharesOut (% of shares outstanding)"
        if not np.isfinite(_short):
            _short=_mia_num(_ccmeta.get("shortPercentOfFloat")); _mp_short_basis="provider shortPercentOfFloat (% of float)" if np.isfinite(_short) else "unavailable"
        if not np.isfinite(_shares): _shares=_mia_num(_ccmeta.get("impliedSharesOutstanding"))
        _range_pos=((price-_cclo)/(_cchi-_cclo)) if np.isfinite(_cclo) and np.isfinite(_cchi) and _cchi>_cclo else np.nan
        # V21.2.87 — Market Position Reference Match + Verified Data Engine. Prefer reproducible trailing 52-week daily history.
        _mp_range_basis="provider metadata"; _mp_vol_basis="provider average volume"
        try:
            _mp_h=history(ticker,"1y")
            if _mp_h is not None and not _mp_h.empty:
                _mp_low=pd.to_numeric(_mp_h.get("Low"),errors="coerce").dropna()
                _mp_high=pd.to_numeric(_mp_h.get("High"),errors="coerce").dropna()
                if len(_mp_low) and len(_mp_high):
                    _cclo=float(_mp_low.min()); _cchi=float(_mp_high.max()); _mp_range_basis="trailing 52-week daily price history"
                    _range_pos=((price-_cclo)/(_cchi-_cclo)) if _cchi>_cclo else np.nan
                _mp_v=pd.to_numeric(_mp_h.get("Volume"),errors="coerce").dropna().tail(20)
                if len(_mp_v)>=10:
                    _ccvol=float(_mp_v.mean()); _mp_vol_basis=f"{len(_mp_v)}-session observed average volume"
        except Exception:
            pass
        if np.isfinite(_mia_num(_ccmeta.get("sharesOutstanding"))):
            _mp_shares_basis="provider reported sharesOutstanding"
        elif np.isfinite(_mia_num(_ccmeta.get("impliedSharesOutstanding"))):
            _mp_shares_basis="provider impliedSharesOutstanding"
        else:
            try:
                _sh=shares_history(ticker)
                if _sh is not None and len(_sh):
                    _shares=float(_sh.iloc[-1]); _mp_shares_basis="provider get_shares_full latest observation"
                else: _mp_shares_basis="unavailable"
            except Exception:
                _mp_shares_basis="unavailable"
        _dist_hi=(price/_cchi-1) if np.isfinite(_cchi) and _cchi else np.nan; _dist_lo=(price/_cclo-1) if np.isfinite(_cclo) and _cclo else np.nan

        st.markdown('<div class="v21261-snapshot-heading">Investment Snapshot</div>',unsafe_allow_html=True)
        _w1,_w2,_w3,_w4,_w5=st.columns([1,1,1,1.08,1.18],gap="small")
        _info='<span class="v21261-info">i</span>'
        with _w1:
            _bear_gap=(_bear/price-1) if np.isfinite(_bear) and price else np.nan
            _base_gap=(_ccbase/price-1) if np.isfinite(_mia_num(_ccbase)) and price else np.nan
            _bull_gap=(_bull/price-1) if np.isfinite(_bull) and price else np.nan
            def _vgap(x): return f'{x:+.0%}' if np.isfinite(x) else '—'
            st.markdown(f'<div class="v21261-card" title="Chrímata valuation model. Bear, Base and Bull are model scenarios; percentages compare each scenario with the current provider price."><div class="v21261-title">Valuation Summary {_info}</div><div class="v21261-val-grid"><div><div class="v21261-val-lbl v21261-neg">Bear</div><div class="v21261-val-num">{display_price(_bear,ticker) if np.isfinite(_bear) else "—"}</div><div class="v21261-neg" style="font-size:8px">{_vgap(_bear_gap)}</div></div><div><div class="v21261-val-lbl" style="color:#086ee8">Base</div><div class="v21261-val-num">{display_price(_ccbase,ticker) if np.isfinite(_mia_num(_ccbase)) else "—"}</div><div class="{"v21261-pos" if np.isfinite(_base_gap) and _base_gap>=0 else "v21261-neg"}" style="font-size:8px">{_vgap(_base_gap)}</div></div><div><div class="v21261-val-lbl v21261-pos">Bull</div><div class="v21261-val-num">{display_price(_bull,ticker) if np.isfinite(_bull) else "—"}</div><div class="{"v21261-pos" if np.isfinite(_bull_gap) and _bull_gap>=0 else "v21261-neg"}" style="font-size:8px">{_vgap(_bull_gap)}</div></div></div><div class="v21261-range"><i class="bear"></i><i class="base"></i><i class="bull"></i></div><div class="v21261-range-labels"><span>{display_price(_bear,ticker) if np.isfinite(_bear) else "—"}<br>Bear</span><span>{display_price(_ccbase,ticker) if np.isfinite(_mia_num(_ccbase)) else "—"}<br>Base</span><span>{display_price(_bull,ticker) if np.isfinite(_bull) else "—"}<br>Bull</span></div></div>',unsafe_allow_html=True)
            st.button("View Full Valuation  →",key=f"v21261_nav_val_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Valuation",))
        with _w2:
            _sparkpts="10,36 35,31 60,32 85,26 110,21 135,15 160,20 185,22 210,16 235,12 260,2"
            st.markdown(f'<div class="v21261-card v21281-fc" title="Chrímata deterministic 12M forecast. Target and return come from the same model payload; positive-return probability is empirically calibrated from completed walk-forward observations and is withheld when evidence is insufficient. AI calculated: No."><div class="v21261-title">Forecasts (Model) {_info}</div><div class="v21281-fc-body"><div class="v21261-k">12 Month Target</div><div class="v21281-fc-target">{display_price(_f_target,ticker) if np.isfinite(_f_target) else "—"}</div><div class="v21281-fc-return {"v21261-pos" if np.isfinite(_ccf12) and _ccf12>=0 else "v21261-neg" if np.isfinite(_ccf12) else "v21261-muted"}">{f"{_ccf12:+.1%}" if np.isfinite(_ccf12) else "Forecast unavailable"}</div><div class="v21261-spark"><svg viewBox="0 0 270 48" preserveAspectRatio="none"><polygon points="10,42 {_sparkpts.split(" ",1)[1]} 260,48 10,48" fill="#d9ebfb" opacity=".85"/><polyline points="{_sparkpts}" fill="none" stroke="#086ee8" stroke-width="2"/></svg></div><div class="v21281-fc-prob">Prob. positive return: {f"{_f_prob:.0%}" if np.isfinite(_f_prob) else "—"}</div></div></div>',unsafe_allow_html=True)
            st.button("View Full Forecasts  →",key=f"v21261_nav_fc_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Forecasts",))
        with _w3:
            _al=str(_ccanalyst.get("label") or "Unavailable"); _ac="v21261-pos" if "buy" in _al.lower() else "v21261-neg" if "sell" in _al.lower() else "v21261-muted"
            _dist=[("Strong Buy","strongBuy","#08a142"),("Buy","buy","#08a142"),("Hold","hold","#ffb000"),("Sell","sell","#ff5b2d"),("Strong Sell","strongSell","#ff2448")]
            _dh=''.join(f'<div><span><i class="v21261-adot" style="background:{c}"></i>{lab}</span><b>{int(_ccanalyst.get(k,0) or 0)}</b></div>' for lab,k,c in _dist)
            # V21.2.82 — reference-matched Analyst Consensus card. Provider evidence only; no fabricated counts/targets.
            _bucket_total=sum(int(_ccanalyst.get(k,0) or 0) for _,k,_ in _dist)
            _analyst_n=int(_ccanalyst.get("analysts") or 0)
            _analyst_count_text=f"{_analyst_n} analysts" if _analyst_n else (f"{_bucket_total} analysts" if _bucket_total else "Analyst count unavailable")
            _ae=_ccanalyst.get("evidence",{}) or {}
            _prov=("Analyst evidence supplied by Yahoo Finance via yfinance. "
                   f"Consensus: {_ae.get('consensus_source','unavailable')}. "
                   f"Provider analyst count: {_analyst_n if _analyst_n else 'unavailable'}. "
                   f"Recommendation bucket total: {_bucket_total}; this is not substituted for target coverage count. "
                   "Mean target is provider evidence. Target return is calculated deterministically by Chrímata. AI calculated: No.")
            st.markdown(f'<div class="v21261-card v21282-analyst" title="{html.escape(_prov, quote=True)}"><div class="v21261-title">Analyst Consensus {_info}</div><div class="v21282-analyst-grid"><div class="v21282-analyst-left"><div class="v21282-analyst-status {_ac}">{html.escape(_al)}</div><div class="v21282-analyst-count">{html.escape(_analyst_count_text)}</div><div class="v21282-analyst-target"><div class="v21282-analyst-target-label">Mean target</div><div class="v21282-analyst-target-value">{display_price(_at,ticker) if np.isfinite(_at) else "—"}</div></div></div><div class="v21282-analyst-dist">{_dh}</div></div></div>',unsafe_allow_html=True)
            st.button("View Full Analyst Forecasts  →",key=f"v21261_nav_an_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Forecasts",))
        with _w4:
            # V21.2.83 — genuine four-quarter TTM where available; like-for-like YoY only with eight quarters.
            _ttm=investment_snapshot_ttm_metrics(ticker)
            _fallback={"Revenue":_rev,"EBITDA":_ebitda,"Net Income":_ni,"EPS":_eps,"Free Cash Flow":_fcf}
            _metric_rows=[]; _basis_notes=[]
            for _label in ["Revenue","EBITDA","Net Income","EPS","Free Cash Flow"]:
                _m=_ttm.get(_label,{})
                _val=_mia_num(_m.get("value")); _growth=_mia_num(_m.get("growth")); _value_basis=str(_m.get("value_basis") or ""); _growth_basis=str(_m.get("growth_basis") or "")
                if not np.isfinite(_val):
                    _val=_mia_num(_fallback.get(_label)); _value_basis="Provider trailing/latest field fallback; four-quarter TTM statement series unavailable"
                _disp=(f"{_cur}{_val:,.2f}" if _label=="EPS" and np.isfinite(_val) and _val>=0 else f"-{_cur}{abs(_val):,.2f}" if _label=="EPS" and np.isfinite(_val) else _ov_fmt(_val,_cur)); _disp=_disp.replace(f"{_cur}-",f"-{_cur}")
                if _label=="Free Cash Flow":
                    _cmp_cur=_mia_num(_m.get("compare_current")); _cmp_prev=_mia_num(_m.get("compare_prior"))
                    if np.isfinite(_cmp_cur) and np.isfinite(_cmp_prev):
                        if _cmp_prev>=0 and _cmp_cur<0:
                            _gcls="v21283-growth-neg"; _gtext="Turned negative"
                        elif _cmp_prev<0 and _cmp_cur>=0:
                            _gcls="v21283-growth-pos"; _gtext="Turned positive"
                        elif _cmp_prev<0 and _cmp_cur<0:
                            _delta=_cmp_cur-_cmp_prev
                            _gcls="v21283-growth-pos" if _delta>0 else "v21283-growth-neg" if _delta<0 else "v21283-growth-na"
                            _gtext="Improving" if _delta>0 else "Deteriorating" if _delta<0 else "Flat"
                            _growth_basis=(_growth_basis+f"; FCF remained negative; absolute change {_delta:+,.0f}").strip("; ")
                        elif np.isfinite(_growth):
                            _gcls="v21283-growth-pos" if _growth>=0 else "v21283-growth-neg"; _gtext=f"{_growth:+.0%}"
                        else:
                            _gcls="v21283-growth-na"; _gtext="—"
                    elif np.isfinite(_growth):
                        _gcls="v21283-growth-pos" if _growth>=0 else "v21283-growth-neg"; _gtext=f"{_growth:+.0%}"
                    else:
                        _gcls="v21283-growth-na"; _gtext="—"
                elif np.isfinite(_growth):
                    _gcls="v21283-growth-pos" if _growth>=0 else "v21283-growth-neg"; _gtext=f"{_growth:+.0%}"
                else:
                    _gcls="v21283-growth-na"; _gtext="—"
                _metric_rows.append(f'<tr><td>{html.escape(_label)}</td><td>{html.escape(_disp)}</td><td class="{_gcls}">{html.escape(_gtext)}</td></tr>')
                _basis_notes.append(f"{_label}: value={_value_basis}; growth={_growth_basis}")
            _mh="".join(_metric_rows)
            _prov="Yahoo Finance via yfinance financial statements. Value basis prefers the latest four reported quarters. Growth hierarchy: TTM vs prior TTM when 8 quarters exist; otherwise latest FY vs prior FY; otherwise unavailable. Annual fallback growth is not represented as TTM growth. " + " | ".join(_basis_notes)
            st.markdown(f'<div class="v21261-card v21283-metrics" title="{html.escape(_prov,quote=True)}"><div class="v21261-title">Key Metrics (TTM) {_info}</div><table class="v21261-table">{_mh}</table></div>',unsafe_allow_html=True)
            st.button("View Full Fundamentals  →",key=f"v21261_nav_fund_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Fundamentals",))
        with _w5:
            _quart="lower quartile" if np.isfinite(_range_pos) and _range_pos<.25 else "upper quartile" if np.isfinite(_range_pos) and _range_pos>=.75 else "middle range" if np.isfinite(_range_pos) else "—"
            _rpct=max(0,min(100,float(_range_pos*100))) if np.isfinite(_range_pos) else 50
            _market=[("20D Avg Volume",_ov_fmt(_ccvol)),("Short Interest",f"{_short:.1%}" if np.isfinite(_short) else "—"),("Shares Outstanding",_ov_fmt(_shares))]
            _mk="".join(f'<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>' for k,v in _market)
            _mp_tip=(f"Market Position provenance — Range: {_mp_range_basis}. Current price: provider/latest market price. "
                     f"20D average volume: {_mp_vol_basis}. Short interest: {_mp_short_basis}; never estimated. "
                     f"Shares outstanding: {_mp_shares_basis}. Range position and quartile are calculated by Chrímata as (current-low)/(high-low). "
                     f"Distance from 52W high: {_dist_hi:.1%}; distance above 52W low: {_dist_lo:.1%}." if np.isfinite(_dist_hi) and np.isfinite(_dist_lo) else
                     f"Market Position provenance — Range: {_mp_range_basis}. 20D average volume: {_mp_vol_basis}. Short interest: {_mp_short_basis}. Shares outstanding: {_mp_shares_basis}.")
            st.markdown(f'<div class="v21261-card v21286-market" title="{html.escape(_mp_tip,quote=True)}"><div class="v21261-title">Market Position {_info}</div><div class="v21261-market-range"><div class="v21286-range-row"><div class="v21286-range-badge">▼</div><div class="v21286-range-main" style="--mp-pos:{_rpct:.1f}%"><div class="v21261-k">52 Week Range</div><div class="v21261-market-track"><i class="v21261-market-now" style="left:{_rpct:.1f}%"></i><i class="v21261-market-high"></i></div><div class="v21261-market-labels"><span>{display_price(_cclo,ticker) if np.isfinite(_cclo) else "—"}</span><span>{display_price(price,ticker) if np.isfinite(price) else "—"}</span><span>{display_price(_cchi,ticker) if np.isfinite(_cchi) else "—"}</span></div></div></div><div class="v21286-range-position">{f"{_range_pos:.0%} of range ({_quart})" if np.isfinite(_range_pos) else "Range position unavailable"}</div></div><table class="v21261-table">{_mk}</table></div>',unsafe_allow_html=True)
            st.button("View Company Details  →",key=f"v21261_nav_det_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Fundamentals",))

        st.markdown('<style>\n/* V21.2.96 — restored native View-all control in the announcement card header */\n[class*="st-key-v21293_nav_ann_legacy_"]{position:relative!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;z-index:999!important;overflow:visible!important;}\n[class*="st-key-v21293_nav_ann_legacy_"] .stButton{height:0!important;min-height:0!important;margin:0!important;padding:0!important;overflow:visible!important;}\n[class*="st-key-v21293_nav_ann_legacy_"] button{position:absolute!important;right:7px!important;bottom:296px!important;width:auto!important;min-height:25px!important;height:25px!important;padding:0 4px!important;border:0!important;background:#fff!important;box-shadow:none!important;color:#0067e8!important;font-size:13px!important;font-weight:700!important;text-decoration:underline!important;}\n[class*="st-key-v21293_nav_ann_legacy_"] button:hover{background:#fff!important;color:#004fb3!important;border:0!important;}\n</style>',unsafe_allow_html=True)
        st.markdown('''<style>
/* V21.3.11 — white reference card + contained disclosure navigation. */
.v21310-ann-title{font-size:13px;font-weight:800;color:#082b5c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.v21310-ann-body{height:105px;overflow:hidden;border-top:1px solid #e5edf7;background:#fff;}
.v21310-ann-row{display:grid;grid-template-columns:92px minmax(0,1fr) 102px 44px;height:21px;align-items:center;border-bottom:1px solid #e5edf7;color:#355b89;font-size:10.5px;}
.v21310-ann-row>span{height:21px;line-height:21px;padding:0 8px;border-right:1px solid #e5edf7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.v21310-ann-row>span:last-child{border-right:0;text-align:center;padding:0}.v21310-ann-row .main{color:#244f82}.v21310-ann-row .meta{color:#6c82a1}.v21310-ann-row a{color:#0067e8!important;font-weight:800;text-decoration:none!important;}
.v21310-ann-empty{height:105px;display:flex;align-items:flex-start;padding:16px 12px;color:#7187a6;font-size:10.5px;background:#fff}.v21310-ann-source{min-height:22px;display:flex;align-items:center;color:#8a9bb4;font-size:9.5px;background:#fff;padding:3px 0 1px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
[class*="st-key-v21310_ann_card_"]{min-height:168px!important;padding:7px 10px 8px!important;overflow:visible!important;background:#fff!important;}
[class*="st-key-v21310_ann_card_"]>div,[class*="st-key-v21310_ann_card_"] [data-testid="stVerticalBlock"]{background:#fff!important;}
[class*="st-key-v21310_ann_card_"] [class*="st-key-v21310_nav_ann_"] button{width:auto!important;min-height:25px!important;height:25px!important;padding:0 2px!important;border:0!important;background:transparent!important;box-shadow:none!important;color:#0067e8!important;font-size:11px!important;font-weight:800!important;white-space:nowrap!important;}
</style>''',unsafe_allow_html=True)

        # V21.2.90 — Company Intelligence & Decision Monitoring Reference Cards.
        # Each card remains evidence-first: provider/stored rows only; unsupported fields render as unavailable.

        st.markdown("""<style>
        [class*="st-key-v21313_news_card_"]{background:#fff!important;border-color:#d8e5f2!important;border-radius:8px!important;min-height:158px!important;height:158px!important;overflow:hidden!important}
        [class*="st-key-v21313_news_card_"] [data-testid="stVerticalBlock"]{gap:0!important}
        [class*="st-key-v21313_news_card_"] .stButton{display:flex!important;justify-content:flex-end!important}
        [class*="st-key-v21313_news_card_"] .stButton>button{width:auto!important;min-height:22px!important;height:22px!important;padding:0 2px!important;border:0!important;background:transparent!important;color:#086ee8!important;box-shadow:none!important;font-size:8.5px!important;font-weight:900!important}
        .v21313-news-title{font-size:10.5px;font-weight:950;color:#10264b;white-space:nowrap}.v21313-news-title span{color:#086ee8;margin-right:4px}
        .v21313-news-body{margin-top:2px;border-top:1px solid #dfe8f2}.v21313-news-row{display:grid;grid-template-columns:68px minmax(0,1fr) 72px;gap:5px;align-items:center;border-bottom:1px solid #dfe8f2;padding:4px 1px;font-size:8.4px;color:#45688f;line-height:1.15}
        .v21313-news-row .main{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21313-news-row .main a{color:#29476f;text-decoration:none}.v21313-news-row .main a:hover{text-decoration:underline}.v21313-news-row .meta{text-align:right;color:#66809c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v21313-news-empty{font-size:8.3px;color:#6b8198;padding:10px 2px}
        </style>""",unsafe_allow_html=True)
        _news=overview_news_safe(ticker,5)
        # V21.2.91 — load the official/regulatory announcement engine directly for
        # the reference card. `latest_announcements_safe` can be provider-thin and
        # previously caused the Overview card to show empty even when ASX had rows.
        try:
            _secid=dict(st.session_state.get("chr_security_identity") or {})
            _id_ticker=str(_secid.get("ticker") or _secid.get("provider_symbol") or ticker)
            _id_exchange=str(_secid.get("exchange") or _secid.get("market") or st.session_state.get("chr_active_exchange","") or _ccmeta.get("exchange") or _ccmeta.get("exchDisp") or "")
            _id_country=str(_secid.get("country") or st.session_state.get("chr_active_country","") or _ccmeta.get("country") or "")
            _v21291_ann_all,_v21291_coverage,_v21292_identity=official_disclosure_gateway(
                _id_ticker,_ann_url,_ann_key,25, exchange=_id_exchange, country=_id_country
            )
        except Exception:
            _v21291_ann_all,_v21291_coverage=pd.DataFrame(),"Announcement source unavailable"
        _ann_df=_v21291_ann_all.head(5).copy() if _v21291_ann_all is not None and not _v21291_ann_all.empty else pd.DataFrame()
        _secid=dict(st.session_state.get("chr_security_identity") or {})
        _prov_ticker=str(_secid.get("ticker") or _secid.get("provider_symbol") or ticker)
        _prov_exchange=str(_secid.get("exchange") or _secid.get("market") or st.session_state.get("chr_active_exchange","") or _ccmeta.get("exchange") or _ccmeta.get("exchDisp") or "")
        _prov_country=str(_secid.get("country") or st.session_state.get("chr_active_country","") or _ccmeta.get("country") or "")
        _v21291_prov=announcement_provenance_global(
            _prov_ticker,_v21291_coverage, exchange=_prov_exchange, country=_prov_country
        )
        _cat_df=_cccatalysts.head(5).copy() if _cccatalysts is not None and not _cccatalysts.empty else pd.DataFrame()

        def _v21290_pick(row, names, default=""):
            for n in names:
                try:
                    v=row.get(n)
                    if pd.notna(v) and str(v).strip() not in ("","nan","None"):
                        return str(v).strip()
                except Exception: pass
            return default
        def _v21290_date(v):
            if not str(v or "").strip(): return "—"
            try: return pd.to_datetime(v).strftime("%d %b %Y")
            except Exception: return str(v)[:12]
        def _v21290_ann_type(title, supplied=""):
            if supplied: return supplied[:18]
            t=str(title).lower()
            if any(x in t for x in ("result","appendix 4e","annual report","half year")): return "Results"
            if "director" in t: return "Director"
            if any(x in t for x in ("trading update","quarterly","activities")): return "Trading Update"
            if "presentation" in t: return "Presentation"
            return "Announcement"

        _m1,_m2,_m3,_m4=st.columns([1.34,1.13,.94,.98],gap="small")
        with _m1:
            _rows=[]
            if not _ann_df.empty:
                for _,r in _ann_df.iterrows():
                    _d=_v21290_date(_v21290_pick(r,["date","Date","published","datetime","release_date"]))
                    _t=_v21290_pick(r,["title","Title","headline","Headline","name","announcement"],"Announcement")
                    _ty=_v21290_ann_type(_t,_v21290_pick(r,["type","Type","category","Category"]))
                    _url=_v21290_pick(r,["PDFURL","pdf_url","document_url","URL","url","link","Link"])
                    _has_pdf=bool(r.get("Has PDF",False)) if hasattr(r,"get") else False
                    _doc_label=("PDF" if _has_pdf else ("FILE" if str(_v21291_prov.get("market") or "") in ("NASDAQ","NYSE") else "VIEW"))
                    _pdf=(f'<a class="v21291-pdf" href="{html.escape(_url,quote=True)}" target="_blank" rel="noopener">{_doc_label}</a>' if _url else '<span class="v21291-na">—</span>')
                    _rows.append(f'<div class="v21290-row"><span>{html.escape(_d)}</span><span class="main" title="{html.escape(_t,quote=True)}">{html.escape(_t)}</span><span class="meta">{html.escape(_ty)}</span><span class="pdf">{_pdf}</span></div>')
            _sec_status=str(getattr(_v21291_ann_all,"attrs",{}).get("status","") or "") if _v21291_ann_all is not None else ""
            _status_msg={"IDENTITY_FAILED":"Disclosure identity could not be resolved.","UPSTREAM_ERROR":"Official disclosure source could not be reached.","PARSE_FAILED":"Official disclosure response could not be parsed.","NO_DISCLOSURES":"No investor-relevant disclosures were returned.","CIK_RESOLUTION_FAILED":"SEC ticker/CIK mapping could not be resolved.","SEC_REQUEST_FAILED":"SEC EDGAR could not be reached.","NO_INVESTOR_FILINGS":"No investor-relevant SEC filings were returned."}.get(_sec_status,"")
            _authority=str(_v21291_prov.get("authority") or "")
            _empty_fallback=("Disclosure source could not be resolved for this listing." if str(_v21291_prov.get("market") or "")=="UNKNOWN" else "No rows returned from "+(_authority or "the configured announcement source")+".")
            _empty_detail=html.escape(_status_msg or _empty_fallback)
            _body="".join(_rows) if _rows else f'<div class="v21290-empty">{_empty_detail}</div>'
            _tip=(f'Source: {_v21291_prov.get("authority","—")}. Coverage: {_v21291_prov.get("coverage","—")}. '+
                  f'Document access: {_v21291_prov.get("document_policy","—")}')
            # V21.3.10 — self-contained reference header; no page-level/absolute positioning.
            _body09=_body.replace('v21290-row','v21310-ann-row').replace('v21290-empty','v21310-ann-empty')
            with st.container(border=True,key=f"v21310_ann_card_{ticker}"):
                _ann_h1,_ann_h2=st.columns([5.2,1.0],gap="small",vertical_alignment="center")
                with _ann_h1:
                    st.markdown(f'<div class="v21310-ann-title"><span class="v21290-icon">♟</span> Latest Announcements &amp; Reports <span class="v21261-info" title="{html.escape(_tip,quote=True)}">i</span></div>',unsafe_allow_html=True)
                with _ann_h2:
                    if st.button("View all →",key=f"v21310_nav_ann_{ticker}",use_container_width=False):
                        _chr_set_cc_sub_v2111("Announcements & Reports")
                        st.rerun()
                st.markdown(f'<div class="v21310-ann-body">{_body09}</div><div class="v21310-ann-source">{html.escape(str(_v21291_prov.get("market") or ""))} · {html.escape(str(_v21291_prov.get("authority") or ""))}</div>',unsafe_allow_html=True)
        with _m2:
            _rows=[]
            if _news is not None and not _news.empty:
                for r in _news.itertuples():
                    _headline=html.escape(str(r.Headline)); _src=html.escape(str(r.Source)); _url=html.escape(str(getattr(r,"URL","") or ""),quote=True)
                    _headline_html=(f'<a href="{_url}" target="_blank" rel="noopener" title="{html.escape(str(r.Headline),quote=True)}">{_headline}</a>' if _url else _headline)
                    _rows.append(f'<div class="v21313-news-row"><span>{html.escape(str(r.Date))}</span><span class="main">{_headline_html}</span><span class="meta">{_src}</span></div>')
            _body="".join(_rows) if _rows else '<div class="v21313-news-empty">No recent company news is available from the configured provider.</div>'
            with st.container(border=True,key=f"v21313_news_card_{ticker}"):
                _nh1,_nh2=st.columns([5.2,1.0],gap="small",vertical_alignment="center")
                with _nh1: st.markdown('<div class="v21313-news-title"><span>▣</span> Recent News</div>',unsafe_allow_html=True)
                with _nh2:
                    if st.button("View all →",key=f"v21313_nav_news_{ticker}",use_container_width=False):
                        _chr_set_cc_sub_v2111("News & Events"); st.rerun()
                st.markdown(f'<div class="v21313-news-body">{_body}</div>',unsafe_allow_html=True)
        with _m3:
            _rows=[]
            if not _cat_df.empty:
                for _,r in _cat_df.iterrows():
                    _rawdate=_v21290_pick(r,["event_date","date","Date"])
                    _d=_v21290_date(_rawdate) if _rawdate and str(_rawdate).upper()!="TBD" else (str(_rawdate) or "TBD")
                    _event=_v21290_pick(r,["event","Event","title","Title"],"Catalyst")
                    _status=_v21290_pick(r,["status","Status"]).lower()
                    _done=any(x in _status for x in ("done","complete","actual","occurred"))
                    _rows.append(f'<div class="v21290-row"><span>{html.escape(_d)}</span><span class="main">{html.escape(_event)}</span><span class="status {"done" if _done else ""}">{"●" if _done else "○"}</span></div>')
            _body="".join(_rows) if _rows else '<div class="v21290-empty">No stored catalysts yet. Add evidence in Catalyst Calendar.</div>'
            st.markdown(f'<div class="v21290-card v21290-cat"><div class="v21290-title"><span class="v21290-icon">✿</span>Upcoming Catalysts</div><span class="v21290-viewall">View all →</span>{_body}</div>',unsafe_allow_html=True)
            st.button("View all catalysts",key=f"v21290_nav_cat_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Catalyst Calendar",))
        with _m4:
            _attention=[]
            if _ccattention is not None and not _ccattention.empty:
                for _,r in _ccattention.head(4).iterrows():
                    _item=_v21290_pick(r,["Item","item","Metric","metric","Condition","condition"],"Research condition")
                    _detail=_v21290_pick(r,["Why","why","Detail","detail","Evidence","evidence","Status","status"],"Evidence requires review")
                    _attention.append((_item,_detail,"Watch" if len(_attention)<2 else "Monitor"))
            if not _attention and '_thesis_rows' in locals() and _thesis_rows is not None and not _thesis_rows.empty:
                for _,r in _thesis_rows.iterrows():
                    _st=str(r.get("status") or "").lower()
                    if _st in {"watch","warning","at risk","attention","broken","pending"}:
                        _attention.append((str(r.get("metric") or r.get("condition") or "Thesis condition"),str(r.get("source") or "Evidence requires review"),"Watch" if len(_attention)<2 else "Monitor"))
                    if len(_attention)>=4: break
            _ah="".join(f'<div class="v21290-attn-item"><span class="v21290-rank">{i}</span><div><div class="v21290-attn-main">{html.escape(a[:58])}</div><div class="v21290-attn-sub">{html.escape(b[:82])}</div></div><span class="v21290-pill {"watch" if c=="Watch" else ""}">{c}</span></div>' for i,(a,b,c) in enumerate(_attention[:4],1))
            if not _ah:_ah='<div class="v21290-empty">No evidence-backed attention item is currently triggered. This is not a statement that the company has no risks.</div>'
            st.markdown(f'<div class="v21290-card v21290-attn"><div class="v21290-title"><span class="v21290-icon">▲</span>What Requires My Attention?</div>{_ah}</div>',unsafe_allow_html=True)

        _qty=float(hold.get("quantity",0) or 0); _avg=float(hold.get("avg_cost",0) or 0); _mv=_qty*price; _pnl=(price-_avg)*_qty if _qty else np.nan; _pp=price/_avg-1 if _qty and _avg else np.nan
        _b1,_b2=st.columns([.98,1.78],gap="small")
        with _b1:
            st.markdown(f'<div class="v21290-bottom"><div class="v21290-bottom-title">♙ <span>Position Context (if in Portfolio)</span></div><div class="v21290-stats"><div class="v21290-stat"><div class="k">Shares</div><div class="v">{f"{_qty:,.0f}" if _qty else "—"}</div></div><div class="v21290-stat"><div class="k">Avg. Cost</div><div class="v">{display_price(_avg,ticker) if _qty else "—"}</div></div><div class="v21290-stat"><div class="k">Market Value</div><div class="v">{_cur+f"{_mv:,.0f}" if _qty else "—"}</div></div><div class="v21290-stat"><div class="k">Unrealised P/L</div><div class="v {"v21261-pos" if np.isfinite(_pnl) and _pnl>=0 else "v21261-neg"}">{f"{_pp:+.1%} ({_cur}{_pnl:+,.0f})" if np.isfinite(_pnl) else "—"}</div></div></div></div>',unsafe_allow_html=True)
        with _b2:
            _needs=[]
            if np.isfinite(_ccbase): _needs.append(f"support the base valuation case of {display_price(_ccbase,ticker)}")
            if _attention: _needs.append("resolve or de-risk the current attention conditions")
            _met=[]
            if '_thesis_rows' in locals() and _thesis_rows is not None and not _thesis_rows.empty:
                for _,r in _thesis_rows.iterrows():
                    if str(r.get("status") or "").lower() in {"met","on track","pass","passed","true"}: _met.append(str(r.get("metric") or r.get("condition") or "thesis condition"))
            if _met: _needs.append("keep evidenced thesis conditions on track")
            _sc=f"For {_ccname}, the evidence would need to "+("; ".join(_needs)+"." if _needs else "strengthen across fundamentals, valuation and measurable thesis conditions before a stronger scenario is supported.")
            st.markdown(f'<div class="v21290-bottom"><div class="v21290-bottom-title">◎ <span>What Would Need to Happen?</span></div><div class="v21290-scenario">{html.escape(_sc)}</div><div class="v21290-source">Scenario narrative is generated from Chrímata valuation, thesis and attention evidence; it is not a price prediction.</div></div>',unsafe_allow_html=True)
            st.button("View Scenario Analysis  →",key=f"v21290_nav_scen_{ticker}",use_container_width=True,on_click=_chr_set_cc_sub_v2111,args=("Valuation",))

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
    st.header(f"Investment Thesis Monitor — {ticker}")
    st.caption("Monitor measurable thesis conditions using reported evidence and deterministic Python calculations. AI does not calculate the financial metrics or pass/fail states.")
    try:
        _ts_existing=thesis_table(ticker)
        _ts_source="Stored thesis conditions"
        if _ts_existing is None or _ts_existing.empty:
            _ts_meta=safe_info(ticker)
            _ts_cls=safe_company_classification(ticker)
            _ts_existing=overview_dynamic_thesis(ticker,_ts_cls.get("sector",""),_ts_cls.get("industry",""),_ts_meta,price,price)
            _ts_source="Chrímata evidence-driven monitoring"
        _ts_summary=calculate_thesis_status(_ts_existing,expected_total=(len(_ts_existing) if _ts_existing is not None and len(_ts_existing) else 6),source=_ts_source)
        _tsa,_tsb,_tsc,_tsd=st.columns(4)
        _tsa.metric("Thesis status",_ts_summary["status_label"])
        _tsb.metric("On track",f"{_ts_summary['on_track_count']} / {_ts_summary['total_conditions']}")
        _tsc.metric("Watch",str(_ts_summary["watch_count"]))
        _tsd.metric("Evidence coverage",f"{_ts_summary['evidence_coverage']:.0%}")
        st.caption(f"{_ts_summary['evaluated_count']} evaluated · {_ts_summary['pending_count']} awaiting evidence · AI calculated: No")
    except Exception:
        pass
    _det=deterministic_financial_thesis(ticker)
    if _det:
        _dm=_det["metrics"]; _ds=_det["scorecard"]; _dv=_det["verification"]
        st.subheader("Deterministic financial evidence")
        _dc1,_dc2,_dc3=st.columns(3)
        _dc1.metric("Revenue YoY", "—" if _dm.get("Revenue_YoY_Pct") is None else f"{_dm['Revenue_YoY_Pct']:.2f}%")
        _dc2.metric("Operating margin", "—" if _dm.get("Operating_Margin_Pct") is None else f"{_dm['Operating_Margin_Pct']:.2f}%")
        _dc3.metric("Free cash flow YoY", "—" if _dm.get("Free_Cash_Flow_YoY_Pct") is None else f"{_dm['Free_Cash_Flow_YoY_Pct']:.2f}%")
        _vr=[]
        for _k,_v in _ds.items():
            _vr.append({"Condition":_k.replace("_"," "),"Status":"On track" if _v is True else ("Watch" if _v is False else "Pending"),"Calculated by":"Deterministic Python"})
        st.dataframe(pd.DataFrame(_vr),use_container_width=True,hide_index=True)
        st.caption("Verification: deterministic_python · AI calculated metrics: No · Missing evidence remains Pending.")
    else:
        st.info("Deterministic financial scorecard is pending because two comparable financial periods are not currently available from the data layer.")
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
        st.info("No user-defined thesis conditions yet. Showing the automatic evidence scorecard used by Overview.")
        _auto_meta=info(ticker) or {}
        _auto_class=safe_company_classification(ticker)
        _auto_price=np.nan
        try:
            _auto_h=history(ticker,"5d")
            if _auto_h is not None and not _auto_h.empty: _auto_price=float(_auto_h["Close"].iloc[-1])
        except Exception: pass
        _auto=overview_dynamic_thesis(ticker,_auto_class.get("sector",""),_auto_class.get("industry",""),_auto_meta,np.nan,_auto_price)
        if _auto is not None and not _auto.empty:
            st.dataframe(_auto.rename(columns={"metric":"Condition","status":"Status","evidence":"Evidence","source":"Source"}),use_container_width=True,hide_index=True)
            st.caption("Automatic statuses use traceable provider statement comparisons where available. Pending means Chrímata does not yet have enough evidence to classify the condition.")

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
    st.header(f"12M Forecast — {ticker}")
    _fc_hist=history(ticker,"5y")
    _fc_live=build_12m_forecast(_fc_hist,current_price=price,security=ticker)
    _fca=_fc_live.get("audit",{}) or {}
    _fr=_mia_num(_fc_live.get("forecast_return")); _ft=_mia_num(_fc_live.get("target_price")); _fp=_mia_num(_fc_live.get("probability_positive"))
    _f1,_f2,_f3,_f4=st.columns(4)
    metric_box(_f1,"12M forecast","—" if not np.isfinite(_fr) else f"{_fr:+.1%}")
    metric_box(_f2,"Model target","—" if not np.isfinite(_ft) else display_price(_ft,ticker))
    metric_box(_f3,"Prob. positive return","—" if not np.isfinite(_fp) else f"{_fp:.0%}")
    metric_box(_f4,"Validation",str(_fc_live.get("validation_label") or "Unavailable"))
    st.caption("Chrímata deterministic model output. It is separate from analyst consensus and is not a price promise or investment recommendation.")
    with st.expander("Forecast evidence ⓘ",expanded=False):
        _fd=_fca.get("diagnostics",{}) or {}
        st.write(f"Model version: {_fca.get('model_version','—')}")
        st.write(f"Price-history observations: {_fca.get('history_observations','—')}")
        st.write(f"Completed 12M training outcomes: {_fca.get('training_outcomes','—')}")
        st.write(f"Walk-forward observations: {_fca.get('walk_forward_observations','—')}")
        st.write(f"Probability calibration observations: {_fca.get('probability_calibration_observations','—')}")
        st.write(f"Direction accuracy: {'—' if _mia_num(_fd.get('direction_accuracy')) is None or not np.isfinite(_mia_num(_fd.get('direction_accuracy'))) else f'{_mia_num(_fd.get('direction_accuracy')):.1%}'}")
        st.write(f"MAE: {'—' if _mia_num(_fd.get('mae')) is None or not np.isfinite(_mia_num(_fd.get('mae'))) else f'{_mia_num(_fd.get('mae')):.1%}'}")
        st.write(f"Forecast origin: {_fca.get('forecast_origin','—')}")
        st.write(f"Method: {_fca.get('method','—')}")
        st.write(f"Status: {_fca.get('status','unavailable')} · {_fca.get('reason','')}")
        st.write("AI calculated: No")
    st.divider()
    render_forecast_tool(ticker,h)
    st.divider()
    render_advanced_forecasting(ticker,h)
    st.divider()
    render_analyst_consensus(ticker,price)

elif page=="News & Events":
    st.markdown(f"## News & Events Intelligence Centre — {ticker}")
    st.caption("Company news, sector context and macro events connected to the currently selected listing. Relevance explains a transmission channel; it is not a prediction of share-price direction.")
    _ni,_ni_ident=news_intelligence(ticker,30,20,20)
    _c1,_c2,_c3,_c4=st.columns(4)
    _c1.metric("Company news",int((_ni.Layer=="Company").sum()) if not _ni.empty else 0)
    _c2.metric("Sector events",int((_ni.Layer=="Sector").sum()) if not _ni.empty else 0)
    _c3.metric("Macro events",int((_ni.Layer=="Macro").sum()) if not _ni.empty else 0)
    _c4.metric("Total relevant events",len(_ni))
    _tabs=st.tabs(["All Relevant Events","Company News","Sector & Competitors","Macro & Market Events"])
    for _tab,_layer in zip(_tabs,[None,"Company","Sector","Macro"]):
        with _tab:
            _d=_ni if _layer is None else _ni[_ni.Layer.eq(_layer)]
            if _d.empty:
                st.info("No events are currently available from the configured provider for this layer.")
            else:
                for _i,_r in _d.head(40).iterrows():
                    with st.expander(f"{_r['Date']} · {_r['Headline']} — {_r['Source']}"):
                        st.markdown(f"**What happened**  \n{_r['Headline']}")
                        st.markdown(f"**Why it may matter to {_ni_ident.get('name',ticker)}**  \n{_r['Why it matters']}")
                        _a,_b,_c=st.columns(3)
                        _a.markdown(f"**Layer**  \n{_r['Layer']}")
                        _b.markdown(f"**Affected KPI**  \n{_r['Affected KPI']}")
                        _c.markdown(f"**Relevance**  \n{_r['Relevance']}")
                        st.markdown(f"**What to watch next**  \n{_r['What to watch']}")
                        if str(_r.get('Macro Factor') or '—') != '—':
                            st.markdown("**So What? — Macro-to-Micro Exposure Map**")
                            _m1,_m2,_m3=st.columns(3)
                            _m1.markdown(f"**Economic factor**  \n{_r['Macro Factor']}")
                            _m2.markdown(f"**Market tracker**  \n{_r['Tracker']}")
                            _m3.markdown(f"**Affected KPI**  \n{_r['Affected KPI']}")
                            st.markdown(f"**Transmission channel**  \n{_r['Transmission']}")
                            st.caption("Mapped deterministically from the selected company's structural exposure profile; not an AI price prediction or proof of causation.")
                        st.caption(f"Category: {_r['Category']} · Source: {_r['Source']}")
                        if str(_r.get('URL') or '').strip(): st.link_button("Open original source ↗",str(_r['URL']))
    st.caption("News provider: Yahoo Finance/yfinance public interface. Sector and macro layers are contextual discovery; verify material events against primary company/exchange/regulatory sources.")

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

elif page in {"About","Privacy","Disclaimer","Terms","Data Sources","Contact"}:
    # V21.2.99 — intentionally minimal placeholders. Full legal/information copy will be added later.
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    st.header(page)
    st.caption("Content coming soon.")

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

# V21.3.02 — Unified footer typography + compact navigation spacing.
# Brand and legal navigation share one visual baseline on desktop while retaining
# native Streamlit callbacks (no browser-page reload / white flash).
def render_chrimata_global_legal_footer():
    st.markdown(r"""
    <style>
    .chr-legal-rule{width:100%;box-sizing:border-box;margin:30px 0 9px;border-top:1px solid #d8e2ef;height:1px;}
    .chr-legal-brand{font-size:11.5px;font-weight:800;color:#263f5f;line-height:1.35;padding-top:3px;white-space:nowrap;}
    [class*="st-key-chr_footer_nav_"]{margin-top:0!important;margin-bottom:0!important;}
    [class*="st-key-chr_footer_nav_"] button{min-height:0!important;height:auto!important;padding:2px 0!important;border:0!important;background:transparent!important;box-shadow:none!important;color:#3f6f9f!important;font-size:11.5px!important;font-weight:800!important;line-height:1.35!important;white-space:nowrap!important;}
    [class*="st-key-chr_footer_nav_"] button:hover{color:#175d9c!important;text-decoration:underline!important;background:transparent!important;border:0!important;}
    .chr-legal-copy{width:100%;box-sizing:border-box;padding:5px 0 88px;color:#6b7f98;font-size:10.5px;line-height:1.45;}
    .chr-legal-copy p{margin:4px 0;}.chr-legal-title{font-weight:750;color:#455f7d;}
    .chr-legal-meta{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid #e4eaf1;color:#8190a3;font-size:9.8px;}
    @media(max-width:900px){
      .chr-legal-brand{white-space:normal;font-size:11px;}
      [class*="st-key-chr_footer_nav_"] button{font-size:11px!important;white-space:normal!important;}
      .chr-legal-copy{padding-bottom:96px;}
    }
    </style>
    <div class="chr-legal-rule"></div>
    """, unsafe_allow_html=True)

    # One aligned header row: brand left, compact navigation group right.
    head=st.columns([5.6, 4.4], gap="small", vertical_alignment="center")
    with head[0]:
        st.markdown('<div class="chr-legal-brand">Chrímata · Market Investment Analyst</div>', unsafe_allow_html=True)
    labels=["About","Privacy","Disclaimer","Terms","Data Sources","Contact"]
    with head[1]:
        nav=st.columns([.68,.76,.96,.66,1.08,.72], gap="small", vertical_alignment="center")
        for i,label in enumerate(labels):
            with nav[i]:
                st.button(label,key=f"chr_footer_nav_{i}",type="tertiary",on_click=_chr_set_legal_route_v21300,args=(label,),use_container_width=True)

    st.markdown(r"""
    <div class="chr-legal-copy">
      <p><span class="chr-legal-title">Information and research only.</span> Chrímata provides market data, analytical tools, estimates and research outputs for informational and educational purposes. It does not provide personal financial advice, investment advice, or a recommendation to buy or sell a financial product.</p>
      <p>Market information may be delayed, incomplete or inaccurate. Forecasts, valuations, scenarios, analyst information and AI-generated analysis involve assumptions and uncertainty and are not guarantees of future performance. Conduct your own research and consider appropriately licensed financial advice before making an investment decision. Past performance is not a reliable indicator of future performance.</p>
      <div class="chr-legal-meta"><span>Data may include exchange/regulatory disclosures, company filings and configured third-party market-data providers. Provenance is displayed where available.</span><span>© 2026 Chrímata. All rights reserved.</span></div>
    </div>
    """, unsafe_allow_html=True)

render_chrimata_global_legal_footer()


