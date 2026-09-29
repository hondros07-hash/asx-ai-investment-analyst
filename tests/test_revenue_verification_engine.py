"""Revenue verification must fail closed and never invent live revenue."""
import os
import unittest
from unittest.mock import patch
from services.revenue_verification_engine import reconcile_annual_revenue


class Response:
    def __init__(self, value): self.value=value
    def raise_for_status(self): pass
    def json(self): return self.value


class RevenueEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data={"periods":["2025-12-31"],"frequency":"Annual (5Y)","currency":"USD",
                   "statements":{"Income Statement":{"Revenue":{"2025-12-31":1000.0}}}}

    def test_no_configuration_fails_closed(self):
        with patch.dict(os.environ,{"AXIA_SEC_USER_AGENT":""}):
            result=reconcile_annual_revenue("ZIP",self.data)
        self.assertEqual(result["filing"]["status"],"Pending")
        self.assertEqual(result["snapshot"]["status"],"Not tested")

    def test_non_us_or_wrong_currency_never_calls_sec(self):
        def fail(*args,**kwargs): raise AssertionError("network must not run")
        self.data["currency"]="AUD"
        result=reconcile_annual_revenue("ZIP.AX",self.data,get=fail)
        self.assertEqual(result["independent"]["status"],"Unavailable")

    def test_exact_filing_reconciles(self):
        directory={"0":{"ticker":"ZIP","cik_str":1234}}
        facts={"cik":1234,"facts":{"us-gaap":{"Revenues":{"units":{"USD":[{
            "form":"10-K","start":"2025-01-01","end":"2025-12-31","val":1000,
            "filed":"2026-02-01","accn":"0000001234-26-000001"}]}}}}}
        def get(url,**kwargs): return Response(directory if "company_tickers" in url else facts)
        with patch.dict(os.environ,{"AXIA_SEC_USER_AGENT":"AXIA Testing test@example.com"}):
            result=reconcile_annual_revenue("ZIP",self.data,get=get)
        self.assertEqual(result["independent"]["status"],"Available")
        self.assertEqual(result["filing"]["status"],"Verified")
        self.assertEqual(result["snapshot"]["status"],"Not applicable")

    def test_mismatch_not_verified(self):
        directory={"0":{"ticker":"ZIP","cik_str":1234}}
        facts={"cik":1234,"facts":{"us-gaap":{"Revenues":{"units":{"USD":[{
            "form":"10-K","start":"2025-01-01","end":"2025-12-31","val":900,
            "filed":"2026-02-01","accn":"0000001234-26-000001"}]}}}}}
        def get(url,**kwargs): return Response(directory if "company_tickers" in url else facts)
        with patch.dict(os.environ,{"AXIA_SEC_USER_AGENT":"AXIA Testing test@example.com"}):
            result=reconcile_annual_revenue("ZIP",self.data,get=get)
        self.assertEqual(result["filing"]["status"],"Mismatch")


if __name__=="__main__": unittest.main()
