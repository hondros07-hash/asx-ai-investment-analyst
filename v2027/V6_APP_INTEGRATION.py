
# Add this block to app.py after you have `hist` loaded.
# It imports the V6 walk-forward engine and creates a rigorous validation panel.

from backtest_engine import (
    nearest_neighbour_walk_forward, calibration_table,
    performance_summary, latest_forecast
)

st.header("V6 — Walk-Forward Prediction & Validation")

@st.cache_data(ttl=3600)
def load_asx200():
    return yf.Ticker("^AXJO").history(period="10y", auto_adjust=True)

benchmark_v6 = load_asx200()

st.caption(
    "This model uses expanding-window walk-forward testing. "
    "A historical prediction can only train on outcomes that were already observable "
    "at that historical date."
)

horizon_v6 = st.selectbox("Forecast horizon", ["1M","3M","6M"], index=1)
neighbours_v6 = st.slider("Similar historical observations", 25, 150, 75, 5)

with st.spinner("Running walk-forward backtest..."):
    preds_v6 = nearest_neighbour_walk_forward(
        hist, benchmark_v6,
        horizon=horizon_v6,
        neighbours=neighbours_v6
    )

if preds_v6.empty:
    st.warning("Not enough historical data for this backtest.")
else:
    perf_v6 = performance_summary(preds_v6)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Predictions", perf_v6.get("predictions",0))
    c2.metric("Directional accuracy", f"{perf_v6.get('directional_accuracy',0)*100:.1f}%")
    c3.metric("Brier score", f"{perf_v6.get('brier_score',float('nan')):.3f}")
    c4.metric("Avg realised return", f"{perf_v6.get('mean_actual_return',0)*100:.1f}%")

    st.subheader("Probability calibration")
    cal_v6 = calibration_table(preds_v6)
    if not cal_v6.empty:
        cal_show=cal_v6.copy()
        cal_show["bucket"]=cal_show["bucket"].astype(str)
        cal_show["avg_predicted"]=cal_show["avg_predicted"].map(lambda x:f"{x*100:.1f}%")
        cal_show["actual_positive_rate"]=cal_show["actual_positive_rate"].map(lambda x:f"{x*100:.1f}%")
        cal_show["avg_return"]=cal_show["avg_return"].map(lambda x:f"{x*100:.1f}%")
        st.dataframe(cal_show, use_container_width=True, hide_index=True)

    st.subheader("Historical predictions")
    show=preds_v6.tail(100).copy()
    for c in ["prob_positive","expected_return","median_return","downside_p10","upside_p90","actual_return"]:
        show[c]=show[c].map(lambda x:f"{x*100:.1f}%" if pd.notna(x) else "Pending")
    st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("Today's historically-derived forecast")
latest_v6 = latest_forecast(hist, benchmark_v6, horizon_v6, neighbours_v6)
if latest_v6:
    c1,c2,c3,c4=st.columns(4)
    c1.metric("P(positive)",f"{latest_v6['prob_positive']*100:.1f}%")
    c2.metric("Expected return",f"{latest_v6['expected_return']*100:.1f}%")
    c3.metric("10th percentile",f"{latest_v6['downside_p10']*100:.1f}%")
    c4.metric("90th percentile",f"{latest_v6['upside_p90']*100:.1f}%")
    st.caption(
        f"Based on {latest_v6['sample_size']} nearest historical observations. "
        "This is an experimental historical model, not a guaranteed forecast."
    )
