"""Bounded, deterministic evidence explanation endpoint; no provider requests."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.explainable_evidence_engine import observation, explain_calculation

router = APIRouter(prefix="/v1/explainability", tags=["explainability"])

class EvidenceIn(BaseModel):
    security_id: str = Field(min_length=1, max_length=40)
    metric: str = Field(min_length=1, max_length=100)
    value: str | float | int | None
    unit: str = Field(min_length=1, max_length=16)
    period: str = Field(min_length=1, max_length=60)
    source_name: str = Field(min_length=1, max_length=120)
    source_url: str = Field(min_length=1, max_length=1024)
    observed_at: str = Field(min_length=1, max_length=64)
    verification: str
    issuer_reconciled: bool = False

class ExplainIn(BaseModel):
    metric: str = Field(min_length=1, max_length=100)
    operator: str
    inputs: list[EvidenceIn] = Field(min_length=2, max_length=2)
    unit: str = Field(min_length=1, max_length=16)
    period: str = Field(min_length=1, max_length=60)
    assumptions: dict = Field(default_factory=dict)

@router.post("/calculate")
def calculate(body: ExplainIn):
    try:
        return explain_calculation(body.metric, body.operator, [x.model_dump() for x in body.inputs],
                                   unit=body.unit, period=body.period, assumptions=body.assumptions)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
