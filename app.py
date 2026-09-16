import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.header(f"{ticker} — INVESTMENT COMMITTEE REPORT")

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="ASX AI Investment Analyst V2",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def money(x):
    if x is None or pd.isna(x):
        return "—"

    x = float(x)

    if abs(x) >= 1_000_000_000:
        return f"A${x / 1_000_000_000:.2f}B"

    if abs(x) >= 1_000_000:
        return f"A${x / 1_000_000:.2f}M"

    if abs(x) >= 1_000:
        return f"A${x / 1_000:.2f}K"

    return f"A${x:,.2f}"


def percentage(x):
    if x is None or pd.isna(x):
        return "—"

    return f"{float(x) * 100:.1f}%"


def number(x):
    if x is None or pd.isna(x):
        return "—"

    return f"{float(x):,.2f}"


def safe_df(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.copy()

    return pd.DataFrame()


def latest_value(df, labels):

    if df.empty:
        return None

    for label in labels:

        if label in df.index:

            series = pd.to_numeric(
                df.loc[label],
                errors="coerce"
            ).dropna()

            if len(series):
                return float(series.iloc[0])

    return None


# ============================================================
# DATA ENGINE
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def load_company(symbol):

    ticker = yf.Ticker(symbol)

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    try:
        history = ticker.history(
            period="5y",
            auto_adjust=False
        )
    except Exception:
        history = pd.DataFrame()

    try:
        annual_income = safe_df(ticker.income_stmt)
    except Exception:
        annual_income = pd.DataFrame()

    try:
        annual_balance = safe_df(ticker.balance_sheet)
    except Exception:
        annual_balance = pd.DataFrame()

    try:
        annual_cashflow = safe_df(ticker.cashflow)
    except Exception:
        annual_cashflow = pd.DataFrame()

    try:
        quarterly_income = safe_df(
            ticker.quarterly_income_stmt
        )
    except Exception:
        quarterly_income = pd.DataFrame()

    try:
        quarterly_balance = safe_df(
            ticker.quarterly_balance_sheet
        )
    except Exception:
        quarterly_balance = pd.DataFrame()

    try:
        quarterly_cashflow = safe_df(
            ticker.quarterly_cashflow
        )
    except Exception:
        quarterly_cashflow = pd.DataFrame()

    try:
        news = ticker.get_news(count=20)
    except Exception:
        news = []

    def get_attr(name):

        try:
            return getattr(ticker, name)
        except Exception:
            return None

    return {
        "info": info,
        "history": history,
        "income": annual_income,
        "balance": annual_balance,
        "cashflow": annual_cashflow,
        "quarterly_income": quarterly_income,
        "quarterly_balance": quarterly_balance,
        "quarterly_cashflow": quarterly_cashflow,
        "news": news,
        "targets": get_attr("analyst_price_targets"),
        "recommendations": get_attr("recommendations"),
        "earnings_estimate": get_attr("earnings_estimate"),
        "revenue_estimate": get_attr("revenue_estimate"),
        "earnings_history": get_attr("earnings_history"),
        "eps_trend": get_attr("eps_trend"),
        "eps_revisions": get_attr("eps_revisions"),
        "growth_estimates": get_attr("growth_estimates"),
    }


# ============================================================
# HEADER
# ============================================================

st.title("📈 ASX AI Investment Analyst")

st.caption(
    "Universal ASX stock research platform • "
    "fundamentals • valuation • technicals • risk • thesis testing"
)

ticker_input = st.text_input(
    "Enter any ASX ticker",
    value="ZIP",
    placeholder="ZIP, CBA, BHP, CSL, XRO, WES..."
)

ticker_code = (
    ticker_input
    .strip()
    .upper()
    .replace(".AX", "")
)

if not ticker_code:
    st.stop()

symbol = ticker_code + ".AX"

with st.spinner(
    f"Collecting data for {ticker_code}..."
):

    try:
        data = load_company(symbol)

    except Exception as error:

        st.error(
            f"Unable to retrieve data: {error}"
        )

        st.stop()


info = data["info"]
history = data["history"]

if history.empty:

    st.error(
        "No market data was returned. "
        "Check that the ticker is correct."
    )

    st.stop()


# ============================================================
# COMPANY INFORMATION
# ============================================================

company_name = (
    info.get("longName")
    or info.get("shortName")
    or ticker_code
)

sector = info.get("sector") or "Unknown"

industry = (
    info.get("industry")
    or "Unknown"
)

price = float(
    history["Close"]
    .dropna()
    .iloc[-1]
)

high_52 = float(
    history["High"]
    .tail(252)
    .max()
)

low_52 = float(
    history["Low"]
    .tail(252)
    .min()
)


# ============================================================
# SNAPSHOT
# ============================================================

st.subheader(company_name)

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric(
    "Current Price",
    f"A${price:.2f}"
)

c2.metric(
    "52W High",
    f"A${high_52:.2f}"
)

c3.metric(
    "52W Low",
    f"A${low_52:.2f}"
)

c4.metric(
    "Market Cap",
    money(info.get("marketCap"))
)

c5.metric(
    "Sector",
    sector
)

c6.metric(
    "Industry",
    industry
)


# ============================================================
# TABS
# ============================================================

tabs = st.tabs(
    [
        "Overview",
        "Financials",
        "Balance Sheet",
        "Cash Flow",
        "Valuation",
        "Estimates",
        "Technicals",
        "News",
        "Sector Lens",
        "Kill My Thesis",
        "AI Committee"
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

with tabs[0]:

    st.subheader("Company snapshot")

    a, b, c = st.columns(3)

    with a:

        st.metric(
            "Revenue",
            money(info.get("totalRevenue"))
        )

        st.metric(
            "Gross Margin",
            percentage(info.get("grossMargins"))
        )

        st.metric(
            "Operating Margin",
            percentage(info.get("operatingMargins"))
        )

    with b:

        st.metric(
            "Trailing P/E",
            number(info.get("trailingPE"))
        )

        st.metric(
            "Forward P/E",
            number(info.get("forwardPE"))
        )

        st.metric(
            "PEG",
            number(info.get("pegRatio"))
        )

    with c:

        st.metric(
            "ROE",
            percentage(info.get("returnOnEquity"))
        )

        st.metric(
            "ROA",
            percentage(info.get("returnOnAssets"))
        )

        st.metric(
            "Beta",
            number(info.get("beta"))
        )

    st.subheader("5-year share-price history")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            name="Share price"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"].rolling(50).mean(),
            name="50-day SMA"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"].rolling(200).mean(),
            name="200-day SMA"
        )
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Price"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "The application deliberately displays missing information "
        "as unavailable rather than inventing numbers."
    )


# ============================================================
# FINANCIALS
# ============================================================

with tabs[1]:

    st.subheader(
        "Annual income statement"
    )

    if data["income"].empty:

        st.warning(
            "Annual income statement unavailable."
        )

    else:

        st.dataframe(
            data["income"],
            use_container_width=True
        )

    st.subheader(
        "Quarterly income statement"
    )

    if data["quarterly_income"].empty:

        st.warning(
            "Quarterly income statement unavailable."
        )

    else:

        st.dataframe(
            data["quarterly_income"],
            use_container_width=True
        )


# ============================================================
# BALANCE SHEET
# ============================================================

with tabs[2]:

    st.subheader(
        "Annual balance sheet"
    )

    if data["balance"].empty:

        st.warning(
            "Balance sheet unavailable."
        )

    else:

        st.dataframe(
            data["balance"],
            use_container_width=True
        )

    cash_balance = latest_value(
        data["balance"],
        [
            "Cash Cash Equivalents And Short Term Investments",
            "Cash And Cash Equivalents",
            "Cash"
        ]
    )

    total_debt = latest_value(
        data["balance"],
        [
            "Total Debt",
            "TotalDebt"
        ]
    )

    equity = latest_value(
        data["balance"],
        [
            "Stockholders Equity",
            "Common Stock Equity",
            "Total Equity Gross Minority Interest"
        ]
    )

    assets = latest_value(
        data["balance"],
        [
            "Total Assets"
        ]
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "Cash",
        money(cash_balance)
    )

    b.metric(
        "Debt",
        money(total_debt)
    )

    c.metric(
        "Equity",
        money(equity)
    )

    d.metric(
        "Assets",
        money(assets)
    )

    st.subheader(
        "Quarterly balance sheet"
    )

    st.dataframe(
        data["quarterly_balance"],
        use_container_width=True
    )


# ============================================================
# CASH FLOW
# ============================================================

with tabs[3]:

    st.subheader(
        "Annual cash flow"
    )

    st.dataframe(
        data["cashflow"],
        use_container_width=True
    )

    operating_cashflow = latest_value(
        data["cashflow"],
        [
            "Operating Cash Flow",
            "Total Cash From Operating Activities"
        ]
    )

    capex = latest_value(
        data["cashflow"],
        [
            "Capital Expenditure",
            "Capital Expenditures"
        ]
    )

    free_cashflow = latest_value(
        data["cashflow"],
        [
            "Free Cash Flow"
        ]
    )

    if (
        free_cashflow is None
        and operating_cashflow is not None
        and capex is not None
    ):

        if capex < 0:

            free_cashflow = (
                operating_cashflow + capex
            )

        else:

            free_cashflow = (
                operating_cashflow - capex
            )

    a, b, c = st.columns(3)

    a.metric(
        "Operating Cash Flow",
        money(operating_cashflow)
    )

    b.metric(
        "Capital Expenditure",
        money(capex)
    )

    c.metric(
        "Estimated Free Cash Flow",
        money(free_cashflow)
    )

    st.subheader(
        "Quarterly cash flow"
    )

    st.dataframe(
        data["quarterly_cashflow"],
        use_container_width=True
    )


# ============================================================
# VALUATION
# ============================================================

with tabs[4]:

    st.subheader(
        "Market valuation"
    )

    valuation_rows = [

        [
            "Trailing P/E",
            info.get("trailingPE")
        ],

        [
            "Forward P/E",
            info.get("forwardPE")
        ],

        [
            "PEG",
            info.get("pegRatio")
        ],

        [
            "Price / Book",
            info.get("priceToBook")
        ],

        [
            "Price / Sales",
            info.get(
                "priceToSalesTrailing12Months"
            )
        ],

        [
            "EV / EBITDA",
            info.get("enterpriseToEbitda")
        ],

        [
            "EV / Revenue",
            info.get("enterpriseToRevenue")
        ],

        [
            "Dividend Yield",
            info.get("dividendYield")
        ]
    ]

    valuation_df = pd.DataFrame(
        valuation_rows,
        columns=["Metric", "Value"]
    )

    st.dataframe(
        valuation_df,
        hide_index=True,
        use_container_width=True
    )

    st.subheader(
        "Bear / Base / Bull valuation model"
    )

    eps = (
        info.get("forwardEps")
        or info.get("trailingEps")
    )

    if eps and eps > 0:

        a, b, c = st.columns(3)

        bear_multiple = a.number_input(
            "Bear P/E",
            min_value=1.0,
            max_value=100.0,
            value=12.0,
            step=0.5
        )

        base_multiple = b.number_input(
            "Base P/E",
            min_value=1.0,
            max_value=100.0,
            value=20.0,
            step=0.5
        )

        bull_multiple = c.number_input(
            "Bull P/E",
            min_value=1.0,
            max_value=100.0,
            value=28.0,
            step=0.5
        )

        scenarios = pd.DataFrame(
            {
                "Scenario": [
                    "Bear",
                    "Base",
                    "Bull"
                ],

                "P/E": [
                    bear_multiple,
                    base_multiple,
                    bull_multiple
                ],

                "EPS": [
                    eps,
                    eps,
                    eps
                ]
            }
        )

        scenarios["Implied Price"] = (
            scenarios["P/E"]
            * scenarios["EPS"]
        )

        scenarios["Upside / Downside"] = (
            scenarios["Implied Price"]
            / price
            - 1
        )

        st.dataframe(
            scenarios.style.format(
                {
                    "EPS": "A${:.2f}",
                    "Implied Price": "A${:.2f}",
                    "Upside / Downside": "{:.1%}"
                }
            ),
            hide_index=True,
            use_container_width=True
        )

    else:

        st.warning(
            "EPS unavailable. P/E valuation cannot be calculated."
        )

    if data["targets"]:

        st.subheader(
            "Analyst price targets"
        )

        st.json(
            data["targets"]
        )


# ============================================================
# ESTIMATES
# ============================================================

with tabs[5]:

    estimate_objects = [

        (
            "Earnings Estimates",
            data["earnings_estimate"]
        ),

        (
            "Revenue Estimates",
            data["revenue_estimate"]
        ),

        (
            "Earnings History",
            data["earnings_history"]
        ),

        (
            "EPS Trend",
            data["eps_trend"]
        ),

        (
            "EPS Revisions",
            data["eps_revisions"]
        ),

        (
            "Growth Estimates",
            data["growth_estimates"]
        )
    ]

    for title, obj in estimate_objects:

        st.subheader(title)

        if isinstance(obj, pd.DataFrame):

            st.dataframe(
                obj,
                use_container_width=True
            )

        elif obj:

            st.write(obj)

        else:

            st.info(
                "Not available for this company."
            )


# ============================================================
# TECHNICALS
# ============================================================

with tabs[6]:

    close = (
        history["Close"]
        .dropna()
    )

    sma20 = (
        close
        .rolling(20)
        .mean()
        .iloc[-1]
    )

    sma50 = (
        close
        .rolling(50)
        .mean()
        .iloc[-1]
    )

    sma200 = (
        close
        .rolling(200)
        .mean()
        .iloc[-1]
    )

    delta = close.diff()

    gain = (
        delta
        .clip(lower=0)
        .rolling(14)
        .mean()
    )

    loss = (
        -delta
        .clip(upper=0)
        .rolling(14)
        .mean()
    )

    rs = (
        gain
        / loss.replace(0, np.nan)
    )

    rsi = (
        100
        - 100 / (1 + rs)
    ).iloc[-1]

    a, b, c, d = st.columns(4)

    a.metric(
        "RSI(14)",
        f"{rsi:.1f}"
    )

    b.metric(
        "20D SMA",
        f"A${sma20:.2f}"
    )

    c.metric(
        "50D SMA",
        f"A${sma50:.2f}"
    )

    d.metric(
        "200D SMA",
        f"A${sma200:.2f}"
    )

    if price > sma50 > sma200:

        trend = "Bullish"

    elif price < sma50 < sma200:

        trend = "Bearish"

    else:

        trend = "Mixed"

    st.markdown(
        f"### Technical trend: **{trend}**"
    )

    st.line_chart(close)


# ============================================================
# NEWS
# ============================================================

with tabs[7]:

    st.subheader(
        "Recent company news"
    )

    news = data["news"]

    if not news:

        st.info(
            "No company news was returned."
        )

    for article in news:

        if not isinstance(article, dict):
            continue

        content = article.get(
            "content",
            article
        )

        title = content.get(
            "title",
            "Untitled"
        )

        provider = content.get(
            "provider",
            {}
        )

        if isinstance(provider, dict):

            publisher = provider.get(
                "displayName",
                ""
            )

        else:

            publisher = ""

        canonical = content.get(
            "canonicalUrl",
            {}
        )

        if isinstance(canonical, dict):

            url = canonical.get(
                "url"
            )

        else:

            url = None

        st.markdown(
            f"**{title}**"
        )

        if publisher:

            st.caption(
                publisher
            )

        if url:

            st.markdown(
                f"[Read article]({url})"
            )

        st.divider()


# ============================================================
# SECTOR LENS
# ============================================================

with tabs[8]:

    st.subheader(
        "Sector-specific KPI framework"
    )

    sector_text = (
        sector + " " + industry
    ).lower()

    if (
        "bank" in sector_text
        or "financial" in sector_text
    ):

        kpis = [
            "Net interest margin (NIM)",
            "CET1 capital",
            "Bad debts / impairments",
            "Loan growth",
            "Deposit growth",
            "ROE",
            "Cost-to-income"
        ]

    elif (
        "mining" in sector_text
        or "metals" in sector_text
        or "basic materials" in sector_text
    ):

        kpis = [
            "Commodity prices",
            "Production volumes",
            "AISC / unit costs",
            "Reserves",
            "Mine life",
            "Capital expenditure",
            "Free cash flow",
            "Net debt"
        ]

    elif (
        "technology" in sector_text
        or "software" in sector_text
    ):

        kpis = [
            "ARR / recurring revenue",
            "Revenue growth",
            "Gross margin",
            "Customer growth",
            "Retention / churn",
            "R&D",
            "Free cash flow",
            "Operating leverage"
        ]

    elif (
        "real estate" in sector_text
        or "reit" in sector_text
    ):

        kpis = [
            "FFO / AFFO",
            "Occupancy",
            "WALE",
            "Gearing",
            "NAV / NTA",
            "Interest coverage"
        ]

    elif (
        "health" in sector_text
        or "biotech" in sector_text
    ):

        kpis = [
            "Revenue",
            "Cash runway",
            "R&D",
            "Pipeline",
            "Regulatory milestones",
            "Dilution"
        ]

    elif (
        "retail" in sector_text
        or "consumer" in sector_text
    ):

        kpis = [
            "Like-for-like sales",
            "Gross margin",
            "Inventory",
            "Store growth",
            "Digital sales",
            "Cash conversion"
        ]

    else:

        kpis = [
            "Revenue growth",
            "EBITDA margin",
            "Operating margin",
            "Cash conversion",
            "ROIC / ROE",
            "Debt",
            "Competitive advantage"
        ]

    for kpi in kpis:

        st.checkbox(
            kpi,
            value=True,
            key="kpi_" + kpi
        )

    st.info(
        "The sector lens identifies the metrics that should be "
        "investigated for this type of company. The next stage is "
        "connecting these KPIs to company announcements and reports."
    )


# ============================================================
# KILL MY THESIS
# ============================================================

with tabs[9]:

    st.subheader(
        "🔨 Kill My Thesis"
    )

    thesis = st.text_area(
        "Enter your investment thesis",
        value=(
            f"{company_name}: earnings and cash generation "
            "continue improving while valuation remains reasonable."
        ),
        height=130
    )

    st.write(
        "The purpose of this module is to search for evidence "
        "that could invalidate the thesis rather than simply "
        "confirming it."
    )

    questions = [

        "Is revenue growth slowing?",

        "Are gross or operating margins deteriorating?",

        "Are reported profits converting into cash?",

        "Is debt increasing faster than earnings?",

        "Is valuation dependent on unrealistic growth?",

        "Are competitors gaining market share?",

        "Are management targets being missed?",

        "Are credit losses, impairments or bad debts rising?",

        "Is dilution becoming a material risk?",

        "What event would permanently invalidate the thesis?"
    ]

    for question in questions:

        st.checkbox(
            question,
            value=True,
            key="kill_" + question
        )

    st.text_area(
        "Paste bearish evidence here",
        placeholder=(
            "Paste an ASX announcement, annual report excerpt, "
            "news article or your own concern here."
        ),
        height=180
    )


# ============================================================
# AI INVESTMENT COMMITTEE
# ============================================================

with tabs[10]:

    st.subheader(
        "🤖 Investment Committee"
    )

    st.write(
        "The production AI committee is designed around six "
        "independent analysts:"
    )

    analysts = [
        "Fundamental Analyst",
        "Valuation Analyst",
        "Bull Analyst",
        "Bear / Kill My Thesis Analyst",
        "Risk Analyst",
        "Technical Analyst"
    ]

    for analyst in analysts:

        st.checkbox(
            analyst,
            value=True,
            key="analyst_" + analyst
        )

    revenue_series = None

    if (
        not data["income"].empty
        and "Total Revenue" in data["income"].index
    ):

        revenue_series = (
            pd.to_numeric(
                data["income"].loc["Total Revenue"],
                errors="coerce"
            )
            .dropna()
        )

    revenue_growth = np.nan

    if (
        revenue_series is not None
        and len(revenue_series) >= 2
        and revenue_series.iloc[1] != 0
    ):

        revenue_growth = (
            revenue_series.iloc[0]
            / revenue_series.iloc[1]
            - 1
        )

    score = 5.0

    reasons = []

    if pd.notna(revenue_growth):

        if revenue_growth > 0.15:

            score += 1

            reasons.append(
                "Recent annual revenue growth is strong."
            )

        elif revenue_growth < 0:

            score -= 1

            reasons.append(
                "Revenue contraction is a warning."
            )

    operating_margin = (
        info.get("operatingMargins")
    )

    if operating_margin is not None:

        if operating_margin > 0.15:

            score += 0.75

            reasons.append(
                "Operating margin is strong."
            )

        elif operating_margin < 0:

            score -= 0.75

            reasons.append(
                "Operating losses increase execution risk."
            )

    roe = info.get(
        "returnOnEquity"
    )

    if (
        roe is not None
        and roe > 0.15
    ):

        score += 0.5

        reasons.append(
            "ROE is healthy."
        )

    forward_pe = info.get(
        "forwardPE"
    )

    if (
        forward_pe is not None
        and forward_pe > 35
    ):

        score -= 0.5

        reasons.append(
            "Forward valuation is demanding."
        )

    score = max(
        0,
        min(10, score)
    )

    st.metric(
        "Preliminary research score",
        f"{score:.1f}/10"
    )

    st.subheader(
        "Committee observations"
    )

    if reasons:

        for reason in reasons:

            st.write(
                "• " + reason
            )

    else:

        st.write(
            "Not enough data for the preliminary screen."
        )

    st.subheader(
        "Questions the full AI committee should answer"
    )

    committee_questions = [

        "What is the strongest bull argument?",

        "What is the strongest bear argument?",

        "What evidence would falsify the thesis?",

        "Is earnings quality supported by cash flow?",

        "Is the balance sheet strong enough for the sector?",

        "What assumptions are embedded in today's valuation?",

        "What catalysts could change market expectations?",

        "What risks could permanently impair the investment case?",

        "What would cause the investment thesis to be abandoned?"
    ]

    for question in committee_questions:

        st.checkbox(
            question,
            value=True,
            key="committee_" + question
        )

    st.warning(
        "The score above is a transparent screening heuristic, "
        "not a personalised recommendation. A true AI committee "
        "requires an AI API plus authoritative company filings, "
        "ASX announcements and news."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "ASX AI Investment Analyst V2 • "
    f"Data refresh: {datetime.now().strftime('%Y-%m-%d %H:%M')} • "
    "Research and educational tool only."
)
