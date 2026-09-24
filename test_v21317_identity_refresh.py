from services.security_identity import canonicalize_security, safe_classification, validate_identity, CACHE_TTL

def test_nike_primary_identity_is_name_based_not_price_based():
    r=canonicalize_security('NKE.TO','NIKE, Inc.')
    assert r['ticker']=='NKE' and r['changed'] is True and r['reason']=='verified_primary_listing'

def test_unknown_international_listing_is_not_rewritten():
    r=canonicalize_security('ABC.TO','ABC Mining Limited')
    assert r['ticker']=='ABC.TO' and r['changed'] is False

def test_metadata_cascade_and_no_fake_nike_defaults():
    r=safe_classification({'category':'Industrials'},{'industry':'Railroads'})
    assert r=={'sector':'Industrials','industry':'Railroads'}
    z=safe_classification({}, {})
    assert z['sector']=='Sector unavailable' and z['industry']=='Industry unavailable'

def test_identity_mismatch_is_detected():
    r=validate_identity('NKE.TO','NIKE, Inc.',{'longName':'Different Canadian Company','currency':'CAD'})
    assert r['valid'] is False

def test_refresh_tiers_separate_fast_and_slow_data():
    assert CACHE_TTL['fast']==60
    assert CACHE_TTL['medium']>=300
    assert CACHE_TTL['slow']>=21600
