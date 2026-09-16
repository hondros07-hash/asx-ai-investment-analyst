
import sqlite3, json, hashlib
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

DB_PATH = Path("v10_research.db")

def conn():
    c=sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS evidence(
      evidence_id TEXT PRIMARY KEY, ticker TEXT, category TEXT, claim TEXT,
      value_text TEXT, direction TEXT, materiality TEXT, horizon TEXT,
      confidence TEXT, source_title TEXT, source_url TEXT, source_type TEXT,
      published_at TEXT, reporting_period TEXT, page TEXT, retrieved_at TEXT,
      thesis_impact TEXT, notes TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS thesis_rules(
      id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, metric TEXT,
      operator TEXT, threshold REAL, unit TEXT, description TEXT, active INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS predictions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, ticker TEXT,
      horizon TEXT, probability REAL, expected_return REAL, model_version TEXT,
      as_of_date TEXT, outcome_return REAL, resolved INTEGER DEFAULT 0)""")
    c.commit()
    return c

def save_evidence(row):
    r=dict(row)
    seed="|".join(str(r.get(k,"")) for k in
                  ["ticker","claim","source_title","published_at","reporting_period"])
    eid=hashlib.sha256(seed.encode()).hexdigest()[:20]
    r["evidence_id"]=eid
    r.setdefault("retrieved_at",datetime.now(timezone.utc).isoformat())
    cols=["evidence_id","ticker","category","claim","value_text","direction","materiality",
          "horizon","confidence","source_title","source_url","source_type","published_at",
          "reporting_period","page","retrieved_at","thesis_impact","notes"]
    vals=[r.get(c) for c in cols]
    with conn() as c:
        c.execute(f"INSERT OR REPLACE INTO evidence ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",vals)
    return eid

def evidence_for(ticker):
    with conn() as c:
        return pd.read_sql_query("SELECT * FROM evidence WHERE ticker=? ORDER BY published_at DESC",
                                 c,params=[ticker.upper()])

def add_thesis_rule(ticker,metric,operator,threshold,unit="",description=""):
    with conn() as c:
        c.execute("""INSERT INTO thesis_rules(ticker,metric,operator,threshold,unit,description)
                     VALUES(?,?,?,?,?,?)""",
                  [ticker.upper(),metric,operator,float(threshold),unit,description])

def thesis_rules(ticker):
    with conn() as c:
        return pd.read_sql_query("SELECT * FROM thesis_rules WHERE ticker=? AND active=1",c,
                                 params=[ticker.upper()])
