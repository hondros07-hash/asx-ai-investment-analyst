from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_compact_shared_height():
 s=Path("app.py").read_text(encoding="utf-8")
 assert "_overview_widget_height=430" in s
 assert "_price_chart_widget_height=_overview_widget_height" in s
 assert 'height=_price_chart_widget_height,key="v21243_price_card"' in s
 assert 'height=_overview_widget_height,key="v21255_thesis_card"' in s
 assert 'height=_overview_widget_height,key="v21257_ai_card"' in s
