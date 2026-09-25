from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_native_header_and_auth_same_component():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'class="chr-native-header-v2303"' in s
 assert 'class="chr-native-auth-v2303"' in s
 assert 'href="?chr_auth=signin"' in s
 assert 'href="?chr_auth=register"' in s
def test_old_streamlit_auth_overlay_removed():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'with st.container(key="v23000_banner_auth")' not in s
 assert 'st.button("Sign in",key="v23000_signin"' not in s
def test_banner_geometry_preserved():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'height:108px;z-index:1000050' in s
 assert 'background-size:100% 108px' in s
def test_native_route_consumed():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'st.query_params.get("chr_auth")' in s
 assert '_chr_auth_q=="signin"' in s
 assert '_chr_auth_q=="register"' in s
def test_auth_route_cleared_on_navigation():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'if "chr_auth" in st.query_params:' in s
 assert 'del st.query_params["chr_auth"]' in s
