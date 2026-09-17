# V19.2 — Phase 3: Something Changed

Adds durable point-in-time change detection.

## Something Changed
New primary workspace showing recorded material changes across monitored companies.

## Monitoring snapshots
Stores point-in-time observations for:
- price / volume
- SMA50 / SMA200 / RSI
- analyst mean target / analyst count / consensus label
- quant 12M scenario
- market cap
- revenue growth / earnings growth
- operating margin
- debt-to-equity
- latest announcement identity

## Change detection
Explicit descriptive rules detect:
- >=5% price change between snapshots
- >=5% analyst target change
- >=5% quant 12M scenario change
- material provider fundamental-field changes
- price crossings of SMA50/SMA200
- analyst consensus category changes
- a different latest announcement

## Workflow integration
- Company Command Centre: Something Changed panel
- Monitor My Thesis: Something Changed panel
- Markets: scan selected companies and record changes
- Dedicated Something Changed workspace with history

Important:
This build performs point-in-time scans when the user runs/saves them. It does NOT
claim to provide a durable background worker or push notifications while Streamlit
is asleep. That requires a separate scheduler/worker in a later production phase.

Deployment diagnostic:
V19.2 • Market Investment Analyst • Something Changed
