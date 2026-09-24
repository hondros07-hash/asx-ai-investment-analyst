import pathlib
import announcement_engine as ae

def test_asx_parser_keeps_dated_row_without_pdf_anchor():
    html='''<table><tr><td>22/09/2026<br>5:10 pm</td><td></td><td>Change in substantial holding 476 pages 3.1MB</td></tr></table>'''
    rows=ae._parse_asx(html,'QAN')
    assert len(rows)==1
    assert rows[0]['Date']=='22/09/2026'
    assert 'Change in substantial holding' in rows[0]['Title']
    assert rows[0]['Source']=='ASX Market Announcements'
    assert rows[0]['ReadURL'].startswith('https://www.asx.com.au/')

def test_asx_parser_prefers_pdf_when_present():
    html='''<table><tr><td>22/09/2026 5:10 pm</td><td><a href="/asxpdf/20260922/pdf/test.pdf">Change in substantial holding</a></td></tr></table>'''
    rows=ae._parse_asx(html,'QAN')
    assert len(rows)==1 and rows[0]['Has PDF'] is True
    assert 'asxpdf' in rows[0]['PDFURL']

def test_view_all_is_not_absolute_positioned():
    s=pathlib.Path('app.py').read_text()
    section=s[s.index('/* V21.3.09'):s.index('# V21.2.90 — Company Intelligence',s.index('/* V21.3.09'))]
    assert 'position:absolute' not in section
    assert 'position:fixed' not in section
    assert 'v21309_nav_ann_' in s
    assert '_chr_set_cc_sub_v2111("Announcements & Reports")' in s

def test_diagnostics_surface_on_empty():
    s=pathlib.Path('app.py').read_text()
    assert 'Disclosure diagnostics' in s
    assert 'st.json(_diag' in s
