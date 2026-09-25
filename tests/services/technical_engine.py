from __future__ import annotations
from typing import Any, Dict, Optional
import math
import numpy as np
import pandas as pd

def _finite(v: Any) -> Optional[float]:
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def _wilder_rsi(close: pd.Series, period: int=14) -> pd.Series:
    """Wilder-style RSI with explicit flat/up-only/down-only edge handling."""
    c=pd.to_numeric(close,errors="coerce").astype(float)
    d=c.diff()
    gain=d.clip(lower=0.0)
    loss=(-d.clip(upper=0.0))
    avg_gain=gain.ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    avg_loss=loss.ewm(alpha=1/period,adjust=False,min_periods=period).mean()
    rs=avg_gain/avg_loss.replace(0,np.nan)
    rsi=100-(100/(1+rs))
    rsi=rsi.mask((avg_loss==0)&(avg_gain>0),100.0)
    rsi=rsi.mask((avg_gain==0)&(avg_loss>0),0.0)
    rsi=rsi.mask((avg_gain==0)&(avg_loss==0),50.0)
    return rsi.clip(0,100)

def core_indicator_frame(history: pd.DataFrame) -> pd.DataFrame:
    """Pure deterministic core indicators. No network calls and no AI."""
    if history is None or history.empty or "Close" not in history:
        return pd.DataFrame()
    x=history.copy()
    c=pd.to_numeric(x["Close"],errors="coerce")
    out=pd.DataFrame(index=x.index)
    out["Price"]=c
    out["RSI"]=_wilder_rsi(c,14)
    out["SMA 20"]=c.rolling(20,min_periods=20).mean()
    out["SMA 50"]=c.rolling(50,min_periods=50).mean()
    out["SMA 200"]=c.rolling(200,min_periods=200).mean()
    e12=c.ewm(span=12,adjust=False,min_periods=12).mean()
    e26=c.ewm(span=26,adjust=False,min_periods=26).mean()
    out["MACD"]=e12-e26
    out["MACD Signal"]=out["MACD"].ewm(span=9,adjust=False,min_periods=9).mean()
    out["MACD Hist"]=out["MACD"]-out["MACD Signal"]
    if {"High","Low"}.issubset(x.columns):
        h=pd.to_numeric(x["High"],errors="coerce"); l=pd.to_numeric(x["Low"],errors="coerce")
        tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
        out["ATR"]=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    else:
        out["ATR"]=np.nan
    if "Volume" in x:
        v=pd.to_numeric(x["Volume"],errors="coerce")
        out["Volume"]=v
        out["Volume Avg 20"]=v.rolling(20,min_periods=20).mean()
        out["Volume Ratio"]=v/out["Volume Avg 20"].replace(0,np.nan)
    else:
        out["Volume"]=np.nan; out["Volume Avg 20"]=np.nan; out["Volume Ratio"]=np.nan
    return out

def calculate_technical_snapshot(history: pd.DataFrame) -> Dict[str,Any]:
    t=core_indicator_frame(history)
    if t.empty:
        return {"status":"pending","technical_status":"Pending","description":"Insufficient price history",
                "evidence_coverage":0,"calculation":"deterministic_python","ai_calculated":False,"signals":{}}
    z=t.iloc[-1]
    price=_finite(z.get("Price"))
    signals={}
    votes=[]

    rsi=_finite(z.get("RSI"))
    if rsi is None:
        signals["rsi"]={"value":None,"period":14,"state":"Pending","vote":None}
    else:
        rsi_state="Oversold" if rsi<30 else "Overbought" if rsi>70 else "Neutral"
        # RSI contributes directional momentum around 50; 30/70 are condition zones, not reversal predictions.
        vote=1 if rsi>55 else -1 if rsi<45 else 0
        signals["rsi"]={"value":rsi,"period":14,"state":rsi_state,"vote":vote}; votes.append(vote)

    for n in (20,50,200):
        sma=_finite(z.get(f"SMA {n}"))
        if price is None or sma is None:
            signals[f"sma_{n}"]={"value":sma,"state":"Pending","vote":None}
        else:
            vote=1 if price>sma else -1 if price<sma else 0
            signals[f"sma_{n}"]={"value":sma,"state":"Above" if vote>0 else "Below" if vote<0 else "At","vote":vote}
            votes.append(vote)

    macd=_finite(z.get("MACD")); macds=_finite(z.get("MACD Signal")); hist=_finite(z.get("MACD Hist"))
    if macd is None or macds is None:
        signals["macd"]={"value":macd,"signal":macds,"histogram":hist,"state":"Pending","vote":None}
    else:
        vote=1 if macd>macds else -1 if macd<macds else 0
        signals["macd"]={"value":macd,"signal":macds,"histogram":hist,"state":"Positive" if vote>0 else "Negative" if vote<0 else "Neutral","vote":vote}; votes.append(vote)

    atr=_finite(z.get("ATR"))
    signals["atr"]={"value":atr,"period":14,"percent_of_price":(atr/price*100 if atr is not None and price else None),"state":"Available" if atr is not None else "Pending","vote":None}

    vr=_finite(z.get("Volume Ratio"))
    signals["volume"]={"ratio_to_20d":vr,"state":"Elevated" if vr is not None and vr>=1.2 else "Normal" if vr is not None else "Pending","vote":None}

    # Six directional evidence slots: RSI, SMA20/50/200, MACD. Volume/ATR are context, not direction.
    available=sum(1 for k in ("rsi","sma_20","sma_50","sma_200","macd") if signals[k]["vote"] is not None)
    coverage=round(available/5*100)
    score=(sum(votes)/len(votes)) if votes else None
    if score is None:
        overall="Pending"; desc="Insufficient technical evidence"
    elif score>=0.4:
        overall="Positive"; desc="Positive composite momentum"
    elif score<=-0.4:
        overall="Negative"; desc="Negative composite momentum"
    else:
        overall="Neutral"; desc="Mixed / neutral technical evidence"

    ma_parts=[]
    for n in (50,200):
        st=signals[f"sma_{n}"]["state"]
        if st!="Pending": ma_parts.append(f"{st.lower()} {n}D MA")
    context=" · ".join(ma_parts[:2]) if ma_parts else desc
    return {"status":"success" if available else "pending","technical_status":overall,"description":desc,
            "context":context,"rsi_value":rsi,"evidence_coverage":coverage,
            "composite_score":score,"signals":signals,"latest_price":price,
            "calculation":"deterministic_python","ai_calculated":False}
