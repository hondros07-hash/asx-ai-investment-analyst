from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
import math
import numpy as np
import pandas as pd

MODEL_VERSION="21.3.22"
HORIZON=252
FEATURES=("ret_21","ret_63","ret_126","ret_252","vol_21","vol_63","ma_20_gap","ma_50_gap","ma_200_gap","drawdown_252")

def _num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except Exception:return None

def price_series(data: Any) -> pd.Series:
    if isinstance(data,pd.Series): x=data
    elif isinstance(data,pd.DataFrame) and "Close" in data:
        x=data["Close"]; x=x.iloc[:,0] if isinstance(x,pd.DataFrame) else x
    else:return pd.Series(dtype=float)
    return pd.to_numeric(x,errors="coerce").replace([np.inf,-np.inf],np.nan).dropna()

def features(px: pd.Series) -> pd.DataFrame:
    r=px.pct_change(); f=pd.DataFrame(index=px.index)
    for n in (21,63,126,252): f[f"ret_{n}"]=px.pct_change(n)
    f["vol_21"]=r.rolling(21).std()*np.sqrt(252)
    f["vol_63"]=r.rolling(63).std()*np.sqrt(252)
    f["ma_20_gap"]=px/px.rolling(20).mean()-1
    f["ma_50_gap"]=px/px.rolling(50).mean()-1
    f["ma_200_gap"]=px/px.rolling(200).mean()-1
    f["drawdown_252"]=px/px.rolling(252).max()-1
    return f.replace([np.inf,-np.inf],np.nan)

def ridge_predict(X,y,x0,alpha=10.0):
    X=np.asarray(X,float); y=np.asarray(y,float); x0=np.asarray(x0,float)
    mu=np.nanmean(X,axis=0); sd=np.nanstd(X,axis=0); sd=np.where(sd<1e-10,1.,sd)
    X=(X-mu)/sd; x0=(x0-mu)/sd
    X1=np.column_stack([np.ones(len(X)),X]); reg=np.eye(X1.shape[1])*alpha; reg[0,0]=0
    beta=np.linalg.pinv(X1.T@X1+reg)@(X1.T@y)
    return float(np.r_[1.,x0]@beta)

def model_prediction(train: pd.DataFrame,x0: pd.Series) -> float:
    y=train["y"].to_numpy(float)
    ridge=ridge_predict(train[list(FEATURES)].values,y,x0[list(FEATURES)].values)
    momentum=float(np.nanmean([x0["ret_21"],x0["ret_63"],x0["ret_126"]]))
    historical=float(np.nanmedian(y))
    return float(np.nanmean([ridge,momentum,historical]))

def walk_forward(px: pd.Series,horizon=HORIZON,min_train=252,step=21) -> pd.DataFrame:
    f=features(px); y=(px.shift(-horizon)/px-1).rename("y")
    valid=pd.concat([f,y],axis=1).dropna()
    rows=[]
    if len(valid)<min_train+12:return pd.DataFrame(columns=["Date","Predicted","Actual"])
    for i in range(min_train,len(valid),step):
        train=valid.iloc[:i]; test=valid.iloc[i]
        try: pred=model_prediction(train,test); actual=float(test["y"])
        except Exception: continue
        rows.append({"Date":valid.index[i],"Predicted":pred,"Actual":actual})
    return pd.DataFrame(rows)

def diagnostics(bt: pd.DataFrame) -> Dict[str,Any]:
    if bt is None or bt.empty:return {"n":0,"mae":None,"rmse":None,"direction_accuracy":None,"correlation":None}
    a=pd.to_numeric(bt["Actual"],errors="coerce"); p=pd.to_numeric(bt["Predicted"],errors="coerce")
    ok=a.notna()&p.notna(); a=a[ok];p=p[ok]
    if not len(a):return {"n":0,"mae":None,"rmse":None,"direction_accuracy":None,"correlation":None}
    return {"n":int(len(a)),"mae":float(np.mean(abs(a-p))),"rmse":float(np.sqrt(np.mean((a-p)**2))),
            "direction_accuracy":float(np.mean((a>0)==(p>0))),
            "correlation":float(a.corr(p)) if len(a)>2 else None}

