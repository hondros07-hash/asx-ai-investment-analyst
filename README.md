Chrímata V20.4.2 — Live Market Intelligence Widgets

# Chrímata V20.3.3 — Reference Market Section & In-Place Chart Fix

- Fixes market-card and timeframe controls so they remain in the same browser tab.
- Clicking a headline market card changes the existing large chart.
- 1D/5D/1M/3M/1Y/5Y controls update that same chart.
- Restyles the market section to closely match the supplied reference: denser cards, larger intraday panel, blue timeframe pills, expanded ASX sector list, compact indices table, latest-price and previous-close labels.
- Preserves the dynamic clock, 60-second provider refresh, flags, navigation, sidebar, banner and scrolling fixes.

Provider/exchange delays still apply.

## V20.3.6 — Smooth Interactive Market Chart
- Replaces query-link chart switching with a client-side embedded market component.
- Five headline cards switch the existing chart without a Streamlit page rerun or white-screen flash.
- 1D / 5D / 1M / 3M / 1Y / 5Y switch in place with a short fade transition.
- Keeps labelled Y-axis values, adaptive X-axis labels, previous-close reference, sectors and expanded indices.
- Market datasets remain provider-driven and use the existing 60-second provider cache.


## V20.4.0 — Interactive ASX Sectors
- Removes the 1-second Streamlit fragment rerun that caused constant page jumping/reflow.
- Keeps the market clock live with a client-side 1-second clock update instead.
- Locks the embedded market component and chart to fixed geometry so the chart does not shrink or stretch after interaction.
- Keeps five-card and timeframe switching entirely client-side with no page navigation.
- Restores a compact plot area with Y-axis values, adaptive X-axis labels, gridlines and previous-close reference.
- Provider data is refreshed on normal app reruns; provider caching remains in place.

### V20.4.0 sector widget
- Shows all configured ASX GICS sector proxies (up to all 11 sectors) in the market dashboard.
- Day / Week / Month / YTD are real client-side controls and update without a Streamlit page reload.
- Sector rows re-rank strongest to weakest for the selected period.
- Week, Month and YTD performance are calculated from provider history for each selected horizon; Day uses the latest provider change.


## V20.4.0 — ASX Sectors Widget Rebuild
- Always renders all 11 configured ASX sector rows; provider gaps show as N/A instead of disappearing.
- Rebuilt Day / Week / Month / YTD segmented controls with Chrímata styling.
- Period switching remains client-side with no full Streamlit page rerun.
- Sector rows rank strongest to weakest for the selected period, with unavailable rows retained at the bottom.


## V20.4.0 — Complete ASX Sector Data Engine
Australia sector performance now uses the official S&P/ASX 200 GICS sector index symbols first (XFJ, XHJ, XRE/XPJ, XNJ, XTJ, XSJ, XDJ, XUJ, XMJ, XIJ, XEJ). If the active provider cannot resolve an official index, Chrímata falls back to an ASX proxy or an equal-weight basket of representative ASX shares. Day, Week, Month and YTD remain client-side interactive in the sector widget.


## V20.4.1 — ASX Indices Widget Rebuild
- Restores the complete nine-row ASX Indices terminal layout: XJO, XAO, XFL, XTO, XKO, XTL, XTX, XJR and XGD.
- Uses provider-compatible symbols for ASX 50 (^AFLI), ASX 100 (^ATOI) and ASX 20 (^ATLI) while displaying canonical ASX codes.
- Keeps unavailable rows visible with an em dash instead of removing them.
- Preserves the five headline cards and the stable client-side market chart/sector interactions.


## V20.4.2 — Live Market Intelligence Widgets
- Top Gainers filters to positive movers only; Biggest Fallers filters to negative movers only.
- Market movers remain country-aware through each market universe and provider quotes.
- Landing-page Watchlist now resolves saved bare tickers to the selected market and uses the same persistent SQLite watchlist store as the full Watchlist page.
- VIX widget now requests CBOE VIX (^VIX), removes the fabricated numeric fallback, supports values above 30, and identifies VIX as a US S&P 500 options-implied volatility measure.
- Existing five-card market overview, stable chart, ASX sectors, and nine-row ASX indices widget are preserved.

## V20.4.5 — Market Data & Search Rebuild
- Rebuilt landing-page security search with visible matching listings and Search → Company Command Centre routing.
- Restored Windows-safe market-heading flag artwork inside the smooth market component.
- Stabilised Global Markets tabs with local client-side state so each country changes on the first click.
- Retains provider-backed dividends and earnings with explicit unavailable states; no fabricated calendar events.
