from pathlib import Path
import ast

def test_app_parses():
    ast.parse(Path("app.py").read_text(encoding="utf-8"))

def test_proven_native_strip_preserved():
    s=Path("app.py").read_text()
    assert 'with st.container(key="v2322_market_strip")' in s
    assert '_chr_native_index_cell_v2322(_code)' in s

def test_minimal_account_links_preserve_actions():
    s=Path("app.py").read_text()
    assert 'st.button("Sign in",key="v2322_signin"' in s
    assert 'st.button("Register",key="v2322_register"' in s
    assert 'background:transparent!important' in s
    assert 'content:"|"' in s
    assert 'text-decoration:underline!important' in s

def test_integrated_market_typography():
    s=Path("app.py").read_text()
    assert 'font-size:17px;font-weight:800;color:#102b46' in s
    assert 'border-right:1px solid #d9e3ed' in s
    assert 'min-height:58px!important' in s

def test_no_architecture_regression():
    s=Path("app.py").read_text()
    assert 'price="—" if q["price"] is None' in s
    assert '_chr_header_market_order_v2321()' in s
    assert '[data-testid="stAppViewContainer"]::before' in s
