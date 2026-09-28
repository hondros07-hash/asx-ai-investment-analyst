"""AXÍA V23.12 — safe per-session navigation cache.

Provider and Streamlit caches remain authoritative. This cache is short-lived,
ticker-and-parameter scoped, and never stores failed/empty provider responses.
"""
from __future__ import annotations
from time import monotonic

SNAPSHOT_TTL_SECONDS = 45
STATE_KEY = "_axia_navigation_snapshot_v23723"
TIMING_KEY = "_axia_navigation_timing_v23723"


def _valid_bars(bars):
    return bars is not None and not getattr(bars, "empty", True)


def company_navigation_snapshot(ticker, history_loader, info_loader, state,
                                *, period="5y", refresh=False, clock=monotonic):
    symbol = str(ticker or "").strip().upper()
    if not symbol:
        raise ValueError("Ticker is required")
    started = clock()
    snapshot = state.get(STATE_KEY)
    key = (symbol, str(period))
    if (not refresh and snapshot and snapshot.get("key") == key
            and 0 <= started - snapshot.get("loaded_at", 0) < SNAPSHOT_TTL_SECONDS
            and _valid_bars(snapshot.get("history"))):
        state[TIMING_KEY] = {"cache": "session", "elapsed_ms": round((clock()-started)*1000, 2),
                             "period": str(period)}
        # Copies prevent mutations on one page leaking into another.
        bars = snapshot["history"]
        return bars.copy(deep=True), dict(snapshot["profile"])

    # Never carry a prior company's snapshot through a failed provider call.
    state.pop(STATE_KEY, None)
    bars = history_loader(symbol) if period == "5y" else history_loader(symbol, period)
    profile = info_loader(symbol) if _valid_bars(bars) else {}
    profile = profile if isinstance(profile, dict) else {}
    if _valid_bars(bars):
        state[STATE_KEY] = {"key": key, "loaded_at": clock(),
                            "history": bars.copy(deep=True), "profile": dict(profile)}
    state[TIMING_KEY] = {"cache": "provider_or_streamlit",
                         "elapsed_ms": round((clock()-started)*1000, 2), "period": str(period)}
    return bars, dict(profile)
