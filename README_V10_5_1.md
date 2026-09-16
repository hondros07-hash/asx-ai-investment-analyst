# V10.5.1 Hotfix

Fixes two related issues introduced with multi-market support:

1. `detect_market()` no longer assumes the supplied yfinance metadata is always a Python dict.
2. Bare US tickers such as `KO`, `AAPL`, `JPM` and `NVDA` are resolved by checking actual price history first, instead of relying on `fast_info.get()`.
3. If a bare ticker does not resolve as a US/global symbol, V10.5.1 then tries the `.AX` ASX suffix.
4. Market metadata failure is non-fatal and can no longer crash the dashboard.

Explicit ASX symbols such as `ZIP.AX` continue to work.
