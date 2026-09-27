"""Run: python -m unittest tests.test_advanced_fundamental_ratios"""
import unittest
from services.advanced_fundamental_ratios_engine import compute

class AdvancedRatioTests(unittest.TestCase):
 def sample(self,sector="general"):
  p,q="2026-06-30","2025-06-30"
  def pair(a,b): return {p:a,q:b}
  return {"periods":[p,q],"frequency":"Annual (5Y)","category":sector,"statements":{
   "Income Statement":{"Revenue":pair(200,180),"Cost of Revenue":pair(100,90),"Operating Income (EBIT)":pair(40,35),"EBITDA":pair(50,45),"Interest Expense":pair(-10,-9),"Pretax Income":pair(30,26),"Tax Provision":pair(6,5)},
   "Balance Sheet":{"Receivables":pair(20,18),"Inventory":pair(10,8),"Accounts Payable":pair(12,10),"Total Debt":pair(80,70),"Net Debt":pair(60,55),"Stockholders Equity":pair(100,90),"Cash & Equivalents":pair(20,15),"Current Assets":pair(60,55),"Current Liabilities":pair(30,25)},
   "Cash Flow":{"Operating Cash Flow":pair(30,25),"Free Cash Flow":pair(20,15)}}}
 def test_ratios(self):
  r,_=compute(self.sample());x=r["2026-06-30"]
  self.assertAlmostEqual(x["Interest Coverage"],4)
  self.assertAlmostEqual(x["Net Debt / EBITDA"],1.2)
  self.assertAlmostEqual(x["DSO (days)"],34.675)
  self.assertAlmostEqual(x["Cash Conversion Cycle (days)"],34.675+32.85-40.15)
  self.assertAlmostEqual(x["ROIC (effective tax proxy)"],32/152.5)
 def test_missing_and_zero_denominator(self):
  d=self.sample();d["statements"]["Income Statement"]["EBITDA"]["2026-06-30"]=0
  d["statements"]["Balance Sheet"]["Accounts Payable"]["2025-06-30"]=None
  r,_=compute(d);self.assertIsNone(r["2026-06-30"]["Net Debt / EBITDA"]);self.assertIsNone(r["2026-06-30"]["Cash Conversion Cycle (days)"])
 def test_sector_suppression(self):
  r,_=compute(self.sample("bank"))
  self.assertIsNone(r["2026-06-30"]["ROIC (effective tax proxy)"])
  self.assertIsNone(r["2026-06-30"]["DSO (days)"])
 def test_ttm_no_average_balance(self):
  d=self.sample();d["frequency"]="TTM"
  r,_=compute(d);self.assertIsNone(r["2026-06-30"]["ROIC (effective tax proxy)"]);self.assertIsNone(r["2026-06-30"]["DSO (days)"])

if __name__=="__main__": unittest.main()
