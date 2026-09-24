import pandas as pd
from services.macro_to_micro_engine import exposure_map,align_series,normalize_100

def test_airline_profile_maps_to_brent_and_fx():
    t=[x.ticker for x in exposure_map("QAN.AX","Industrials","Airlines","Australia")]
    assert "BZ=F" in t and "AUDUSD=X" in t

def test_alignment_and_rebase_are_deterministic():
    i=pd.to_datetime(["2026-01-01","2026-01-02","2026-01-03"]); a=pd.Series([10.,11.,12.],index=i); b=pd.Series([100.,102.,104.],index=i)
    o=normalize_100(align_series(a,b)); assert o.iloc[0]["stock"]==100. and o.iloc[0]["macro"]==100.; assert round(o.iloc[-1]["stock"],2)==120.; assert round(o.iloc[-1]["macro"],2)==104.
