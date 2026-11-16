import unittest

from core.shutdown_timer import format_duration, validate_timer_input


class TestShutdownTimer(unittest.TestCase):
    def test_validate_timer_input_rejects_zero(self):
        with self.assertRaises(ValueError):
            validate_timer_input(0, 0, 0)

    def test_validate_timer_input_accepts_positive_values(self):
        self.assertEqual(validate_timer_input(2, 30, 0), 9000)

    def test_format_duration_formats_hms(self):
        self.assertEqual(format_duration(9000), "02:30:00")


if __name__ == "__main__":
    unittest.main()
