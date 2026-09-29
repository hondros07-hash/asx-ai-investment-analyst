from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.personal_research_routes import router

app=FastAPI();app.include_router(router);client=TestClient(app)
def test_disabled_by_default(monkeypatch):
 monkeypatch.delenv("AXIA_RESEARCH_MEMORY_ENABLED",raising=False)
 assert client.get("/v1/research-journal/entries",params={"security_id":"ZIP.AX"}).status_code==404
def test_anonymous_cannot_read(monkeypatch):
 monkeypatch.setenv("AXIA_RESEARCH_MEMORY_ENABLED","true")
 assert client.get("/v1/research-journal/timeline",params={"security_id":"ZIP.AX"}).status_code==401
def test_anonymous_cannot_write(monkeypatch):
 monkeypatch.setenv("AXIA_RESEARCH_MEMORY_ENABLED","true")
 assert client.post("/v1/research-journal/entries",json={"security_id":"ZIP.AX","entry_type":"note","title":"Test","body":"Private"}).status_code==401
