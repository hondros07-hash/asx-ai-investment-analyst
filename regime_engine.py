
import numpy as np, pandas as pd

def classify_regime(market=None, rates=None, aud=None, volatility=None,
                    china=None, commodities=None):
    result={}
    if market is not None and len(market)>=200:
        c=market["Close"]
        result["equities"]="RISK-ON" if c.iloc[-1] > c.rolling(200).mean().iloc[-1] else "RISK-OFF"
    if rates is not None and len(rates)>=63:
        d=rates.iloc[-1]-rates.iloc[-63]
        result["rates"]="RISING" if d>.10 else "FALLING" if d<-.10 else "STABLE"
    if aud is not None and len(aud)>=63:
        r=aud.iloc[-1]/aud.iloc[-63]-1
        result["aud"]="STRONG" if r>.03 else "WEAK" if r<-.03 else "STABLE"
    if volatility is not None and len(volatility):
        v=float(volatility.iloc[-1])
        result["volatility"]="HIGH" if v>25 else "LOW" if v<15 else "NORMAL"
    result["china"]=china or "NOT SCORED"
    result["commodities"]=commodities or "MIXED/NOT SCORED"
    return result

def event_transmission(event, macro_importance, sector_impact, company_relevance,
                       direction, magnitude, horizon, mechanism, counterargument,
                       confidence, confirmation):
    return {
      "event":event,"macro_importance":macro_importance,"sector_impact":sector_impact,
      "company_relevance":company_relevance,"direction":direction,"magnitude":magnitude,
      "horizon":horizon,"mechanism":mechanism,"counterargument":counterargument,
      "confidence":confidence,"confirmation_or_disproof":confirmation
    }
