import unittest
from services.operating_income_engine import calculate
from services.independent_financial_kpi_engines import run_independently


def snapshot(latest=425100000, prior=405240000, frequency="Annual (5Y)"):
    return {"frequency": frequency, "periods": ["2026-06-30", "2025-06-30"],
            "statements": {"Income Statement": {"Operating Income (EBIT)":
                {"2026-06-30": latest, "2025-06-30": prior}}}}


class OperatingIncomeTests(unittest.TestCase):
    def test_growth_and_period(self):
        result = calculate(snapshot(), "AUD")
        self.assertEqual(result["value"], 425100000)
        self.assertEqual(result["period"], "2026-06-30")
        self.assertEqual(result["delta"], "+4.9% YoY")

    def test_turnaround(self):
        result = calculate(snapshot(20, -10), "AUD")
        self.assertEqual(result["delta"], "Turnaround")
        self.assertEqual(result["comparison_status"], "turnaround")

    def test_turned_negative(self):
        result = calculate(snapshot(-20, 10), "AUD")
        self.assertEqual(result["delta"], "Turned negative")

    def test_zero_baseline(self):
        result = calculate(snapshot(10, 0), "AUD")
        self.assertIsNone(result["delta"])
        self.assertEqual(result["comparison_status"], "zero_baseline")

    def test_negative_improvement(self):
        self.assertEqual(calculate(snapshot(-5, -10), "AUD")["delta"], "+50.0% YoY")

    def test_missing_comparison(self):
        data = snapshot()
        del data["statements"]["Income Statement"]["Operating Income (EBIT)"]["2025-06-30"]
        self.assertIsNone(calculate(data, "AUD")["delta"])

    def test_ttm_no_false_yoy(self):
        self.assertIsNone(calculate(snapshot(frequency="TTM"), "AUD")["delta"])

    def test_no_other_card_is_affected(self):
        data = snapshot()
        data["statements"]["Income Statement"]["Revenue"] = {"2026-06-30": 100, "2025-06-30": 90}
        result = run_independently(data, "AUD")
        self.assertEqual(result["Operating Income"]["delta"], "+4.9% YoY")
        self.assertEqual(result["Revenue"]["value"], 100)


if __name__ == "__main__":
    unittest.main()
