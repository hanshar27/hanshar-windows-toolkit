import tempfile
import unittest
from pathlib import Path

from core.app_state import DEFAULT_STATE, load_app_state, save_app_state


class TestAppState(unittest.TestCase):
    def test_load_app_state_returns_expected_keys(self):
        values = load_app_state()
        self.assertIn("last_page", values)
        self.assertIn("status", values)
        self.assertNotIn("theme", values)

    def test_save_app_state_persists_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            payload = {"last_page": "Settings", "theme": "light", "status": "Saved"}
            saved = save_app_state(payload, path)
            self.assertEqual(saved["last_page"], "Settings")
            self.assertNotIn("theme", saved)
            reloaded = load_app_state(path)
            self.assertNotIn("theme", reloaded)
            self.assertEqual(reloaded["status"], "Saved")


if __name__ == "__main__":
    unittest.main()
