import ast
from pathlib import Path
import pytest
from services.trial_eligibility import validate_registration_email, EligibilityError, decision_from_signals,normalize_device_signal,keyed_digest

def test_disposable_blocked():
 with pytest.raises(EligibilityError):validate_registration_email('x@mailinator.com')
def test_permanent_accepted():validate_registration_email('person@example.org')
def test_shared_device_not_automatic_denial():assert decision_from_signals(False,True)=='review'
def test_prior_verified_identity_denied():assert decision_from_signals(True,False)=='ineligible'
def test_signal_is_keyed(monkeypatch):
 monkeypatch.setenv('CHRIMATA_TRIAL_HMAC_SECRET','a'*40)
 assert keyed_digest('x','email')!=keyed_digest('x','device')
 assert len(normalize_device_signal('f'*64))==64
def test_bad_device_signal():
 with pytest.raises(EligibilityError):normalize_device_signal('raw-device-id')
def test_no_automatic_trial_grant_on_confirmation():
 sql=Path('supabase/migrations/20260925_v23_4_5_trial_eligibility.sql').read_text()
 assert "trial_started_at=now(),trial_ends_at=now()+interval '30 days'" in sql
 assert "if v_decision='eligible' then" in sql
 assert "auth.role() <> 'service_role'" in sql
 assert 'enable row level security' in sql
def test_api_parses_and_route():
 s=Path('api_gateway.py').read_text();ast.parse(s)
 assert '/api/v1/me/activate-trial' in s
 assert 'register_attempt(get_supabase_admin_client()' in Path('services/account_auth.py').read_text()
