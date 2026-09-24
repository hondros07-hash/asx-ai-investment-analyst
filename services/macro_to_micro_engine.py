from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import numpy as np
from services.macro_mapper import get_exposure_matrix

@dataclass(frozen=True)
class MacroExposure:
    ticker: str
    label: str
    unit: str
    channel: str

def exposure_map(ticker:str,sector:str="",industry:str="",country:str="")->List[MacroExposure]:
    matrix=get_exposure_matrix(ticker,sector,industry,country)
    return [MacroExposure(x["tracker"],x["label"],"",x["transmission"]) for x in matrix["exposures"]]

def fetch_close(ticker:str,period:str="1y",interval:str="1d")->pd.Series:
    try:
        import yfinance as yf
        df=yf.Ticker(ticker).history(period=period,interval=interval,auto_adjust=True)
        if df is None or df.empty or "Close" not in df:return pd.Series(dtype=float,name=ticker)
        s=pd.to_numeric(df["Close"],errors="coerce").dropna();s.name=ticker;return s
    except Exception:return pd.Series(dtype=float,name=ticker)

def align_series(stock:pd.Series,macro:pd.Series)->pd.DataFrame:
    if stock is None or stock.empty or macro is None or macro.empty:return pd.DataFrame(columns=["stock","macro"])
    def daily(s):
        out=s.copy();idx=pd.to_datetime(out.index)
        if getattr(idx,"tz",None) is not None:idx=idx.tz_localize(None)
        out.index=idx.normalize();return out.groupby(level=0).last()
    return pd.concat([daily(stock).rename("stock"),daily(macro).rename("macro")],axis=1).sort_index().ffill(limit=5).dropna(subset=["stock","macro"])

def normalize_100(frame:pd.DataFrame)->pd.DataFrame:
    if frame is None or frame.empty:return pd.DataFrame(columns=["stock","macro"])
    out=frame[["stock","macro"]].dropna().copy()
    for col in ("stock","macro"):
        base=float(out[col].iloc[0]);out[col]=(out[col]/base*100.0) if base else np.nan
    return out.dropna()

def macro_by_label(exposures:List[MacroExposure],label:str)->Optional[MacroExposure]:
    for item in exposures:
        if item.label==label:return item
    return exposures[0] if exposures else None
