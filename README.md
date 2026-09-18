# Chrímata V20.2.9 — Market Overview Flag Header

Adds the selected country’s real embedded flag artwork directly before the Market Overview title while retaining same-tab country navigation.

# Chrímata V20.2.7 — Reference Navigation Hard Fix

Removes the deployed phantom header gap and replaces country Streamlit buttons with stable white flag navigation anchors.


V20.2.7: Windows-safe embedded SVG country flags and same-tab native Streamlit market switching.


## V20.2.9
- Fixes full-page landing dashboard scrolling so the bottom widgets remain reachable.
- Market overview quote cache reduced to 60 seconds.
- Headline quotes prefer Twelve Data when `TWELVE_DATA_API_KEY` is configured, with Yahoo/yfinance fallback.
- Main market chart now requests 5-minute intraday bars for the current session.
- Preserves V20.2.8 country flags, same-tab navigation, banner and sidebar.

Real-time entitlement depends on the configured provider/exchange subscription; delayed feeds remain delayed.
