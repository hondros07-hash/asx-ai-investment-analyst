"""Run: python -m unittest tests.test_earnings_quality_engine"""
import unittest
from services.earnings_quality_engine import calculate,export_rows

class EarningsQualityTests(unittest.TestCase):
 def sample(self):
  p,q="2026-06-30","2025-06-30"
  return {"periods":[p,q],"frequency":"Annual (5Y)","derived":{("Free Cash Flow",p):"Derived"},
   "statements":{"Income Statement":{"Net Income":{p:50,q:40},"Diluted Shares":{p:110,q:100},"Revenue":{p:200,q:180}},
    "Balance Sheet":{"Total Assets":{p:500,q:400},"Receivables":{p:30,q:25},"Inventory":{p:10,q:9}},
    "Cash Flow":{"Operating Cash Flow":{p:60,q:45},"Free Cash Flow":{p:30,q:25}}}}
 def test_conversion_and_accruals(self):
  row=calculate(self.sample())[0]
  self.assertAlmostEqual(row["metrics"]["Operating cash conversion"],1.2)
  self.assertAlmostEqual(row["metrics"]["Free cash flow conversion"],.6)
  self.assertAlmostEqual(row["metrics"]["Accruals / average assets"],-10/450)
  self.assertAlmostEqual(row["metrics"]["Diluted share count change"],.1)
  self.assertTrue(row["derived_fcf"])
 def test_no_prior_assets_no_accruals(self):
  self.assertIsNone(calculate(self.sample())[1]["metrics"]["Accruals / average assets"])
 def test_nonpositive_net_income_withheld(self):
  data=self.sample();data["statements"]["Income Statement"]["Net Income"]["2026-06-30"]=0
  self.assertIsNone(calculate(data)[0]["metrics"]["Operating cash conversion"])
 def test_ttm_suppresses_unmatched_metrics(self):
  data=self.sample();data["frequency"]="TTM"
  row=calculate(data)[0]["metrics"]
  self.assertIsNone(row["Accruals / average assets"])
  self.assertIsNone(row["Diluted share count change"])
 def test_export_provenance(self):
  self.assertEqual(export_rows(calculate(self.sample()))[0]["FCF basis"],"Derived from OCF and CapEx")

if __name__=="__main__": unittest.main()
