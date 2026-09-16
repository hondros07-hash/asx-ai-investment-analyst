# V18.0.3 — Responsive Price Display

Fixes quote-card prices being rendered as `$17...`, `$21...`, etc.

Changes:
- adds compact exchange-aware `display_price()` formatting
- prevents Streamlit metric values from using ellipsis
- reduces metric typography responsively
- splits seven-card quote rows into wider rows where applicable
- preserves V18.0.2 full SQLite schema migrations and V18 features

Deployment diagnostic:
`V18.0.3 • Market Investment Analyst • responsive price display`
