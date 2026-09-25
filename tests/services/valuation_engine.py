from dataclasses import dataclass,asdict
from typing import Any,Mapping,Optional
import math
@dataclass(frozen=True)
class DCFScenario: growth:float;discount_rate:float;terminal_growth:float
T={"default":{"Bear":DCFScenario(0,.12,.015),"Base":DCFScenario(.05,.10,.025),"Bull":DCFScenario(.10,.09,.03)},
"technology":{"Bear":DCFScenario(.02,.13,.015),"Base":DCFScenario(.08,.105,.025),"Bull":DCFScenario(.14,.095,.03)},
"consumer":{"Bear":DCFScenario(0,.115,.015),"Base":DCFScenario(.04,.095,.025),"Bull":DCFScenario(.08,.085,.03)},
"industrial":{"Bear":DCFScenario(-.02,.12,.01),"Base":DCFScenario(.04,.10,.02),"Bull":DCFScenario(.08,.09,.025)},
"energy_materials":{"Bear":DCFScenario(-.05,.13,.005),"Base":DCFScenario(.02,.105,.015),"Bull":DCFScenario(.06,.095,.02)}}
def n(v):
 try:x=float(v);return x if math.isfinite(x) else None
 except:return None
def methodology_for(s="",i=""):
 x=f"{s} {i}".lower()
 if any(k in x for k in ("financial","bank","insurance","reit","real estate")):return "unsupported"
 if any(k in x for k in ("technology","software","semiconductor","internet")):return "technology"
 if any(k in x for k in ("consumer","retail","apparel","footwear","restaurant")):return "consumer"
 if any(k in x for k in ("industrial","airline","transport","aerospace","machinery")):return "industrial"
 if any(k in x for k in ("energy","oil","gas","material","mining","metal")):return "energy_materials"
 return "default"
def dcf_value(fcf,shares,cash,debt,sc,years=5):
 fcf=n(fcf);shares=n(shares);cash=n(cash) or 0;debt=n(debt) or 0
 if fcf is None or fcf<=0:return {"status":"unavailable","reason":"Positive trailing free cash flow is required."}
 if shares is None or shares<=0:return {"status":"unavailable","reason":"Verified shares outstanding are required."}
 if sc.discount_rate<=sc.terminal_growth:return {"status":"unavailable","reason":"Discount rate must exceed terminal growth."}
 cur=fcf;pv=0;flows=[]
 for y in range(1,years+1):
  cur*=1+sc.growth;d=cur/(1+sc.discount_rate)**y;pv+=d;flows.append({"year":y,"fcf":cur,"present_value":d})
 tv=cur*(1+sc.terminal_growth)/(sc.discount_rate-sc.terminal_growth);pvt=tv/(1+sc.discount_rate)**years;ev=pv+pvt;eq=ev+cash-debt
 return {"status":"success","enterprise_value":ev,"equity_value":eq,"value_per_share":eq/shares,"pv_forecast_fcf":pv,"terminal_value":tv,"pv_terminal_value":pvt,"cashflows":flows}
def calculate_dcf_scenarios(fcf,shares,cash=0,debt=0,current_price=None,sector="",industry="",financial_currency=None,listing_currency=None,fx_rate_financial_to_listing=None,assumptions=None):
 m=methodology_for(sector,industry)
 if m=="unsupported":return {"status":"unsupported","reason":"FCF DCF is not the default methodology for banks, insurers, REITs or similar financial businesses.","ai_calculated":False}
 template=T[m] if not assumptions else {k:DCFScenario(float(v["growth"]),float(v["discount_rate"]),float(v["terminal_growth"])) for k,v in assumptions.items()}
 fc=(financial_currency or "").upper() or None;lc=(listing_currency or "").upper() or None;fx=1.
 if fc and lc and fc!=lc:
  fx=n(fx_rate_financial_to_listing)
  if fx is None or fx<=0:return {"status":"unavailable","reason":f"Currency normalization required ({fc} → {lc}) but no verified FX rate was available.","ai_calculated":False}
 price=n(current_price);rows={}
 for name,sc in template.items():
  r=dcf_value(fcf,shares,cash,debt,sc)
  if r["status"]=="success":
   ml=r["value_per_share"]*fx;rows[name]={"value_per_share":ml,"model_gap":ml/price-1 if price and price>0 else None,"assumptions":asdict(sc),**{k:v for k,v in r.items() if k not in ("value_per_share","status")}}
  else:rows[name]=r
 base=rows.get("Base",{});bv=n(base.get("value_per_share"));gap=n(base.get("model_gap"))
 label="Unavailable" if bv is None or gap is None else ("Below base case" if gap>=.1 else "Above base case" if gap<=-.1 else "Near base case")
 return {"status":"success" if bv is not None else "unavailable","valuation_label":label,"base_case":bv,"model_gap":gap,"scenarios":rows,"financial_currency":fc,"listing_currency":lc,"fx_rate":fx,"methodology":"5-year FCF DCF","assumption_template":m,"calculation":"deterministic_python","ai_calculated":False}
def provider_inputs(meta):
 meta=meta or {}
 return {"fcf":n(meta.get("freeCashflow") or meta.get("freeCashFlow")),"shares":n(meta.get("sharesOutstanding") or meta.get("impliedSharesOutstanding")),"cash":n(meta.get("totalCash")) or 0,"debt":n(meta.get("totalDebt")) or 0,"financial_currency":meta.get("financialCurrency"),"listing_currency":meta.get("currency"),"sector":meta.get("sector") or meta.get("sectorDisp") or "","industry":meta.get("industry") or meta.get("industryDisp") or ""}
