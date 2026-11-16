import ctypes
import unittest
from unittest import mock

from core.memory_tools import (
    ELEVATED_ACTION_ARGUMENT,
    MEMORY_PURGE_STANDBY_LIST,
    SYSTEM_MEMORY_LIST_INFORMATION,
    _purge_standby_list,
    build_elevation_parameters,
    clear_standby_memory,
)


class TestMemoryTools(unittest.TestCase):
    def test_clear_standby_memory_rejects_non_windows(self):
        with mock.patch("core.memory_tools.platform.system", return_value="Linux"):
            with self.assertRaisesRegex(RuntimeError, "Windows"):
                clear_standby_memory()

    def test_clear_standby_memory_requires_administrator(self):
        with mock.patch("core.memory_tools.platform.system", return_value="Windows"):
            with mock.patch("core.memory_tools.is_administrator", return_value=False):
                with self.assertRaisesRegex(PermissionError, "Administrator"):
                    clear_standby_memory()

    def test_clear_standby_memory_purges_standby_list_for_administrator(self):
        with mock.patch("core.memory_tools.platform.system", return_value="Windows"):
            with mock.patch("core.memory_tools.is_administrator", return_value=True):
                with mock.patch("core.memory_tools._purge_standby_list") as purge:
                    clear_standby_memory()
        purge.assert_called_once_with()

    def test_purge_uses_windows_standby_list_command(self):
        ntdll = mock.Mock()
        ntdll.NtSetSystemInformation.return_value = 0
        with mock.patch("core.memory_tools._enable_privilege") as enable_privilege:
            with mock.patch("core.memory_tools.ctypes.WinDLL", return_value=ntdll):
                _purge_standby_list()

        enable_privilege.assert_called_once_with("SeProfileSingleProcessPrivilege")
        call_args = ntdll.NtSetSystemInformation.call_args.args
        self.assertEqual(call_args[0], SYSTEM_MEMORY_LIST_INFORMATION)
        command = ctypes.cast(call_args[1], ctypes.POINTER(ctypes.c_ulong)).contents.value
        self.assertEqual(command, MEMORY_PURGE_STANDBY_LIST)

    def test_packaged_elevation_parameters_include_action(self):
        parameters = build_elevation_parameters(r"C:\Program Files\Toolkit.exe", frozen=True)
        self.assertIn(ELEVATED_ACTION_ARGUMENT, parameters)
        self.assertNotIn("main.py", parameters)

    def test_source_elevation_parameters_include_script_and_action(self):
        with mock.patch("core.memory_tools.sys.argv", [r"C:\project\main.py"]):
            parameters = build_elevation_parameters("python.exe", frozen=False)
        self.assertIn("main.py", parameters)
        self.assertIn(ELEVATED_ACTION_ARGUMENT, parameters)


if __name__ == "__main__":
    unittest.main()
