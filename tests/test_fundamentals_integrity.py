"""Run with: python -m unittest tests.test_fundamentals_integrity"""
import unittest
from services.fundamentals_integrity_engine import validate

class IntegrityTests(unittest.TestCase):
    def sample(self):
        p="2026-06-30"
        return {"periods":[p],"currency":"Unconfirmed","frequency":"Annual (5Y)","derived":{},
                "statements":{"Income Statement":{"Revenue":{p:100},"Cost of Revenue":{p:40},"Gross Profit":{p:60}},
                "Balance Sheet":{"Total Assets":{p:100},"Total Liabilities":{p:60},"Stockholders Equity":{p:40}},
                "Cash Flow":{"Operating Cash Flow":{p:20},"Capital Expenditure":{p:-5},"Free Cash Flow":{p:15}}}}
    def test_consistent_statements(self):
        rows=validate(self.sample())
        self.assertEqual(sum(r["Status"]=="Pass" for r in rows),3)
        self.assertTrue(any(r["Status"]=="Unconfirmed" for r in rows))
    def test_balance_mismatch(self):
        data=self.sample();data["statements"]["Balance Sheet"]["Total Liabilities"]["2026-06-30"]=50
        self.assertTrue(any(r["Check"]=="Assets = liabilities + equity" and r["Status"]=="Mismatch" for r in validate(data)))
    def test_derived_is_not_independently_verified(self):
        data=self.sample();data["derived"][("Free Cash Flow","2026-06-30")]="Derived"
        self.assertTrue(any(r["Check"]=="FCF definition consistency" and r["Status"]=="Not testable" for r in validate(data)))
    def test_missing_is_not_pass(self):
        data=self.sample();data["statements"]["Balance Sheet"]["Total Liabilities"]["2026-06-30"]=None
        self.assertTrue(any(r["Check"]=="Assets = liabilities + equity" and r["Status"]=="Not testable" for r in validate(data)))

if __name__=="__main__": unittest.main()