def calibrated_positive_probability(bt: pd.DataFrame,current_prediction: float,min_oos=12,max_neighbours=30) -> Tuple[Optional[float],int]:
    """Empirical local calibration using only completed out-of-sample predictions."""
    if bt is None or bt.empty or _num(current_prediction) is None:return None,0
    x=bt.copy(); x["Predicted"]=pd.to_numeric(x["Predicted"],errors="coerce"); x["Actual"]=pd.to_numeric(x["Actual"],errors="coerce")
    x=x.dropna(subset=["Predicted","Actual"])
    if len(x)<min_oos:return None,len(x)
    x["distance"]=(x["Predicted"]-float(current_prediction)).abs()
    n=min(max_neighbours,max(min_oos,len(x)//2))
    near=x.nsmallest(n,"distance")
    # Jeffreys/Beta smoothing avoids presenting 0%/100% from small samples as certainty.
    wins=int((near["Actual"]>0).sum())
    return float((wins+0.5)/(len(near)+1.0)),int(len(near))

def build_12m_forecast(data: Any,current_price: Any=None,security: str="",bridge: Optional[Dict[str,Any]]=None,
                       fx_rate: Any=None,security_ratio: Any=None) -> Dict[str,Any]:
    px=price_series(data); spot=_num(current_price) or (_num(px.iloc[-1]) if len(px) else None)
    audit={"model_version":MODEL_VERSION,"security":security,"history_observations":int(len(px)),
           "horizon_trading_days":HORIZON,"ai_calculated":False,"bridge":dict(bridge or {"status":"not_used"}),
           "method":"ridge + momentum + historical-median ensemble; expanding-window walk-forward; empirical local probability calibration"}
    if len(px)<504 or spot is None or spot<=0:
        audit.update({"status":"unavailable","reason":"At least ~2 years of daily price history required"})
        return {"status":"unavailable","forecast_return":None,"target_price":None,"probability_positive":None,"audit":audit}
    f=features(px).dropna()
    if f.empty:
        audit.update({"status":"unavailable","reason":"Feature history unavailable"})
        return {"status":"unavailable","forecast_return":None,"target_price":None,"probability_positive":None,"audit":audit}
    y=(px.shift(-HORIZON)/px-1).rename("y")
    train=pd.concat([features(px),y],axis=1).dropna()
    if len(train)<150:
        audit.update({"status":"unavailable","reason":"Insufficient completed 12M outcomes"})
        return {"status":"unavailable","forecast_return":None,"target_price":None,"probability_positive":None,"audit":audit}
    pred=model_prediction(train,f.iloc[-1])
    bt=walk_forward(px); diag=diagnostics(bt); prob,pn=calibrated_positive_probability(bt,pred)
    target=spot*(1+pred)
    br=audit["bridge"]
    if br.get("status")=="verified":
        ratio=_num(security_ratio); fx=_num(fx_rate)
        if ratio is None or ratio<=0:
            audit.update({"status":"unavailable","reason":"Verified share-equivalence ratio required for bridged forecast","diagnostics":diag})
            return {"status":"unavailable","forecast_return":None,"target_price":None,"probability_positive":None,"audit":audit}
        if fx is None or fx<=0:
            audit.update({"status":"unavailable","reason":"Verified FX rate required for bridged forecast","diagnostics":diag})
            return {"status":"unavailable","forecast_return":None,"target_price":None,"probability_positive":None,"audit":audit}
        target=target*ratio*fx
        pred=target/spot-1
    confidence="Validation limited"
    if diag["n"]>=30 and diag["direction_accuracy"] is not None and diag["direction_accuracy"]>=.60: confidence="Higher validation"
    elif diag["n"]>=20 and diag["direction_accuracy"] is not None and diag["direction_accuracy"]>=.55: confidence="Moderate validation"
    audit.update({"status":"ready","training_outcomes":int(len(train)),"walk_forward_observations":diag["n"],
                  "probability_calibration_observations":pn,"diagnostics":diag,"validation_label":confidence,
                  "forecast_origin":str(px.index[-1]),"target_formula":"current_price * (1 + forecast_return)"})
    return {"status":"ready","forecast_return":float(pred),"target_price":float(target),
            "probability_positive":prob,"validation_label":confidence,"audit":audit}
