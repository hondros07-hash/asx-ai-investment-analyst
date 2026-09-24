import numpy as np, pandas as pd
from services.forecast_engine import build_12m_forecast,calibrated_positive_probability,MODEL_VERSION
def synthetic(n=1600):
 idx=pd.bdate_range("2019-01-01",periods=n); r=.00025+.01*np.sin(np.arange(n)/37)/10
 return pd.DataFrame({"Close":100*np.exp(np.cumsum(r))},index=idx)
def test_deterministic_repeated_results():
 d=synthetic(); a=build_12m_forecast(d,security="TEST"); b=build_12m_forecast(d,security="TEST")
 assert a["forecast_return"]==b["forecast_return"] and a["target_price"]==b["target_price"]
def test_target_formula():
 a=build_12m_forecast(synthetic(),current_price=123,security="TEST")
 assert a["status"]=="ready" and abs(a["target_price"]-123*(1+a["forecast_return"]))<1e-9
def test_ai_false_and_version():
 a=build_12m_forecast(synthetic(),security="TEST")
 assert a["audit"]["ai_calculated"] is False and a["audit"]["model_version"]==MODEL_VERSION
def test_probability_withheld_when_small_sample():
 bt=pd.DataFrame({"Predicted":[.1]*5,"Actual":[.1,-.1,.2,-.2,.1]})
 p,n=calibrated_positive_probability(bt,.1); assert p is None and n==5
def test_insufficient_history_unavailable():
 a=build_12m_forecast(synthetic(400),security="NEW"); assert a["status"]=="unavailable"
def test_bridge_requires_ratio():
 a=build_12m_forecast(synthetic(),security="X",bridge={"status":"verified"},fx_rate=1.2,security_ratio=None)
 assert a["status"]=="unavailable" and "share-equivalence" in a["audit"]["reason"]
def test_probability_is_bounded_if_available():
 a=build_12m_forecast(synthetic(),security="TEST")
 p=a["probability_positive"]; assert p is None or 0<p<1
