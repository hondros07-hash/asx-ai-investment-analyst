"""User-facing Supabase Auth operations.

Uses the publishable/anon key, never the service-role key. Email confirmation behavior
is controlled by the Supabase project's Auth settings.
"""
from __future__ import annotations
import os
from typing import Any, Dict

class AccountAuthError(RuntimeError): pass

def _client():
    url=os.getenv("SUPABASE_URL","").strip()
    key=(os.getenv("SUPABASE_ANON_KEY","") or os.getenv("SUPABASE_PUBLISHABLE_KEY","")).strip()
    if not url or not key: raise AccountAuthError("Account authentication is not configured")
    from supabase import create_client
    return create_client(url,key)

def register_user(email:str,password:str,device_signal:str|None=None)->Dict[str,Any]:
    from services.trial_eligibility import register_attempt
    from config.supabase_client import get_supabase_admin_client
    register_attempt(get_supabase_admin_client(),email,device_signal)
    r=_client().auth.sign_up({"email":email.strip(),"password":password})
    user=getattr(r,"user",None); session=getattr(r,"session",None)
    return {"user_id":str(getattr(user,"id","") or ""), "email":getattr(user,"email",email),
            "email_confirmation_required":session is None,
            "access_token":getattr(session,"access_token",None) if session else None}

def sign_in_user(email:str,password:str)->Dict[str,Any]:
    r=_client().auth.sign_in_with_password({"email":email.strip(),"password":password})
    user=getattr(r,"user",None); session=getattr(r,"session",None)
    if not user or not session: raise AccountAuthError("Sign in was not completed")
    return {"user_id":str(user.id),"email":getattr(user,"email",email),
            "access_token":session.access_token,"refresh_token":getattr(session,"refresh_token",None)}


def activate_verified_trial(user_id:str,email:str)->str:
    """Backend-only idempotent activation; SQL verifies email confirmation and eligibility."""
    from config.supabase_client import get_supabase_admin_client
    from services.trial_eligibility import keyed_digest
    admin=get_supabase_admin_client()
    key=keyed_digest(email.strip().lower(),'email')
    existing=admin.table('trial_eligibility').select('decision').eq('user_id',user_id).limit(1).execute()
    if getattr(existing,'data',None):return existing.data[0]['decision']
    r=admin.table('trial_registration_attempts').select('device_key').eq('email_key',key).eq('status','pending').order('created_at',desc=True).limit(1).execute()
    pending=getattr(r,'data',None) or []
    if not pending:raise AccountAuthError('Trial eligibility record unavailable')
    result=admin.rpc('finalize_chrimata_trial',{'p_user_id':user_id,'p_email_key':key,'p_device_key':pending[0].get('device_key')}).execute()
    return result.data
