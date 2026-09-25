
import pandas as pd

def select_peers(company_row, universe, sector_col="sector", max_peers=8):
    if sector_col not in universe or sector_col not in company_row:
        return pd.DataFrame()
    peers=universe[universe[sector_col]==company_row[sector_col]].copy()
    if "ticker" in company_row and "ticker" in peers:
        peers=peers[peers.ticker!=company_row["ticker"]]
    if "market_cap" in peers and company_row.get("market_cap"):
        target=float(company_row["market_cap"])
        peers["size_distance"]=(peers["market_cap"].astype(float)/target).apply(
            lambda x: abs(__import__("math").log(max(x,1e-9))))
        peers=peers.sort_values("size_distance")
    return peers.head(max_peers)
