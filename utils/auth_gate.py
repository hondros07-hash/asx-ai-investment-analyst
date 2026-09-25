"""FastAPI authentication/identity dependency.

Bearer JWT is verified with Supabase Auth. Internal exceptions are never returned to clients.
"""
from __future__ import annotations
import logging
from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.supabase_client import get_supabase_admin_client
log=logging.getLogger(__name__)
security=HTTPBearer(auto_error=False)

def _claims_dict(response: Any) -> Dict[str,Any]:
    if isinstance(response,dict): return response.get("claims",response)
    claims=getattr(response,"claims",None)
    return claims if isinstance(claims,dict) else {}

async def get_current_active_user(credentials: HTTPAuthorizationCredentials=Depends(security))->Dict[str,Any]:
    if credentials is None or credentials.scheme.lower()!="bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Authentication required",
                            headers={"WWW-Authenticate":"Bearer"})
    try:
        client=get_supabase_admin_client()
        # Supabase recommends verified claims/JWKS over a network get_user call where supported.
        response=client.auth.get_claims(credentials.credentials)
        claims=_claims_dict(response)
        uid=claims.get("sub")
        if not uid: raise ValueError("verified token missing subject")
        return {"id":uid,"email":claims.get("email")}
    except HTTPException: raise
    except Exception:
        log.exception("Supabase token validation failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired session",
                            headers={"WWW-Authenticate":"Bearer"})
