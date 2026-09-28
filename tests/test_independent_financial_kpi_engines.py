import unittest
from unittest.mock import patch
from services import independent_financial_kpi_engines as engine


class IndependentKPITests(unittest.TestCase):
    def setUp(self):
        self.data = {"periods": ["2026-06-30", "2025-06-30"],
                     "frequency": "Annual (5Y)",
                     "statements": {
                         "Income Statement": {
                             "Revenue": {"2026-06-30": 110.0, "2025-06-30": 100.0},
                             "Operating Income (EBIT)": {"2026-06-30": 22.0, "2025-06-30": 20.0},
                             "Net Income": {"2026-06-30": 11.0, "2025-06-30": 10.0}},
                         "Cash Flow": {"Free Cash Flow": {"2026-06-30": 8.0, "2025-06-30": 7.0}}},
                     "ratios": {"2026-06-30": {"Operating Margin": 0.2},
                                "2025-06-30": {"Operating Margin": 0.2}}}

    def test_all_five_have_separate_results(self):
        results = engine.run_independently(self.data, "AUD")
        self.assertEqual(len(results), 5)
        self.assertEqual(results["Revenue"]["value"], 110)
        self.assertEqual(results["Operating Income"]["value"], 22)
        self.assertEqual(results["Operating Margin"]["value"], 0.2)

    def test_one_engine_failure_does_not_break_other_cards(self):
        with patch.dict(engine.ENGINES, {"Revenue": lambda *_: 1 / 0}):
            results = engine.run_independently(self.data, "AUD")
        self.assertEqual(results["Revenue"]["status"], "error")
        self.assertEqual(results["Net Income"]["value"], 11)
        self.assertEqual(results["Free Cash Flow"]["value"], 8)

    def test_missing_metric_does_not_use_other_metric(self):
        self.data["statements"]["Cash Flow"] = {}
        results = engine.run_independently(self.data, "AUD")
        self.assertIsNone(results["Free Cash Flow"]["value"])
        self.assertEqual(results["Revenue"]["value"], 110)


if __name__ == "__main__":
    unittest.main()
