from __future__ import annotations
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
import math, re
import pandas as pd

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except:return None

def _norm(s): return re.sub(r"[^a-z0-9]","",str(s or "").lower())

ALIASES={
"operating_cash_flow":("Operating Cash Flow","Total Cash From Operating Activities","Cash Flow From Continuing Operating Activities"),
 "capex":("Capital Expenditure","Capital Expenditures","Capital Expenditure Reported","Purchase Of PPE","Purchases Of PPE","Purchase Of Property Plant And Equipment","Purchases Of Property Plant And Equipment"),
"cash":("Cash Cash Equivalents And Short Term Investments","Cash And Cash Equivalents","Cash"),
"debt":("Total Debt","Long Term Debt And Capital Lease Obligation","Long Term Debt","Current Debt And Capital Lease Obligation"),
"shares":("Ordinary Shares Number","Share Issued","Diluted Average Shares","Basic Average Shares"),
}

def _latest_statement_value(df: Optional[pd.DataFrame], aliases: Iterable[str]) -> Tuple[Optional[float],Optional[str],Optional[str]]:
    if df is None or getattr(df,"empty",True): return None,None,None
    rows={_norm(i):i for i in df.index}
    # Exact normalized alias first, then conservative contains matching for provider label variations.
    candidates=[]
    for a in aliases:
        k=_norm(a)
        if k in rows: candidates.append(rows[k])
    if not candidates:
        for a in aliases:
            k=_norm(a)
            if len(k)>=8:
                for nk,raw in rows.items():
                    if k in nk or nk in k:
                        candidates.append(raw)
    for raw in dict.fromkeys(candidates):
        row=pd.to_numeric(df.loc[raw],errors="coerce").dropna()
        if row.empty: continue
        # Prefer TTM when explicitly present; otherwise newest datetime column; otherwise first provider column.
        chosen=None
        for c in row.index:
            if "ttm" in str(c).lower() or "trailing" in str(c).lower(): chosen=c; break
        if chosen is None:
            dated=[]
            for c in row.index:
                try: dated.append((pd.Timestamp(c),c))
                except: pass
            if dated: chosen=max(dated,key=lambda x:x[0])[1]
        if chosen is None: chosen=row.index[0]
        return _num(row.loc[chosen]),str(raw),str(chosen)
    return None,None,None

def recover_financial_inputs(meta: Mapping[str,Any], cashflow: Optional[pd.DataFrame]=None,
                             balance_sheet: Optional[pd.DataFrame]=None,
                             income_statement: Optional[pd.DataFrame]=None) -> Dict[str,Any]:
    """Metadata → statements → deterministic derivation. Never invents missing inputs."""
    meta=meta or {}; audit={"inputs":{},"ai_calculated":False,"calculation":"deterministic_python"}
    fcf=_num(meta.get("freeCashflow") or meta.get("freeCashFlow"))
    if fcf is not None:
        audit["inputs"]["fcf"]={"status":"verified","source":"provider_metadata","value":fcf}
    else:
        ocf,orow,oper=_latest_statement_value(cashflow,ALIASES["operating_cash_flow"])
        capex,crow,cper=_latest_statement_value(cashflow,ALIASES["capex"])
        if ocf is not None and capex is not None:
            # Providers commonly report capex as negative cash outflow. FCF = OCF + negative capex;
            # if capex is positive expenditure magnitude, subtract it.
            fcf=ocf+capex if capex<0 else ocf-capex
            audit["inputs"]["fcf"]={"status":"derived","source":"cash_flow_statement","value":fcf,
                "formula":"Operating Cash Flow - Capital Expenditure","operating_cash_flow":ocf,
                "capital_expenditure":capex,"rows":[orow,crow],"periods":[oper,cper]}
        else:
            audit["inputs"]["fcf"]={"status":"missing","source":None,"value":None,
                "reason":"Provider FCF absent and cash-flow statement did not contain both OCF and capex."}

    shares=_num(meta.get("sharesOutstanding") or meta.get("impliedSharesOutstanding"))
    if shares is not None:
        audit["inputs"]["shares"]={"status":"verified","source":"provider_metadata","value":shares}
    else:
        shares,srow,sper=_latest_statement_value(balance_sheet,ALIASES["shares"])
        if shares is None: shares,srow,sper=_latest_statement_value(income_statement,ALIASES["shares"])
        audit["inputs"]["shares"]={"status":"verified" if shares is not None else "missing",
            "source":"financial_statement" if shares is not None else None,"value":shares,"row":srow,"period":sper}

    cash=_num(meta.get("totalCash"))
    if cash is not None:audit["inputs"]["cash"]={"status":"verified","source":"provider_metadata","value":cash}
    else:
        cash,row,per=_latest_statement_value(balance_sheet,ALIASES["cash"])
        audit["inputs"]["cash"]={"status":"verified" if cash is not None else "missing","source":"balance_sheet" if cash is not None else None,"value":cash,"row":row,"period":per}

    debt=_num(meta.get("totalDebt"))
    if debt is not None:audit["inputs"]["debt"]={"status":"verified","source":"provider_metadata","value":debt}
    else:
        debt,row,per=_latest_statement_value(balance_sheet,ALIASES["debt"])
        audit["inputs"]["debt"]={"status":"verified" if debt is not None else "missing","source":"balance_sheet" if debt is not None else None,"value":debt,"row":row,"period":per}

    fc=meta.get("financialCurrency"); lc=meta.get("currency")
    audit["inputs"]["financial_currency"]={"status":"verified" if fc else "missing","source":"provider_metadata" if fc else None,"value":fc}
    audit["inputs"]["listing_currency"]={"status":"verified" if lc else "missing","source":"provider_metadata" if lc else None,"value":lc}
    audit["complete_for_dcf"]=fcf is not None and fcf>0 and shares is not None and shares>0
    return {"fcf":fcf,"shares":shares,"cash":cash or 0.0,"debt":debt or 0.0,
            "financial_currency":fc,"listing_currency":lc,
            "sector":meta.get("sector") or meta.get("sectorDisp") or "",
            "industry":meta.get("industry") or meta.get("industryDisp") or "","audit":audit}

