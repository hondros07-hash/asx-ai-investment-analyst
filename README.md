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

## V21.3.07 — Verified Global Disclosure Pipeline + Deterministic View-All Navigation
- Hardened ASX public announcement parsing across current/legacy markup and multiple supported search windows.
- Added explicit ASX request/parser diagnostics instead of silently collapsing transport/parser failures into a generic empty result.
- Updated the SEC EDGAR default automated-client User-Agent and retained configurable `SEC_USER_AGENT` support.
- Full Announcements & Reports workspace now uses the same listing-aware global disclosure router as the Overview card.
- Rebuilt the Overview `View all →` action as a deterministic state transition that clears stale deep-link parameters and explicitly reruns into Announcements & Reports.
- Added regression tests for ASX normalization/document links, META/SEC normalization, six-market routing, and View-All navigation wiring.
