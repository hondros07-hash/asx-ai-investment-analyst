"""AXÍA V23.8.4: numerical reverse-valuation and sensitivity primitives.

A caller supplies a validated company-specific valuation function. No generic
DCF is passed off as a verified company valuation. No fabricated assumptions.
"""
from math import isfinite

def solve_single_variable(valuation_fn,target,lower,upper,tolerance=1e-6,iterations=100):
    target=float(target); lo=float(lower); hi=float(upper)
    if not all(isfinite(x) for x in (target,lo,hi)) or lo>=hi: raise ValueError("Invalid bounds")
    a=float(valuation_fn(lo))-target; b=float(valuation_fn(hi))-target
    if not all(isfinite(x) for x in (a,b)): return {"status":"invalid_model_output","value":None}
    if abs(a)<=tolerance:return {"status":"solved","value":lo}
    if abs(b)<=tolerance:return {"status":"solved","value":hi}
    if a*b>0:return {"status":"not_bracketed","value":None}
    for _ in range(iterations):
        mid=(lo+hi)/2; error=float(valuation_fn(mid))-target
        if not isfinite(error):return {"status":"invalid_model_output","value":None}
        if abs(error)<=tolerance:return {"status":"solved","value":mid}
        if a*error<=0:hi=mid;b=error
        else:lo=mid;a=error
    return {"status":"iteration_limit","value":(lo+hi)/2}

def implied_matrix(valuation_fn,target,growth_values,margin_values):
    target=float(target)
    if not isfinite(target):raise ValueError("Invalid target")
    cells=[]
    for growth in growth_values:
        row=[]
        for margin in margin_values:
            value=float(valuation_fn(float(growth),float(margin)))
            row.append({"growth":growth,"margin":margin,"value":value if isfinite(value) else None,
                        "delta_to_target":value-target if isfinite(value) else None})
        cells.append(row)
    return {"target":target,"cells":cells,"note":"Sensitivity grid, not a unique market-implied forecast."}

def pivotal_sensitivities(base_inputs,valuation_fn,shocks):
    base=float(valuation_fn(**base_inputs))
    if not isfinite(base):return []
    result=[]
    for name,shock in shocks.items():
        if name not in base_inputs:continue
        changed=dict(base_inputs);changed[name]=base_inputs[name]+shock
        value=float(valuation_fn(**changed))
        if isfinite(value):
            result.append({"metric":name,"shock":shock,"value_change":value-base,
                           "absolute_sensitivity":abs(value-base)})
    return sorted(result,key=lambda x:x["absolute_sensitivity"],reverse=True)
