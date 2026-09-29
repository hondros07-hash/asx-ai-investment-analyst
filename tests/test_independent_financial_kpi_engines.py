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

    def test_operating_income_decline_exposes_prior_year_evidence(self):
        self.data["statements"]["Income Statement"]["Operating Income (EBIT)"]["2026-06-30"] = 17.64
        result = engine.operating_income(self.data, "AUD")
        self.assertEqual(result["comparison_status"], "declining")
        self.assertEqual(result["previous_value"], 20.0)
        self.assertEqual(result["previous_period"], "2025-06-30")
        self.assertEqual(result["delta"], "-11.8% YOY")

    def test_operating_income_loss_narrowing_is_improvement(self):
        self.data["statements"]["Income Statement"]["Operating Income (EBIT)"] = {
            "2026-06-30": -8.0, "2025-06-30": -10.0}
        result = engine.operating_income(self.data, "AUD")
        self.assertEqual(result["comparison_status"], "improving")
        self.assertEqual(result["delta"], "Loss narrowed YoY")

    def test_operating_income_turnaround_and_new_loss(self):
        values = self.data["statements"]["Income Statement"]["Operating Income (EBIT)"]
        values["2025-06-30"], values["2026-06-30"] = -10.0, 2.0
        self.assertEqual(engine.operating_income(self.data, "AUD")["comparison_status"], "turnaround")
        values["2025-06-30"], values["2026-06-30"] = 10.0, -2.0
        self.assertEqual(engine.operating_income(self.data, "AUD")["comparison_status"], "turned_negative")

    def test_operating_income_missing_comparison_is_not_invented(self):
        del self.data["statements"]["Income Statement"]["Operating Income (EBIT)"]["2025-06-30"]
        result = engine.operating_income(self.data, "AUD")
        self.assertIsNone(result["previous_value"])
        self.assertIsNone(result["previous_period"])
        self.assertEqual(result["comparison_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
