"""V24.2 workspace API contract tests without live provider calls."""
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app
client=TestClient(app)

def test_markets_cover_seven_supported_exchanges():
 from api.workspace_routes import MARKETS
 assert set(MARKETS)=={"ASX","NASDAQ","NYSE","LSE","HKEX","TSE","TSX"}

def test_screen_requires_query_and_does_not_invent_results():
 response=client.get("/v1/workspace/screen?market=ASX")
 assert response.status_code==200
 assert response.json()["results"]==[]
 assert response.json()["status"]=="query_required"

def test_unknown_market_rejected():
 assert client.get("/v1/workspace/screen?market=OTHER&q=bank").status_code==422

def test_quote_rejects_invalid_ticker():
 assert client.get("/v1/workspace/quote/BAD!").status_code==422

def test_unavailable_market_quote_is_explicit():
 from api.workspace_routes import MARKETS
 with patch("api.workspace_routes._provider",return_value=[{"market":m,"price":None,"status":"unavailable"} for m in MARKETS]):
  response=client.get("/v1/workspace/markets")
 assert response.status_code==200
 assert response.json()["live"] is False
 assert all(row["price"] is None for row in response.json()["markets"])
