"""Chrímata V23.3.0 centralized trial + feature entitlement engine."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional

PLANS=("free","general","premium")
PLAN_RANK={"free":0,"general":1,"premium":2}

FEATURE_REQUIREMENTS={
    "market.home":"free",
    "market.global":"general",
    "research.basic":"free",
    "research.scorecard":"general",
    "research.valuation":"general",
    "research.forecast":"general",
    "research.ai_brief":"premium",
    "news.preview":"free",
    "news.full":"general",
    "news.macro_intelligence":"premium",
    "portfolio.basic":"free",
    "portfolio.advanced":"premium",
    "alerts.basic":"general",
    "alerts.advanced":"premium",
}

def _utc(value: Any) -> Optional[datetime]:
    if not value: return None
    if isinstance(value,datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def evaluate_entitlement(row: Dict[str,Any], now: Optional[datetime]=None)->Dict[str,Any]:
    now=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    trial_start=_utc(row.get("trial_started_at"))
    trial_end=_utc(row.get("trial_ends_at"))
    trial_active=bool(trial_start and trial_end and trial_start <= now < trial_end)
    plan=str(row.get("plan") or "free").lower()
    if plan not in PLANS: plan="free"
    status=str(row.get("status") or "active").lower()
    paid_active=status in {"active","trialing"} or plan=="free"
    effective_plan="premium" if trial_active else (plan if paid_active else "free")
    days_remaining=max(0,(trial_end-now).days + (1 if trial_active and (trial_end-now).seconds else 0)) if trial_end else 0
    return {**row,"plan":plan,"effective_plan":effective_plan,"trial_active":trial_active,
            "trial_ends_at":trial_end.isoformat() if trial_end else None,
            "trial_days_remaining":days_remaining}

def feature_access(feature: str, entitlement: Dict[str,Any])->Dict[str,Any]:
    required=FEATURE_REQUIREMENTS.get(feature,"premium")
    effective=entitlement.get("effective_plan","free")
    allowed=PLAN_RANK.get(effective,0) >= PLAN_RANK[required]
    return {"status":"ok" if allowed else "gate_locked","feature":feature,"allowed":allowed,
            "effective_plan":effective,"required_tier":None if allowed else required,
            "trial_active":bool(entitlement.get("trial_active"))}
