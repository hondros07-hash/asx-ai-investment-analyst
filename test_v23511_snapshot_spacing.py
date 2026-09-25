from pathlib import Path
import ast
s=Path("app.py").read_text()
def test_parse(): ast.parse(s)
def test_heading_gap():
 assert ".v21261-snapshot-heading{font-size:16px;font-weight:950;color:#10264b;margin:2px 0 0;padding-bottom:12px" in s
def test_existing_card_preserved():
 assert ".v21261-card{background:#fff" in s
 assert "View Full Valuation" in s
