import unittest
from datetime import date
from services.financial_kpi_engine import (
    Observation, build_kpi, calculate_growth, chart_points,
    delta_state, format_financial_value,
)


def obs(year, quarter, value, currency="USD"):
    month = quarter * 3
    return Observation(f"Q{quarter} {year}", date(year, month, 28),
                       value, currency, "quarterly", "reported")


class FinancialKPITests(unittest.TestCase):
    def test_format_and_sign(self):
        self.assertEqual(format_financial_value(47940000000, "USD"), "$47.94B")
        self.assertEqual(format_financial_value(-1200000, "USD"), "-$1.20M")

    def test_growth_zero_and_negative_denominator(self):
        self.assertIsNone(calculate_growth(10, 0))
        self.assertIsNone(calculate_growth(10, -2))
        self.assertAlmostEqual(calculate_growth(102, 100), 2)

    def test_yoy_and_qoq(self):
        rows = [obs(2024, q, 100) for q in range(1, 5)] + [obs(2025, 1, 110)]
        self.assertAlmostEqual(build_kpi(rows, "quarterly").growth_pct, 10)
        self.assertAlmostEqual(build_kpi(rows, "quarterly", "qoq").growth_pct, 10)

    def test_ttm(self):
        rows = [obs(y, q, 100 if y == 2024 else 110)
                for y in (2024, 2025) for q in range(1, 5)]
        result = build_kpi(rows, "ttm")
        self.assertEqual(result.value, 440)
        self.assertEqual(result.previous, 400)
        self.assertAlmostEqual(result.growth_pct, 10)
        self.assertEqual(chart_points(result)[-1]["value"], 110)

    def test_incomplete_and_mismatched(self):
        self.assertEqual(build_kpi([obs(2025, 1, 5)], "ttm").status, "incomplete_ttm")
        self.assertEqual(build_kpi([obs(2025, 1, 5), obs(2025, 2, 6, "AUD")],
                                   "quarterly").status, "currency_mismatch")

    def test_reverse_scale(self):
        self.assertEqual(delta_state(5, True), "negative")
        self.assertEqual(delta_state(-5, True), "positive")


if __name__ == "__main__":
    unittest.main()
