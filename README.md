# Market Investment Analyst V5

This build includes:
- 5-year market data and charts
- fundamental analysis
- technical indicators
- quantitative metrics
- sector-specific KPI lens
- current macro/micro AI web research
- valuation dashboard
- 1/3/6-month historical return baseline
- architecture for a future calibrated prediction/backtesting engine

## Setup
1. Upload app.py and requirements.txt to your GitHub repo.
2. Deploy/reboot Streamlit.
3. In Streamlit App Settings -> Secrets add:
   OPENAI_API_KEY = "your-key"
4. Never commit the API key to GitHub.

## Important
The forecast panel is intentionally a historical baseline, not a trained probability forecast. A rigorous production forecast requires point-in-time data, walk-forward validation, calibration, and benchmark testing.
