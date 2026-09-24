import ast
from pathlib import Path
def source(): return Path("app.py").read_text(encoding="utf-8")
def test_compact_fcf_label():
 s=source()
 assert 'return "FCF unavailable"' in s
 assert '_compact_valuation_blocker(_vaudit' in s
def test_full_diagnostic_remains():
 s=source()
 assert 'Live Valuation Diagnostics' in s
 assert 'Blocking reason:' in s
def test_card_hard_clips_overflow():
 s=source()
 assert '.v21269-valuation-card{align-items:flex-start!important;padding:8px 10px!important;min-width:0!important;overflow:hidden!important}' in s
 assert '.v21269-val-move{font-size:10px;font-weight:900;line-height:1.15;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}' in s
def test_card_no_long_raw_blocker_slice():
 assert 'str(_vblock[0])[:42]' not in source()
def test_app_parses():
 ast.parse(source())
