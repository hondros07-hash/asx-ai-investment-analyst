
# V8 Streamlit integration.
# Requires V7's universe_engine.py and V8's ensemble_engine.py.

from ensemble_engine import (
    add_benchmark_targets, sector_neutralise, train_competing_models,
    latest_ensemble_forecast, prediction_deciles
)

st.header("V8 — Competing Models + Ensemble")

st.info(
    "V8 trains separate 1M, 3M and 6M statistical models. "
    "Probabilities come from fitted models and are evaluated on chronological unseen data. "
    "The AI research layer is not allowed to invent these probabilities."
)

v8_horizon = st.selectbox("V8 horizon", ["1M","3M","6M"], index=1, key="v8_h")
v8_objective = st.radio(
    "Prediction objective",
    ["outperform","positive"],
    format_func=lambda x: "Outperform ASX 200" if x=="outperform" else "Positive absolute return",
    horizontal=True
)

if "v7_panel" not in st.session_state:
    st.warning("Run the V7 Universe Backtest first so V8 has a multi-stock point-in-time price panel.")
else:
    panel_v8 = st.session_state["v7_panel"].copy()
    bm_v8 = yf.Ticker("^AXJO").history(period="10y", auto_adjust=True)
    panel_v8 = add_benchmark_targets(panel_v8, bm_v8["Close"])
    panel_v8 = sector_neutralise(panel_v8)

    if st.button("Train & Test V8 Ensemble", type="primary"):
        with st.spinner("Training competing models on chronological data and testing on unseen dates..."):
            result_v8 = train_competing_models(
                panel_v8, horizon=v8_horizon, objective=v8_objective
            )
        st.session_state["v8_result"] = result_v8
        st.session_state["v8_panel"] = panel_v8

if st.session_state.get("v8_result") is not None:
    r = st.session_state["v8_result"]

    st.subheader("Data split")
    st.write(
        f"Training through **{r['train_end']}** → validation through "
        f"**{r['validation_end']}** → unseen test **{r['test_start']} to {r['test_end']}**."
    )

    st.subheader("Validation performance")
    st.dataframe(r["validation_metrics"], use_container_width=True, hide_index=True)

    st.subheader("Completely unseen test performance")
    st.dataframe(r["test_metrics"], use_container_width=True, hide_index=True)

    st.write("**Ensemble weights selected from validation data only**")
    st.json(r["weights"])

    st.subheader("Probability calibration on unseen test data")
    cal = r["calibration"].copy()
    cal["bucket"] = cal["bucket"].astype(str)
    st.dataframe(cal, use_container_width=True, hide_index=True)

    st.subheader("Model disagreement")
    st.caption(
        "High disagreement means the competing models do not see the setup the same way; "
        "treat the ensemble probability with lower confidence."
    )
    p = r["test_predictions"].copy()
    st.dataframe(p.tail(200), use_container_width=True, hide_index=True)

    st.subheader("Probability deciles")
    dec = prediction_deciles(p, r["horizon"])
    if not dec.empty:
        st.dataframe(dec, use_container_width=True, hide_index=True)

    st.subheader("Latest universe probabilities")
    latest = latest_ensemble_forecast(r, st.session_state["v8_panel"])
    if not latest.empty:
        show_cols = ["ticker","date","ensemble_probability","model_disagreement",
                     "mom1","mom3","mom6","vol60","rsi","rel3"]
        show_cols = [c for c in show_cols if c in latest.columns]
        st.dataframe(latest[show_cols].head(30), use_container_width=True, hide_index=True)

st.warning(
    "V8 is an experimental price/volume ensemble. It is NOT yet the final Fundamental + "
    "Valuation + Quant + Technical + Macro ensemble because free Yahoo history does not provide "
    "a reliable point-in-time fundamental database. Adding current fundamentals to historical "
    "rows would create look-ahead bias, so V8 deliberately does not do that."
)
