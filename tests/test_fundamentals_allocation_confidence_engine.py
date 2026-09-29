"""Evidence and reconciliation regression tests for Overview cards."""
import unittest
from services.fundamentals_allocation_confidence_engine import capital_bridge, confidence

class AllocationConfidenceTests(unittest.TestCase):
 def setUp(self):
  self.data={"periods":["2026-06-30"],"currency":"USD",
    "statements":{"Income Statement":{},"Balance Sheet":{},
      "Cash Flow":{"Operating Cash Flow":{"2026-06-30":100_000_000},
                   "Capital Expenditure":{"2026-06-30":-20_000_000},
                   "Free Cash Flow":{"2026-06-30":80_000_000}}},
    "derived":{}}
 def test_reconciled_bridge(self):
  b=capital_bridge(self.data)
  self.assertTrue(b["reconciles"])
  self.assertEqual(b["capex"],-20_000_000)
  self.assertFalse(b["allocation_available"])
 def test_unreconciled_total_not_represented_as_reconciled(self):
  self.data["statements"]["Cash Flow"]["Free Cash Flow"]["2026-06-30"]=90_000_000
  self.assertFalse(capital_bridge(self.data)["reconciles"])
 def test_missing_values_not_imputed(self):
  self.data["statements"]["Cash Flow"]["Operating Cash Flow"]={}
  b=capital_bridge(self.data)
  self.assertIsNone(b["ocf"])
  self.assertFalse(b["reconciles"])
 def test_no_unverified_filing_badges(self):
  a=confidence(self.data)
  self.assertEqual(a["filing_links"],0)
  self.assertFalse(a["filing_verified"])
  self.assertGreaterEqual(a["not_testable"],1)
if __name__=="__main__": unittest.main()
