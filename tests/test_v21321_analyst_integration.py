from pathlib import Path
def test_overview_uses_engine_return():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '_aup=_mia_num(_ccanalyst.get("percentage_return"))' in s
def test_single_service_for_overview():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '_ccanalyst=analyst_consensus_snapshot(ticker,price)' in s
def test_evidence_ui():
 assert 'with st.expander("Provider evidence ⓘ"' in Path("app.py").read_text(encoding="utf-8")
