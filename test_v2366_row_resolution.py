import unittest
import pandas as pd
from services.valuation_evidence import _row,ALIASES,_fcf_from_statement
class TestRowResolution(unittest.TestCase):
 def test_provider_variant(self):
  df=pd.DataFrame({'2025-06-30':[150,-30]},index=['Net Cash Provided By Operating Activities','Payments To Acquire Property Plant And Equipment'])
  value,proof=_fcf_from_statement(df)
  self.assertEqual(value,120)
 def test_transposed(self):
  df=pd.DataFrame({'Operating Cash Flow':[150],'Capital Expenditure':[-30]},index=['2025-06-30'])
  value,proof=_fcf_from_statement(df)
  self.assertEqual(value,120)
 def test_missing_capex_is_not_zero(self):
  df=pd.DataFrame({'2025-06-30':[150]},index=['Operating Cash Flow'])
  value,proof=_fcf_from_statement(df)
  self.assertIsNone(value)
if __name__=='__main__':unittest.main()
