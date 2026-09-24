from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import numpy as np

@dataclass(frozen=True)
class MacroExposure:
    ticker: str
    label: str
    unit: str
    channel: str

DEFAULT_EXPOSURES=[MacroExposure("^GSPC","S&P 500","Index","Broad equity-market conditions"),MacroExposure("AUDUSD=X","AUD/USD","USD per AUD","Australian-dollar translation / risk conditions")]
AIRLINE_EXPOSURES=[MacroExposure("BZ=F","Brent Crude Oil","USD/bbl","Fuel-cost exposure"),MacroExposure("AUDUSD=X","AUD/USD","USD per AUD","FX exposure"),MacroExposure("^AXJO","S&P/ASX 200","Index","Australian equity-market conditions")]
BANK_EXPOSURES=[MacroExposure("^AXJO","S&P/ASX 200","Index","Domestic market conditions"),MacroExposure("^TNX","U.S. 10Y Treasury Yield","%","Global rate / discount-rate conditions"),MacroExposure("AUDUSD=X","AUD/USD","USD per AUD","FX / risk conditions")]
MINING_EXPOSURES=[MacroExposure("GC=F","Gold","USD/oz","Commodity-price exposure"),MacroExposure("HG=F","Copper","USD/lb","Industrial-metals exposure"),MacroExposure("AUDUSD=X","AUD/USD","USD per AUD","Revenue/cost translation"),MacroExposure("^AXJO","S&P/ASX 200","Index","Australian market conditions")]
ENERGY_EXPOSURES=[MacroExposure("BZ=F","Brent Crude Oil","USD/bbl","Oil-price exposure"),MacroExposure("NG=F","Natural Gas","USD","Gas-price exposure"),MacroExposure("AUDUSD=X","AUD/USD","USD per AUD","FX exposure")]
TECH_EXPOSURES=[MacroExposure("^IXIC","NASDAQ Composite","Index","Technology-sector risk appetite"),MacroExposure("^TNX","U.S. 10Y Treasury Yield","%","Discount-rate exposure"),MacroExposure("DX-Y.NYB","U.S. Dollar Index","Index","USD / global financial conditions")]

def exposure_map(ticker:str,sector:str="",industry:str="",country:str="")->List[MacroExposure]:
    text=" ".join([str(ticker),str(sector),str(industry),str(country)]).lower()
    if any(k in text for k in ("airline","aviation","air transport","qantas")): return AIRLINE_EXPOSURES
    if any(k in text for k in ("bank","financial services","diversified banks","regional banks")): return BANK_EXPOSURES
    if any(k in text for k in ("mining","miner","metals","materials","gold","copper","resources")): return MINING_EXPOSURES
    if any(k in text for k in ("energy","oil","gas","petroleum")): return ENERGY_EXPOSURES
    if any(k in text for k in ("technology","software","semiconductor","internet","interactive media")): return TECH_EXPOSURES
    return DEFAULT_EXPOSURES

def fetch_close(ticker:str,period:str="1y",interval:str="1d")->pd.Series:
    try:
        import yfinance as yf
        df=yf.Ticker(ticker).history(period=period,interval=interval,auto_adjust=True)
        if df is None or df.empty or "Close" not in df: return pd.Series(dtype=float,name=ticker)
        s=pd.to_numeric(df["Close"],errors="coerce").dropna(); s.name=ticker; return s
    except Exception: return pd.Series(dtype=float,name=ticker)

def align_series(stock:pd.Series,macro:pd.Series)->pd.DataFrame:
    if stock is None or stock.empty or macro is None or macro.empty: return pd.DataFrame(columns=["stock","macro"])
    def daily(s):
        out=s.copy(); idx=pd.to_datetime(out.index)
        if getattr(idx,"tz",None) is not None: idx=idx.tz_localize(None)
        out.index=idx.normalize(); return out.groupby(level=0).last()
    return pd.concat([daily(stock).rename("stock"),daily(macro).rename("macro")],axis=1).sort_index().ffill(limit=5).dropna(subset=["stock","macro"])

def normalize_100(frame:pd.DataFrame)->pd.DataFrame:
    if frame is None or frame.empty: return pd.DataFrame(columns=["stock","macro"])
    out=frame[["stock","macro"]].dropna().copy()
    for col in ("stock","macro"):
        base=float(out[col].iloc[0]); out[col]=(out[col]/base*100.0) if base else np.nan
    return out.dropna()

def macro_by_label(exposures:List[MacroExposure],label:str)->Optional[MacroExposure]:
    for item in exposures:
        if item.label==label: return item
    return exposures[0] if exposures else None
