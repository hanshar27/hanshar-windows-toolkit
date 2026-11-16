import unittest

from core.startup_manager import APP_NAME, build_startup_command, is_startup_enabled, set_startup_enabled


class TestStartupManager(unittest.TestCase):
    def test_build_startup_command_contains_app_path(self):
        command = build_startup_command("C:/Windows/System32/calc.exe")
        self.assertIn("calc.exe", command)

    def test_set_startup_enabled_returns_bool(self):
        result = set_startup_enabled(False, app_name=APP_NAME, app_path="C:/Windows/System32/calc.exe")
        self.assertIsInstance(result, bool)

    def test_is_startup_enabled_returns_bool(self):
        self.assertIsInstance(is_startup_enabled(APP_NAME), bool)


if __name__ == "__main__":
    unittest.main()
