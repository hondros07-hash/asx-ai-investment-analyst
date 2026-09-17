# V18.3.3 — Forecast Function Fix

The Forecast page traceback showed that V18.3.2 correctly passed `h` to
`render_forecast_tool(ticker,h)`, but the renderer itself still called
`research_forecast(df)`. Since `df` did not exist in that function, Streamlit
raised NameError.

V18.3.3 changes the internal call to `research_forecast(h)`, audits every
Forecast renderer call, retains the partial-horizon chart fix, and preserves all
V18.3.2 database/runtime fixes.

Deployment diagnostic:
V18.3.3 • Market Investment Analyst • forecast function fix
