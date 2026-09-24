from services.macro_mapper import get_exposure_matrix, relevant_exposures, primary_exposure_for_text

def test_qantas_structural_map():
    m=get_exposure_matrix('QAN.AX')
    assert m['template']=='airlines'
    assert m['ai_generated'] is False
    brent=[x for x in m['exposures'] if x['tracker']=='BZ=F'][0]
    assert 'Fuel Expense' in brent['affected_kpis']
    assert 'Operating Margin' in brent['affected_kpis']

def test_news_headline_maps_to_business_kpi():
    x=primary_exposure_for_text('Brent crude oil rises after supply disruption','QAN.AX')
    assert x['tracker']=='BZ=F'
    assert 'Fuel Expense' in x['affected_kpis']

def test_irrelevant_headline_not_forced_into_exposure():
    assert relevant_exposures('Company appoints a new director','QAN.AX') == []
