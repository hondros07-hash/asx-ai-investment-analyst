# V13.1.1 — Hover Help Hotfix

Fixes the recursion error introduced in V13.1.

Cause:
The automated conversion of metric cards also replaced the native `target.metric(...)`
call inside the new `metric_box()` helper. That caused `metric_box()` to call itself
indefinitely until Python raised a recursion-related TypeError/error.

Fix:
`metric_box()` now correctly calls `target.metric(...)` and injects Streamlit's native
`help=` tooltip only when a glossary description exists.

No investment logic or market-data calculations were changed.
