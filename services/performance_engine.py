"""AXÍA V23.7.7 — bounded, observable data loading primitives.

Opt-in module: existing pages and valuation logic remain unchanged until their
individual data providers are migrated and benchmarked.
"""
from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import wraps
from threading import Lock
from time import monotonic, perf_counter
from typing import Callable, Hashable
import logging

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CachePolicy:
    ttl_seconds: float
    max_entries: int = 256

    def __post_init__(self):
        if self.ttl_seconds <= 0 or self.max_entries < 1:
            raise ValueError("TTL and cache capacity must be positive")


# Explicit data classes: never cache intraday quotes for the lifetime of filings.
POLICIES = {
    "quote": CachePolicy(30, 512),
    "history": CachePolicy(300, 256),
    "fundamentals": CachePolicy(3600, 256),
    "filings": CachePolicy(900, 256),
    "identity": CachePolicy(86400, 1024),
}


class BoundedTTLCache:
    """Thread-safe bounded cache; monotonic expiry and no caching failures."""
    def __init__(self, policy: CachePolicy):
        self.policy = policy
        self._items: OrderedDict[Hashable, tuple[float, object]] = OrderedDict()
        self._lock = Lock()
        self.hits = self.misses = 0

    def get_or_load(self, key: Hashable, loader: Callable[[], object]):
        now = monotonic()
        with self._lock:
            record = self._items.get(key)
            if record is not None:
                expires, value = record
                if expires > now:
                    self._items.move_to_end(key)
                    self.hits += 1
                    return value
                del self._items[key]
            self.misses += 1
        value = loader()  # Never hold the global lock across provider I/O.
        if value is None or (hasattr(value, "empty") and value.empty):
            return value
        with self._lock:
            self._items[key] = (monotonic() + self.policy.ttl_seconds, value)
            self._items.move_to_end(key)
            while len(self._items) > self.policy.max_entries:
                self._items.popitem(last=False)
        return value

    def clear(self):
        with self._lock:
            self._items.clear()

    def stats(self):
        with self._lock:
            return {"entries": len(self._items), "hits": self.hits,
                    "misses": self.misses, "capacity": self.policy.max_entries}


class PerformanceMonitor:
    """Aggregate timings without recording tickers, credentials or user data."""
    def __init__(self):
        self._lock = Lock()
        self._stats = {}

    def measure(self, label: str):
        def decorator(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                start = perf_counter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    duration = perf_counter() - start
                    with self._lock:
                        n, total, peak = self._stats.get(label, (0, 0.0, 0.0))
                        self._stats[label] = (n + 1, total + duration, max(peak, duration))
                    if duration >= 2:
                        log.warning("AXIA slow operation %s: %.2fs", label, duration)
            return wrapped
        return decorator

    def snapshot(self):
        with self._lock:
            return {name: {"calls": n, "mean_ms": round(1000 * total / n, 1),
                           "max_ms": round(1000 * peak, 1)}
                    for name, (n, total, peak) in self._stats.items()}


monitor = PerformanceMonitor()
caches = {name: BoundedTTLCache(policy) for name, policy in POLICIES.items()}


def cached_load(kind: str, key: Hashable, loader: Callable[[], object]):
    """Provider opt-in; key must include exchange, symbol, currency and parameters."""
    if kind not in caches:
        raise ValueError(f"Unknown cache class: {kind}")
    return caches[kind].get_or_load(key, monitor.measure(f"provider.{kind}")(loader))


def resource_snapshot():
    """Safe operational counters; no account, ticker or portfolio identifiers."""
    return {"cache": {name: cache.stats() for name, cache in caches.items()},
            "timings": monitor.snapshot()}
