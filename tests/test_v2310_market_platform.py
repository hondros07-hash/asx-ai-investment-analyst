import asyncio
from services.market_registry import MARKETS, DEFAULT_GLOBAL_MARKETS
from services.geo_router import resolve_market_layout
from services.market_broadcast import MarketBroadcastCache

def test_registry_has_existing_six_and_greece():
    assert {"AU","US","GB","JP","HK","CA","GR"} <= set(MARKETS)
def test_greek_geo_default():
    x=resolve_market_layout("GR",{"subscription_tier":"free"})
    assert x["home_market"]=="GR" and len(x["secondary_markets"])==5 and "GR" not in x["secondary_markets"]
def test_saved_preference_beats_geo():
    x=resolve_market_layout("GR",{"subscription_tier":"pro","home_market":"AU","custom_market_slots":["GR","US","JP","HK","CA"]})
    assert x["home_market"]=="AU" and x["secondary_markets"][0]=="GR" and x["geo_source"]=="saved_preference"
def test_invalid_geo_neutral_fallback():
    assert resolve_market_layout("ZZ",{})["home_market"]=="US"
def test_cache_one_refresh_many_readers():
    calls={"n":0}
    async def fetch(code):
        calls["n"]+=1; return {"index":{"symbol":"TEST","price":123.4},"source":"test"}
    async def run():
        c=MarketBroadcastCache()
        await c.refresh("AU",fetch,60)
        assert c.get("AU").payload["index"]["price"]==123.4
        assert c.get("AU").payload["index"]["price"]==123.4
    asyncio.run(run())
    assert calls["n"]==1
def test_stale_last_good_on_provider_failure():
    async def good(code): return {"value":1}
    async def bad(code): raise RuntimeError("provider down")
    async def run():
        c=MarketBroadcastCache(); await c.refresh("US",good,60); r=await c.refresh("US",bad,60)
        assert r.stale and r.payload["value"]==1 and "provider down" in r.error
    asyncio.run(run())
