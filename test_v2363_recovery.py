import unittest
import pandas as pd
from services.valuation_evidence import recover_financial_inputs_v2362
from services.valuation_engine import methodology_for
class TestValuationRecovery(unittest.TestCase):
 def test_half_year(self):
  d=pd.to_datetime(['2026-06-30','2025-12-31'])
  cf=pd.DataFrame([[120,100],[-20,-10]],index=['Operating Cash Flow','Capital Expenditure'],columns=d)
  r=recover_financial_inputs_v2362({},quarterly_cf=cf)
  self.assertEqual(r['fcf'],190)
  self.assertIn('half-years',r['audit']['inputs']['fcf']['period'])
 def test_quarterly(self):
  d=pd.to_datetime(['2026-06-30','2026-03-31','2025-12-31','2025-09-30'])
  cf=pd.DataFrame([[100]*4,[-20]*4],index=['Operating Cash Flow','Capital Expenditure'],columns=d)
  self.assertEqual(recover_financial_inputs_v2362({},quarterly_cf=cf)['fcf'],320)
 def test_missing_quarter(self):
  d=pd.to_datetime(['2026-06-30','2026-03-31','2025-09-30','2025-06-30'])
  cf=pd.DataFrame([[100]*4,[-20]*4],index=['Operating Cash Flow','Capital Expenditure'],columns=d)
  self.assertIsNone(recover_financial_inputs_v2362({},quarterly_cf=cf)['fcf'])
 def test_negative_fcf_is_not_missing(self):
  r=recover_financial_inputs_v2362({'freeCashflow':-12})
  self.assertEqual(r['fcf'],-12)
  self.assertEqual(r['audit']['inputs']['fcf']['status'],'verified')
 def test_missing_balance_sheet_not_zero(self):
  r=recover_financial_inputs_v2362({'freeCashflow':100,'sharesOutstanding':1000})
  self.assertIsNone(r['cash']);self.assertIsNone(r['debt'])
  self.assertFalse(r['audit']['balance_sheet_complete'])
 def test_annual_fallback(self):
  d=pd.to_datetime(['2026-06-30'])
  cf=pd.DataFrame([[100],[-20]],index=['Operating Cash Flow','Capital Expenditure'],columns=d)
  self.assertEqual(recover_financial_inputs_v2362({},annual_cf=cf)['fcf'],80)
 def test_credit_service_methodology(self):
  self.assertEqual(methodology_for('Financial Services','Credit Services'),'unsupported')
 def test_no_fabricated_zero(self):
  self.assertIsNone(recover_financial_inputs_v2362({})['fcf'])
if __name__=='__main__':unittest.main()
