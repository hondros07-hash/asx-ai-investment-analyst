# V18 — Investment Command Centre

Implemented:
- Polished Company Investment Command Centre
- Your position / market value / unrealised P&L
- Attention queue
- Thesis summary
- Company KPI evidence ledger
- KPI previous-vs-latest change detection
- Persistent valuation assumptions
- Bear/Base/Bull scenario integration
- Reverse valuation targets ($3/$4/$5/$6)
- Technical regime + support/resistance + relative strength vs broad benchmark
- Latest announcements surface
- Catalysts
- Before I Invest integration of valuation, KPI evidence, announcements and concentration
- Monitor My Thesis evidence-capture workflow with provenance

Evidence discipline:
V18 does not fabricate company-reported KPI values. KPI observations require a reporting period and source before saving.

Important prototype boundaries:
- Automatic extraction of KPI values from PDFs is not claimed as complete; V18 creates the evidence ledger and comparison engine needed for that next connection.
- ASX announcement completeness depends on the active provider/fallback.
- Portfolio concentration uses holdings known to the prototype, not all external wealth/accounts.
- Local SQLite storage on Streamlit Community Cloud is not guaranteed durable.
- Background alert delivery and live broker execution remain outside this build.
