
import sqlite3, pandas as pd
DB="v10_research.db"
def init():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS watchlist(
        ticker TEXT PRIMARY KEY, thesis TEXT, added_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
def add(ticker,thesis=""):
    init()
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR REPLACE INTO watchlist(ticker,thesis) VALUES(?,?)",[ticker.upper(),thesis])
def remove(ticker):
    init()
    with sqlite3.connect(DB) as c:c.execute("DELETE FROM watchlist WHERE ticker=?",[ticker.upper()])
def get():
    init()
    with sqlite3.connect(DB) as c:return pd.read_sql_query("SELECT * FROM watchlist ORDER BY added_at DESC",c)
