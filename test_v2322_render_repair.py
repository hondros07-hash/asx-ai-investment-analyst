from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_native_market_strip_is_first_class():
 s=Path("app.py").read_text()
 assert 'with st.container(key="v2322_market_strip")' in s
 assert '_m1,_m2,_m3,_m4,_m5,_signin,_register=st.columns' in s
 assert '_chr_native_index_cell_v2322(_code)' in s
def test_old_failed_account_row_removed():
 s=Path("app.py").read_text()
 assert 'with st.container(key="v230032_account_bar")' not in s
def test_auth_actions_preserved_in_new_strip():
 s=Path("app.py").read_text()
 assert 'st.button("Sign in",key="v2322_signin"' in s
 assert 'st.button("Register",key="v2322_register"' in s
 assert 'args=("Sign In",)' in s and 'args=("Register",)' in s
def test_fallback_missing_values_and_geo():
 s=Path("app.py").read_text()
 assert 'price="—" if q["price"] is None' in s
 assert '_chr_header_market_order_v2321()' in s
def test_banner_not_changed():
 s=Path("app.py").read_text()
 assert '[data-testid="stAppViewContainer"]::before' in s
 assert 'height:108px;z-index:999990' in s
