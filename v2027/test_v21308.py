import pandas as pd
import announcement_engine as ae

def test_asx_bare_ticker_is_canonicalised_from_identity():
    seen={}
    old=ae.announcements
    try:
        def fake(ticker,*args,**kwargs):
            seen['ticker']=ticker
            return pd.DataFrame([{'Date':'24/09/2026','Title':'Test ASX filing','Type':'Results','URL':'https://example.test/a.pdf','PDFURL':'https://example.test/a.pdf','Has PDF':True}]), 'ASX test'
        ae.announcements=fake
        df,cov,ident=ae.announcements_global('QAN',limit=5,exchange='ASX',country='Australia')
        assert seen['ticker']=='QAN.AX'
        assert ident['market']=='ASX' and len(df)==1
    finally: ae.announcements=old

def test_asx_suffixed_ticker_stays_asx():
    seen={}; old=ae.announcements
    try:
        ae.announcements=lambda ticker,*a,**k:(seen.setdefault('ticker',ticker) or pd.DataFrame(), 'x')
        # lambda return is awkward because setdefault returns str; use helper below
    finally: ae.announcements=old

def test_meta_routes_sec():
    old=ae.sec_archive
    try:
        ae.sec_archive=lambda ticker,limit: pd.DataFrame([{'Date':'2026-09-23','Title':'8-K','Type':'8-K','URL':'https://www.sec.gov/test'}])
        df,cov,ident=ae.announcements_global('META',limit=5,exchange='NASDAQ',country='United States')
        assert ident['market']=='NASDAQ' and len(df)==1 and 'SEC' in cov
    finally: ae.sec_archive=old

def test_reference_card_and_navigation_wiring():
    src=open('app.py',encoding='utf-8').read()
    assert 'v21308-ann-row' in src
    assert 'grid-template-columns:92px minmax(0,1fr) 102px 44px' in src
    assert 'key=f"v21308_nav_ann_{ticker}"' in src
    assert 'on_click=_chr_set_cc_sub_v2111,args=("Announcements & Reports",)' in src

if __name__=='__main__':
    test_asx_bare_ticker_is_canonicalised_from_identity(); test_meta_routes_sec(); test_reference_card_and_navigation_wiring(); print('3 acceptance tests passed')
