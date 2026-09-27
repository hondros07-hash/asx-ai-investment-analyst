"""Conservative provider-statement cash allocation: no unsupported dividends or buybacks."""
import math
def finite(x): return isinstance(x,(int,float)) and math.isfinite(x)
def build(data):
 cf=(data.get("statements") or {}).get("Cash Flow") or {}
 periods=data.get("periods") or []
 out=[]
 for p in reversed(periods):
  def v(k):
   x=(cf.get(k) or {}).get(p)
   return x if finite(x) else None
  ocf=v("Operating Cash Flow"); capex=v("Capital Expenditure"); fcf=v("Free Cash Flow"); financing=v("Financing Cash Flow")
  investment=abs(capex) if capex is not None else None
  calculated=ocf-investment if ocf is not None and investment is not None else None
  out.append({"Period":p,"Operating cash flow":ocf,"Capital expenditure (absolute)":investment,"Free cash flow":fcf,"Financing cash flow (net)":financing,"OCF less CapEx":calculated,"FCF bridge difference":fcf-calculated if fcf is not None and calculated is not None else None,"FCF basis":"Derived OCF − absolute CapEx" if ("Free Cash Flow",p) in (data.get("derived") or {}) else "Provider-transcribed or unavailable"})
 return out
