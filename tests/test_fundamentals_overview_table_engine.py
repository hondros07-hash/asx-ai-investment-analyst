"""Regression checks for Financial Overview tables."""
import unittest
from services.fundamentals_overview_table_engine import statements, ratio_rows

class OverviewTableTests(unittest.TestCase):
    def setUp(self):
        self.data={"periods":["2026-06-30","2025-06-30"],
                   "statements":{"Income Statement":{"Revenue":{"2026-06-30":100_000_000,"2025-06-30":80_000_000},
                      "Operating Income (EBIT)":{"2026-06-30":-5_000_000},
                      "Diluted EPS":{"2026-06-30":1.2}},
                      "Cash Flow":{"Free Cash Flow":{"2026-06-30":20_000_000}}},
                   "ratios":{"2026-06-30":{"Gross Margin":0.6}}}
    def test_statements_preserve_missing_and_negative(self):
        rows=statements(self.data)
        self.assertEqual(rows[0]["Operating Income"],-5_000_000)
        self.assertIsNone(rows[0]["Gross Profit"])
        self.assertIsNone(rows[1]["Free Cash Flow"])
    def test_ratios_use_comparable_periods_and_no_fabricated_roic(self):
        rows={row["Metric"]:row for row in ratio_rows(self.data)}
        self.assertEqual(rows["Gross Margin"]["Values"],[None,0.6])
        self.assertEqual(rows["Free Cash Flow Margin"]["Values"],[None,0.2])
        self.assertEqual(rows["ROIC"]["Values"],[None,None])
    def test_zero_revenue_withholds_cash_flow_margin(self):
        self.data["statements"]["Income Statement"]["Revenue"]["2026-06-30"]=0
        rows={row["Metric"]:row for row in ratio_rows(self.data)}
        self.assertIsNone(rows["Free Cash Flow Margin"]["Values"][-1])
if __name__=="__main__": unittest.main()
