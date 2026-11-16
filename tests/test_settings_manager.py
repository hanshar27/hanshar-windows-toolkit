import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.settings_manager import load_settings, save_settings


class TestSettingsManager(unittest.TestCase):
    def test_load_settings_returns_expected_keys(self):
        values = load_settings()
        self.assertIn("app_name", values)
        self.assertIn("blur_intensity", values)
        self.assertIn("require_confirmation", values)
        self.assertNotIn("theme", values)

    def test_save_settings_persists_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            payload = {
                "theme": "dark",
                "blur_intensity": 70,
                "startup_on_login": True,
                "require_confirmation": False,
            }
            saved = save_settings(payload, path)
            self.assertNotIn("theme", saved)
            reloaded = load_settings(path)
            self.assertEqual(reloaded["blur_intensity"], 70)
            self.assertTrue(reloaded["startup_on_login"])
            self.assertFalse(reloaded["require_confirmation"])
            self.assertNotIn("theme", reloaded)

    def test_legacy_theme_setting_is_removed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            path.write_text(
                '{"theme": "violet_glow", "blur_intensity": "invalid"}',
                encoding="utf-8",
            )
            settings = load_settings(path)
            self.assertNotIn("theme", settings)
            self.assertEqual(settings["blur_intensity"], 55)

    def test_packaged_settings_are_saved_in_persistent_user_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("core.settings_manager.sys.frozen", True, create=True):
                with mock.patch.dict(os.environ, {"LOCALAPPDATA": tmpdir}):
                    save_settings({"blur_intensity": 80})
                    settings_path = (
                        Path(tmpdir)
                        / "Hanshar Windows Toolkit"
                        / "config.json"
                    )
                    self.assertTrue(settings_path.is_file())
                    self.assertEqual(load_settings()["blur_intensity"], 80)


if __name__ == "__main__":
    unittest.main()
