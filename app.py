import os
import math
import json
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ASX AI Investment Analyst",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# HELPERS
# ============================================================

def safe_number(value):
    try:
        if value is None:
            return None
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    except Exception:
        return None


def fmt_money(value, decimals=2):
    value = safe_number(value)
    if value is None:
        return "N/A"

    abs_value = abs(value)

    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"

    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs_value >= 1_000:
        return f"${value / 1_000:,.2f}K"

    return f"${value:,.{decimals}f}"


def fmt_number(value, decimals=2):
    value = safe_number(value)
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def fmt_percent(value, decimals=1):
    value = safe_number(value)
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def get_info_value(info, *keys):
    for key in keys:
        value = info.get(key)
        if value is not None:
            return value
    return None


def normalise_ticker(raw_ticker):
    ticker = raw_ticker.strip().upper()

    if not ticker:
        return ""

    # Automatically add .AX for normal ASX tickers
    if "." not in ticker:
        ticker = ticker + ".AX"

    return ticker


def display_ticker(yahoo_ticker):
    return yahoo_ticker.replace(".AX", "")


def safe_statement(ticker_obj, attribute):
    try:
        df = getattr(ticker_obj, attribute)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def find_statement_value(df, possible_rows, column=None):
    if df is None or df.empty:
        return None

    if column is None:
        if len(df.columns) == 0:
            return None
        column = df.columns[0]

    for row in possible_rows:
        if row in df.index:
            try:
                return safe_number(df.loc[row, column])
            except Exception:
                pass

    return None


def calculate_growth(current, previous):
    current = safe_number(current)
    previous = safe_number(previous)

    if current is None or previous is None or previous == 0:
        return None

    return (current - previous) / abs(previous)


# ============================================================
# TECHNICAL ANALYSIS
# ============================================================

def calculate_technicals(history):
    if history is None or history.empty:
        return history

    df = history.copy()

    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()
    df["SMA_200"] = df["Close"].rolling(200).mean()

    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["RSI_14"] = 100 - (100 / (1 + rs))

    exp12 = df["Close"].ewm(span=12, adjust=False).mean()
    exp26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = exp12 - exp26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    return df


# ============================================================
# SECTOR FRAMEWORK
# ============================================================

