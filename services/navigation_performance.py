"""AXÍA V23.7.23 — short-lived, per-session navigation snapshot.

The existing Streamlit data caches remain authoritative across sessions. This
layer avoids repeated cache deserialisation and repeated profile/history work
while moving between research subpages for the same listing. It never caches
failures and does not alter intraday/live quote freshness policies.
"""
from __future__ import annotations
from time import monotonic

SNAPSHOT_TTL_SECONDS = 45
STATE_KEY = "_axia_navigation_snapshot_v23723"
TIMING_KEY = "_axia_navigation_timing_v23723"

def company_navigation_snapshot(ticker, history_loader, info_loader, state):
    symbol = str(ticker or "").strip().upper()
    started = monotonic()
    snapshot = state.get(STATE_KEY)
    if (snapshot and snapshot.get("ticker") == symbol
            and started - snapshot.get("loaded_at", 0) < SNAPSHOT_TTL_SECONDS
            and snapshot.get("history") is not None
            and not snapshot["history"].empty):
        state[TIMING_KEY] = {"ticker": symbol, "cache": "session",
                             "elapsed_ms": round((monotonic() - started) * 1000, 2)}
        return snapshot["history"], snapshot["profile"]

    # Keep loaders on the Streamlit script thread: Streamlit cache decorators
    # and session state should not be invoked from unmanaged worker threads.
    bars = history_loader(symbol)
    profile = info_loader(symbol)
    if bars is not None and not bars.empty:
        state[STATE_KEY] = {"ticker": symbol, "loaded_at": monotonic(),
                            "history": bars, "profile": profile or {}}
    else:
        state.pop(STATE_KEY, None)
    state[TIMING_KEY] = {"ticker": symbol, "cache": "provider_or_streamlit",
                         "elapsed_ms": round((monotonic() - started) * 1000, 2)}
    return bars, profile or {}
