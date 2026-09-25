from pathlib import Path
import ast,re
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_proven_banner_renderer_restored():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '[data-testid="stAppViewContainer"]::before' in s
 assert 'background-image:url(data:image/jpeg;base64,{banner_b64})' in s
 assert 'background-size:100% 108px' in s
 assert 'height:108px;z-index:999990' in s
def test_v2303_banner_disabler_removed():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '[data-testid="stAppViewContainer"]::before{display:none' not in s
 assert 'chr-native-header-v2303' not in s
def test_auth_isolated():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'chr-auth-isolated-v23031' in s
 assert 'href="?chr_auth=signin"' in s
 assert 'href="?chr_auth=register"' in s
 assert 'z-index:1000015' in s
def test_no_streamlit_button_overlay():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'with st.container(key="v23000_banner_auth")' not in s
def test_routes_preserved():
 s=Path("app.py").read_text(encoding="utf-8")
 assert '_chr_auth_q=="signin"' in s and '_chr_auth_q=="register"' in s
 assert 'del st.query_params["chr_auth"]' in s
