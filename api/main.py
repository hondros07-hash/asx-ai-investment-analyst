"""AXÍA Phase 2 API: independent of Streamlit; existing UI remains untouched.

Run: uvicorn api.main:app --host 127.0.0.1 --port 8000
No API keys, CORS wildcard, or public production deployment are configured.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import lru_cache
from math import isfinite
from threading import Lock
from time import monotonic
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
import yfinance as yf

from services.fundamentals_core import load_uncached
from services.independent_financial_kpi_engines import run_independently
from services.valuation_engine import calculate_dcf_scenarios, provider_inputs
from services.forecast_engine import build_12m_forecast

app = FastAPI(title="AXÍA Research API", version="24.3.0",
              description="Provider-transcribed research data, not audited issuer filings.")
_POOL = ThreadPoolExecutor(max_workers=6)
_CACHE = {}
_CACHE_LOCK = Lock()
_TTL = 3600


def _safe(value):
    """Normalize provider values to JSON-safe primitives."""
    import numpy as np
    import pandas as pd
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _ticker(value: str) -> str:
    value = value.strip().upper()
    if not value or len(value) > 24 or not all(c.isalnum() or c in ".^=-_" for c in value):
        raise HTTPException(422, "Invalid ticker")
    return value


def _provider(fn):
    future = _POOL.submit(fn)
    try:
        return future.result(timeout=20)
    except TimeoutError:
        future.cancel()
        raise HTTPException(504, "Provider request timed out")
    except Exception:
        raise HTTPException(503, "Provider temporarily unavailable")


def _snapshot(ticker: str, period: str):
    key = (ticker, period)
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry and monotonic() - entry[0] < _TTL:
            return entry[1]
    result = _provider(lambda: load_uncached(ticker, period))
    if not isinstance(result, dict) or not result:
        raise HTTPException(503, "Financial data unavailable")
    with _CACHE_LOCK:
        if len(_CACHE) >= 96:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[key] = (monotonic(), result)
    return result


Period = Literal["Annual (5Y)", "Quarterly (8Q)", "TTM"]


class ValuationRequest(BaseModel):
    fcf: float
    shares: float = Field(gt=0)
    cash: float = 0
    debt: float = 0
    current_price: float | None = Field(default=None, gt=0)
    sector: str = Field(default="", max_length=120)
    industry: str = Field(default="", max_length=120)
    financial_currency: str | None = Field(default=None, max_length=8)
    listing_currency: str | None = Field(default=None, max_length=8)
    fx_rate_financial_to_listing: float | None = Field(default=None, gt=0)

    @field_validator("fcf", "shares", "cash", "debt", "current_price", "fx_rate_financial_to_listing")
    @classmethod
    def finite(cls, value):
        if value is not None and not isfinite(value):
            raise ValueError("Value must be finite")
        return value


class ForecastRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=24)
    current_price: float | None = Field(default=None, gt=0)

    @field_validator("current_price")
    @classmethod
    def finite(cls, value):
        if value is not None and not isfinite(value):
            raise ValueError("Value must be finite")
        return value


@app.get("/health")
def health():
    return {"status": "ok", "service": "axia-research-api", "version": app.version}


@app.get("/v1/companies/search")
def company_search(q: str = Query(min_length=1, max_length=80), limit: int = Query(10, ge=1, le=20)):
    term = q.strip()
    if not term:
        raise HTTPException(422, "Search query required")
    def search():
        result = yf.Search(term, max_results=limit, news_count=0)
        return [{"symbol": row.get("symbol"), "name": row.get("shortname") or row.get("longname"),
                 "exchange": row.get("exchange"), "quote_type": row.get("quoteType")}
                for row in (result.quotes or [])[:limit] if row.get("symbol")]
    return {"query": term, "results": _provider(search), "source": "Yahoo Finance search"}


@app.get("/v1/companies/{ticker}/financial-statements")
def financial_statements(ticker: str, period: Period = "Annual (5Y)"):
    ticker = _ticker(ticker)
    data = _snapshot(ticker, period)
    return {"ticker": ticker, "period": period, "data": _safe(data),
            "provenance": {"source": data.get("provider"), "checked_at": data.get("provider_checked_at"),
                           "cache_ttl_seconds": _TTL, "issuer_reconciled": False}}


@app.get("/v1/companies/{ticker}/kpis")
def independent_kpis(ticker: str, period: Period = "Annual (5Y)"):
    ticker = _ticker(ticker)
    data = _snapshot(ticker, period)
    return {"ticker": ticker, "period": period, "currency": data.get("currency"),
            "metrics": _safe(run_independently(data, data.get("currency"))),
            "source": data.get("provider"), "checked_at": data.get("provider_checked_at")}


@app.post("/v1/valuations/dcf")
def valuation(request: ValuationRequest):
    return calculate_dcf_scenarios(**request.model_dump())


@app.get("/v1/companies/{ticker}/valuation")
def company_valuation(ticker: str):
    ticker = _ticker(ticker)
    data = _snapshot(ticker, "Annual (5Y)")
    inputs = provider_inputs(data.get("meta") or {})
    result = calculate_dcf_scenarios(**inputs)
    return {"ticker": ticker, "valuation": _safe(result), "source": data.get("provider"),
            "checked_at": data.get("provider_checked_at")}


@app.post("/v1/forecasts/12m")
def forecast(request: ForecastRequest):
    ticker = _ticker(request.ticker)
    def compute():
        history = yf.Ticker(ticker).history(period="5y", interval="1d", auto_adjust=True)
        return build_12m_forecast(history, current_price=request.current_price, security=ticker)
    return {"ticker": ticker, "forecast": _safe(_provider(compute)),
            "source": "Yahoo Finance price history", "model": "AXÍA existing 12-month forecast engine"}


@app.get("/v1/companies/{ticker}/forecast")
def company_forecast(ticker: str):
    return forecast(ForecastRequest(ticker=_ticker(ticker)))

# V24.1: isolated read-only Company Command Centre research endpoints.
from api.research_routes import router as research_router
app.include_router(research_router)

from api.workspace_routes import router as workspace_router
app.include_router(workspace_router)

# Deployment health routes never depend on third-party market providers.
from api.health import router as health_router
app.include_router(health_router)

# V24.7 research memory: off by default; authenticated and owner-scoped.
from api.research_memory_routes import router as research_memory_router
app.include_router(research_memory_router)
