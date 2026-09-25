import numpy as np, pandas as pd
from services.technical_engine import core_indicator_frame,calculate_technical_snapshot
def hist(n=260,trend=1):
    idx=pd.date_range("2025-01-01",periods=n,freq="B")
    c=pd.Series(100+trend*np.arange(n)*.2+np.sin(np.arange(n)/5),index=idx)
    return pd.DataFrame({"Open":c-.2,"High":c+.5,"Low":c-.5,"Close":c,"Volume":1_000_000+np.arange(n)*100},index=idx)
def test_core_indicators_exist():
    t=core_indicator_frame(hist()); assert all(x in t for x in ["RSI","SMA 20","SMA 50","SMA 200","MACD","MACD Signal","ATR","Volume Ratio"])
def test_rsi_bounded():
    r=calculate_technical_snapshot(hist())["rsi_value"]; assert 0<=r<=100
def test_full_history_has_full_directional_coverage():
    r=calculate_technical_snapshot(hist()); assert r["evidence_coverage"]==100
def test_short_history_does_not_fail_missing_200d():
    r=calculate_technical_snapshot(hist(80)); assert r["signals"]["sma_200"]["state"]=="Pending" and r["evidence_coverage"]<100
def test_no_history_is_pending():
    r=calculate_technical_snapshot(pd.DataFrame()); assert r["technical_status"]=="Pending" and r["evidence_coverage"]==0
def test_no_ai_calculation():
    r=calculate_technical_snapshot(hist()); assert r["calculation"]=="deterministic_python" and r["ai_calculated"] is False
