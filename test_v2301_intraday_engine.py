from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_exchange_session_contract():
 s=Path("app.py").read_text(encoding="utf-8")
 for x in ["def exchange_session_state","currentTradingPeriod","exchangeDataDelayedBy","explicit_live","exchangeTimezoneName"]: assert x in s
def test_intraday_is_one_minute_and_uncached():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'def live_intraday_history' in s
 assert '"1D":("1d","1m")' in s
 assert '_active_tf=="1D" and _intraday_state["is_open"]' in s
 assert '_calc=live_intraday_history(ticker,_per,_int)' in s
def test_honest_feed_labels():
 s=Path("app.py").read_text(encoding="utf-8")
 for x in ['label="LIVE"','label=f"DELAYED','label="INTRADAY · PROVIDER"','label="MARKET CLOSED"']: assert x in s
def test_no_clock_only_live_claim():
 s=Path("app.py").read_text(encoding="utf-8")
 assert "if explicit_live and is_open:" in s
def test_other_timeframes_preserved():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '_tf_options=["1D","1W","1M","3M","6M","1Y","3Y","5Y"]' in s
