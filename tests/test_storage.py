import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from core.storage_manager import delete_entries, scan_cache_locations


class TestStorage(unittest.TestCase):
    def test_safe_scan_finds_temp_files_without_protected_paths(self):
        root = tempfile.mkdtemp(prefix="rwt_storage_")
        local_root = os.path.join(root, "AppData", "Local")
        temp_dir = os.path.join(local_root, "Temp")
        protected_dir = os.path.join(root, "Users", "Me", "Documents")
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(protected_dir, exist_ok=True)

        temp_file = os.path.join(temp_dir, "cache.tmp")
        protected_file = os.path.join(protected_dir, "important.txt")

        with open(temp_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("temporary cache data")
        with open(protected_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("do not delete")

        result = scan_cache_locations(mode="safe", base_dir=local_root)

        found_temp = any(item.get("path") == temp_file for item in result["entries"])
        found_protected = any(item.get("path") == protected_file for item in result["entries"])

        self.assertTrue(found_temp)
        self.assertFalse(found_protected)
        self.assertGreater(result["file_count"], 0)

        shutil.rmtree(root)

    def test_scans_temp_windows_temp_prefetch_and_recycle_bin(self):
        with tempfile.TemporaryDirectory(prefix="rwt_storage_") as root:
            local_root = os.path.join(root, "AppData", "Local")
            windows_root = os.path.join(root, "Windows")
            targets = {
                "%TEMP% User Temp": os.path.join(local_root, "Temp"),
                "Windows Temp": os.path.join(windows_root, "Temp"),
                "Prefetch": os.path.join(windows_root, "Prefetch"),
            }
            for index, directory in enumerate(targets.values()):
                os.makedirs(directory, exist_ok=True)
                with open(os.path.join(directory, f"cache{index}.tmp"), "w", encoding="utf-8") as file_handle:
                    file_handle.write("cache")

            with patch.dict(os.environ, {
                "LOCALAPPDATA": local_root,
                "TEMP": targets["%TEMP% User Temp"],
                "WINDIR": windows_root,
            }), patch("core.storage_manager._query_recycle_bin", return_value={"size_bytes": 100, "item_count": 2}):
                result = scan_cache_locations(mode="safe")

            categories = {entry["category"] for entry in result["entries"]}
            self.assertTrue(set(targets).issubset(categories))
            self.assertIn("Recycle Bin", categories)
            self.assertEqual(result["file_count"], 5)
            self.assertEqual(result["categories"]["Recycle Bin"], 2)

    def test_recycle_bin_cleanup_uses_windows_shell_action(self):
        entries = [{
            "category": "Recycle Bin",
            "action": "empty_recycle_bin",
            "item_count": 3,
        }]
        with patch("core.storage_manager._empty_recycle_bin") as empty_recycle_bin:
            deleted, errors = delete_entries(entries)

        empty_recycle_bin.assert_called_once_with()
        self.assertEqual(deleted, 3)
        self.assertEqual(errors, [])

    def test_temp_scan_and_cleanup_protect_pyinstaller_runtime_files(self):
        with tempfile.TemporaryDirectory(prefix="rwt_storage_") as root:
            temp_root = os.path.join(root, "Temp")
            runtime_dir = os.path.join(temp_root, "_MEI12345")
            os.makedirs(runtime_dir)
            runtime_file = os.path.join(runtime_dir, "base_library.zip")
            with open(runtime_file, "w", encoding="utf-8") as file_handle:
                file_handle.write("runtime")

            with patch.dict(os.environ, {
                "TEMP": temp_root,
                "TMP": temp_root,
                "LOCALAPPDATA": os.path.join(root, "Local"),
                "WINDIR": os.path.join(root, "Windows"),
            }), patch("core.storage_manager.tempfile.gettempdir", return_value=temp_root):
                result = scan_cache_locations(mode="safe")
                self.assertFalse(any(item.get("path") == runtime_file for item in result["entries"]))
                deleted, errors = delete_entries([{"path": runtime_file}])

            self.assertEqual(deleted, 0)
            self.assertTrue(os.path.isfile(runtime_file))
            self.assertTrue(any("protected temporary runtime file" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
