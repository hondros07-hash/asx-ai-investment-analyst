
from __future__ import annotations
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

RANGES = {
    "1D": ("1d", "5m"),
    "3D": ("5d", "15m"),
    "5D": ("5d", "15m"),
    "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"),
    "6M": ("6mo", "1d"),
    "YTD": ("ytd", "1d"),
    "1Y": ("1y", "1d"),
    "3Y": ("3y", "1d"),
    "5Y": ("5y", "1d"),
    "MAX": ("max", "1wk"),
}

def _download(ticker, period, interval):
    try:
        d = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        return d.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()

def range_data(ticker: str, selected: str) -> pd.DataFrame:
    period, interval = RANGES[selected]
    d = _download(ticker, period, interval)
    if d.empty:
        return d
    if selected == "3D":
        # Keep the latest three distinct trading dates, preserving intraday observations.
        dates = pd.Index(d.index.date).unique()
        if len(dates) > 3:
            d = d[pd.Index(d.index.date).isin(dates[-3:])]
    return d

def summary(d: pd.DataFrame):
    if d.empty:
        return {}
    first = float(d["Close"].iloc[0]); last = float(d["Close"].iloc[-1])
    return {
        "start": first, "last": last, "change": last-first,
        "change_pct": (last/first-1) if first else np.nan,
        "high": float(d["High"].max()) if "High" in d else float(d["Close"].max()),
        "low": float(d["Low"].min()) if "Low" in d else float(d["Close"].min()),
        "volume": float(d["Volume"].sum()) if "Volume" in d else np.nan,
    }

def previous_close(ticker: str):
    d = _download(ticker, "5d", "1d")
    if len(d) < 2: return None
    return float(d["Close"].iloc[-2])

def comparison_series(primary: pd.DataFrame, compare_ticker: str):
    if primary.empty or not compare_ticker:
        return pd.DataFrame()
    # Fetch enough daily history to cover the primary range. For intraday, align by nearest
    # timestamps after downloading the same nominal period is handled by caller.
    return pd.DataFrame()

def price_figure(d: pd.DataFrame, ticker: str, mode="Price", show_volume=True,
                 show_sma20=False, show_sma50=False, show_sma200=False,
                 compare_df=None, compare_label=None):
    fig = go.Figure()
    if d.empty:
        return fig
    if mode == "Percentage":
        base = float(d["Close"].iloc[0])
        y = (d["Close"]/base - 1)*100
        fig.add_trace(go.Scatter(x=d.index, y=y, mode="lines", name=ticker,
                                 hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>"))
        if compare_df is not None and not compare_df.empty:
            s = compare_df["Close"].reindex(d.index, method="nearest")
            s = s.dropna()
            if not s.empty:
                y2=(s/float(s.iloc[0])-1)*100
                fig.add_trace(go.Scatter(x=y2.index,y=y2,mode="lines",
                                         name=compare_label or "Comparison",
                                         hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>"))
        ytitle="Return (%)"
    else:
        fig.add_trace(go.Scatter(x=d.index,y=d["Close"],mode="lines",name=ticker,
                                 hovertemplate="%{x}<br>$%{y:.3f}<extra></extra>"))
        for n,show in [(20,show_sma20),(50,show_sma50),(200,show_sma200)]:
            if show and len(d)>=n:
                fig.add_trace(go.Scatter(x=d.index,y=d["Close"].rolling(n).mean(),
                                         mode="lines",name=f"SMA {n}"))
        ytitle="Price"
    fig.update_layout(height=480,margin=dict(l=10,r=10,t=20,b=10),
                      xaxis_title=None,yaxis_title=ytitle,hovermode="x unified",
                      legend=dict(orientation="h"))
    fig.update_xaxes(rangeslider_visible=False)
    return fig
