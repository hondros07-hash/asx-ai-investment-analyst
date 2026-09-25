"""Server-side profile and entitlement access. Service role remains backend-only."""
from __future__ import annotations
from typing import Any, Dict
from config.supabase_client import get_supabase_admin_client
from services.entitlement_engine import evaluate_entitlement, feature_access

def _one(data):
    if isinstance(data,dict): return data
    if isinstance(data,list) and data: return data[0]
    return None

def get_profile(user_id:str)->Dict[str,Any]:
    c=get_supabase_admin_client()
    r=c.table("profiles").select("id,email,home_market_override,custom_market_slots,updated_at").eq("id",user_id).limit(1).execute()
    return _one(getattr(r,"data",None)) or {"id":user_id,"home_market_override":None,"custom_market_slots":[]}

def get_entitlement(user_id:str)->Dict[str,Any]:
    c=get_supabase_admin_client()
    fields="plan,status,valid_until,trial_started_at,trial_ends_at,billing_interval,provider_customer_ref,updated_at"
    r=c.table("entitlements").select(fields).eq("user_id",user_id).limit(1).execute()
    row=_one(getattr(r,"data",None)) or {"plan":"free","status":"active"}
    return evaluate_entitlement(row)

def get_user_state(user:Dict[str,Any])->Dict[str,Any]:
    return {"user":user,"profile":get_profile(user["id"]),"entitlement":get_entitlement(user["id"])}

def check_user_feature(user_id:str,feature:str)->Dict[str,Any]:
    return feature_access(feature,get_entitlement(user_id))
