import unittest
from datetime import date
import pandas as pd
from services.dividend_calendar_engine import normalize_dividends, top_five


class DividendCalendarTests(unittest.TestCase):
    def setUp(self):
        self.today=date(2026,9,29)
        self.rows=pd.DataFrame([
            {"Ticker":"HVN.AX","Company":"Harvey Norman","Ex-Date":"2026-10-06","Pay-Date":"2026-11-01","Amount":0.13,"Source":"Provider"},
            {"Ticker":"FPH.NZ","Company":"Fisher & Paykel","Ex-Date":"2026-10-07","Pay-Date":"2026-11-03","Amount":0.2},
            {"Ticker":"OLD.AX","Ex-Date":"2026-08-01","Pay-Date":"2026-09-28"},
            {"Ticker":"UNKNOWN.AX","Ex-Date":"2026-10-02","Pay-Date":"—"},
            {"Ticker":"LATE.AX","Ex-Date":"2026-10-02","Pay-Date":"2027-01-01"},
        ])
    def test_country_and_payment_window(self):
        au=normalize_dividends(self.rows,"Australia",self.today)
        self.assertEqual(au["Ticker"].tolist(),["HVN.AX"])
        self.assertEqual(au.iloc[0]["Evidence status"],"Provider-reported · official filing not reconciled")
        self.assertEqual(normalize_dividends(self.rows,"New Zealand",self.today)["Ticker"].tolist(),["FPH.NZ"])
    def test_top_five(self):
        rows=pd.concat([self.rows.iloc[[0]]]*7,ignore_index=True)
        self.assertEqual(len(top_five(rows)),5)
    def test_missing_pay_date_not_guessed(self):
        self.assertNotIn("UNKNOWN.AX",normalize_dividends(self.rows,"Australia",self.today)["Ticker"].tolist())


if __name__=="__main__":unittest.main()
