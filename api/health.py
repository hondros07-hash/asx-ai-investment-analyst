"""Dependency-free liveness/readiness endpoints: no market-provider calls."""
from fastapi import APIRouter
router = APIRouter()
@router.get("/health/live", include_in_schema=False)
def live():
    return {"status": "ok", "service": "axia-api"}
@router.get("/health/ready", include_in_schema=False)
def ready():
    return {"status": "ready", "service": "axia-api"}
