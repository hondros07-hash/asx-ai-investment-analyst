"""Centralized market broadcast/cache layer.

One upstream refresh can serve every connected client. Provider retrieval is injected so
this module never fabricates values and remains independent of yfinance or a licensed feed.
"""
from __future__ import annotations
import asyncio, time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional
from services.market_registry import MARKETS

Fetcher = Callable[[str], Awaitable[Dict[str, Any]]]

@dataclass
class CacheRecord:
    payload: Dict[str, Any]
    fetched_at: float
    expires_at: float
    stale: bool = False
    error: Optional[str] = None

class MarketBroadcastCache:
    def __init__(self):
        self._cache: Dict[str, CacheRecord] = {}
        self._locks={code: asyncio.Lock() for code in MARKETS}

    def get(self, code: str) -> Optional[CacheRecord]:
        return self._cache.get(code.upper())

    async def refresh(self, code: str, fetcher: Fetcher, ttl_seconds: int = 60) -> CacheRecord:
        code=code.upper()
        if code not in MARKETS: raise KeyError(f"Unsupported market: {code}")
        async with self._locks[code]:
            now=time.time()
            try:
                data=await fetcher(code)
                if not isinstance(data,dict): raise TypeError("provider payload must be a dict")
                rec=CacheRecord(data,now,now+max(1,int(ttl_seconds)),False,None)
                self._cache[code]=rec
                return rec
            except Exception as exc:
                prior=self._cache.get(code)
                if prior:
                    prior.stale=True; prior.error=str(exc)
                    return prior
                raise

    async def refresh_many(self, codes, fetcher: Fetcher, ttl_resolver=None):
        async def one(code):
            ttl=ttl_resolver(code) if ttl_resolver else 60
            return code, await self.refresh(code,fetcher,ttl)
        results=await asyncio.gather(*(one(c) for c in codes),return_exceptions=True)
        return results

broadcast_cache=MarketBroadcastCache()

def serialize_record(code: str, rec: CacheRecord):
    return {
        "market":code,
        "data":rec.payload,
        "freshness":{"fetched_at_epoch":rec.fetched_at,"expires_at_epoch":rec.expires_at,
                     "stale":rec.stale,"error":rec.error},
    }
