import ast
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import announcement_engine as ae
from services.company_intelligence_engine import orchestrate_company_synthesis

ROOT=Path(__file__).parent
SRC=(ROOT/'app.py').read_text()

def test_layout_and_navigation():
    assert 'st-key-v2373_cat_card_' in SRC
    assert 'v21290-viewall">View all' not in SRC
    assert 'View all catalysts",key=' not in SRC
    assert '.v21313-news-row .main a{display:block;max-width:100%;overflow:hidden;text-overflow:ellipsis' in SRC
    assert 'Company Intelligence · evidence diagnostics' in SRC
    assert 'margin-bottom:1.25rem!important' in SRC

def test_sec_requires_real_contact():
    with patch.dict('os.environ', {'SEC_USER_AGENT':''}):
        with patch.object(ae,'_get',side_effect=AssertionError('must not request')):
            result=ae.sec_archive_gateway('KO')
    assert result.empty and result.attrs['status']=='SEC_USER_AGENT_REQUIRED'

def test_sec_parses_issuer_and_filing():
    import json
    mapping={'fields':['cik','name','ticker','exchange'],'data':[[21344,'Coca-Cola','KO','NYSE']]}
    submissions={'name':'THE COCA-COLA COMPANY','tickers':['KO'], 'filings':{'recent':{'form':['10-K'], 'accessionNumber':['0000021344-26-000001'],'primaryDocument':['ko10k.htm'],'filingDate':['2026-02-01']}}}
    def fake_get(url,*args,**kwargs):
        return (json.dumps(mapping if 'company_tickers_exchange' in url else submissions).encode(),'application/json')
    with patch.dict('os.environ',{'SEC_USER_AGENT':'AXIA research research@example.org'}),patch.object(ae,'_get',side_effect=fake_get):
        df=ae.sec_archive_gateway('KO')
    assert len(df)==1 and df.attrs['status']=='SUCCESS'
    assert 'sec.gov/Archives/' in df.iloc[0]['ReadURL']

def test_sec_rejects_mismatched_issuer():
    import json
    mapping={'fields':['cik','name','ticker','exchange'],'data':[[21344,'Coca-Cola','KO','NYSE']]}
    submissions={'tickers':['NOTKO'],'filings':{'recent':{}}}
    def fake_get(url,*args,**kwargs):
        return (json.dumps(mapping if 'company_tickers_exchange' in url else submissions).encode(),'application/json')
    with patch.dict('os.environ',{'SEC_USER_AGENT':'AXIA research research@example.org'}),patch.object(ae,'_get',side_effect=fake_get):
        df=ae.sec_archive_gateway('KO')
    assert df.attrs['status']=='IDENTITY_MISMATCH'

def test_intelligence_no_headline_only_promotion():
    result=orchestrate_company_synthesis('KO',raw_event={'source_type':'news','event_key':'credit_loss_rate','verified':True,'source':'news','evidence_id':'abc'})
    assert result['status']=='insufficient_evidence'
