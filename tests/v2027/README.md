# Chrímata V20.2.6 — Reference Navigation Hard Fix

Removes the deployed phantom header gap and replaces country Streamlit buttons with stable white flag navigation anchors.


## V20.5.9 — Global Corporate Actions Calendar
Upcoming Dividends now uses a forward-calendar provider hierarchy: Twelve Data dividends_calendar when the existing TWELVE_DATA_API_KEY entitlement supports it, optional Financial Modeling Prep via FMP_API_KEY, then Yahoo declared corporate actions as fallback. Only confirmed/declared events are shown; historical dividends are never projected into the future.


## V20.6.2 — Sidebar Subtitle Alignment & AU/US Dividend Engine Repair
- Gold sidebar subtitles share the exact grid text origin with white titles.
- AU/US forward dividend calendars no longer get restricted to the small dashboard universe.
- AU/US provider fallbacks query country, MIC/exchange, then market-wide calendar, then declared per-security events.
