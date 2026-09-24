from pathlib import Path
import pandas as pd
import announcement_engine as ae

def test_gateway_routes_asx_bare_identity():
    old=ae.announcements
    try:
        def fake(ticker,*a,**k):
            assert ticker=='QAN.AX'
            return pd.DataFrame([{'Date':'24/09/2026','Title':'Annual Report','URL':'https://www.asx.com.au/x','Has PDF':False}]),'ASX Market Announcements'
        ae.announcements=fake
        df,cov,ident=ae.official_disclosure_gateway('QAN',limit=5,exchange='ASX')
        assert ident['market']=='ASX' and len(df)==1 and df.attrs['status']=='SUCCESS'
    finally: ae.announcements=old

def test_sec_gateway_has_two_official_identity_routes():
    src=Path('announcement_engine.py').read_text()
    assert 'company_tickers_exchange.json' in src
    assert 'browse-edgar' in src and 'output":"atom' in src
    assert 'data.sec.gov/submissions/CIK' in src

def test_overview_and_full_page_share_gateway():
    src=Path('app.py').read_text()
    assert src.count('official_disclosure_gateway(')>=2
    assert 'background:#fff!important' in src
    assert 'v21310-ann-source' in src

if __name__=='__main__':
    test_gateway_routes_asx_bare_identity(); test_sec_gateway_has_two_official_identity_routes(); test_overview_and_full_page_share_gateway()
    print('V21.3.12 acceptance: 3/3 passed')
