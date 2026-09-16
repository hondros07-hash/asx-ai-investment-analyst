# V11.1 — Global Market Terminal

Adds a Markets workspace for ASX, NASDAQ, NYSE and commodities.

With a Twelve Data API key:
- Exchange-filtered stock catalogs use `/stocks`.
- Commodity catalog uses `/commodities`.
- Selected quote tracking uses `/quote`.
- Catalog pagination avoids attempting to render thousands of securities at once.
- Source/timestamp fields are displayed.

Without a key:
- The UI clearly falls back to a curated non-exhaustive universe.
- Yahoo/yfinance prices are explicitly labelled fallback, not exchange-grade real-time.

Production note:
A true all-symbol live terminal should use a central collector/cache/database or licensed streaming backend. It should not make thousands of individual quote requests from Streamlit on every rerun.
