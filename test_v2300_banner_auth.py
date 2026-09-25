from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path('app.py').read_text(encoding='utf-8'))
def test_banner_auth_controls():
 s=Path('app.py').read_text(encoding='utf-8')
 assert 'key="v23000_banner_auth"' in s
 assert 'st.button("Sign in"' in s and 'st.button("Register"' in s
 assert 'position:fixed!important;right:22px!important;top:10px!important' in s
 assert '_chr_set_auth_route_v23000' in s
def test_auth_not_faked():
 s=Path('app.py').read_text(encoding='utf-8')
 assert 'Authentication service is not connected yet.' in s
 assert 'disabled=True' in s
