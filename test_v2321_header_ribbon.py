from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_ribbon_and_auth():
 s=Path("app.py").read_text()
 assert ("_account_ribbon,_account_signin,_account_register" in s or 'with st.container(key="v2322_market_strip")' in s)
 assert ('st.button("Sign in",key="v230032_signin"' in s or 'st.button("Sign in",key="v2322_signin"' in s)
 assert ('st.button("Register",key="v230032_register"' in s or 'st.button("Register",key="v2322_register"' in s)
def test_data_integrity():
 s=Path("app.py").read_text()
 assert 'price="—" if q["price"] is None' in s and "st.cache_data(ttl=60" in s
def test_geo_responsive_and_api():
 s=Path("app.py").read_text(); a=Path("api_gateway.py").read_text()
 assert '"GR":("ATHEX","GD.AT","🇬🇷")' in s and "@media(max-width:700px)" in s
 assert '@app.get("/api/v1/header-markets")' in a and "broadcast_cache.get(code)" in a
