import sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import announcement_engine as ae

ASX_FIXTURE='''<html><table><tr><td>22/09/2026<br>5:10 pm</td><td></td><td><a href="/asxpdf/20260922/pdf/abc123.pdf">Change in substantial holding</a> 476 pages 3.1MB</td></tr><tr><td>14/09/2026<br>8:30 am</td><td>price sensitive</td><td><a href="/asxpdf/20260914/pdf/def456.pdf">FY26 Full Year Results</a> 42 pages 2.0MB</td></tr></table></html>'''

def test_asx_parser_rows_and_links():
    rows=ae._parse_asx(ASX_FIXTURE,'QAN')
    assert len(rows)==2
    assert rows[0]['Title']=='Change in substantial holding'
    assert rows[0]['URL'].startswith('https://www.asx.com.au/asxpdf/')
    assert rows[1]['Type']=='Results'

def test_global_routing():
    assert ae.resolve_announcement_market('QAN.AX','ASX','Australia')['market']=='ASX'
    assert ae.resolve_announcement_market('META','NASDAQ','United States')['market']=='NASDAQ'
    assert ae.resolve_announcement_market('VOD.L','LSE','United Kingdom')['market']=='LSE'
    assert ae.resolve_announcement_market('0700.HK','HKEX','Hong Kong')['market']=='HKEX'
    assert ae.resolve_announcement_market('7203.T','TSE','Japan')['market']=='TSE'
    assert ae.resolve_announcement_market('SHOP.TO','TSX','Canada')['market']=='TSX'

def test_sec_submissions_normalization(monkeypatch):
    mapping={'fields':['cik','name','ticker','exchange'],'data':[[1326801,'Meta Platforms, Inc.','META','Nasdaq']]}
    submission={'name':'Meta Platforms, Inc.','filings':{'recent':{'form':['10-Q','8-K'],'accessionNumber':['0001326801-26-000001','0001326801-26-000002'],'primaryDocument':['meta-20260930.htm','meta-8k.htm'],'filingDate':['2026-09-20','2026-09-18']}}}
    def fake_get(url,headers=None,timeout=25):
        if 'company_tickers_exchange' in url: return json.dumps(mapping).encode(),'application/json'
        if 'submissions/CIK' in url: return json.dumps(submission).encode(),'application/json'
        raise AssertionError(url)
    monkeypatch.setattr(ae,'_get',fake_get)
    df=ae.sec_archive('META',5)
    assert len(df)==2 and df.attrs['status']=='OK'
    assert df.iloc[0]['Type']=='10-Q'
    assert 'sec.gov/Archives/edgar/data/1326801/' in df.iloc[0]['URL']

def test_view_all_is_deterministic_source():
    src=(Path(__file__).resolve().parents[1]/'app.py').read_text()
    assert 'key=f"v21306_nav_ann_{ticker}"' in src
    assert '_chr_set_cc_sub_v2111("Announcements & Reports")' in src
    assert 'st.rerun()' in src
    fn=src[src.index('def _chr_set_cc_sub_v2111'):src.index('st.sidebar.markdown',src.index('def _chr_set_cc_sub_v2111'))]
    assert 'chr_primary_nav' in fn and 'chr_cc_page' in fn and 'chr_compare' in fn
