# V10.2 — Live Data Foundation

Adds `live_data_provider.py` and a provider-neutral routing layer.

## Current routing
- ASX: Yahoo/yfinance prototype/research fallback
- US equities: Twelve Data when API key is configured
- FX: Twelve Data when API key is configured
- Commodities: Twelve Data when the subscribed plan supports them

## Streamlit setup
In Streamlit app settings, add this secret:
`TWELVE_DATA_API_KEY = "your key"`

Never commit the real key to GitHub.

## Licensing
External/public display rights depend on the data provider and exchange. This build does not bypass exchange licensing. Twelve Data individual plans are intended for personal/internal use; ASX data has additional restrictions.

## Next provider
A licensed ASX adapter can be added behind the same interface without changing the analytical engines.
