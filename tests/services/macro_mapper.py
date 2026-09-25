from __future__ import annotations
from copy import deepcopy
from typing import Dict, List, Optional

# Deterministic structural exposure dictionary. This maps economic factors to
# business KPIs; it does not predict share-price direction or claim causation.

TEMPLATES = {
    "airlines": {
        "sector_keywords": ["airline", "airlines", "aviation", "air transport", "passenger transport"],
        "exposures": [
            {"factor":"Crude Oil / Jet Fuel","tracker":"BZ=F","label":"Brent Crude Oil","keywords":["oil","brent","crude","jet fuel","fuel price","refining margin"],"affected_kpis":["Fuel Expense","Operating Margin","EBIT","Free Cash Flow"],"transmission":"Fuel is a major airline input cost. Oil and refining-price changes can alter fuel expense, subject to hedging and pricing responses.","directionality":"Higher input prices can pressure costs before hedging/pricing offsets.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"AUD/USD","tracker":"AUDUSD=X","label":"AUD/USD","keywords":["aud","australian dollar","usd","us dollar","currency","fx","foreign exchange"],"affected_kpis":["Fuel Expense","International Revenue","Operating Margin"],"transmission":"Currency moves can change AUD-equivalent USD costs and translated international revenue, subject to hedging.","directionality":"Depends on the balance of foreign-currency revenue, costs and hedges.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"Australian Equity Market","tracker":"^AXJO","label":"S&P/ASX 200","keywords":["asx 200","australian shares","equity market","risk sentiment"],"affected_kpis":["Valuation","Cost of Capital"],"transmission":"Broad market risk appetite and discount-rate conditions can influence valuation independently of operating performance.","directionality":"Context dependent.","time_horizon":"Immediate to medium term","confidence":"Medium"},
        ]},
    "banking": {
        "sector_keywords":["bank","banking","financial services","diversified banks","regional banks"],
        "exposures":[
            {"factor":"Interest Rates / Bond Yields","tracker":"^TNX","label":"U.S. 10Y Treasury Yield","keywords":["interest rate","rates","bond yield","treasury yield","central bank","rba","fed"],"affected_kpis":["Net Interest Margin","Credit Growth","Funding Costs","Valuation"],"transmission":"Rate changes can affect asset yields, deposit/funding costs, credit demand and valuation.","directionality":"Depends on repricing, deposit mix, funding structure and credit cycle.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"Australian Equity Market","tracker":"^AXJO","label":"S&P/ASX 200","keywords":["asx 200","australian shares","equity market"],"affected_kpis":["Valuation","Wealth/Markets Revenue"],"transmission":"Market conditions can influence valuation and market-sensitive fee income.","directionality":"Context dependent.","time_horizon":"Immediate to medium term","confidence":"Medium"},
            {"factor":"AUD/USD","tracker":"AUDUSD=X","label":"AUD/USD","keywords":["aud","australian dollar","usd","currency","fx"],"affected_kpis":["Markets Revenue","Funding Costs"],"transmission":"FX and global risk conditions can affect markets activity and offshore funding conditions.","directionality":"Context dependent.","time_horizon":"Near term","confidence":"Medium"},
        ]},
    "mining": {
        "sector_keywords":["mining","miner","metals","materials","resources","gold","copper"],
        "exposures":[
            {"factor":"Gold","tracker":"GC=F","label":"Gold","keywords":["gold","bullion","gold price"],"affected_kpis":["Revenue","EBITDA","Operating Margin","Free Cash Flow"],"transmission":"Commodity prices affect realised selling prices for exposed producers.","directionality":"Higher realised prices can support revenue and margins, all else equal.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"Copper","tracker":"HG=F","label":"Copper","keywords":["copper","copper price","industrial metals"],"affected_kpis":["Revenue","EBITDA","Operating Margin","Free Cash Flow"],"transmission":"Commodity prices affect realised selling prices for exposed producers.","directionality":"Higher realised prices can support revenue and margins, all else equal.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"AUD/USD","tracker":"AUDUSD=X","label":"AUD/USD","keywords":["aud","australian dollar","usd","currency","fx"],"affected_kpis":["Revenue","Operating Costs","Operating Margin"],"transmission":"Many commodities are USD-priced while Australian costs may be AUD-denominated.","directionality":"Depends on revenue/cost currency mix and hedging.","time_horizon":"Near to medium term","confidence":"High"},
        ]},
    "energy": {
        "sector_keywords":["energy","oil","gas","petroleum","lng"],
        "exposures":[
            {"factor":"Crude Oil","tracker":"BZ=F","label":"Brent Crude Oil","keywords":["oil","brent","crude","opec"],"affected_kpis":["Revenue","EBITDA","Operating Margin","Free Cash Flow"],"transmission":"Oil prices can affect realised prices and project economics for oil-exposed producers.","directionality":"Higher realised prices can support revenue and cash flow, all else equal.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"Natural Gas","tracker":"NG=F","label":"Natural Gas","keywords":["natural gas","gas price","lng"],"affected_kpis":["Revenue","EBITDA","Free Cash Flow"],"transmission":"Gas/LNG prices can affect realised revenue for exposed producers.","directionality":"Higher realised prices can support revenue, all else equal.","time_horizon":"Near to medium term","confidence":"High"},
            {"factor":"AUD/USD","tracker":"AUDUSD=X","label":"AUD/USD","keywords":["aud","australian dollar","usd","currency","fx"],"affected_kpis":["Revenue","Operating Costs","Free Cash Flow"],"transmission":"Currency changes alter translated commodity revenue and local costs.","directionality":"Depends on currency mix and hedging.","time_horizon":"Near to medium term","confidence":"High"},
        ]},
    "technology": {
        "sector_keywords":["technology","software","semiconductor","internet","interactive media"],
        "exposures":[
            {"factor":"Technology Market","tracker":"^IXIC","label":"NASDAQ Composite","keywords":["nasdaq","technology stocks","tech sector","risk appetite"],"affected_kpis":["Valuation","Cost of Capital"],"transmission":"Technology-sector risk appetite can affect valuation multiples independently of company operations.","directionality":"Context dependent.","time_horizon":"Immediate to medium term","confidence":"Medium"},
            {"factor":"Long-term Yields","tracker":"^TNX","label":"U.S. 10Y Treasury Yield","keywords":["treasury yield","bond yield","interest rate","rates","fed"],"affected_kpis":["Valuation","Cost of Capital"],"transmission":"Changes in discount rates can affect the present value assigned to longer-duration earnings.","directionality":"Higher discount rates can pressure valuation multiples, all else equal.","time_horizon":"Immediate to medium term","confidence":"High"},
            {"factor":"U.S. Dollar","tracker":"DX-Y.NYB","label":"U.S. Dollar Index","keywords":["dollar index","us dollar","usd","currency","fx"],"affected_kpis":["International Revenue","Operating Margin"],"transmission":"Currency moves can affect translated international revenue and costs.","directionality":"Depends on geographic revenue/cost mix and hedging.","time_horizon":"Near to medium term","confidence":"Medium"},
        ]},
    "generic": {
        "sector_keywords":["market","economy"],
        "exposures":[
            {"factor":"Broad Equity Market","tracker":"^GSPC","label":"S&P 500","keywords":["s&p 500","equity market","stocks","risk sentiment"],"affected_kpis":["Valuation","Cost of Capital"],"transmission":"Broad market conditions can influence valuation and risk appetite.","directionality":"Context dependent.","time_horizon":"Immediate to medium term","confidence":"Medium"},
            {"factor":"AUD/USD","tracker":"AUDUSD=X","label":"AUD/USD","keywords":["aud","australian dollar","usd","currency","fx"],"affected_kpis":["Revenue","Costs","Valuation"],"transmission":"FX can affect companies with cross-border revenue, costs or funding.","directionality":"Depends on company-specific currency exposure.","time_horizon":"Near to medium term","confidence":"Low"},
        ]},
}

TICKER_OVERRIDES = {
    "QAN.AX": {"template":"airlines","sector":"Industrials","industry":"Airlines"},
}

def _template_key(ticker:str, sector:str="", industry:str="") -> str:
    t=str(ticker or "").upper().strip()
    if t in TICKER_OVERRIDES: return TICKER_OVERRIDES[t]["template"]
    text=f"{sector} {industry}".lower()
    for key, tpl in TEMPLATES.items():
        if key=="generic": continue
        if any(k in text for k in tpl["sector_keywords"]): return key
    return "generic"

def get_exposure_matrix(ticker:str, sector:str="", industry:str="", country:str="") -> Dict:
    ticker=str(ticker or "").upper().strip()
    override=TICKER_OVERRIDES.get(ticker,{})
    sector=sector or override.get("sector","")
    industry=industry or override.get("industry","")
    key=_template_key(ticker,sector,industry)
    tpl=deepcopy(TEMPLATES[key])
    return {"ticker":ticker,"sector":sector,"industry":industry,"country":country,"template":key,"sector_keywords":tpl["sector_keywords"],"exposures":tpl["exposures"],"mapping_method":"ticker_override" if ticker in TICKER_OVERRIDES else ("industry_template" if key!="generic" else "generic_fallback"),"ai_generated":False}

def relevant_exposures(text:str, ticker:str, sector:str="", industry:str="", country:str="") -> List[Dict]:
    hay=str(text or "").lower()
    matrix=get_exposure_matrix(ticker,sector,industry,country)
    matches=[]
    for exp in matrix["exposures"]:
        hits=sorted({k for k in exp["keywords"] if k.lower() in hay})
        if hits:
            item=deepcopy(exp); item["matched_keywords"]=hits; matches.append(item)
    return matches

def primary_exposure_for_text(text:str, ticker:str, sector:str="", industry:str="", country:str="") -> Optional[Dict]:
    matches=relevant_exposures(text,ticker,sector,industry,country)
    return matches[0] if matches else None
