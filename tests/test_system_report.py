import json
import tempfile
import unittest
from pathlib import Path

from core.system_report import generate_system_report, read_system_report


class TestSystemReport(unittest.TestCase):
    def test_generate_system_report_creates_json(self):
        payload = generate_system_report()
        self.assertIn("system", payload)
        self.assertIn("snapshot", payload)
        report = read_system_report()
        self.assertIn("generated_at", report)


if __name__ == "__main__":
    unittest.main()
