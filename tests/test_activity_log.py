import unittest

from core.activity_log import append_log, read_logs


class TestActivityLog(unittest.TestCase):
    def test_append_log_and_read_logs(self):
        record = append_log("test_event", "sample detail")
        self.assertEqual(record["event"], "test_event")
        logs = read_logs(10)
        self.assertTrue(any(item.get("event") == "test_event" for item in logs))


if __name__ == "__main__":
    unittest.main()
