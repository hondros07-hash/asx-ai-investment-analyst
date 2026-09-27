from datetime import datetime,timezone
from services.catalyst_intelligence_engine import build_catalyst_preview

NOW=datetime(2026,9,27,tzinfo=timezone.utc)
def test_unverified_confirmed_is_downgraded():
    rows=[{"ticker":"ZIP.AX","event":"Quarterly report","event_date":"2026-10-15","evidence_status":"confirmed"}]
    out=build_catalyst_preview("ZIP.AX",rows,now=NOW)
    assert out[0]["date_status"]=="estimated"
def test_ticker_and_duplicate_guard():
    rows=[{"ticker":"ZIP.AX","event":"Annual results","event_date":"2026-11-01"},
          {"ticker":"ZIP.AX","event":"Annual results","event_date":"2026-11-01"},
          {"ticker":"BHP.AX","event":"Annual results","event_date":"2026-11-01"}]
    assert len(build_catalyst_preview("ZIP.AX",rows,now=NOW))==1
def test_no_invented_date():
    out=build_catalyst_preview("ZIP.AX",[{"event":"Potential approval","date":"TBD"}],now=NOW)
    assert out[0]["event_date"] is None
    assert out[0]["date_status"]=="potential"
def test_date_revision_preserved():
    rows=[{"event":"AGM","date":"2026-11-01","previous_date":"2026-10-15"}]
    assert build_catalyst_preview("ZIP.AX",rows,now=NOW)[0]["date_revised"]
