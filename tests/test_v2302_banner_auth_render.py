from pathlib import Path
import ast,re
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_banner_below_auth_layer():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'height:108px;z-index:999990' in s
 assert 'z-index:1000010!important' in s
def test_auth_inside_banner_visible_zone():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'right:24px!important;top:70px!important' in s
 assert '.st-key-v23000_banner_auth{display:block!important;visibility:visible!important;opacity:1!important}' in s
def test_controls_and_routes_preserved():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'st.button("Sign in",key="v23000_signin"' in s
 assert 'st.button("Register",key="v23000_register"' in s
 assert '_chr_set_auth_route_v23000' in s
 assert 'if page in {"Sign In","Register"}:' in s
def test_banner_geometry_unchanged():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'background-size:100% 108px' in s
