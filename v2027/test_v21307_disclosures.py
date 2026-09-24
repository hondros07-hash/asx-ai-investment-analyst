import json, importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('ae',Path(__file__).with_name('announcement_engine.py')); ae=importlib.util.module_from_spec(spec); spec.loader.exec_module(ae)

def test_asx_json_normalization():
    old=ae._get
    payload={'data':{'displayName':'QANTAS AIRWAYS LIMITED','items':[{'announcementType':'SECURITY HOLDER DETAILS','date':'2026-09-22T07:10:00Z','documentKey':'2924-TEST','headline':'Change in substantial holding','isPriceSensitive':False,'url':''}]}}
    ae._get=lambda *a,**k:(json.dumps(payload).encode(),'application/json')
    try:
        df=ae.asx_company_announcements_api('QAN.AX',5)
        assert len(df)==1 and df.iloc[0]['Title']=='Change in substantial holding'
        assert df.iloc[0]['Source']=='ASX company announcements feed'
        assert 'asxCode=QAN' in df.iloc[0]['ReadURL']
    finally: ae._get=old

def test_market_routing():
    assert ae.resolve_announcement_market('QAN.AX')['market']=='ASX'
    assert ae.resolve_announcement_market('META','NMS','United States')['market']=='NASDAQ'
    assert ae.resolve_announcement_market('BHP.L')['market']=='LSE'
    assert ae.resolve_announcement_market('0700.HK')['market']=='HKEX'
    assert ae.resolve_announcement_market('7203.T')['market']=='TSE'
    assert ae.resolve_announcement_market('RY.TO')['market']=='TSX'

def test_sec_normalization():
    old=ae._get
    def fake(url,*a,**k):
        if 'company_tickers_exchange' in url:
            return json.dumps({'fields':['cik','name','ticker','exchange'], 'data':[[1326801,'Meta Platforms, Inc.','META','Nasdaq']]}).encode(),'application/json'
        if 'submissions/CIK0001326801' in url:
            return json.dumps({'name':'Meta Platforms, Inc.','filings':{'recent':{'form':['8-K'],'accessionNumber':['0001326801-26-000001'],'primaryDocument':['meta-20260924.htm'],'filingDate':['2026-09-24']}}}).encode(),'application/json'
        raise AssertionError(url)
    ae._get=fake
    try:
        df=ae.sec_archive('META',5)
        assert len(df)==1 and df.iloc[0]['Type']=='8-K' and 'sec.gov/Archives/edgar/data/1326801/' in df.iloc[0]['URL']
    finally: ae._get=old

def test_view_all_wiring():
    s=Path(__file__).with_name('app.py').read_text()
    assert 'key=f"v21307_nav_ann_{ticker}"' in s
    assert 'on_click=_chr_set_cc_sub_v2111,args=("Announcements & Reports",)' in s
    assert '[class*="st-key-v21307_nav_ann_"] button' in s
    assert 'use_container_width=False' in s
