"""Contract tests for the five-question investor brief."""
import unittest

from services.investor_simplicity import build_investor_brief


class InvestorSimplicityTests(unittest.TestCase):
    def test_missing_evidence_is_not_good_news(self):
        result = build_investor_brief({"ticker": "ZIP.AX"}, {})
        self.assertEqual(result["available_count"], 0)
        self.assertEqual(len(result["sections"]), 5)
        self.assertTrue(all(s["evidence_status"] == "unavailable" for s in result["sections"]))

    def test_verified_requires_source_and_date(self):
        result = build_investor_brief({}, {"performance": {"summary": "Revenue rose", "status": "verified"}})
        self.assertEqual(result["sections"][1]["evidence_status"], "unavailable")

    def test_attributed_verified_evidence_survives(self):
        item = {"summary": "Revenue rose", "status": "verified", "source": "Annual report",
                "as_of": "2026-06-30", "detail_url": "/research/financials"}
        result = build_investor_brief({"name": "Example"}, {"performance": item})
        self.assertEqual(result["sections"][1]["summary"], "Revenue rose")
        self.assertEqual(result["sections"][1]["detail_url"], "/research/financials")
        self.assertEqual(result["available_count"], 1)

    def test_unknown_status_cannot_become_verified(self):
        result = build_investor_brief({}, {"risks": {"summary": "No risks", "status": "green"}})
        self.assertEqual(result["sections"][3]["evidence_status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
