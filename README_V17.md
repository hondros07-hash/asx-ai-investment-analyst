# V17 — Decision Brief + Thesis Monitor

V17 implements the two core product workflows:

## Before I Invest
Answers: "What do I need to know before committing more capital?"
- stores current holding and average cost
- accepts a proposed investment amount (default $10,000)
- calculates additional shares, spend, new holding and new average cost
- estimates concentration using only portfolio data known to the prototype
- surfaces thesis conditions, KPI checklist, technical confluence, support/resistance and catalysts
- highlights items requiring attention
- can prepare (not submit) a paper-trade scenario
- can save an alert rule and record a decision review

## Monitor My Thesis
Answers: "Are the reasons I invested still true?"
- shows current measurable thesis conditions
- saves review baselines
- compares current conditions with the last stored baseline
- highlights changed values and conditions requiring attention
- points to catalysts, alerts and company announcements for new evidence

## Evidence discipline
V17 does not invent company KPI values. Company-reported values must be populated from actual source documents. Calculated market/technical values remain distinguishable from reported facts and interpretation.

## Prototype limitations
- External broker holdings are not yet automatically reconciled.
- Portfolio weight only uses holdings/cash known to the prototype.
- Background alerts are stored rules, not a durable notification worker.
- SQLite persistence can be ephemeral on Streamlit Community Cloud.
- Live trading remains disabled.
