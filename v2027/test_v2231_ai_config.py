from pathlib import Path
import ast
def test_app_parses(): ast.parse(Path("app.py").read_text(encoding="utf-8"))
def test_streamlit_secret_bridge():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'st.secrets.get("OPENAI_API_KEY"' in s
 assert 'os.environ.get("OPENAI_API_KEY"' in s
 assert 'st.secrets.get("CHRIMATA_BRIEF_MODEL"' in s
 assert '"gpt-5.6-luna"' in s
def test_no_secret_leak_to_public_warning():
 s=Path("app.py").read_text(encoding="utf-8")
 assert 'st.warning(f"AI synthesis unavailable ({_aie})' not in s
 assert "ai_service_not_configured" in s
def test_fastapi_local_env_loader_and_git_safety():
 assert "load_dotenv()" in Path("main.py").read_text(encoding="utf-8")
 g=Path(".gitignore").read_text(encoding="utf-8")
 assert ".env" in g and "!.env.example" in g
def test_no_real_env_packaged():
 assert not Path(".env").exists()