def sector_framework(sector, industry):
    combined = f"{sector} {industry}".lower()

    if "bank" in combined:
        return [
            "Net interest margin",
            "CET1 capital ratio",
            "Bad debts / impairment charges",
            "Return on equity",
            "Loan growth",
            "Deposit growth",
            "Funding costs",
        ]

    if any(word in combined for word in ["mining", "metals", "gold", "copper", "iron"]):
        return [
            "Production volumes",
            "Realised commodity prices",
            "AISC / unit costs",
            "Reserves and mine life",
            "Capital expenditure",
            "Free cash flow",
            "Balance sheet strength",
        ]

    if any(word in combined for word in ["software", "technology", "internet"]):
        return [
            "ARR / recurring revenue",
            "Customer growth",
            "Customer retention / churn",
            "Gross margin",
            "Operating leverage",
            "Free cash flow",
            "Sales efficiency",
        ]

    if any(word in combined for word in ["retail", "consumer cyclical"]):
        return [
            "Same-store sales",
            "Gross margin",
            "Inventory growth",
            "Store growth",
            "Online sales",
            "Operating margin",
            "Free cash flow",
        ]

    if any(word in combined for word in ["reit", "real estate"]):
        return [
            "Funds from operations",
            "Occupancy",
            "WALE",
            "Gearing",
            "Net tangible assets",
            "Distribution growth",
            "Interest coverage",
        ]

    if any(word in combined for word in ["healthcare", "biotechnology", "medical"]):
        return [
            "Revenue growth",
            "Product pipeline",
            "Regulatory approvals",
            "R&D expenditure",
            "Cash burn",
            "Gross margin",
            "Commercialisation progress",
        ]

    if any(word in combined for word in ["credit services", "financial services", "fintech"]):
        return [
            "Transaction / payment volume",
            "Customer growth",
            "Revenue growth",
            "Transaction margin",
            "Credit losses / bad debts",
            "Cash EBITDA / Cash EBTDA",
            "Operating leverage",
            "International growth",
            "Regulatory risk",
        ]

    return [
        "Revenue growth",
        "Earnings growth",
        "Operating margin",
        "Free cash flow",
        "Return on equity",
        "Balance sheet strength",
        "Competitive position",
    ]


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=900)
def load_company_data(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    try:
        history = ticker.history(period="5y", auto_adjust=False)
    except Exception:
        history = pd.DataFrame()

    annual_income = safe_statement(ticker, "income_stmt")
    quarterly_income = safe_statement(ticker, "quarterly_income_stmt")

    annual_balance = safe_statement(ticker, "balance_sheet")
    quarterly_balance = safe_statement(ticker, "quarterly_balance_sheet")

    annual_cashflow = safe_statement(ticker, "cashflow")
    quarterly_cashflow = safe_statement(ticker, "quarterly_cashflow")

    try:
        analyst_targets = ticker.analyst_price_targets
    except Exception:
        analyst_targets = None

    try:
        earnings_estimate = ticker.earnings_estimate
    except Exception:
        earnings_estimate = pd.DataFrame()

    try:
        revenue_estimate = ticker.revenue_estimate
    except Exception:
        revenue_estimate = pd.DataFrame()

    try:
        earnings_history = ticker.earnings_history
    except Exception:
        earnings_history = pd.DataFrame()

    try:
        eps_trend = ticker.eps_trend
    except Exception:
        eps_trend = pd.DataFrame()

    try:
        eps_revisions = ticker.eps_revisions
    except Exception:
        eps_revisions = pd.DataFrame()

    try:
        growth_estimates = ticker.growth_estimates
    except Exception:
        growth_estimates = pd.DataFrame()

    try:
        news = ticker.news or []
    except Exception:
        news = []

    return {
        "info": info,
        "history": history,
        "annual_income": annual_income,
        "quarterly_income": quarterly_income,
        "annual_balance": annual_balance,
        "quarterly_balance": quarterly_balance,
        "annual_cashflow": annual_cashflow,
        "quarterly_cashflow": quarterly_cashflow,
        "analyst_targets": analyst_targets,
        "earnings_estimate": earnings_estimate,
        "revenue_estimate": revenue_estimate,
        "earnings_history": earnings_history,
        "eps_trend": eps_trend,
        "eps_revisions": eps_revisions,
        "growth_estimates": growth_estimates,
        "news": news,
    }


# ============================================================
# FINANCIAL SUMMARY
# ============================================================

def build_financial_summary(data):
    info = data["info"]
    income = data["annual_income"]
    balance = data["annual_balance"]
    cashflow = data["annual_cashflow"]

    revenue = None
    previous_revenue = None
    net_income = None
    previous_net_income = None
    operating_cashflow = None
    capex = None

    if not income.empty:
        columns = list(income.columns)

        revenue = find_statement_value(
            income,
            ["Total Revenue", "Operating Revenue"],
            columns[0],
        )

        net_income = find_statement_value(
            income,
            ["Net Income", "Net Income Common Stockholders"],
            columns[0],
        )

        if len(columns) > 1:
            previous_revenue = find_statement_value(
                income,
                ["Total Revenue", "Operating Revenue"],
                columns[1],
            )

            previous_net_income = find_statement_value(
                income,
                ["Net Income", "Net Income Common Stockholders"],
                columns[1],
            )

    if not cashflow.empty:
        columns = list(cashflow.columns)

        operating_cashflow = find_statement_value(
            cashflow,
            [
                "Operating Cash Flow",
                "Total Cash From Operating Activities",
            ],
            columns[0],
        )

        capex = find_statement_value(
            cashflow,
            [
                "Capital Expenditure",
                "Capital Expenditures",
            ],
            columns[0],
        )

    free_cash_flow = None

    if operating_cashflow is not None:
        if capex is not None:
            # Capex is often negative in financial statements
            free_cash_flow = operating_cashflow + capex
        else:
            free_cash_flow = operating_cashflow

    cash = None
    debt = None

    if not balance.empty:
        columns = list(balance.columns)

        cash = find_statement_value(
            balance,
            [
                "Cash Cash Equivalents And Short Term Investments",
                "Cash And Cash Equivalents",
                "Cash",
            ],
            columns[0],
        )

        debt = find_statement_value(
            balance,
            [
                "Total Debt",
                "Long Term Debt And Capital Lease Obligation",
            ],
            columns[0],
        )

    return {
        "revenue": revenue,
        "revenue_growth": calculate_growth(revenue, previous_revenue),
        "net_income": net_income,
        "net_income_growth": calculate_growth(net_income, previous_net_income),
        "operating_cashflow": operating_cashflow,
        "free_cash_flow": free_cash_flow,
        "cash": cash,
        "debt": debt,
        "net_debt": (
            debt - cash
            if debt is not None and cash is not None
            else None
        ),
        "market_cap": get_info_value(info, "marketCap"),
        "enterprise_value": get_info_value(info, "enterpriseValue"),
        "trailing_pe": get_info_value(info, "trailingPE"),
        "forward_pe": get_info_value(info, "forwardPE"),
        "price_to_sales": get_info_value(info, "priceToSalesTrailing12Months"),
        "price_to_book": get_info_value(info, "priceToBook"),
        "roe": get_info_value(info, "returnOnEquity"),
        "roa": get_info_value(info, "returnOnAssets"),
        "gross_margin": get_info_value(info, "grossMargins"),
        "operating_margin": get_info_value(info, "operatingMargins"),
        "profit_margin": get_info_value(info, "profitMargins"),
        "revenue_growth_yahoo": get_info_value(info, "revenueGrowth"),
        "earnings_growth": get_info_value(info, "earningsGrowth"),
        "debt_to_equity": get_info_value(info, "debtToEquity"),
        "current_ratio": get_info_value(info, "currentRatio"),
        "quick_ratio": get_info_value(info, "quickRatio"),
        "dividend_yield": get_info_value(info, "dividendYield"),
        "eps": get_info_value(info, "trailingEps"),
        "forward_eps": get_info_value(info, "forwardEps"),
    }


# ============================================================
# VALUATION MODEL
# ============================================================

def valuation_model(current_price, eps, forward_eps):
    current_price = safe_number(current_price)

    selected_eps = safe_number(forward_eps)

    if selected_eps is None or selected_eps <= 0:
        selected_eps = safe_number(eps)

    if current_price is None or selected_eps is None or selected_eps <= 0:
        return None

    current_pe = current_price / selected_eps

    # Simple starting multiples.
    # User can adjust these in the UI later.
    bear_pe = max(5.0, current_pe * 0.70)
    base_pe = max(7.0, current_pe)
    bull_pe = max(9.0, current_pe * 1.30)

    return {
        "eps_used": selected_eps,
        "current_pe": current_pe,
        "bear_pe": bear_pe,
        "base_pe": base_pe,
        "bull_pe": bull_pe,
        "bear_value": selected_eps * bear_pe,
        "base_value": selected_eps * base_pe,
        "bull_value": selected_eps * bull_pe,
    }


# ============================================================
# RULE-BASED INVESTMENT COMMITTEE
# ============================================================

def committee_score(summary, current_price, valuation):
    score = 5.0
    positives = []
    negatives = []

    revenue_growth = summary.get("revenue_growth")
    if revenue_growth is None:
        revenue_growth = summary.get("revenue_growth_yahoo")

    if revenue_growth is not None:
        if revenue_growth > 0.15:
            score += 0.8
            positives.append("Strong revenue growth.")
        elif revenue_growth > 0:
            score += 0.3
            positives.append("Revenue is growing.")
        elif revenue_growth < 0:
            score -= 0.8
            negatives.append("Revenue is declining.")

    earnings_growth = summary.get("earnings_growth")

    if earnings_growth is not None:
        if earnings_growth > 0.15:
            score += 0.7
            positives.append("Strong earnings growth.")
        elif earnings_growth < 0:
            score -= 0.7
            negatives.append("Earnings growth is negative.")

    operating_margin = summary.get("operating_margin")

    if operating_margin is not None:
        if operating_margin > 0.15:
            score += 0.5
            positives.append("Healthy operating margin.")
        elif operating_margin < 0:
            score -= 0.7
            negatives.append("Operating margin is negative.")

    free_cash_flow = summary.get("free_cash_flow")

    if free_cash_flow is not None:
        if free_cash_flow > 0:
            score += 0.5
            positives.append("Free cash flow is positive.")
        else:
            score -= 0.5
            negatives.append("Free cash flow is negative.")

    roe = summary.get("roe")

    if roe is not None:
        if roe > 0.15:
            score += 0.4
            positives.append("Return on equity is strong.")
        elif roe < 0:
            score -= 0.5
            negatives.append("Return on equity is negative.")

    if valuation is not None:
        if current_price < valuation["base_value"]:
            score += 0.4
            positives.append(
                "Share price is below the simple base-case valuation."
            )
        elif current_price > valuation["bull_value"]:
            score -= 0.5
            negatives.append(
                "Share price is above the simple bull-case valuation."
            )

    score = max(0.0, min(10.0, score))

    return score, positives, negatives


# ============================================================
# OPENAI
# ============================================================

def get_openai_key():
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    return os.getenv("OPENAI_API_KEY")


def create_evidence_pack(
    ticker_name,
    company_name,
    sector,
    industry,
    current_price,
    summary,
    valuation,
    thesis,
    sector_metrics,
):
    evidence = {
        "ticker": ticker_name,
        "company": company_name,
        "sector": sector,
        "industry": industry,
        "current_share_price": current_price,
        "financial_summary": summary,
        "valuation": valuation,
        "investor_thesis": thesis,
        "sector_metrics_to_investigate": sector_metrics,
    }

    return json.dumps(evidence, indent=2, default=str)


def run_ai_committee(
    api_key,
    evidence_pack,
    company_name,
    ticker_name,
):
    try:
        from openai import OpenAI
    except ImportError:
        return None, (
            "The OpenAI package is not installed. "
            "Add 'openai' to requirements.txt."
        )

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
You are an institutional-quality ASX investment research committee.

Company: {company_name}
Ticker: {ticker_name}

You have six specialist roles:

1. FUNDAMENTAL ANALYST
Analyse revenue, earnings, margins, cash flow, balance sheet,
returns on capital and operating trends.

2. VALUATION ANALYST
Analyse valuation multiples, earnings expectations and the
Bear/Base/Bull valuation supplied in the evidence.

3. BULL ANALYST
Construct the strongest evidence-based bullish case.
Do not ignore risks.

4. BEAR ANALYST / KILL MY THESIS
Actively attempt to disprove the investor's thesis.
Look for deteriorating fundamentals, accounting concerns,
credit risk, margin pressure, competitive threats,
valuation risk and missing evidence.

5. RISK ANALYST
Identify financial, operational, regulatory, competitive,
macroeconomic and valuation risks.

6. INVESTMENT COMMITTEE
Synthesize the evidence without blindly averaging the analysts.

IMPORTANT RULES:

- Use ONLY the evidence supplied below.
- Never invent financial figures.
- If information is unavailable, explicitly say "Not available".
- Distinguish verified evidence from interpretation.
- Do not treat missing evidence as positive evidence.
- Challenge the investor's thesis rather than confirming it.
- This is investment research, not personal financial advice.
- Explain both positive and negative evidence.
- Do not claim that a valuation model is precise.
- Identify what information should be researched next.

Return the report with these exact headings:

# EXECUTIVE SUMMARY

# FUNDAMENTAL ANALYST

# VALUATION ANALYST

# BULL CASE

# BEAR CASE — KILL MY THESIS

# RISK ANALYST

# THESIS STATUS

Classify the thesis as one of:
SUPPORTED
PARTIALLY SUPPORTED
UNPROVEN
WEAKENING
BROKEN

Explain why.

# INVESTMENT COMMITTEE SCORE

Give a research-quality score from 0.0 to 10.0.
This is NOT a buy/sell recommendation.
Explain what drives the score.

# WHAT WOULD CHANGE THE THESIS?

# TOP 5 THINGS TO RESEARCH NEXT

# DATA LIMITATIONS

Evidence pack:

{evidence_pack}
"""

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt,
        )

        return response.output_text, None

    except Exception as exc:
        return None, str(exc)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("ASX AI Analyst")

raw_ticker = st.sidebar.text_input(
    "Enter ASX ticker",
    value="ZIP",
    placeholder="ZIP, BHP, CBA, CSL...",
)

ticker_symbol = normalise_ticker(raw_ticker)

st.sidebar.markdown("---")

st.sidebar.subheader("Investment Thesis")

default_thesis = (
    "Revenue and earnings continue growing, margins improve, "
    "cash generation strengthens and the company's competitive "
    "position remains intact."
)

thesis = st.sidebar.text_area(
    "What must be true for your investment to work?",
    value=default_thesis,
    height=180,
)

st.sidebar.markdown("---")

analyse_button = st.sidebar.button(
    "Run Investment Analysis",
    type="primary",
    use_container_width=True,
)


# ============================================================
# HEADER
# ============================================================

st.title("ASX AI Investment Analyst")

st.caption(
    "Fundamentals • Valuation • Bull Case • Bear Case • "
    "Kill My Thesis • Risk • Technicals • Investment Committee"
)

if not ticker_symbol:
    st.info("Enter an ASX ticker in the sidebar.")
    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

with st.spinner(f"Loading {display_ticker(ticker_symbol)} data..."):
    data = load_company_data(ticker_symbol)

info = data["info"]
history = data["history"]

if history.empty and not info:
    st.error(
        "No market data was found. Check the ticker and try again."
    )
    st.stop()


# ============================================================
# COMPANY DETAILS
# ============================================================

ticker_name = display_ticker(ticker_symbol)

company_name = get_info_value(
    info,
    "longName",
    "shortName",
) or ticker_name

sector = info.get("sector", "Not available")
industry = info.get("industry", "Not available")

current_price = get_info_value(
    info,
    "currentPrice",
    "regularMarketPrice",
)

if current_price is None and not history.empty:
    current_price = safe_number(history["Close"].iloc[-1])

summary = build_financial_summary(data)

sector_metrics = sector_framework(sector, industry)

valuation = valuation_model(
    current_price,
    summary.get("eps"),
    summary.get("forward_eps"),
)

rule_score, positives, negatives = committee_score(
    summary,
    current_price,
    valuation,
)


# ============================================================
# COMPANY HEADER
# ============================================================

st.header(f"{ticker_name} — {company_name}")

st.write(f"**Sector:** {sector}")
st.write(f"**Industry:** {industry}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Share Price",
        fmt_money(current_price),
    )

with col2:
    st.metric(
        "Market Cap",
        fmt_money(summary.get("market_cap")),
    )

with col3:
    st.metric(
        "Trailing P/E",
        fmt_number(summary.get("trailing_pe")),
    )

with col4:
    st.metric(
        "Preliminary Score",
        f"{rule_score:.1f} / 10",
    )


# ============================================================
# TABS
# ============================================================

tabs = st.tabs(
    [
        "Investment Committee",
        "Fundamentals",
        "Valuation",
        "Kill My Thesis",
        "Technicals",
        "Financial Statements",
        "Analyst Data",
        "News",
        "AI Research",
    ]
)


# ============================================================
# INVESTMENT COMMITTEE TAB
# ============================================================

with tabs[0]:

    st.header(f"{ticker_name} — INVESTMENT COMMITTEE REPORT")

    st.subheader("Preliminary Research Score")

    st.metric(
        "Research Quality Score",
        f"{rule_score:.1f} / 10",
    )

    st.caption(
        "This score is a research framework, not a buy/sell recommendation."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Evidence Supporting the Case")

        if positives:
            for item in positives:
                st.write(f"✓ {item}")
        else:
            st.write("Insufficient positive evidence identified.")

    with right:
        st.subheader("Evidence Against the Case")

        if negatives:
            for item in negatives:
                st.write(f"⚠ {item}")
        else:
            st.write("No major negative signals detected in available data.")

    st.subheader("Investor Thesis")

    st.info(thesis)

    st.subheader("Sector Research Lens")

    for metric in sector_metrics:
        st.write(f"• {metric}")

    st.warning(
        "Important: Yahoo Finance does not provide every sector-specific "
        "KPI. Metrics such as TTV, credit losses, AISC, ARR, CET1 or WALE "
        "may require company reports and ASX announcements."
    )


# ============================================================
# FUNDAMENTALS TAB
# ============================================================

with tabs[1]:

    st.header("Fundamental Analysis")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Revenue",
            fmt_money(summary.get("revenue")),
        )

        st.metric(
            "Revenue Growth",
            fmt_percent(
                summary.get("revenue_growth")
                if summary.get("revenue_growth") is not None
                else summary.get("revenue_growth_yahoo")
            ),
        )

    with c2:
        st.metric(
            "Net Income",
            fmt_money(summary.get("net_income")),
        )

        st.metric(
            "Earnings Growth",
            fmt_percent(summary.get("earnings_growth")),
        )

    with c3:
        st.metric(
            "Operating Cash Flow",
            fmt_money(summary.get("operating_cashflow")),
        )

        st.metric(
            "Free Cash Flow",
            fmt_money(summary.get("free_cash_flow")),
        )

    with c4:
        st.metric(
            "Cash",
            fmt_money(summary.get("cash")),
        )

        st.metric(
            "Debt",
            fmt_money(summary.get("debt")),
        )

    st.subheader("Profitability")

    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric(
            "Gross Margin",
            fmt_percent(summary.get("gross_margin")),
        )

    with p2:
        st.metric(
            "Operating Margin",
            fmt_percent(summary.get("operating_margin")),
        )

    with p3:
        st.metric(
            "Profit Margin",
            fmt_percent(summary.get("profit_margin")),
        )

    with p4:
        st.metric(
            "Return on Equity",
            fmt_percent(summary.get("roe")),
        )

    st.subheader("Balance Sheet")

    b1, b2, b3 = st.columns(3)

    with b1:
        st.metric(
            "Net Debt",
            fmt_money(summary.get("net_debt")),
        )

    with b2:
        st.metric(
            "Debt / Equity",
            fmt_number(summary.get("debt_to_equity")),
        )

    with b3:
        st.metric(
            "Current Ratio",
            fmt_number(summary.get("current_ratio")),
        )


# ============================================================
# VALUATION TAB
# ============================================================

with tabs[2]:

    st.header("Valuation")

    v1, v2, v3, v4 = st.columns(4)

    with v1:
        st.metric(
            "Trailing P/E",
            fmt_number(summary.get("trailing_pe")),
        )

    with v2:
        st.metric(
            "Forward P/E",
            fmt_number(summary.get("forward_pe")),
        )

    with v3:
        st.metric(
            "Price / Sales",
            fmt_number(summary.get("price_to_sales")),
        )

    with v4:
        st.metric(
            "Price / Book",
            fmt_number(summary.get("price_to_book")),
        )

    st.subheader("Bear / Base / Bull Model")

    if valuation is None:

        st.warning(
            "A P/E scenario valuation cannot currently be calculated "
            "because usable positive EPS data is unavailable."
        )

    else:

        bear_pe = st.number_input(
            "Bear Case P/E",
            min_value=1.0,
            value=float(round(valuation["bear_pe"], 1)),
            step=0.5,
        )

        base_pe = st.number_input(
            "Base Case P/E",
            min_value=1.0,
            value=float(round(valuation["base_pe"], 1)),
            step=0.5,
        )

        bull_pe = st.number_input(
            "Bull Case P/E",
            min_value=1.0,
            value=float(round(valuation["bull_pe"], 1)),
            step=0.5,
        )

        eps_used = valuation["eps_used"]

        bear_value = eps_used * bear_pe
        base_value = eps_used * base_pe
        bull_value = eps_used * bull_pe

        vc1, vc2, vc3 = st.columns(3)

        with vc1:
            st.metric(
                "Bear Value",
                fmt_money(bear_value),
            )

        with vc2:
            st.metric(
                "Base Value",
                fmt_money(base_value),
            )

        with vc3:
            st.metric(
                "Bull Value",
                fmt_money(bull_value),
            )

        valuation_table = pd.DataFrame(
            {
                "Scenario": ["Bear", "Base", "Bull"],
                "P/E Multiple": [bear_pe, base_pe, bull_pe],
                "EPS Used": [eps_used, eps_used, eps_used],
                "Implied Value": [
                    bear_value,
                    base_value,
                    bull_value,
                ],
                "Upside / Downside": [
                    (
                        bear_value / current_price - 1
                        if current_price
                        else np.nan
                    ),
                    (
                        base_value / current_price - 1
                        if current_price
                        else np.nan
                    ),
                    (
                        bull_value / current_price - 1
                        if current_price
                        else np.nan
                    ),
                ],
            }
        )

        st.dataframe(
            valuation_table,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "These scenarios are sensitivity analysis, not price targets. "
            "Change the P/E assumptions to test your own valuation."
        )


# ============================================================
# KILL MY THESIS TAB
# ============================================================

with tabs[3]:

    st.header("Kill My Thesis")

    st.write(
        "The purpose of this section is to actively search for evidence "
        "that could prove the investment thesis wrong."
    )

    st.subheader("Your Thesis")

    st.info(thesis)

    st.subheader("Questions the Bear Analyst Must Answer")

    kill_questions = [
        "Is revenue growth slowing or reversing?",
        "Are earnings growing more slowly than revenue?",
        "Are operating margins deteriorating?",
        "Is free cash flow materially weaker than reported earnings?",
        "Is debt increasing faster than the business is growing?",
        "Are returns on capital deteriorating?",
        "Is the valuation assuming too much future growth?",
        "Is management relying heavily on adjusted earnings measures?",
        "Are competitors gaining market share?",
        "Are there regulatory or industry changes that could damage the thesis?",
    ]

    for question in kill_questions:
        st.write(f"• {question}")

    st.subheader("Sector-Specific Thesis Tests")

    for metric in sector_metrics:
        st.write(f"• Is **{metric}** improving, stable, or deteriorating?")

    st.subheader("Current Warning Signals")

    if negatives:
        for negative in negatives:
            st.warning(negative)
    else:
        st.write(
            "The basic Yahoo Finance dataset has not identified a major "
            "warning signal. This does NOT mean the thesis is safe."
        )


# ============================================================
# TECHNICALS TAB
# ============================================================

with tabs[4]:

    st.header("Technical Analysis")

    if history.empty:

        st.warning("Price history is unavailable.")

    else:

        technicals = calculate_technicals(history)

        latest = technicals.iloc[-1]

        t1, t2, t3, t4 = st.columns(4)

        with t1:
            st.metric(
                "Current Price",
                fmt_money(latest.get("Close")),
            )

        with t2:
            st.metric(
                "50-Day MA",
                fmt_money(latest.get("SMA_50")),
            )

        with t3:
            st.metric(
                "200-Day MA",
                fmt_money(latest.get("SMA_200")),
            )

        with t4:
            st.metric(
                "RSI (14)",
                fmt_number(latest.get("RSI_14")),
            )

        chart_data = technicals[
            ["Close", "SMA_50", "SMA_200"]
        ].dropna(how="all")

        st.line_chart(chart_data)

        if len(history) > 0:

            high_52 = safe_number(
                history["High"].tail(252).max()
            )

            low_52 = safe_number(
                history["Low"].tail(252).min()
            )

            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "52-Week High",
                    fmt_money(high_52),
                )

            with c2:
                st.metric(
                    "52-Week Low",
                    fmt_money(low_52),
                )


# ============================================================
# FINANCIAL STATEMENTS TAB
# ============================================================

with tabs[5]:

    st.header("Financial Statements")

    statement_choice = st.selectbox(
        "Statement",
        [
            "Annual Income Statement",
            "Quarterly Income Statement",
            "Annual Balance Sheet",
            "Quarterly Balance Sheet",
            "Annual Cash Flow",
            "Quarterly Cash Flow",
        ],
    )

    statement_map = {
        "Annual Income Statement": data["annual_income"],
        "Quarterly Income Statement": data["quarterly_income"],
        "Annual Balance Sheet": data["annual_balance"],
        "Quarterly Balance Sheet": data["quarterly_balance"],
        "Annual Cash Flow": data["annual_cashflow"],
        "Quarterly Cash Flow": data["quarterly_cashflow"],
    }

    selected_statement = statement_map[statement_choice]

    if selected_statement.empty:
        st.warning("This financial statement is unavailable.")
    else:
        st.dataframe(
            selected_statement,
            use_container_width=True,
        )


# ============================================================
# ANALYST DATA TAB
# ============================================================

with tabs[6]:

    st.header("Analyst Estimates")

    targets = data["analyst_targets"]

    if targets:
        st.subheader("Analyst Price Targets")

        try:
            target_df = pd.DataFrame(
                {
                    "Measure": list(targets.keys()),
                    "Value": list(targets.values()),
                }
            )

            st.dataframe(
                target_df,
                use_container_width=True,
                hide_index=True,
            )
        except Exception:
            st.write(targets)

    st.subheader("Earnings Estimates")

    if not data["earnings_estimate"].empty:
        st.dataframe(
            data["earnings_estimate"],
            use_container_width=True,
        )
    else:
        st.write("Not available.")

    st.subheader("Revenue Estimates")

    if not data["revenue_estimate"].empty:
        st.dataframe(
            data["revenue_estimate"],
            use_container_width=True,
        )
    else:
        st.write("Not available.")

    st.subheader("EPS Trend")

    if not data["eps_trend"].empty:
        st.dataframe(
            data["eps_trend"],
            use_container_width=True,
        )
    else:
        st.write("Not available.")

    st.subheader("EPS Revisions")

    if not data["eps_revisions"].empty:
        st.dataframe(
            data["eps_revisions"],
            use_container_width=True,
        )
    else:
        st.write("Not available.")

    st.subheader("Growth Estimates")

    if not data["growth_estimates"].empty:
        st.dataframe(
            data["growth_estimates"],
            use_container_width=True,
        )
    else:
        st.write("Not available.")


# ============================================================
# NEWS TAB
# ============================================================

with tabs[7]:

    st.header("Company News")

    news = data["news"]

    if not news:

        st.write("No recent news was returned.")

    else:

        for article in news[:15]:

            content = article.get("content", article)

            title = (
                content.get("title")
                or article.get("title")
                or "Untitled article"
            )

            provider = content.get("provider", {})

            provider_name = (
                provider.get("displayName")
                if isinstance(provider, dict)
                else None
            )

            st.subheader(title)

            if provider_name:
                st.caption(provider_name)

            summary_text = content.get("summary")

            if summary_text:
                st.write(summary_text)

            canonical = content.get("canonicalUrl", {})

            url = None

            if isinstance(canonical, dict):
                url = canonical.get("url")

            if not url:
                click_through = content.get("clickThroughUrl", {})

                if isinstance(click_through, dict):
                    url = click_through.get("url")

            if url:
                st.link_button(
                    "Read article",
                    url,
                )

            st.markdown("---")


# ============================================================
# AI RESEARCH TAB
# ============================================================

with tabs[8]:

    st.header("AI Investment Committee")

    st.write(
        "This layer uses AI to challenge the thesis and synthesize "
        "the available financial evidence."
    )

    api_key = get_openai_key()

    if not api_key:

        st.warning(
            "OpenAI API key not detected. The rest of the application "
            "will continue working normally."
        )

        st.write(
            "When you are ready, add an OPENAI_API_KEY to your "
            "Streamlit secrets. Do NOT put the API key directly "
            "inside app.py or upload it to GitHub."
        )

    else:

        st.success("AI engine connected.")

        if analyse_button:

            evidence_pack = create_evidence_pack(
                ticker_name=ticker_name,
                company_name=company_name,
                sector=sector,
                industry=industry,
                current_price=current_price,
                summary=summary,
                valuation=valuation,
                thesis=thesis,
                sector_metrics=sector_metrics,
            )

            with st.spinner(
                "The Investment Committee is analysing the evidence..."
            ):

                ai_report, ai_error = run_ai_committee(
                    api_key=api_key,
                    evidence_pack=evidence_pack,
                    company_name=company_name,
                    ticker_name=ticker_name,
                )

            if ai_error:

                st.error(
                    f"AI analysis failed: {ai_error}"
                )

            elif ai_report:

                st.markdown(ai_report)

        else:

            st.info(
                "Enter your thesis and click "
                "'Run Investment Analysis' in the sidebar."
            )


# ============================================================
# DATA LIMITATIONS
# ============================================================

st.markdown("---")

with st.expander("Data Sources & Important Limitations"):

    st.write(
        """
This application currently uses Yahoo Finance through yfinance
for market and financial data.

Not every ASX company exposes the same data fields. Some metrics
may therefore display N/A.

Company-specific operating KPIs such as transaction volume,
credit losses, AISC, ARR, churn, CET1, WALE and other specialised
metrics generally require company reports, investor presentations
and ASX announcements.

The Bear/Base/Bull model is a sensitivity model and should not be
treated as a forecast.

AI-generated analysis can make mistakes and must be checked
against primary company documents.

This application is a research tool and does not provide personal
financial advice.
"""
    )
