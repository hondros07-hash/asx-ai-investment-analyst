"""Chrímata V23.4.4 — API adapter for the global dividend intelligence grid."""
from __future__ import annotations
import os
from typing import Any, Dict
import pandas as pd
from corporate_actions_calendar import corporate_actions_calendar

MARKETS={
 "AU":{"name":"Australia","currency":"AUD","universe":["BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","WES.AX","MQG.AX","WOW.AX","TLS.AX","QAN.AX","ZIP.AX","FMG.AX","RIO.AX","HVN.AX","ORG.AX","WDS.AX","STO.AX","GMG.AX","SCG.AX","QBE.AX","ASX.AX"]},
 "US":{"name":"United States","currency":"USD","universe":["AAPL","MSFT","NVDA","AMZN","GOOGL","META","JPM","V","WMT","XOM","KO","PEP","COST","HD","MCD","JNJ","ABBV"]},
 "GB":{"name":"United Kingdom","currency":"GBP","universe":["SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","RIO.L","GSK.L","BARC.L","VOD.L","BATS.L","LLOY.L","TSCO.L"]},
 "JP":{"name":"Japan","currency":"JPY","universe":["7203.T","6758.T","9984.T","8306.T","6861.T","8035.T","9432.T","7974.T","6501.T","7267.T"]},
 "HK":{"name":"Hong Kong","currency":"HKD","universe":["0700.HK","9988.HK","3690.HK","1299.HK","0005.HK","0388.HK","2318.HK","0941.HK"]},
 "CA":{"name":"Canada","currency":"CAD","universe":["RY.TO","TD.TO","ENB.TO","CNR.TO","BNS.TO","BMO.TO","CNQ.TO","MFC.TO","BCE.TO","T.TO"]},
 "GR":{"name":"Greece","currency":"EUR","universe":["ETE.AT","ALPHA.AT","EUROB.AT","TPEIR.AT","OPAP.AT","OTE.AT"]},
}

def _native(v):
    if v is None:return None
    try:
        if pd.isna(v):return None
    except Exception:pass
    if isinstance(v,(str,bool,int,float)):return v
    if isinstance(v,pd.Timestamp):return v.isoformat()
    return str(v)

def dividend_calendar_payload(market_code:str,horizon_days:int=120)->Dict[str,Any]:
    code=(market_code or '').upper().strip()
    cfg=MARKETS.get(code)
    if not cfg:return {"status":"INVALID_MARKET","market_region":code,"dividend_calendar":[]}
    td=os.getenv('TWELVE_DATA_API_KEY','').strip()
    fmp=os.getenv('FMP_API_KEY','').strip()
    df=corporate_actions_calendar(cfg['name'],tuple(cfg['universe']),horizon_days,td,fmp)
    attrs=getattr(df,'attrs',{}) or {}
    rows=[]
    if df is not None and not df.empty:
        for _,r in df.iterrows():
            currency=_native(r.get('Currency'))
            if not currency or currency=='—':currency=cfg['currency']
            rows.append({
              "ticker":_native(r.get('Ticker')),"company":_native(r.get('Company')),
              "ex_date":_native(r.get('Ex-Date')),"record_date":_native(r.get('Record-Date')),
              "pay_date":_native(r.get('Pay-Date')),"amount":_native(r.get('Amount')),
              "currency":currency,"dividend_type":_native(r.get('Type')),
              "franking":_native(r.get('Franking')) if code=='AU' else None,
              "source":_native(r.get('Source')),"verified":bool(r.get('Verified',False)),
            })
    status=str(attrs.get('status') or ('SUCCESS' if rows else 'UNAVAILABLE'))
    diagnostics=dict(attrs.get('diagnostics') or {})
    return {"status":status,"market_region":code,"market_name":cfg['name'],
      "horizon_days":horizon_days,"dividend_calendar":rows,
      "freshness":{"cache_seconds":900,"confirmed_only":True},
      "provenance":{"providers_attempted":diagnostics.get('attempted',[]),
                    "providers_configured":diagnostics.get('configured',[]),
                    "ai_calculated_math":False}}
