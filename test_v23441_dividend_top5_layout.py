from pathlib import Path
import ast
app=Path("app.py").read_text()
js=Path("frontend/components/UpcomingDividendsGrid.js").read_text()
api=Path("services/dividend_api.py").read_text()

def test_app_parses(): ast.parse(app)
def test_streamlit_next_five():
 assert 'sort_values(["_sort_ex","Ticker"],na_position="last").head(5)' in app
def test_diagnostic_banner_removed():
 assert "Confirmed declared events ·" not in app
 assert "chr-div-evidence" not in app
 assert "15-minute cache" not in js
 assert "Sources:" not in js
def test_streamlit_footer_anchored_bottom():
 assert ".chr-grid-bottom>.chr-panel>footer{margin-top:auto!important}" in app
def test_react_top_five_sorted():
 assert '.sort((a,b)=>String(a.ex_date||"9999").localeCompare(String(b.ex_date||"9999"))).slice(0,5)' in js
def test_react_view_all_is_bottom_footer():
 assert 'mt-auto flex justify-end' in js
 assert 'View all dividends →' in js
def test_api_preserves_full_calendar_for_view_all():
 assert '"dividend_calendar":rows' in api
 assert "head(5)" not in api
