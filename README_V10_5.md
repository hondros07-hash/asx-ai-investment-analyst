# V10.5 — Candlestick Chart Upgrade

Adds candlestick charting to the V10.4 ASX/NASDAQ/NYSE market dashboard.

## Chart modes
- Line
- Candlestick (OHLC)

## Existing ranges retained
1D, 3D, 5D, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y, MAX.

## Candlestick features
- Open / High / Low / Close candles
- Green rising candles and red falling candles
- OHLC hover information
- SMA 20 / 50 / 200 overlays
- Volume display retained
- Intraday candles on short periods when provider data is available
- Range slider disabled for a cleaner terminal-style display

Percentage and benchmark comparison views intentionally remain line charts because
normalized returns are the appropriate comparison format.

Data freshness and candle resolution depend on the active market-data provider.
