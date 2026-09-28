"""Offline regression tests for the navigation performance boundary."""
import unittest
from unittest.mock import Mock
import pandas as pd
from services.navigation_performance import company_navigation_snapshot, STATE_KEY, TIMING_KEY

class NavigationPerformanceTests(unittest.TestCase):
    def setUp(self):
        self.state = {}
        self.bars = pd.DataFrame({"Close": [1., 2.]})
        self.history = Mock(return_value=self.bars)
        self.profile = Mock(return_value={"longName": "Zip Co"})
        self.now = [100.]
        self.clock = lambda: self.now[0]

    def load(self, ticker="ZIP.AX", **kwargs):
        return company_navigation_snapshot(ticker, self.history, self.profile,
                                           self.state, clock=self.clock, **kwargs)

    def test_same_ticker_hits_cache_without_provider_calls(self):
        self.load()
        self.load()
        self.assertEqual(self.history.call_count, 1)
        self.assertEqual(self.profile.call_count, 1)
        self.assertEqual(self.state[TIMING_KEY]["cache"], "session")

    def test_different_listing_and_period_are_separate(self):
        self.load()
        self.load("ZIP")
        self.load("ZIP", period="1y")
        self.assertEqual(self.history.call_count, 3)
        self.history.assert_any_call("ZIP", "1y")

    def test_expiry_and_refresh(self):
        self.load()
        self.now[0] += 46
        self.load()
        self.load(refresh=True)
        self.assertEqual(self.history.call_count, 3)

    def test_mutation_cannot_poison_cache(self):
        bars, profile = self.load()
        bars.loc[0, "Close"] = 999
        profile["longName"] = "Wrong"
        fresh, new_profile = self.load()
        self.assertEqual(fresh.loc[0, "Close"], 1.)
        self.assertEqual(new_profile["longName"], "Zip Co")

    def test_failed_provider_does_not_keep_old_snapshot_or_load_profile(self):
        self.load()
        self.history.return_value = pd.DataFrame()
        self.load("OTHER")
        self.assertNotIn(STATE_KEY, self.state)
        self.assertEqual(self.profile.call_count, 1)

    def test_no_ticker_rejected(self):
        with self.assertRaises(ValueError):
            self.load("")

if __name__ == "__main__":
    unittest.main()
