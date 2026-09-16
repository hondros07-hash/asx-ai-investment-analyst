# V11.3 — Company & Multi-Listing Search

The sidebar now accepts either:
- a ticker/code, or
- a company name.

Provider-backed search returns matching listings with company name, symbol, exchange, country and currency where available. Multiple listings are displayed separately so the user chooses the security/exchange they want to analyse.

Examples:
- `QAN.AX` -> resolves ticker and displays company identity.
- `Qantas` -> searches company directory and presents matching listings.
- `Apple` -> presents provider-supported Apple listings.
- A company with multiple supported listings -> each listing appears as a separate selection.

When Twelve Data is unavailable, V11.3 falls back to the project's curated Yahoo/yfinance universe. The fallback is intentionally not described as a complete global security master.