def issuer_fingerprint(meta: Mapping[str,Any]) -> Dict[str,Any]:
    m=meta or {}
    raw_site=str(m.get("website") or "").strip().lower()
    raw_site=re.sub(r"^https?://","",raw_site).split("/")[0].split("?")[0]
    if raw_site.startswith("www."): raw_site=raw_site[4:]
    return {"name":_norm(m.get("longName") or m.get("shortName")),
            "website":_norm(raw_site),
            "isin":_norm(m.get("isin")),"sector":_norm(m.get("sector")),
            "industry":_norm(m.get("industry"))}

def verify_primary_listing_relationship(selected_meta: Mapping[str,Any], candidate_meta: Mapping[str,Any]) -> Dict[str,Any]:
    """Conservative bridge: requires strong issuer evidence; ticker/name resemblance alone never passes."""
    a=issuer_fingerprint(selected_meta); b=issuer_fingerprint(candidate_meta)
    evidence=[]; score=0
    if a["isin"] and b["isin"] and a["isin"]==b["isin"]: evidence.append("matching_isin");score+=100
    if a["website"] and b["website"] and a["website"]==b["website"]: evidence.append("matching_website");score+=55
    if a["name"] and b["name"] and a["name"]==b["name"]: evidence.append("matching_legal_name");score+=35
    if a["sector"] and b["sector"] and a["sector"]==b["sector"]: evidence.append("matching_sector");score+=5
    if a["industry"] and b["industry"] and a["industry"]==b["industry"]: evidence.append("matching_industry");score+=5
    verified=("matching_isin" in evidence) or ("matching_website" in evidence and "matching_legal_name" in evidence)
    return {"verified":verified,"score":score,"evidence":evidence,
            "reason":"Verified issuer relationship" if verified else "Issuer relationship not sufficiently verified",
            "ai_calculated":False}

def bridge_payload(selected_ticker: str, selected_meta: Mapping[str,Any], candidate_ticker: Optional[str],
                   candidate_meta: Optional[Mapping[str,Any]]) -> Dict[str,Any]:
    if not candidate_ticker or not candidate_meta:
        return {"status":"not_used","verified":False,"reason":"No primary-listing candidate supplied","ai_calculated":False}
    v=verify_primary_listing_relationship(selected_meta,candidate_meta)
    return {"status":"verified" if v["verified"] else "rejected","selected_ticker":selected_ticker,
            "candidate_ticker":candidate_ticker,**v}

