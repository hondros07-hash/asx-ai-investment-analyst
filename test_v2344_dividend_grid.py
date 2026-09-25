from pathlib import Path
import ast
main=Path('main.py').read_text(); svc=Path('services/dividend_api.py').read_text(); api=Path('frontend/lib/api.js').read_text(); grid=Path('frontend/components/UpcomingDividendsGrid.js').read_text(); view=Path('frontend/components/views/DividendIntelligence.js').read_text(); router=Path('frontend/components/DashboardRouter.js').read_text(); broker=Path('corporate_actions_calendar.py').read_text()
def test_python_parses(): ast.parse(main); ast.parse(svc); ast.parse(broker)
def test_fastapi_endpoint(): assert '/api/v1/corporate-actions/dividends' in main and 'dividend_calendar_payload' in main
def test_contract():
 for x in ['ticker','company','ex_date','pay_date','amount','currency','dividend_type','franking','source','verified']: assert f'"{x}"' in svc
def test_all_markets():
 for x in ['"AU"','"US"','"GB"','"JP"','"HK"','"CA"','"GR"']: assert x in svc
def test_frontend_fetch(): assert 'fetchDividendCalendar' in api and '/api/v1/corporate-actions/dividends' in api
def test_grid_states():
 for x in ['Dividend data unavailable','No confirmed upcoming dividends found','Confirmed ex-dates','AI calculated math: False']: assert x in grid
def test_backend_currency_not_country_guess(): assert 'row?.currency' in grid and 'Intl.NumberFormat' in grid
def test_au_franking_conditional(): assert 'marketRegion.toUpperCase()==="AU"' in grid and 'Franking' in grid
def test_market_tabs_and_router(): assert "['AU','Australia']" in view and 'dividends' in router and 'DividendIntelligence' in router
def test_fmp_marketwide_venue_recovery(): assert '_venue_belongs(market,x.get("mic_code"),x.get("exchange")) or _belongs' in broker
def test_no_fake_dividend_rows(): assert 'BHP Group Limited' not in grid and 'Commonwealth Bank' not in grid
def test_cache_contract(): assert '"cache_seconds":900' in svc
