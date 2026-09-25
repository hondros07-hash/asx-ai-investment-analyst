from pathlib import Path
def test_router_files():
 for p in ["frontend/components/DashboardRouter.js","frontend/lib/api.js","frontend/app/page.js","frontend/package.json"]: assert Path(p).exists()
def test_parallel_prefetch_and_cache():
 s=Path("frontend/lib/api.js").read_text()
 assert "Promise.allSettled" in s and "cache=new Map()" in s and "inflight=new Map()" in s
 for x in ["scorecard","valuation","technicals","consensus","forecast"]: assert x in s
def test_client_state_navigation():
 s=Path("frontend/components/DashboardRouter.js").read_text()
 assert '"use client"' in s and "useState" in s and "useTransition" in s
 assert "history.replaceState" in s and "window.location" not in s
 assert "warmTicker" in s
def test_context_preserved():
 s=Path("frontend/components/DashboardRouter.js").read_text()
 assert 'useState("CBA.AX")' in s and "setTicker(next)" in s
