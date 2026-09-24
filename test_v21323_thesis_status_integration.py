from pathlib import Path
def src():return Path("app.py").read_text(encoding="utf-8")
def test_engine_imported():assert "from services.thesis_status_engine import calculate_thesis_status" in src()
def test_compact_card_uses_aggregator():
 s=src(); assert "_th_summary=calculate_thesis_status(_th_monitor" in s
def test_semantic_card_lines():
 s=src()
 assert 'conditions on track"' in s and 'awaiting evidence"' in s
 assert 'watch items"' not in s
def test_no_thesis_ellipsis():
 s=src()
 assert ".v21278-thesis-value{font-size:clamp" in s
 assert "white-space:normal;overflow-wrap:anywhere" in s
def test_full_page_uses_same_aggregator():
 assert "_ts_summary=calculate_thesis_status(_ts_existing" in src()
