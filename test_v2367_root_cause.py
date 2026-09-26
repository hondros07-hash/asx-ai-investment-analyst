import unittest
import pandas as pd
from services.valuation_evidence import cashflow_row_diagnostics, recover_financial_inputs_v2362
class RootCauseTests(unittest.TestCase):
 def test_populated_statement_derives_fcf(self):
  d=pd.to_datetime(['2026-06-30','2025-06-30'])
  cf=pd.DataFrame([[100,90],[-20,-18]],index=['Operating Cash Flow','Capital Expenditure'],columns=d)
  result=recover_financial_inputs_v2362({},annual_cf=cf)
  self.assertEqual(result['fcf'],80)
  self.assertEqual(cashflow_row_diagnostics(cf)['matched_periods'],['2026-06-30','2025-06-30'])
 def test_missing_capex_diagnostic(self):
  cf=pd.DataFrame([[100]],index=['Operating Cash Flow'],columns=[pd.Timestamp('2026-06-30')])
  self.assertIsNone(cashflow_row_diagnostics(cf)['capex_row'])
 def test_negative_is_not_missing(self):
  cf=pd.DataFrame([[10],[-20]],index=['Operating Cash Flow','Capital Expenditure'],columns=[pd.Timestamp('2026-06-30')])
  result=recover_financial_inputs_v2362({},annual_cf=cf)
  self.assertEqual(result['fcf'],-10)
  self.assertEqual(result['audit']['inputs']['fcf']['status'],'derived')
if __name__=='__main__':unittest.main()
