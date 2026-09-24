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
