"""V23.4.5: server-side, privacy-conscious trial eligibility.

A device signal is optional and never alone proves identity. A trusted payment identity
may be added later by a verified Stripe webhook, not a browser-provided field.
"""
from __future__ import annotations
import hashlib, hmac, os, re
from datetime import datetime, timezone
from typing import Optional

DISPOSABLE_DOMAINS=frozenset({'mailinator.com','10minutemail.com','guerrillamail.com','tempmail.com','yopmail.com','trashmail.com','getnada.com','sharklasers.com'})
class EligibilityError(ValueError): pass

def email_domain(email:str)->str:
    address=email.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',address): raise EligibilityError('Enter a valid email address')
    return address.rsplit('@',1)[1]

def validate_registration_email(email:str)->None:
    if email_domain(email) in DISPOSABLE_DOMAINS: raise EligibilityError('Please use a permanent email address')

def keyed_digest(value:str, purpose:str)->str:
    secret=os.getenv('CHRIMATA_TRIAL_HMAC_SECRET','')
    if len(secret)<32: raise RuntimeError('Trial eligibility secret is not configured')
    return hmac.new(secret.encode(),(purpose+':'+value).encode(),hashlib.sha256).hexdigest()

def normalize_device_signal(value:Optional[str])->Optional[str]:
    if not value:return None
    if not re.fullmatch(r'[a-fA-F0-9]{64}',value):raise EligibilityError('Invalid device signal')
    return keyed_digest(value.lower(),'device')

def register_attempt(client,email:str,device_signal:Optional[str]=None)->dict:
    """Persist a pending registration signal. Never grant a trial in this operation."""
    validate_registration_email(email)
    email_key=keyed_digest(email.strip().lower(),'email')
    device_key=normalize_device_signal(device_signal)
    record={'email_key':email_key,'device_key':device_key,'status':'pending'}
    result=client.table('trial_registration_attempts').insert(record).execute()
    data=getattr(result,'data',None) or []
    if not data:raise RuntimeError('Registration eligibility record was not stored')
    return data[0]

def decision_from_signals(prior_trial:bool,device_seen:bool=False)->str:
    # A shared device is only a review signal; a verified prior identity is decisive.
    return 'ineligible' if prior_trial else ('review' if device_seen else 'eligible')
