# Chrímata V21.2.84 — Key Metrics Growth Fallback Engine

- Preserves genuine four-quarter TTM values where available.
- Growth hierarchy: TTM vs prior TTM (8 quarters) → latest FY vs prior FY → unavailable.
- Annual fallback growth is explicitly identified in provenance and is never presented as a TTM comparison.
- Missing comparisons remain `—`; no growth figures are fabricated.
- Corrects negative currency formatting such as `-A$36.70M`.
- Investment Snapshot layout and unrelated engines are unchanged.

## V21.2.92 — Global Exchange Announcement & Filing Resolution Engine
- Resolves the selected listing before choosing a disclosure authority.
- ASX routes to ASX announcements; NASDAQ/NYSE to SEC EDGAR; LSE, HKEX, TSE and TSX to their jurisdiction-specific disclosure adapters/official portals.
- Never falls back to SEC for a resolved non-US listing.
- Overview provenance now shows market + authority.
- Header “View all →” opens the official disclosure portal; duplicate lower button removed.
- Missing market feeds remain explicitly unavailable rather than fabricated.


## V21.2.94 — Global Legal Disclaimer & Data Attribution Footer
Adds a consistent site-wide information-only disclaimer, investment-risk wording, data-source attribution and copyright footer to every Chrímata workspace. The component is rendered once after page routing so future workspaces inherit it automatically.

## V21.2.96 — SEC Filing Retrieval Repair + View-All Restoration
- Rebuilt SEC ticker-to-CIK resolution around the SEC exchange-aware ticker map with legacy-map fallback.
- Uses the official SEC submissions endpoint and links directly to authoritative primary filing documents.
- Removes per-filing PDF probing from the Overview path to reduce SEC requests and throttling risk.
- Adds explicit SEC retrieval diagnostics (CIK resolution, request failure, no investor filings).
- Restores the native View all navigation control to the announcement card header.
- Uses FILE for SEC/EDGAR documents because EDGAR primary documents are commonly HTML rather than PDF.

## V21.3.05 — Global Disclosure Retrieval Engine + Universal View-All Navigation
- ASX public parser now inspects document-link neighbourhoods even when unrelated table rows exist, with current-year fallback search.
- US NASDAQ/NYSE listings continue through SEC EDGAR submissions.
- LSE/HKEX/TSE/TSX retain configurable official-feed adapters and now have an issuer-owned investor-relations fallback when no feed is configured.
- Latest Announcements & Reports uses a real visible Streamlit `View all →` control in the card header; navigation no longer depends on an HTML label/overlay.
- No disclosure rows are fabricated: unavailable sources remain explicit and provenance is retained.

## V21.3.08 — Dynamic Ticker Disclosure Engine + Reference Card Rebuild
- Hardened ASX public announcement parsing across current/legacy markup and multiple supported search windows.
- Added explicit ASX request/parser diagnostics instead of silently collapsing transport/parser failures into a generic empty result.
- Updated the SEC EDGAR default automated-client User-Agent and retained configurable `SEC_USER_AGENT` support.
- Full Announcements & Reports workspace now uses the same listing-aware global disclosure router as the Overview card.
- Rebuilt the Overview `View all →` action as a deterministic state transition that clears stale deep-link parameters and explicitly reruns into Announcements & Reports.
- Added regression tests for ASX normalization/document links, META/SEC normalization, six-market routing, and View-All navigation wiring.


### V21.3.08 fixes
- Disclosure retrieval now follows the active listing identity even when an ASX search result stores a bare code such as `QAN` rather than `QAN.AX`.
- ASX identities are canonicalised before the disclosure adapter is called, preventing accidental SEC fallback.
- The Overview disclosure card is rebuilt to the compact five-row reference layout.
- `View all →` remains a real Streamlit control and targets the selected ticker's Announcements & Reports workspace.
- No ticker-specific announcement data is hard-coded.

## V21.3.09 — Live Disclosure Diagnostics + Retrieval & Header Navigation Repair
- Keeps disclosure retrieval dynamic to the currently selected listing/ticker; no company-specific announcement data is hard-coded.
- ASX parser now retains valid dated announcement rows even when ASX markup does not expose an `asxpdf`/`displayAnnouncement` link in the expected form; document access falls back to the official ASX company-announcement search rather than discarding the row.
- ASX transport/parser diagnostics retain query, response byte count, content type, parsed row count, and exception details for deployed troubleshooting.
- Empty disclosure cards expose a collapsed `Disclosure diagnostics` panel so Streamlit Cloud failures can be diagnosed from the deployed app.
- Rebuilt `View all →` as a native Streamlit button inside the card's header columns. No absolute/fixed positioning is used, preventing the control from escaping beneath the sidebar.
- `View all →` deterministically selects `Announcements & Reports` and reruns while preserving the selected security identity.
- Acceptance tests cover ASX no-PDF markup, ASX PDF markup, non-overlapping View-All layout, and diagnostics wiring.


## V21.3.10
Rebuilt dynamic disclosure card: selected listing drives market adapter; ASX uses multiple official routes; production card no longer exposes diagnostic UI; View all remains contained in the card header.

## V21.3.11 — Disclosure Pipeline Root-Cause Repair + White Reference Card
- Adds a table-data fallback parser for the official ASX announcement results page, so disclosure metadata can still render when ASX changes anchor/PDF markup.
- Keeps retrieval dynamic to the currently selected listing; no company announcements are hard-coded.
- Keeps direct PDF links when recoverable; otherwise VIEW opens the official ASX ticker announcement search.
- Forces the Latest Announcements & Reports reference card interior to white and contains View all navigation inside the card header.

## V21.3.12 — Official Disclosure Provider Gateway + Production Reference Card
- One listing-aware disclosure gateway now powers both the Overview card and full Announcements & Reports page.
- ASX listings are canonicalised from the active security identity and routed only to ASX adapters.
- U.S. listings use SEC ticker mapping with an independent official SEC Company Atom CIK fallback, then data.sec.gov submissions.
- Provider failures preserve explicit machine states instead of being flattened into a false “no rows” result.
- Production announcement card is white, contains its provenance inside the card, and keeps View all inside the header.

## V21.3.13 — Dynamic News Intelligence Engine + News & Events Intelligence Centre
- Recent News is driven by the currently selected ticker and renders as a compact five-row white reference card.
- Removed the oversized secondary "View all news" button; the header control navigates internally while preserving the selected ticker.
- Added `news_intelligence_engine.py` with Company, Sector and Macro discovery layers.
- Added News & Events Intelligence Centre with All Relevant Events, Company News, Sector & Competitors, and Macro & Market Events views.
- Expandable event intelligence explains relevance channel, affected KPI, what to watch, source and original-source link when available.
- Current provider is Yahoo Finance through yfinance; contextual sector/macro discovery is not presented as a prediction or as verified company impact.


## V21.3.17 — Security Identity Validation + Metadata Fallback + Smart Refresh Engine
- Canonical listing identity is resolved before Company Command Centre data is loaded.
- Verified primary-listing overrides are company-name based, never inferred from price magnitude.
- International sector/industry metadata uses a safe cascade and leaves genuinely missing classifications unavailable.
- Refresh policy separates fast quote data (60s), medium market/news data (10m), and slow company metadata/fundamentals (6h).
- Nike search includes the verified NYSE primary listing NKE.
