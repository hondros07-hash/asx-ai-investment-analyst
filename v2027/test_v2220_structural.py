import ast
from pathlib import Path
def test_brief():
 s=Path("services/brief_engine.py").read_text(encoding="utf-8"); ast.parse(s)
 for x in ["assemble_evidence_packet","generate_research_brief","asyncio.gather","client.responses.create","ai_calculated","ai_summarized","insufficient_evidence"]: assert x in s
def test_guardrails():
 s=Path("services/brief_engine.py").read_text(encoding="utf-8").lower()
 for x in ["use only facts","never perform new financial calculations","investment recommendation","untrusted data"]: assert x in s
def test_route():
 s=Path("main.py").read_text(encoding="utf-8"); ast.parse(s)
 assert "/api/v1/widget/research-brief" in s and 'version="22.2.0"' in s
