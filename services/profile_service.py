"""Server-side profile and entitlement access. Service role remains backend-only."""
from __future__ import annotations
from typing import Any, Dict
from config.supabase_client import get_supabase_admin_client

FREE_ENTITLEMENTS={"custom_market_slots":False,"advanced_research":False,"ai_research_brief":False}
PRO_ENTITLEMENTS={"custom_market_slots":True,"advanced_research":True,"ai_research_brief":True}

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
    r=c.table("entitlements").select("plan,status,valid_until").eq("user_id",user_id).limit(1).execute()
    row=_one(getattr(r,"data",None)) or {"plan":"free","status":"active","valid_until":None}
    # Only active Pro is treated as Pro. Billing/webhook logic can later maintain this server-controlled row.
    plan="pro" if row.get("plan")=="pro" and row.get("status")=="active" else "free"
    return {**row,"effective_plan":plan,"features":PRO_ENTITLEMENTS if plan=="pro" else FREE_ENTITLEMENTS}

def get_user_state(user:Dict[str,Any])->Dict[str,Any]:
    return {"user":user,"profile":get_profile(user["id"]),"entitlement":get_entitlement(user["id"])}
