
import sqlite3, json
from datetime import datetime, timezone
import pandas as pd

DB="v10_research.db"

def register_model(version,horizon,features,validation_metrics,test_metrics):
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS model_registry(
          version TEXT,horizon TEXT,created_at TEXT,features TEXT,
          validation_metrics TEXT,test_metrics TEXT,
          PRIMARY KEY(version,horizon))""")
        c.execute("""INSERT OR REPLACE INTO model_registry VALUES(?,?,?,?,?,?)""",
          [version,horizon,datetime.now(timezone.utc).isoformat(),
           json.dumps(features),json.dumps(validation_metrics),json.dumps(test_metrics)])

def registry():
    with sqlite3.connect(DB) as c:
        try:return pd.read_sql_query("SELECT * FROM model_registry ORDER BY created_at DESC",c)
        except:return pd.DataFrame()

def drift_flag(recent_brier,baseline_brier,tolerance=.15):
    if baseline_brier is None or recent_brier is None:return "UNKNOWN"
    return "DRIFT WARNING" if recent_brier > baseline_brier*(1+tolerance) else "OK"
