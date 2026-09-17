
# V9 Streamlit integration
# This does NOT fabricate historical fundamentals. Upload a point-in-time CSV
# where available_date is the date the market could actually know the information.

from point_in_time_engine import (
    load_pit_csv, point_in_time_join, freshness_days,
    winsorize_cross_section, sector_neutral_zscores,
    derive_fundamental_factors, FUNDAMENTAL_FIELDS,
    VALUATION_FIELDS, REVISION_FIELDS
)
from v9_ensemble_engine import train_v9

st.header("V9 — Point-in-Time Fundamental + Valuation Ensemble")

st.info(
    "V9 only uses a financial observation after its `available_date`. "
    "This prevents an annual result released in March from being used in a January backtest."
)

pit_file=st.file_uploader(
    "Upload point-in-time fundamentals/valuation/revisions CSV",
    type=["csv"], key="v9_pit"
)

st.caption(
    "Required columns: ticker, period_end, available_date. "
    "Optional fields include revenue_growth, eps_growth, margins, ROE, ROIC, "
    "net_debt_ebitda, valuation multiples, FCF yield and analyst revisions."
)

if pit_file is not None and "v7_panel" in st.session_state:
    try:
        pit=load_pit_csv(pit_file)
        p=point_in_time_join(st.session_state["v7_panel"],pit)
        p=freshness_days(p)

        raw_cols=[
            c for c in FUNDAMENTAL_FIELDS+VALUATION_FIELDS+REVISION_FIELDS
            if c in p.columns
        ]
        p=winsorize_cross_section(p,raw_cols)
        p=sector_neutral_zscores(p,raw_cols)
        p=derive_fundamental_factors(p)

        # Preserve V8 benchmark targets if present; otherwise construct them.
        bm=yf.Ticker("^AXJO").history(period="10y",auto_adjust=True)
        p=add_benchmark_targets(p,bm["Close"])
        st.session_state["v9_panel"]=p

        st.success(
            f"Point-in-time dataset joined: {len(p):,} market observations, "
            f"{pit.ticker.nunique():,} companies with supplied PIT records."
        )

        st.subheader("Data provenance check")
        cols=[c for c in ["ticker","date","period_end","available_date",
                          "fundamental_age_days","fundamental_quality",
                          "fundamental_growth","valuation_factor","revision_factor"]
              if c in p.columns]
        st.dataframe(p[cols].dropna(subset=["available_date"]).tail(100),
                     use_container_width=True,hide_index=True)

        h=st.selectbox("V9 horizon",["1M","3M","6M"],index=1,key="v9_h")
        obj=st.radio("V9 objective",["outperform","positive"],horizontal=True,key="v9_o")

        if st.button("Train V9 Point-in-Time Ensemble",type="primary"):
            with st.spinner("Training V9 without future financial information..."):
                result=train_v9(p,h,obj)
            st.session_state["v9_result"]=result

        if st.session_state.get("v9_result") is not None:
            r=st.session_state["v9_result"]
            st.subheader("Features actually admitted to the model")
            st.json(r.get("v9_feature_groups",{}))
            st.subheader("Validation")
            st.dataframe(r["validation_metrics"],use_container_width=True,hide_index=True)
            st.subheader("Unseen test")
            st.dataframe(r["test_metrics"],use_container_width=True,hide_index=True)
            st.subheader("Calibration")
            cal=r["calibration"].copy()
            cal["bucket"]=cal["bucket"].astype(str)
            st.dataframe(cal,use_container_width=True,hide_index=True)
            st.write("**Ensemble weights**")
            st.json(r["weights"])

    except Exception as e:
        st.error(f"V9 dataset error: {e}")

elif "v7_panel" not in st.session_state:
    st.warning("Run V7 first to build the market panel.")
else:
    st.warning(
        "No point-in-time financial dataset uploaded. V9 will not substitute current "
        "Yahoo fundamentals because that would introduce look-ahead bias."
    )
