import unittest
from services.security_identity import names_compatible, validate_identity


class IdentityTests(unittest.TestCase):
    def test_coca_cola_name_variants(self):
        self.assertTrue(names_compatible("The Coca-Cola Company", "Coca-Cola"))
        self.assertTrue(validate_identity("KO", "The Coca-Cola Company",
                                          {"longName": "The Coca-Cola Company"})["valid"])

    def test_wrong_company_is_rejected(self):
        result = validate_identity("KO", "The Coca-Cola Company",
                                   {"longName": "PepsiCo, Inc."})
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "company_name_mismatch")

    def test_missing_provider_name_is_not_verified(self):
        result = validate_identity("KO", "The Coca-Cola Company", {})
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "provider_name_missing")


if __name__ == "__main__":
    unittest.main()
