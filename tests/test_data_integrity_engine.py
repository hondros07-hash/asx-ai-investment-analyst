"""V23.9 data integrity regression tests (stdlib only)."""
import unittest
from services.data_integrity_engine import identity, currency_code, audit_snapshot

class DataIntegrityTests(unittest.TestCase):
    def test_explicit_listing_and_ambiguous_bare_symbol(self):
        self.assertEqual(identity("ZIP.AX")["exchange"], "ASX")
        self.assertEqual(identity("ZIP")["exchange"], "Unconfirmed")
        self.assertFalse(identity("ZIP")["exchange_confirmed"])
        self.assertEqual(identity("KO", {"longName": "The Coca-Cola Company"})["name"],
                         "The Coca-Cola Company")

    def test_financial_currency_not_inferred_from_exchange(self):
        self.assertEqual(currency_code({"currency": "AUD"}), "Unconfirmed")
        self.assertEqual(currency_code({"financialCurrency": "usd"}), "USD")

    def test_ratios_are_fractional_and_invalid_values_are_removed(self):
        snapshot = {"ticker": "ZIP.AX", "meta": {"financialCurrency": "AUD"},
                    "periods": ["2025-12-31"],
                    "ratios": {"2025-12-31": {"Operating Margin": -0.12,
                                            "Current Ratio": -1,
                                            "Gross Margin": float("inf"),
                                            "Net Margin": 0.23}},
                    "statements": {}}
        result = audit_snapshot(snapshot)
        values = result["ratios"]["2025-12-31"]
        self.assertEqual(values["Operating Margin"], -0.12)
        self.assertEqual(values["Net Margin"], 0.23)
        self.assertIsNone(values["Current Ratio"])
        self.assertIsNone(values["Gross Margin"])
        self.assertEqual(result["status"], "error")

    def test_duplicate_periods_and_nonfinite_statements_flagged(self):
        result = audit_snapshot({"ticker": "KO", "meta": {}, "periods": ["2025", "2025"],
                                 "statements": {"Income Statement": {"Revenue": {"2025": float("nan")}}}})
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("duplicate_periods", codes)
        self.assertIn("invalid_statement_value", codes)

if __name__ == "__main__":
    unittest.main()
