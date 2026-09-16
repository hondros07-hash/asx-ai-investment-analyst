# V18.2.3 — Responsive Metric Cards

Root cause fixed globally.

An older V18.0.3 rule forced every Streamlit metric value to `white-space: nowrap`.
That protected numeric prices from ellipsis, but caused long text such as
`Financial Services` and `Consumer Defensive` to overflow into adjacent cards.

V18.2.3:
- removes the global nowrap rule from metric values
- allows metric values, labels and deltas to wrap safely
- uses responsive metric typography
- adds min-width protection for Streamlit grid cards
- adds a reusable text_metric_box helper
- applies the helper to Sector, Industry, Exchange, Market, Currency and benchmark fields
- retains Company Snapshot, Forecast Research and Analyst Consensus

Deployment diagnostic:
V18.2.3 • Market Investment Analyst • responsive metric cards
