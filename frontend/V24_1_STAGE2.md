# AXÍA V24.1 — Company Command Centre migration (Stage 2)

Seven previously placeholder Next.js sections now request read-only FastAPI endpoints:

| Section | Data contract | Remaining limitation |
| --- | --- | --- |
| Technical | Existing deterministic technical engine and adjusted daily bars | Provider delays and history gaps |
| Quant | Existing deterministic indicator frame | Not a full statistical/backtest workspace |
| News | Yahoo Finance company news with source URLs | Not a regulatory feed |
| Announcements | SEC EDGAR submissions only when verified CIK and AXIA_SEC_USER_AGENT are available | Non-US official exchange connectors not yet migrated |
| Report Intelligence | Same verified SEC filing links | AI document extraction not migrated |
| Thesis Scorecard | Existing financial integrity/provider context | User-authored rules require authenticated persistent storage |
| Catalyst Calendar | Provider calendar date entries | Saved user catalysts not migrated |

No simulated company filings, research conclusions, user rules, or model values are returned. Official source URLs are presented only when provided. A genuine SEC application name and contact must be configured in `AXIA_SEC_USER_AGENT`; no fabricated contact is shipped.

## Verification before merge

Run `python -m pytest tests/test_v241_research_routes.py` and existing API tests, then `cd frontend && npm run lint && npm run build`. Test ZIP.AX, KO and QAN.AX; confirm ZIP.AX does not show US filings, and SEC routes without configured contact return unavailable. Test provider timeouts and empty data, navigation across all eleven pages, mobile layout and existing Stage 1 financial results.

## Cutover

This is Stage 2 UI/API wiring, not full functional parity. The current Streamlit website remains authoritative. Stage 3 and 4 must migrate saved state, official non-US disclosures, authenticated workspaces and complete report analysis before production domain cutover.
