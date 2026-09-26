import unittest
import pandas as pd
from services.valuation_evidence import recover_financial_inputs_v2362
class PipelineTests(unittest.TestCase):
 def test_derived_annual_interim_bridge(self):
  annual=pd.DataFrame({pd.Timestamp('2025-06-30'):[120,-20]},index=['Operating Cash Flow','Capital Expenditure'])
  interim=pd.DataFrame({pd.Timestamp('2025-12-31'):[70,-10],pd.Timestamp('2024-12-31'):[50,-10]},index=['Operating Cash Flow','Capital Expenditure'])
  r=recover_financial_inputs_v2362({},annual_cf=annual,quarterly_cf=interim)
  self.assertEqual(r['fcf'],120)
  self.assertEqual(r['audit']['inputs']['fcf']['source'],'annual_plus_interim_bridge')
 def test_missing_rows_not_fabricated(self):
  annual=pd.DataFrame({pd.Timestamp('2025-06-30'):[100]},index=['Operating Cash Flow'])
  r=recover_financial_inputs_v2362({},annual_cf=annual)
  self.assertIsNone(r['fcf'])
  self.assertEqual(r['audit']['inputs']['fcf']['status'],'missing')
 def test_negative_fcf_is_not_missing(self):
  annual=pd.DataFrame({pd.Timestamp('2025-06-30'):[10,-20]},index=['Operating Cash Flow','Capital Expenditure'])
  r=recover_financial_inputs_v2362({},annual_cf=annual)
  self.assertEqual(r['fcf'],-10)
  self.assertEqual(r['audit']['inputs']['fcf']['status'],'derived')
  self.assertFalse(r['audit']['complete_for_dcf'])
if __name__=='__main__':unittest.main()
