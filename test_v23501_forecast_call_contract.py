import ast
from pathlib import Path
from services.forecast_widget_engine import summarize_forecast

def test_call_contract():
    tree=ast.parse(Path("app.py").read_text())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="_chr_forecast_summary"]
    assert len(calls)==1
    call=calls[0]
    assert len(call.args)==2
    assert {k.arg for k in call.keywords}=={"reference_price","currency"}
    assert [a.id for a in call.args]==["_fc12","ticker"]

def test_service_contract():
    data={"status":"ready","target_price":120,"forecast_return":.2,"audit":{}}
    result=summarize_forecast(data,"ABC",reference_price=100,currency="AUD")
    assert result["status"]=="ready" and result["target_ticker"]=="ABC" and result["currency"]=="AUD"
