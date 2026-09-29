"""Owner-scoped append-only journal endpoints; reuse verified V24.7 bearer session."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from api.research_memory_routes import session, rows

router = APIRouter(prefix="/v1/research-journal", tags=["research-journal"])
KINDS = {"thesis","note","decision","review"}

class EntryIn(BaseModel):
    security_id: str = Field(min_length=1,max_length=40,pattern=r"^[A-Za-z0-9.^=_-]+$")
    entry_type: str
    title: str = Field(min_length=1,max_length=200)
    body: str = Field(min_length=1,max_length=10000)
    evidence_refs: list[str] = Field(default_factory=list,max_length=20)
    revision_of: UUID | None = None

@router.get("/entries")
def list_entries(security_id: str = Query(min_length=1,max_length=40), ctx=Depends(session)):
    db, uid = ctx
    return {"entries":rows(db.table("axia_research_journal").select("*").eq("user_id",uid)
        .eq("security_id",security_id).is_("archived_at","null").order("recorded_at",desc=True).limit(100))}

@router.post("/entries",status_code=201)
def add_entry(body: EntryIn,ctx=Depends(session)):
    db,uid=ctx
    if body.entry_type not in KINDS:
        raise HTTPException(422,"Unsupported entry type")
    if body.revision_of is not None:
        prior=rows(db.table("axia_research_journal").select("id").eq("user_id",uid)
            .eq("security_id",body.security_id).eq("id",str(body.revision_of)).limit(1))
        if not prior: raise HTTPException(404,"Previous entry not found")
    payload=body.model_dump(mode="json")
    payload["user_id"]=uid
    result=rows(db.table("axia_research_journal").insert(payload))
    return {"entry":result[0] if result else None}

@router.get("/timeline")
def timeline(security_id: str = Query(min_length=1,max_length=40),ctx=Depends(session)):
    db,uid=ctx
    notes=rows(db.table("axia_research_journal").select("id,security_id,entry_type,title,recorded_at,revision_of")
        .eq("user_id",uid).eq("security_id",security_id).order("recorded_at",desc=True).limit(100))
    snapshots=rows(db.table("axia_research_snapshots").select("id,security_id,observed_at,recorded_at")
        .eq("user_id",uid).eq("security_id",security_id).order("recorded_at",desc=True).limit(100))
    events=[{"kind":"journal",**n} for n in notes]+[{"kind":"snapshot",**s} for s in snapshots]
    return {"security_id":security_id,"events":sorted(events,key=lambda x:x["recorded_at"],reverse=True)[:100]}
