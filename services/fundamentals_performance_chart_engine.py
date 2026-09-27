"""Presentation-only financial performance chart series. Never estimate missing data."""
import math

def finite(value):
 return isinstance(value,(int,float)) and math.isfinite(value)

def performance(data):
 periods=list(reversed(data.get("periods") or []))
 statements=data.get("statements") or {}
 inc=statements.get("Income Statement") or {}
 cf=statements.get("Cash Flow") or {}
 def value(table,key,p):
  v=(table.get(key) or {}).get(p)
  return v if finite(v) else None
 rows=[]
 for p in periods:
  revenue=value(inc,"Revenue",p)
  operating=value(inc,"Operating Income (EBIT)",p)
  net=value(inc,"Net Income",p)
  fcf=value(cf,"Free Cash Flow",p)
  rows.append({"Period":p,"Revenue":revenue,"Operating income":operating,"Net income":net,"Free cash flow":fcf,
   "Operating margin":operating/revenue*100 if finite(operating) and finite(revenue) and revenue>0 else None,
   "Net income margin":net/revenue*100 if finite(net) and finite(revenue) and revenue>0 else None})
 return rows
