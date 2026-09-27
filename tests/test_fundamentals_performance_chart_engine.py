import unittest
from services.fundamentals_performance_chart_engine import performance

class PerformanceChartTests(unittest.TestCase):
 def sample(self):
  return {"periods":["FY26","FY25"],"statements":{"Income Statement":{"Revenue":{"FY26":200,"FY25":100},"Operating Income (EBIT)":{"FY26":40,"FY25":20},"Net Income":{"FY26":20,"FY25":10}},"Cash Flow":{"Free Cash Flow":{"FY26":15,"FY25":8}}}}
 def test_oldest_first_and_margins(self):
  rows=performance(self.sample())
  self.assertEqual([r["Period"] for r in rows],["FY25","FY26"])
  self.assertEqual(rows[-1]["Operating margin"],20)
  self.assertEqual(rows[-1]["Net income margin"],10)
 def test_missing_and_zero_revenue(self):
  data=self.sample();data["statements"]["Income Statement"]["Revenue"]["FY26"]=0
  data["statements"]["Cash Flow"]["Free Cash Flow"]["FY26"]=None
  row=performance(data)[-1]
  self.assertIsNone(row["Operating margin"])
  self.assertIsNone(row["Net income margin"])
  self.assertIsNone(row["Free cash flow"])
 def test_no_mutation(self):
  data=self.sample();original=list(data["periods"]);performance(data)
  self.assertEqual(data["periods"],original)

if __name__=="__main__": unittest.main()
