import unittest

from core.gaming_tools import get_power_plans


class TestGamingTools(unittest.TestCase):
    def test_get_power_plans_returns_expected_keys(self):
        plans = get_power_plans()
        self.assertIn("high_performance", plans)
        self.assertIn("balanced", plans)
        self.assertIn("power_saver", plans)


if __name__ == "__main__":
    unittest.main()
