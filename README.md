# Chrímata V20.3.0 — Market Overview Flag Header

Adds the selected country’s real embedded flag artwork directly before the Market Overview title while retaining same-tab country navigation.

# Chrímata V20.2.7 — Reference Navigation Hard Fix

Removes the deployed phantom header gap and replaces country Streamlit buttons with stable white flag navigation anchors.


V20.2.7: Windows-safe embedded SVG country flags and same-tab native Streamlit market switching.


## V20.3.0
- Fixes full-page landing dashboard scrolling so the bottom widgets remain reachable.
- Market overview quote cache reduced to 60 seconds.
- Headline quotes prefer Twelve Data when `TWELVE_DATA_API_KEY` is configured, with Yahoo/yfinance fallback.
- Main market chart now requests 5-minute intraday bars for the current session.
- Preserves V20.2.8 country flags, same-tab navigation, banner and sidebar.

Real-time entitlement depends on the configured provider/exchange subscription; delayed feeds remain delayed.


## V20.3.0
- Dynamic market clock refreshes every second using a Streamlit fragment.
- Market quote and mover caches refresh every 60 seconds while the Home dashboard is open.
- Live/data-updated timestamp distinguishes clock time from provider quote freshness.
- Existing market-provider entitlements still determine whether quotes are real-time or delayed.

## V20.3.1 — Interactive Market Cards
- Click any top market card to load that instrument into the large chart panel.
- Selected card receives a blue active outline.
- Chart title, latest price and direction update with the selected instrument.
- 1D / 5D / 1M / 3M / 1Y / 5Y controls now load provider history for the selected instrument.
- Selection is retained through URL query parameters and stays in the same browser tab.
- Preserves V20.3.0 dynamic clock and 60-second provider cache/refresh behaviour.