def _row(df, aliases):
    if df is None or getattr(df, "empty", True): return None, None
    lookup={_norm(i):i for i in df.index}
    for alias in aliases:
        key=_norm(alias)
        if key in lookup:
            raw=lookup[key]
            values=pd.to_numeric(df.loc[raw],errors="coerce")
            if isinstance(values,pd.DataFrame): values=values.iloc[0]
            return values, str(raw)
    return None,None

def _dated_values(row):
    out={}
    if row is None:return out
    for col,value in row.items():
        n=_num(value)
        if n is None:continue
        try:
            dt=pd.Timestamp(col)
            if pd.isna(dt):continue
            out[dt]=n
        except (ValueError,TypeError):continue
    return out

def _fcf_from_statement(frame, quarterly=False):
    """Use direct FCF or matched OCF/capex dates, never mix reporting periods."""
    direct,label=_row(frame,("Free Cash Flow","FreeCashFlow"))
    if direct is not None:
        values=_dated_values(direct)
        if quarterly:
            result=_four_quarter_sum(values)
            if result is not None:return result,{"source":"quarterly_cash_flow","row":label,"period":"TTM: four consecutive quarters"}
        elif values:
            dt=max(values)
            return values[dt],{"source":"annual_cash_flow","row":label,"period":str(dt.date())}
    ocf,orow=_row(frame,ALIASES["operating_cash_flow"])
    cap,crow=_row(frame,ALIASES["capex"])
    if ocf is None or cap is None:return None,None
    o=_dated_values(ocf);c=_dated_values(cap)
    paired={dt:o[dt]+c[dt] if c[dt]<0 else o[dt]-c[dt] for dt in o.keys()&c.keys()}
    if quarterly:
        value=_four_quarter_sum(paired)
        if value is None:return None,None
        return value,{"source":"quarterly_cash_flow","rows":[orow,crow],"period":"TTM: four consecutive matched quarters"}
    if paired:
        dt=max(paired)
        return paired[dt],{"source":"annual_cash_flow","rows":[orow,crow],"period":str(dt.date())}
    return None,None

def _four_quarter_sum(values):
    dates=sorted(values,reverse=True)
    if len(dates)<4:return None
    latest=dates[:4]
    # A genuine four-quarter sequence spans about nine months and has no missing quarter.
    gaps=[(latest[i]-latest[i+1]).days for i in range(3)]
    if not all(65<=gap<=120 for gap in gaps):return None
    return sum(values[d] for d in latest)

def recover_financial_inputs_v2362(meta, annual_cf=None, quarterly_cf=None, annual_bs=None,
                                   quarterly_bs=None, annual_inc=None, quarterly_inc=None):
    """Annual/TTM recovery with period-matched inputs and transparent provenance."""
    meta=meta or {}
    # Metadata is normally trailing FCF. If absent, prefer verified four-quarter TTM.
    recovered=recover_financial_inputs(meta,annual_cf,annual_bs,annual_inc)
    audit=recovered["audit"]
    if _num(meta.get("freeCashflow")) is None and _num(meta.get("freeCashFlow")) is None:
        val,prov=_fcf_from_statement(quarterly_cf,quarterly=True)
        if val is None:val,prov=_fcf_from_statement(annual_cf,quarterly=False)
        if val is not None:
            recovered["fcf"]=val
            audit["inputs"]["fcf"]={"status":"derived","value":val,**prov}
    for key,aliases,metadata_key in (
        ("cash",ALIASES["cash"],"totalCash"),
        ("debt",ALIASES["debt"],"totalDebt"),
        ("shares",ALIASES["shares"],"sharesOutstanding")):
        if _num(meta.get(metadata_key)) is not None:continue
        if key=="shares":
            frames=(quarterly_bs,annual_bs,quarterly_inc,annual_inc)
        else:frames=(quarterly_bs,annual_bs)
        for frame in frames:
            val,row,period=_latest_statement_value(frame,aliases)
            if val is not None:
                recovered[key]=val
                audit["inputs"][key]={"status":"verified","value":val,"source":"quarterly_statement" if frame is quarterly_bs or frame is quarterly_inc else "annual_statement","row":row,"period":period}
                break
    audit["complete_for_dcf"]=bool(_num(recovered["fcf"]) is not None and recovered["fcf"]>0
                                   and _num(recovered["shares"]) is not None and recovered["shares"]>0)
    # Zero is legitimate only when explicitly reported; missing cash/debt must block the equity bridge.
    audit["balance_sheet_complete"]=all(audit["inputs"].get(k,{}).get("status")!="missing" for k in ("cash","debt"))
    return recovered
