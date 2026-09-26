import unittest
import pandas as pd
from services.valuation_evidence import recover_financial_inputs_v2362

class RecoveryTests(unittest.TestCase):
    def test_ttm_matched_quarters(self):
        dates=pd.to_datetime(["2026-06-30","2026-03-31","2025-12-31","2025-09-30"])
        cf=pd.DataFrame([[100,110,120,130],[-20,-20,-20,-20]],index=["Operating Cash Flow","Capital Expenditure"],columns=dates)
        bs=pd.DataFrame([[50],[10],[1000]],index=["Cash And Cash Equivalents","Total Debt","Ordinary Shares Number"],columns=[dates[0]])
        r=recover_financial_inputs_v2362({"currency":"AUD","financialCurrency":"AUD"},quarterly_cf=cf,quarterly_bs=bs)
        self.assertEqual(r["fcf"],380)
        self.assertTrue(r["audit"]["balance_sheet_complete"])
        self.assertTrue(r["audit"]["complete_for_dcf"])
    def test_missing_quarter_not_annualized(self):
        dates=pd.to_datetime(["2026-06-30","2026-03-31","2025-09-30","2025-06-30"])
        cf=pd.DataFrame([[100]*4,[-20]*4],index=["Operating Cash Flow","Capital Expenditure"],columns=dates)
        r=recover_financial_inputs_v2362({},quarterly_cf=cf)
        self.assertIsNone(r["fcf"])
    def test_missing_debt_not_zero(self):
        r=recover_financial_inputs_v2362({"freeCashflow":100,"sharesOutstanding":1000,"totalCash":20,"currency":"AUD","financialCurrency":"AUD"})
        self.assertFalse(r["audit"]["balance_sheet_complete"])
    def test_annual_fallback(self):
        dt=pd.to_datetime(["2025-12-31"])
        cf=pd.DataFrame([[100],[-25]],index=["Operating Cash Flow","Capital Expenditure"],columns=dt)
        r=recover_financial_inputs_v2362({},annual_cf=cf)
        self.assertEqual(r["fcf"],75)
        self.assertEqual(r["audit"]["inputs"]["fcf"]["source"],"annual_cash_flow")
if __name__=="__main__":unittest.main()
