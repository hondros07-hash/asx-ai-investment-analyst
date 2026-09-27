"""Regression tests: python -m unittest tests.test_fundamentals_statement_view"""
import unittest
from services.fundamentals_statement_view_engine import transform,row_trend,display_frame,statement_table

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
 def test_inline_sparkline_and_reversed_periods(self):
  d=self.sample()
  def fmt(v,ratio=False,eps=False): return "—" if v is None else f"{v:,.2f}"
  frame=statement_table(d,"Income Statement","Reported values",fmt,reverse=True)
  self.assertEqual(list(frame.columns),["Line item","10Y Trend","2025-06-30","2026-06-30"])
  self.assertTrue(frame.loc[0,"10Y Trend"].startswith("data:image/svg+xml;base64,"))
  self.assertEqual(frame.loc[0,"2026-06-30"],"120.00 †")
  self.assertEqual(frame.loc[0,"2025-06-30"],"100.00")
 def test_inline_sparkline_missing_and_disabled(self):
  d=self.sample()
  d["statements"]["Income Statement"]["Net Income"]["2025-06-30"]=None
  def fmt(v,ratio=False,eps=False): return "—" if v is None else f"{v:,.2f}"
  frame=statement_table(d,"Income Statement","Common size",fmt)
  self.assertIsNone(frame.loc[1,"10Y Trend"])
  plain=statement_table(d,"Income Statement","Period growth",fmt,sparklines=False)
  self.assertNotIn("10Y Trend",plain.columns)
 def test_original_unchanged(self):
  d=self.sample();transform(d,"Income Statement","Common size")
  self.assertEqual(d["statements"]["Income Statement"]["Revenue"]["2026-06-30"],120)
  self.assertEqual(row_trend(d,"Income Statement","Revenue"),[100,120])

if __name__=="__main__": unittest.main()
