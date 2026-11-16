import os
import unittest

from core.report_exporter import export_activity_csv, export_activity_json


class TestReportExporter(unittest.TestCase):
    def test_export_activity_csv_creates_file(self):
        path = export_activity_csv()
        self.assertTrue(os.path.exists(path))

    def test_export_activity_json_creates_file(self):
        path = export_activity_json()
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
