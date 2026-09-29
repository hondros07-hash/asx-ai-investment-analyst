import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.research_memory_routes import router

app=FastAPI()
app.include_router(router)
client=TestClient(app)

def test_feature_off_by_default(monkeypatch):
    monkeypatch.delenv("AXIA_RESEARCH_MEMORY_ENABLED",raising=False)
    assert client.get("/v1/research-memory/snapshots",params={"security_id":"ZIP.AX"}).status_code==404

def test_no_anonymous_access(monkeypatch):
    monkeypatch.setenv("AXIA_RESEARCH_MEMORY_ENABLED","true")
    assert client.get("/v1/research-memory/snapshots",params={"security_id":"ZIP.AX"}).status_code==401

def test_unconfigured_storage_not_available(monkeypatch):
    monkeypatch.setenv("AXIA_RESEARCH_MEMORY_ENABLED","true")
    monkeypatch.delenv("SUPABASE_URL",raising=False)
    assert client.get("/v1/research-memory/snapshots",params={"security_id":"ZIP.AX"},headers={"Authorization":"Bearer test"}).status_code==503

def test_no_public_write(monkeypatch):
    monkeypatch.setenv("AXIA_RESEARCH_MEMORY_ENABLED","true")
    assert client.post("/v1/research-memory/conditions",json={"security_id":"ZIP.AX","label":"growth","metric":"revenue","operator":">","threshold":1,"period":"FY26"}).status_code==401
