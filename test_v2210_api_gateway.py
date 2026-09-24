from pathlib import Path
import ast
def test_main_parses(): ast.parse(Path("main.py").read_text(encoding="utf-8"))
def test_gateway_parses(): ast.parse(Path("api_gateway.py").read_text(encoding="utf-8"))
def test_routes_declared():
 s=Path("main.py").read_text(encoding="utf-8")
 for p in ["/api/v1/widget/scorecard","/api/v1/widget/valuation","/api/v1/widget/technicals","/api/v1/widget/consensus","/api/v1/widget/forecast","/health"]:
  assert p in s
def test_decoupled_from_streamlit():
 assert "streamlit" not in Path("main.py").read_text(encoding="utf-8").lower()
 assert "streamlit" not in Path("api_gateway.py").read_text(encoding="utf-8").lower()
def test_production_controls():
 s=Path("main.py").read_text(encoding="utf-8")
 assert "run_in_threadpool" in s
 assert "CHRIMATA_CORS_ORIGINS" in s
 assert "_native" in s and "_ticker" in s
