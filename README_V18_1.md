# V18.1 — Company Snapshot Header

Adds a reusable company identity/market snapshot to Company Command Centre.

Includes:
- company logo when metadata/website favicon is available; initials fallback otherwise
- company name, ticker, exchange, sector and industry
- latest loaded price and daily move
- volume, market cap, P/E, dividend yield and 1-year return
- graphical 52-week range with current-price marker
- shares outstanding, exchange and latest loaded session
- Add to Watchlist and alert shortcut buttons
- explicit market-data provenance label

The header is generic and is not hard-coded for ZIP.AX.
Missing metadata renders as an em dash instead of inventing a value.

Retains V18.0.5 Streamlit magic-render fix, V18.0.3 responsive price display,
and V18.0.2 schema migrations.

Deployment diagnostic:
V18.1 • Market Investment Analyst • company snapshot header
