# V16 — Institutional Research Workstation

V16 consolidates the requested research/workflow upgrades:

- Company Command Centre
- Company-type KPI framework
- Thesis Scorecard with measurable conditions
- Catalyst Calendar
- Technical confluence matrix
- Market structure / support-resistance context
- No-code Strategy Builder
- Risk & Position Sizing Centre
- Portfolio Intelligence
- Research Alerts rule store
- Workspace presets/customisation
- Data provenance labels
- Existing V15 Paper Trading / OMS
- Existing V14 multi-indicator Technical Lab
- Existing announcements/report workflow

Important boundaries:
1. Company-specific KPI templates define what should be monitored; they do not invent reported values.
2. Report intelligence remains evidence-first. Values should only be populated from retrieved source documents.
3. V16 alert rules are stored locally but are not a durable background notification service.
4. SQLite on Streamlit Community Cloud is prototype persistence and can be ephemeral.
5. Paper trading remains simulated; live brokerage execution is disabled.
6. Workspace presets/module selection are implemented. True drag/drop cards require a custom Streamlit component/frontend.
7. Portfolio intelligence currently uses paper positions and historical price data; full dividends/tax/FX attribution requires transaction/account feeds.
