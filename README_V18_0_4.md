# V18.0.4 — UI Render Hotfix

Fixes the large Streamlit `DeltaGenerator` documentation block appearing under Catalysts.

Cause:
A Streamlit display command (`st.dataframe` / `st.info`) was being passed as a value
to another output command. Streamlit display methods return a `DeltaGenerator`; writing
that return object caused its representation/help content to appear in the app.

Fix:
- renders the catalysts dataframe directly
- renders the empty-state info message directly
- never writes the returned Streamlit UI object
- retains V18.0.3 responsive price display
- retains V18.0.2 full SQLite schema migrations

Deployment diagnostic:
`V18.0.4 • Market Investment Analyst • UI render hotfix`
