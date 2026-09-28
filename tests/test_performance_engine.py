import unittest
from services.performance_engine import BoundedTTLCache, CachePolicy, PerformanceMonitor, cached_load, resource_snapshot


class PerformanceEngineTests(unittest.TestCase):
    def test_reuse_and_capacity(self):
        cache = BoundedTTLCache(CachePolicy(60, 2))
        calls = []
        def load():
            calls.append(1)
            return len(calls)
        self.assertEqual(cache.get_or_load("a", load), 1)
        self.assertEqual(cache.get_or_load("a", load), 1)
        self.assertEqual(len(calls), 1)
        cache.get_or_load("b", load)
        cache.get_or_load("c", load)
        self.assertLessEqual(cache.stats()["entries"], 2)
        self.assertEqual(cache.get_or_load("a", load), 4)

    def test_failed_fetch_is_not_cached(self):
        cache = BoundedTTLCache(CachePolicy(60))
        with self.assertRaises(RuntimeError):
            cache.get_or_load("x", lambda: (_ for _ in ()).throw(RuntimeError()))
        self.assertEqual(cache.stats()["entries"], 0)

    def test_monitor_records_failure(self):
        monitor = PerformanceMonitor()
        @monitor.measure("test")
        def failing():
            raise RuntimeError()
        with self.assertRaises(RuntimeError):
            failing()
        self.assertEqual(monitor.snapshot()["test"]["calls"], 1)

    def test_unknown_kind(self):
        with self.assertRaises(ValueError):
            cached_load("unknown", "x", lambda: 1)

    def test_resource_snapshot(self):
        self.assertIn("cache", resource_snapshot())
        self.assertIn("timings", resource_snapshot())


if __name__ == "__main__":
    unittest.main()
