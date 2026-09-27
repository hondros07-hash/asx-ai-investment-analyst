from datetime import date
from services.portfolio_position_engine import position_summary
from services.scenario_intelligence_engine import solve_single_variable, implied_matrix, pivotal_sensitivities

def test_weighted_lots():
    result=position_summary([{"quantity":10,"unit_cost":2,"fees":1,"acquired_on":"2025-01-01"},{"quantity":5,"unit_cost":4,"fees":0,"acquired_on":"2026-09-01"}],price=3,portfolio_value=100,as_of=date(2026,9,27))
    assert result["shares"]==15 and result["cost_basis"]==41
    assert result["average_cost"]==41/15 and result["unrealised_pnl"]==4
    assert result["portfolio_weight"]==.45
    assert result["tax_lots"][0]["potential_12_month_status"]=="review_eligibility"
def test_no_position_does_not_invent_average():
    assert position_summary([],price=2)["average_cost"] is None
def test_reverse_solver():
    result=solve_single_variable(lambda x:2*x+1,11,0,10)
    assert result["status"]=="solved" and abs(result["value"]-5)<1e-5
def test_unbracketed_target():
    assert solve_single_variable(lambda x:x,20,0,10)["status"]=="not_bracketed"
def test_matrix_and_sensitivity():
    result=implied_matrix(lambda g,m:100*g*m,25,[1,2],[.1,.2])
    assert len(result["cells"])==2
    ranked=pivotal_sensitivities({"growth":1,"margin":.1},lambda growth,margin:100*growth*margin,{"growth":.1,"margin":.05})
    assert ranked[0]["metric"]=="margin"
