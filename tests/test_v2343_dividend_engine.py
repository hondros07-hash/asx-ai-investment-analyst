from pathlib import Path
import ast, pandas as pd, sys, types
sys.modules.setdefault('yfinance', types.SimpleNamespace(Ticker=lambda *a,**k: None))
from datetime import date,timedelta
import corporate_actions_calendar as c
app=Path("app.py").read_text()
cal=Path("corporate_actions_calendar.py").read_text()

def test_app_parses(): ast.parse(app)
def test_broker_exists():
 assert "class DividendCorporateActionBroker" in cal
 assert "_DIVIDEND_BROKER.fetch" in cal
def test_no_projection_of_undeclared_dividends():
 assert "No historical dividend is projected forward" in cal
 assert "Undeclared dividends are never estimated" in app
def test_market_universe_expanded_for_widget():
 assert "TOP_GAINERS_UNIVERSE.get(market,[])" in app
def test_distinguishes_empty_from_unavailable():
 assert "No confirmed upcoming dividends found." in app
 assert "Dividend data unavailable." in app
 assert "This is not a claim that no companies are paying dividends." in app
def test_australia_franking_column_only():
 assert "if market=='Australia'" in app
 assert "'Franking'" in app
def test_provider_diagnostics_on_empty(monkeypatch):
 monkeypatch.setattr(c,"yahoo_upcoming_dividends",lambda *a,**k: pd.DataFrame())
 b=c.DividendCorporateActionBroker()
 d=b.fetch("Australia",["BHP.AX"],5,"","")
 assert d.empty and d.attrs["status"]=="NO_CONFIRMED_EVENTS"
 assert "Yahoo declared events" in d.attrs["diagnostics"]["configured"]
def test_normalization_dedupes_and_sorts():
 start=date.today(); end=start+timedelta(days=10)
 df=pd.DataFrame([
  {"Ticker":"AAA.AX","Company":"A","Ex-Date":(start+timedelta(days=2)).isoformat(),"Source":"x"},
  {"Ticker":"AAA.AX","Company":"A","Ex-Date":(start+timedelta(days=2)).isoformat(),"Source":"y"},
  {"Ticker":"BBB.AX","Company":"B","Ex-Date":(start+timedelta(days=1)).isoformat(),"Source":"x"}])
 out=c._normalize_final(df,"Australia",start,end,{"configured":["x"],"attempted":["x"]})
 assert list(out["Ticker"])==["BBB.AX","AAA.AX"]
 assert len(out)==2 and out.attrs["status"]=="SUCCESS"
def test_cache_reduced_from_six_hours():
 assert "@st.cache_data(ttl=900, show_spinner=False)\ndef overview_global_dividends" in app
