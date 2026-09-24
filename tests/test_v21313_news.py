import sys, types
sys.path.insert(0,'.')
sys.modules.setdefault('yfinance',types.SimpleNamespace())
import news_intelligence_engine as n

def test_row_classifies_macro_channel():
    item={'title':'Oil prices rise sharply','publisher':'Reuters','providerPublishTime':1700000000,'link':'https://example.com/a'}
    r=n._row(item,'QAN.AX','Macro')
    assert r['Category']=='Commodity / input costs'
    assert r['Layer']=='Macro'
    assert r['URL'].startswith('https://')

def test_columns_contract():
    assert {'Date','Headline','Source','Layer','Why it matters','Affected KPI','What to watch'}.issubset(set(n.NEWS_COLUMNS))
