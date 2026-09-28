"""Compatibility adapter: Streamlit caching lives at the UI boundary only.

All financial retrieval, normalization, ratios and derivations are implemented in
services.fundamentals_core and can be imported without Streamlit.
Existing load(ticker, frequency) and load.clear() remain compatible.
"""
import streamlit as st
from services.fundamentals_core import (
    ROWS, SECTOR, number, pick, category, derive, load_uncached,
)


@st.cache_data(ttl=3600, show_spinner=False, max_entries=96)
def load(ticker, frequency="Annual (5Y)"):
    return load_uncached(ticker, frequency)
