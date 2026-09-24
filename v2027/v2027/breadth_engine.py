
import pandas as pd
def market_breadth(close_frame):
    sma50=close_frame.rolling(50).mean()
    sma200=close_frame.rolling(200).mean()
    return pd.DataFrame({
      "pct_above_50d":(close_frame>sma50).mean(axis=1),
      "pct_above_200d":(close_frame>sma200).mean(axis=1),
      "advance_ratio":(close_frame.pct_change()>0).mean(axis=1)
    })
