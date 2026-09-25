from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_proven_banner_untouched():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '[data-testid="stAppViewContainer"]::before' in s
 assert 'background-size:100% 108px' in s
 assert 'height:108px;z-index:999990' in s
def test_native_account_bar_exists():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'with st.container(key="v230032_account_bar")' in s
 assert 'st.button("Sign in",key="v230032_signin"' in s
 assert 'st.button("Register",key="v230032_register"' in s
def test_no_html_auth_overlay():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'chr-auth-isolated-v23031' not in s
 assert 'href="?chr_auth=signin"' not in s
 assert 'chr-native-header-v2303' not in s
def test_account_bar_is_compact_and_right_aligned():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'min-height:31px!important' in s
 assert 'justify-content:flex-end!important' in s
 assert 'st.columns([12,1.05,1.15]' in s
def test_routes_preserved():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'st.session_state["chr_auth_route_v23000"]=target' in s
 assert 'if page in {"Sign In","Register"}:' in s
