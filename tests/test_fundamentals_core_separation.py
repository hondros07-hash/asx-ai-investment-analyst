"""Phase 1 migration contract: core must remain importable without Streamlit."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch

from services import fundamentals_core


class FundamentalsSeparationTests(unittest.TestCase):
    def test_core_has_no_streamlit_imports_or_calls(self):
        source = Path(fundamentals_core.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names]
        self.assertFalse(any(name and (name == "streamlit" or name.startswith("streamlit."))
                             for name in imports))
        self.assertNotIn("st.", source)

    def test_core_returns_plain_snapshot_when_provider_empty(self):
        with patch.object(fundamentals_core.yf, "Ticker") as ticker:
            ticker.return_value.info = {}
            ticker.return_value.income_stmt = None
            ticker.return_value.balance_sheet = None
            ticker.return_value.cashflow = None
            result = fundamentals_core.load_uncached("TEST", "Annual (5Y)")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["periods"], [])
        self.assertEqual(result["ticker"], "TEST")
        self.assertEqual(result["frequency"], "Annual (5Y)")

    def test_existing_loader_retains_clear_api(self):
        from services.fundamentals_engine import load
        self.assertTrue(callable(load))
        self.assertTrue(callable(load.clear))


if __name__ == "__main__":
    unittest.main()
