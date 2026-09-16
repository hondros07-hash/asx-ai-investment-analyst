# V18.0.5 — Streamlit Magic Render Fix

Root cause confirmed from the rendered page:
a bare Python conditional expression such as

    st.dataframe(...) if not cats.empty else st.info(...)

returns a Streamlit DeltaGenerator. Streamlit's magic display system can then
auto-render that returned object, producing the large DeltaGenerator API/help
documentation block.

V18.0.5 replaces every bare Streamlit display ternary in app.py with explicit
if/else statements, so there is no returned UI object left as a bare expression.

Also retains:
- V18.0.3 responsive price display
- V18.0.2 full database schema migrations
- V18 Investment Command Centre

Deployment diagnostic:
V18.0.5 • Market Investment Analyst • Streamlit magic render fix
