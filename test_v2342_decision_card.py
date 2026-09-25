from pathlib import Path
import ast
s=Path("app.py").read_text()
def test_app_parses(): ast.parse(s)
def test_visible_card():
 assert "v2342-card" in s and "Company Intelligence" in s
 assert "WHAT CHANGED" in s and "WHY IT MATTERS" in s and "WHAT TO WATCH NEXT" in s
 assert "WHAT WOULD CHANGE THE THESIS?" in s
def test_integration():
 assert "EvidenceToThesisEngine" in s and "_v2342_evidence_thesis_engine.integrate" in s
def test_verified_only():
 assert "Never infer exposure from sector alone" in s and "verified company exposure mapping" in s
def test_headline_guardrail():
 assert "A headline is evidence context, not a causal event key." in s
def test_insufficient_evidence_visible():
 assert "INSUFFICIENT EVIDENCE" in s
def test_no_ai_math():
 assert "AI calculated math: False" in s
