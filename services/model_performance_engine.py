"""Point-in-time forecast ledger and deterministic outcome evaluation.

No market data is fetched. Historical records are never rewritten by this module.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json

def number(value):
    if isinstance(value,bool): raise ValueError("Boolean is not a price")
    try: result=Decimal(str(value))
    except (InvalidOperation,TypeError): raise ValueError("Invalid numeric value")
    if not result.is_finite(): raise ValueError("Non-finite value")
    return result

def instant(value):
    try: result=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (AttributeError,ValueError): raise ValueError("ISO timestamp required")
    if result.tzinfo is None: raise ValueError("Timezone required")
    return result.astimezone(timezone.utc)

def freeze_forecast(row):
    required=("security_id","model_id","model_version","issued_at","target_at","currency","horizon","predicted_price","reference_price","assumptions_digest","source_digest")
    if any(not row.get(k) and row.get(k)!=0 for k in required): raise ValueError("Incomplete forecast")
    issued,target=instant(row["issued_at"]),instant(row["target_at"])
    if issued>=target or issued>datetime.now(timezone.utc): raise ValueError("Invalid forecast chronology")
    if number(row["reference_price"])<=0 or number(row["predicted_price"])<=0: raise ValueError("Prices must be positive")
    for field in ("security_id","model_id","model_version","currency","horizon","assumptions_digest","source_digest"):
        if not isinstance(row[field],str) or not row[field].strip(): raise ValueError("Invalid "+field)
    if len(row["currency"])!=3 or not row["currency"].isalpha(): raise ValueError("Invalid currency")
    frozen={k:row[k] for k in required}
    frozen["issued_at"]=issued.isoformat();frozen["target_at"]=target.isoformat()
    frozen["predicted_price"]=str(number(row["predicted_price"]))
    frozen["reference_price"]=str(number(row["reference_price"]))
    frozen["currency"]=row["currency"].upper()
    digest=sha256(json.dumps(frozen,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {**frozen,"forecast_id":digest,"status":"pending"}

def evaluate(forecast,outcome,*,as_of):
    as_of=instant(as_of);target=instant(forecast["target_at"])
    if as_of<target:return {"status":"pending","reason":"Forecast horizon has not elapsed"}
    if outcome is None:return {"status":"unavailable","reason":"No verified outcome"}
    if outcome.get("security_id")!=forecast["security_id"] or outcome.get("currency")!=forecast["currency"]:
        return {"status":"not_comparable","reason":"Security or currency mismatch"}
    observed=instant(outcome["observed_at"])
    if observed<target or observed>as_of:return {"status":"not_comparable","reason":"Outcome outside eligible observation window"}
    if not outcome.get("source_url","").startswith("https://") or not outcome.get("verified",False):
        return {"status":"unavailable","reason":"Verified outcome source required"}
    actual=number(outcome["price"]);predicted=number(forecast["predicted_price"])
    if actual<=0:return {"status":"unavailable","reason":"Invalid outcome price"}
    reference=number(forecast["reference_price"])
    error=predicted-actual
    return {"status":"evaluated","forecast_id":forecast["forecast_id"],"actual_price":str(actual),
      "absolute_error":str(abs(error)),"absolute_percentage_error":str(abs(error)/actual*100),
      "predicted_return_percent":str((predicted/reference-1)*100),
      "realised_return_percent":str((actual/reference-1)*100),
      "direction_correct":(predicted>reference)==(actual>reference) if predicted!=reference and actual!=reference else None,
      "outcome_source":outcome["source_url"],"observed_at":observed.isoformat()}

def aggregate(results):
    evaluated=[x for x in results if x.get("status")=="evaluated"]
    if not evaluated:return {"status":"insufficient_evidence","sample_size":0}
    errors=[number(x["absolute_percentage_error"]) for x in evaluated]
    directional=[x["direction_correct"] for x in evaluated if x["direction_correct"] is not None]
    return {"status":"descriptive_only","sample_size":len(evaluated),
      "mean_absolute_percentage_error":str(sum(errors)/len(errors)),
      "directional_sample_size":len(directional),
      "directional_accuracy_percent":str(Decimal(sum(directional))/len(directional)*100) if directional else None,
      "note":"Historical sample only; no future performance claim"}
