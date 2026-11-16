import unittest

from core.network_tools import validate_host


class TestNetworkTools(unittest.TestCase):
    def test_validate_host_accepts_ip_address(self):
        self.assertTrue(validate_host("8.8.8.8"))

    def test_validate_host_rejects_empty_value(self):
        self.assertFalse(validate_host(""))


if __name__ == "__main__":
    unittest.main()
