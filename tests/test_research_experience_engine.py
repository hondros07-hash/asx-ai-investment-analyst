import unittest
from services.research_experience_engine import validate_research_condition, evidence_reference


class ResearchExperienceTests(unittest.TestCase):
    def test_missing_evidence_is_not_zero(self):
        self.assertFalse(validate_research_condition("Revenue growth", 5, None, "FY26 report")[0])

    def test_source_is_required(self):
        self.assertFalse(validate_research_condition("Revenue growth", 5, 8, "")[0])

    def test_valid_condition(self):
        self.assertTrue(validate_research_condition("Revenue growth", 5, 8, "FY26 report p. 4")[0])

    def test_only_http_urls_are_linkable(self):
        self.assertIsNone(evidence_reference("javascript:alert(1)")["url"])
        self.assertIsNone(evidence_reference("FY26 report p. 4")["url"])
        self.assertEqual(evidence_reference("https://example.com/report.pdf")["url"], "https://example.com/report.pdf")


if __name__ == "__main__":
    unittest.main()
