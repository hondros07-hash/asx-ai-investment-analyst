import unittest
from services.sector_kpi_engine import kpi_rows, disclosure_destinations

class SectorKpiTests(unittest.TestCase):
 def test_bnpl_rows_are_not_invented(self):
  rows=kpi_rows("bnpl")
  self.assertTrue(any("Transaction Volume" in row["Metric"] for row in rows))
  self.assertTrue(all(row["Value"]=="Not verified" for row in rows))
 def test_asx_disclosure_destination(self):
  self.assertEqual(disclosure_destinations("ZIP.AX")[0]["url"],"https://www.asx.com.au/markets/company/ZIP")
 def test_no_invented_destination(self):
  self.assertEqual(disclosure_destinations(""),[])

if __name__=="__main__": unittest.main()
