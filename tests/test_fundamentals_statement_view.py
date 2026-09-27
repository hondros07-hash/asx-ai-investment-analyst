"""Regression tests: python -m unittest tests.test_fundamentals_statement_view"""
import unittest
from services.fundamentals_statement_view_engine import transform,row_trend,display_frame

class StatementViewTests(unittest.TestCase):
 def sample(self):
  return {"periods":["2026-06-30","2025-06-30"],"frequency":"Annual (5Y)","derived":{("Revenue","2026-06-30"):"Derived"},
   "statements":{"Income Statement":{"Revenue":{"2026-06-30":120,"2025-06-30":100},"Net Income":{"2026-06-30":12,"2025-06-30":10},"Diluted EPS":{"2026-06-30":1,"2025-06-30":.8}}}}
 def test_growth_and_missing_prior(self):
  d=self.sample();r=transform(d,"Income Statement","Period growth")
  self.assertAlmostEqual(r.loc[0,"2026-06-30"],20)
  self.assertIsNone(r.loc[0,"2025-06-30"])
 def test_common_size(self):
  r=transform(self.sample(),"Income Statement","Common size")
  self.assertAlmostEqual(r.loc[1,"2026-06-30"],10)
  self.assertIsNone(r.loc[2,"2026-06-30"])
 def test_nonpositive_growth_base_withheld(self):
  d=self.sample();d["statements"]["Income Statement"]["Revenue"]["2025-06-30"]=0
  self.assertIsNone(transform(d,"Income Statement","Period growth").loc[0,"2026-06-30"])
 def test_ttm_growth_withheld(self):
  d=self.sample();d["frequency"]="TTM"
  self.assertIsNone(transform(d,"Income Statement","Period growth").loc[0,"2026-06-30"])
 def test_formatted_numeric_columns_do_not_raise_lossy_setitem(self):
  d=self.sample()
  def fmt(v,ratio=False,eps=False): return "—" if v is None else f"{v:,.2f}"
  for mode in ("Reported values","Period growth","Common size"):
   frame=display_frame(d,"Income Statement",mode,fmt)
   self.assertTrue(all(frame[p].dtype==object for p in d["periods"]))
   self.assertIsInstance(frame.loc[0,"2026-06-30"],str)
  self.assertIn("†",display_frame(d,"Income Statement","Reported values",fmt).loc[0,"2026-06-30"])
 def test_original_unchanged(self):
  d=self.sample();transform(d,"Income Statement","Common size")
  self.assertEqual(d["statements"]["Income Statement"]["Revenue"]["2026-06-30"],120)
  self.assertEqual(row_trend(d,"Income Statement","Revenue"),[100,120])

if __name__=="__main__": unittest.main()
