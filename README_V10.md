# ASX AI Investment Analyst V10 — Research Operating System

V10 intentionally combines the major missing layers identified after V9.

## Included
1. Evidence/provenance database
2. Announcement / annual-report structured intelligence engine
3. Bear/Base/Bull DCF valuation lab
4. Market-regime classifier
5. Event-to-price transmission schema
6. Kill My Thesis rule database
7. Catalyst/evidence framework
8. Portfolio risk analytics and correlation
9. Model registry and drift helper
10. Provider abstraction layer
11. V6–V9 engines remain included

## Important distinction
"Included" means the software architecture/engine is present. Some modules cannot be fully populated
without external production data.

V10 does NOT pretend to include:
- licensed exchange-grade ASX real-time/order-book data
- a survivorship-bias-free delisted ASX database
- a commercial point-in-time fundamental/estimate database
- an official automated ASX announcement feed
- cloud-persistent database/authentication
- scheduled alerts

Those are integrations/infrastructure, not calculations that can safely be fabricated from Yahoo data.

## Suggested next engineering phase
Integrate production data providers and persistent Postgres/Supabase, then wire the modules into one
unified Streamlit navigation rather than continuing to add isolated prototype panels.
