# V14.2 — Dual Page Hotfix

Fixes both errors shown in the screenshots.

Technical:
- Adds module-level `import plotly.graph_objects as go`
- Adds module-level `from plotly.subplots import make_subplots`
- Plotly is already declared in requirements.txt.

Announcements:
- Repairs the ASX provider/fallback control flow.
- An empty provider result no longer tries to access a missing URL column.
- An empty provider now falls through to the ASX public fallback.
- An empty fallback returns a normalized empty announcement table instead of crashing.

V14's multi-indicator Technical Analysis Lab and earlier hover-help fixes are retained.
