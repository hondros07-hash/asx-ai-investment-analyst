"""Server-only Supabase configuration for Chrímata."""
from __future__ import annotations
import os
from functools import lru_cache

class SupabaseConfigurationError(RuntimeError): pass

@lru_cache(maxsize=1)
def get_supabase_admin_client():
    """Create the trusted backend client lazily. Never expose its secret to a browser."""
    url=os.getenv("SUPABASE_URL","").strip()
    key=os.getenv("SUPABASE_SERVICE_ROLE_KEY","").strip()
    if not url or not key:
        raise SupabaseConfigurationError("Supabase server configuration is unavailable")
    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseConfigurationError("Supabase Python package is not installed") from exc
    return create_client(url,key)

def supabase_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL","").strip() and os.getenv("SUPABASE_SERVICE_ROLE_KEY","").strip())
