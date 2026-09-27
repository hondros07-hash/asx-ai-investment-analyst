import unittest
from services.capital_allocation_engine import build
class CapitalAllocationTests(unittest.TestCase):
 def test_bridge_and_derived_provenance(self):
  data={"periods":["FY26"],"derived":{("Free Cash Flow","FY26"):"Derived"},"statements":{"Cash Flow":{"Operating Cash Flow":{"FY26":100},"Capital Expenditure":{"FY26":-30},"Free Cash Flow":{"FY26":70},"Financing Cash Flow":{"FY26":-20}}}}
  row=build(data)[0]
  self.assertEqual(row["OCF less CapEx"],70)
  self.assertEqual(row["FCF bridge difference"],0)
  self.assertIn("Derived",row["FCF basis"])
 def test_missing_is_not_zero(self):
  data={"periods":["FY26"],"statements":{"Cash Flow":{"Operating Cash Flow":{"FY26":100}}}}
  row=build(data)[0]
  self.assertIsNone(row["FCF bridge difference"])
  self.assertIsNone(row["Capital expenditure (absolute)"])
if __name__=="__main__": unittest.main()
