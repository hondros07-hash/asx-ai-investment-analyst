from pathlib import Path
import ast
from services.company_intelligence_engine import orchestrate_company_synthesis

ROOT=Path(__file__).resolve().parent
SRC=(ROOT/'app.py').read_text()

def test_app_compiles(): ast.parse(SRC)
def test_news_context_is_not_verified_event():
    result=orchestrate_company_synthesis('KO',raw_event={'source_type':'news','what_changed':'headline'},exposures=[])
    assert result['status']=='insufficient_evidence'
def test_sec_secrets_bridge():
    assert 'st.secrets.get("SEC_USER_AGENT"' in SRC
    assert 'os.environ["SEC_USER_AGENT"]=_sec_ua' in SRC
def test_news_has_two_column_layout_and_separate_source():
    assert 'grid-template-columns:56px minmax(0,1fr)' in SRC
    assert '.v21313-news-row .meta{grid-column:2;' in SRC
def test_news_context_and_diagnostics_are_separate():
    assert '_orchestrated["news_context"]=_headlines' in SRC
    assert '"NEWS CONTEXT ONLY"' in SRC
    assert 'expanded=False' in SRC
