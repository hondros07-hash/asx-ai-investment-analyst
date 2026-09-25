from pathlib import Path
from datetime import datetime,timezone,timedelta
from services.entitlement_engine import evaluate_entitlement,feature_access

NOW=datetime(2026,9,25,tzinfo=timezone.utc)

def test_active_trial_is_full_premium_access():
 e=evaluate_entitlement({"plan":"free","status":"active","trial_started_at":NOW-timedelta(days=1),"trial_ends_at":NOW+timedelta(days=29)},NOW)
 assert e["trial_active"] and e["effective_plan"]=="premium"
 assert feature_access("research.ai_brief",e)["allowed"]

def test_expired_trial_returns_to_free():
 e=evaluate_entitlement({"plan":"free","status":"active","trial_started_at":NOW-timedelta(days=31),"trial_ends_at":NOW-timedelta(days=1)},NOW)
 assert not e["trial_active"] and e["effective_plan"]=="free"
 x=feature_access("research.valuation",e)
 assert x["status"]=="gate_locked" and x["required_tier"]=="general"

def test_general_and_premium_gates():
 g=evaluate_entitlement({"plan":"general","status":"active"},NOW)
 p=evaluate_entitlement({"plan":"premium","status":"active"},NOW)
 assert feature_access("market.global",g)["allowed"]
 assert not feature_access("research.ai_brief",g)["allowed"]
 assert feature_access("research.ai_brief",p)["allowed"]

def test_migration_starts_trial_after_verification():
 s=Path("supabase/migrations/20260925_v23_3_0_trial_tiers.sql").read_text()
 assert "after update of email_confirmed_at on auth.users" in s
 assert "now()+interval '30 days'" in s
 assert "plan in ('free','general','premium')" in s
 assert "grant" not in s.lower()  # migration never broadens client entitlement permissions

def test_registration_ui_is_functional_not_disabled():
 s=Path("app.py").read_text()
 assert "_chr_register_user_v2330(_email,_password)" in s
 assert "disabled=True" not in s[s.index('if page in {"Sign In","Register"}:'):s.index('elif page=="Markets":')]
 assert "30 days of full Chrímata access" in s

def test_api_has_trial_and_gate_routes():
 s=Path("api_gateway.py").read_text()
 assert '@app.post("/api/v1/auth/register")' in s
 assert '@app.get("/api/v1/me/trial")' in s
 assert '@app.get("/api/v1/me/access/{feature_key:path}")' in s

def test_no_service_role_in_user_auth():
 s=Path("services/account_auth.py").read_text()
 assert "SUPABASE_SERVICE_ROLE_KEY" not in s
 assert "SUPABASE_ANON_KEY" in s
