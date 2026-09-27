"""Statement integrity checks. Missing evidence is never treated as a passed check."""
import math
import pandas as pd

def finite(v):
    return isinstance(v,(int,float)) and math.isfinite(v)

def validate(data):
    statements=data.get("statements") or {}
    periods=data.get("periods") or []
    inc=statements.get("Income Statement") or {}
    bal=statements.get("Balance Sheet") or {}
    cf=statements.get("Cash Flow") or {}
    results=[]
    def value(table,key,period): return (table.get(key) or {}).get(period)
    def add(period,check,status,detail,variance=None,reported=None,expected=None,tolerance=None):
        results.append({"Period":period,"Check":check,"Status":status,"Reported value":reported,"Expected value":expected,"Difference":variance,"Tolerance":tolerance,"Detail":detail})
    for p in periods:
        assets=value(bal,"Total Assets",p); liabilities=value(bal,"Total Liabilities",p); equity=value(bal,"Stockholders Equity",p)
        if all(finite(x) for x in (assets,liabilities,equity)):
            difference=assets-liabilities-equity
            tolerance=max(1.0,abs(assets)*.001)
            add(p,"Assets = liabilities + equity","Pass" if abs(difference)<=tolerance else "Mismatch",
                "Tolerance: 0.1% of assets or 1 reporting unit, whichever is greater.",difference,assets,liabilities+equity,tolerance)
        else: add(p,"Assets = liabilities + equity","Not testable","Total assets, total liabilities and equity are all required.")
        revenue=value(inc,"Revenue",p); cost=value(inc,"Cost of Revenue",p); gross=value(inc,"Gross Profit",p)
        if ("Gross Profit",p) in (data.get("derived") or {}):
            add(p,"Gross profit reconciliation","Not testable","Gross profit is derived from the same inputs; not independent evidence.")
        elif all(finite(x) for x in (revenue,cost,gross)):
            difference=gross-(revenue-abs(cost))
            tolerance=max(1.0,abs(revenue)*.001)
            add(p,"Gross profit reconciliation","Pass" if abs(difference)<=tolerance else "Mismatch",
                "Reported gross profit compared with revenue less absolute cost of revenue.",difference,gross,revenue-abs(cost),tolerance)
        else: add(p,"Gross profit reconciliation","Not testable","Revenue, cost of revenue and gross profit are required.")
        ocf=value(cf,"Operating Cash Flow",p); capex=value(cf,"Capital Expenditure",p); fcf=value(cf,"Free Cash Flow",p)
        if ("Free Cash Flow",p) in (data.get("derived") or {}):
            add(p,"FCF definition consistency","Not testable","FCF is derived from OCF and CapEx; not independent evidence.")
        elif all(finite(x) for x in (ocf,capex,fcf)):
            difference=fcf-(ocf-abs(capex))
            tolerance=max(1.0,abs(ocf)*.001)
            add(p,"FCF definition consistency","Pass" if abs(difference)<=tolerance else "Definition differs",
                "Provider FCF may exclude or include additional items; investigate rather than overwrite.",difference,fcf,ocf-abs(capex),tolerance)
        else: add(p,"FCF definition consistency","Not testable","Operating cash flow, capital expenditure and FCF are required.")
        for group,table in statements.items():
            for key,values in table.items():
                v=values.get(p)
                if v is not None and not finite(v):
                    add(p,"Finite value: "+group+" / "+key,"Invalid","Non-finite or non-numeric statement value.")
    if data.get("currency") in (None,"","Unconfirmed"):
        add("All","Provider financial currency","Unconfirmed","Do not label monetary amounts AUD, EUR or another currency without provider/filing reconciliation.")
    else: add("All","Provider financial currency","Provider-reported","Currency metadata exists; still requires filing reconciliation.")
    if data.get("frequency")=="TTM":
        add("TTM","Period alignment","Provisional","Four aligned quarter labels alone do not prove consecutive, non-overlapping fiscal quarters.")
    else:
        dates=[]
        for p in periods:
            try: dates.append(pd.Timestamp(p))
            except (ValueError,TypeError): add(p,"Reporting date","Invalid","Could not parse provider period date.")
        if len(dates)!=len(set(dates)): add("All","Reporting dates","Mismatch","Duplicate period dates.")
    return results

def summary(rows):
    return {status:sum(r["Status"]==status for r in rows) for status in ("Pass","Mismatch","Definition differs","Not testable","Invalid","Unconfirmed","Provider-reported","Provisional")}
