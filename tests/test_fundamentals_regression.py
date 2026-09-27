"""Regression coverage for Fundamentals financial calculations."""
import unittest
import ast
from pathlib import Path
from services.fundamentals_engine import category, derive

class FundamentalsRegressionTests(unittest.TestCase):
 def test_issuer_logo_url_uses_unshadowed_url_encoder(self):
  source=Path(__file__).resolve().parents[1].joinpath("views/fundamentals_view.py").read_text(encoding="utf-8")
  tree=ast.parse(source)
  header=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="_issuer_header")
  encoder_calls=[node for node in ast.walk(header) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="url_quote"]
  self.assertGreaterEqual(len(encoder_calls),2)
  self.assertFalse(any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=="quote" for node in ast.walk(header)))

 def test_exchange_aware_zip(self):
  self.assertEqual(category({"longName":"Zip Co Limited"},"ZIP.AX"),"bnpl")
  self.assertEqual(category({"longName":"ZipRecruiter, Inc."},"ZIP"),"general")

 def test_missing_data_and_negative_equity(self):
  period="2025-12-31"
  data={"periods":[period],"Income Statement":{"Revenue":{period:100},"Net Income":{period:10},"Operating Income (EBIT)":{period:20},"Gross Profit":{period:50},"Cost of Revenue":{period:50},"Diluted EPS":{period:None},"Diluted Shares":{period:10}},
   "Balance Sheet":{"Total Assets":{period:200},"Stockholders Equity":{period:-5},"Cash & Equivalents":{period:20},"Total Debt":{period:50},"Net Debt":{period:None},"Current Assets":{period:100},"Current Liabilities":{period:40},"Inventory":{period:None},"Receivables":{period:30}},
   "Cash Flow":{"Operating Cash Flow":{period:30},"Capital Expenditure":{period:-5},"Free Cash Flow":{period:None}}}
  result=derive(data)
  self.assertEqual(result["Cash Flow"]["Free Cash Flow"][period],25)
  self.assertEqual(result["Balance Sheet"]["Net Debt"][period],30)
  self.assertEqual(result["ratios"][period]["Quick Ratio"],1.25)
  self.assertIsNone(result["ratios"][period]["ROE"])
  self.assertIsNone(result["ratios"][period]["Debt / Equity"])
  self.assertEqual(result["Income Statement"]["Diluted EPS"][period],1)

if __name__=="__main__": unittest.main()
