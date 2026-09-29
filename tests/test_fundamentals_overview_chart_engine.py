"""Regression tests for the independent Financial Overview chart adapters."""
import unittest
from services.fundamentals_overview_chart_engine import performance_series, margin_series

class OverviewChartsTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "periods": ["2026-06-30", "2025-06-30"],
            "statements": {
                "Income Statement": {
                    "Revenue": {"2026-06-30": 100_000_000, "2025-06-30": 80_000_000},
                    "Operating Income (EBIT)": {"2026-06-30": -5_000_000, "2025-06-30": 10_000_000},
                    "Net Income": {"2026-06-30": None, "2025-06-30": 8_000_000},
                },
                "Cash Flow": {"Free Cash Flow": {"2026-06-30": 3_000_000}},
            },
        }

    def test_chronological_order_and_actual_values(self):
        rows = performance_series(self.data)
        self.assertEqual([r["Period"] for r in rows], ["2025-06-30", "2026-06-30"])
        self.assertEqual(rows[-1]["Operating Income"], -5_000_000)
        self.assertIsNone(rows[-1]["Net Income"])
        self.assertIsNone(rows[0]["Free Cash Flow"])

    def test_margins_are_percent_and_preserve_missing(self):
        rows = margin_series(self.data)
        self.assertEqual(rows[-1]["Operating Margin"], -5.0)
        self.assertIsNone(rows[-1]["Net Income Margin"])
        self.assertEqual(rows[0]["Net Income Margin"], 10.0)

    def test_zero_revenue_does_not_create_margin(self):
        self.data["statements"]["Income Statement"]["Revenue"]["2026-06-30"] = 0
        self.assertIsNone(margin_series(self.data)[-1]["Operating Margin"])

    def test_missing_data_is_not_interpolated(self):
        self.assertEqual(performance_series({"periods": ["2026-06-30"], "statements": {}})[0]["Revenue"], None)
        self.assertIsNone(margin_series({"periods": ["2026-06-30"], "statements": {}})[0]["Operating Margin"])

if __name__ == "__main__":
    unittest.main()
