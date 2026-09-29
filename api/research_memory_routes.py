"""Feature-gated authenticated research memory. No service-role key or anonymous access."""
from __future__ import annotations
import os
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from services.research_memory_engine import compare_snapshots, evaluate_condition

router = APIRouter(prefix="/v1/research-memory", tags=["research-memory"])

def enabled():
    if os.getenv("AXIA_RESEARCH_MEMORY_ENABLED", "").lower() != "true":
        raise HTTPException(404, "Research memory is not enabled")

def session(authorization: str | None = Header(default=None)):
    enabled()
    if not authorization or not authorization.startswith("Bearer ") or not authorization[7:].strip():
        raise HTTPException(401, "Valid bearer token required")
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()
    if not url or not key:
        raise HTTPException(503, "Authenticated storage is not configured")
    from supabase import create_client
    client = create_client(url, key)
    token = authorization[7:].strip()
    try:
        user = client.auth.get_user(token).user
        if not user or not user.id:
            raise ValueError("Unverified user")
        client.postgrest.auth(token)
    except Exception:
        raise HTTPException(401, "Session could not be verified")
    return client, str(user.id)

class SnapshotIn(BaseModel):
    security_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9.^=_-]+$")
    listing_currency: str | None = Field(default=None, max_length=8)
    observed_at: str
    metrics: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)

class ConditionIn(BaseModel):
    security_id: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9.^=_-]+$")
    label: str = Field(min_length=1, max_length=200)
    metric: str = Field(min_length=1, max_length=100)
    operator: str = Field(pattern=r"^(>=|<=|==|>|<)$")
    threshold: float
    period: str = Field(min_length=1, max_length=60)
    currency: str | None = Field(default=None, max_length=8)

def rows(query):
    try:
        return query.execute().data or []
    except Exception:
        raise HTTPException(503, "Research storage unavailable")

@router.get("/snapshots")
def snapshots(security_id: str = Query(min_length=1,max_length=40), ctx=Depends(session)):
    client, uid = ctx
    return {"snapshots": rows(client.table("axia_research_snapshots").select("*").eq("user_id",uid).eq("security_id",security_id).order("recorded_at",desc=True).limit(50))}

@router.post("/snapshots", status_code=201)
def save_snapshot(body: SnapshotIn, ctx=Depends(session)):
    client, uid = ctx
    record = {**body.model_dump(), "user_id": uid}
    result = rows(client.table("axia_research_snapshots").insert(record))
    return {"snapshot": result[0] if result else None}

@router.get("/changes")
def changes(security_id: str = Query(min_length=1,max_length=40), ctx=Depends(session)):
    client, uid = ctx
    history = rows(client.table("axia_research_snapshots").select("*").eq("user_id",uid).eq("security_id",security_id).order("recorded_at",desc=True).limit(2))
    if len(history)<2:
        return {"status":"insufficient_history","changes":[],"message":"Two dated snapshots are required."}
    before, after = history[1], history[0]
    return {"status":"available", **compare_snapshots({"id":before["id"],"security_id":before["security_id"],"currency":before["listing_currency"],"metrics":before["metrics"]},{"id":after["id"],"security_id":after["security_id"],"currency":after["listing_currency"],"metrics":after["metrics"]})}

@router.get("/conditions")
def conditions(security_id: str = Query(min_length=1,max_length=40), ctx=Depends(session)):
    client, uid = ctx
    return {"conditions": rows(client.table("axia_thesis_conditions").select("*").eq("user_id",uid).eq("security_id",security_id).is_("archived_at","null").order("created_at",desc=True).limit(100))}

@router.post("/conditions", status_code=201)
def save_condition(body: ConditionIn, ctx=Depends(session)):
    client, uid = ctx
    result = rows(client.table("axia_thesis_conditions").insert({**body.model_dump(),"user_id":uid}))
    return {"condition":result[0] if result else None}

@router.post("/conditions/{condition_id}/evaluate")
def evaluate_saved_condition(condition_id: UUID, evidence: dict, ctx=Depends(session)):
    client, uid = ctx
    matching = rows(client.table("axia_thesis_conditions").select("*").eq("id",str(condition_id)).eq("user_id",uid).is_("archived_at","null").limit(1))
    if not matching:
        raise HTTPException(404,"Condition not found")
    result = evaluate_condition(matching[0], evidence)
    # Evaluation is read-only until ingestion provenance and observation RLS are end-to-end tested.
    return {"condition_id":str(condition_id),**result,"persisted":False}
