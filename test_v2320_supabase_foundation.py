from pathlib import Path
from services.geo_router import resolve_market_layout
from services.entitlement_engine import FEATURE_REQUIREMENTS

def test_sql_rls_and_server_controlled_entitlements():
 s=Path("supabase/migrations/20260925_v23_2_0_identity.sql").read_text()
 assert "alter table public.profiles enable row level security" in s
 assert "alter table public.entitlements enable row level security" in s
 assert "grant select on table public.entitlements to authenticated" in s
 assert "grant select, update on table public.entitlements to authenticated" not in s
 assert "set search_path = ''" in s
def test_no_secret_in_repo():
 for p in [Path(".env.example"),Path("config/supabase_client.py")]:
  s=p.read_text()
  assert "eyJ" not in s and "service_role=" not in s.lower()
def test_auth_returns_generic_client_error():
 s=Path("utils/auth_gate.py").read_text()
 assert 'detail="Invalid or expired session"' in s
 assert "detail=str(" not in s
def test_feature_entitlements():
 assert FEATURE_REQUIREMENTS["market.global"]=="general"
 assert FEATURE_REQUIREMENTS["research.ai_brief"]=="premium"
def test_saved_home_and_pro_slots_feed_existing_geo_engine():
 x=resolve_market_layout(None,{"subscription_tier":"pro","home_market":"GR","custom_market_slots":["US","GB","JP","HK","CA"]})
 assert x["home_market"]=="GR" and x["secondary_markets"]==["US","GB","JP","HK","CA"]
def test_api_has_authenticated_me_routes():
 s=Path("api_gateway.py").read_text()
 assert '@app.get("/api/v1/me")' in s
 assert '@app.get("/api/v1/me/market-layout")' in s
 assert "Depends(get_current_active_user)" in s
