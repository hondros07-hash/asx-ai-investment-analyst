from services.valuation_summary_engine import summarize_valuation
def test_missing_input_diagnostics():
 r=summarize_valuation({'status':'unavailable','reason':'Positive trailing free cash flow is required.','audit':{'inputs':{'fcf':{'status':'missing'},'shares':{'status':'verified','value':100},'cash':{'status':'missing'},'debt':{'status':'missing'}},'blocking_reasons':['Positive Free Cash Flow unavailable']}},2,'QAN.AX')
 assert r['bear_price'] is None
 assert 'Free cash flow' in r['diagnostics']['missing']
 assert r['diagnostics']['cash_or_debt_assumed_zero']
 assert 'Positive Free Cash Flow unavailable' in r['diagnostics']['blockers']
def test_complete_scenarios_unchanged():
 r=summarize_valuation({'status':'success','listing_currency':'AUD','scenarios':{'Bear':{'value_per_share':1},'Base':{'value_per_share':2},'Bull':{'value_per_share':5}}},2,'TEST.AX')
 assert r['marker_positions_pct']=={'bear':0,'base':25,'bull':100}
