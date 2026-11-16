import unittest
from unittest.mock import patch

from core.system_monitor import get_system_snapshot


class TestSystemMonitor(unittest.TestCase):
    def test_get_system_snapshot_returns_expected_keys(self):
        snapshot = get_system_snapshot()
        self.assertIn("cpu_usage", snapshot)
        self.assertIn("ram_usage", snapshot)
        self.assertIn("disk_usage", snapshot)
        self.assertIn("gpu_temperature", snapshot)
        self.assertNotIn("cpu_temperature", snapshot)

    def test_snapshot_uses_gpu_temperature_not_cpu_temperature(self):
        with patch("core.system_monitor.get_gpu_temperature", return_value=54.5):
            snapshot = get_system_snapshot()
        self.assertEqual(snapshot["gpu_temperature"], 54.5)
        self.assertNotIn("cpu_temperature", snapshot)


if __name__ == "__main__":
    unittest.main()
