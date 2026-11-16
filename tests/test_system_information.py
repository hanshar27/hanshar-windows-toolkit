import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.system_information import (
    REPORT_TIMEOUT_SECONDS,
    _run_report,
    collect_system_information_reports,
    get_system_information_report_paths,
    get_system_information_reports_dir,
    read_system_information_report,
)


class TestSystemInformation(unittest.TestCase):
    def test_collects_and_reads_complete_reports(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            system_root = root / "Windows"
            system_directory = system_root / "System32"
            system_directory.mkdir(parents=True)
            (system_directory / "msinfo32.exe").touch()
            (system_directory / "dxdiag.exe").touch()
            output_directory = root / "reports"

            def create_report(command, **kwargs):
                report_path = Path(command[-1])
                report_path.write_bytes(
                    b"\xff\xfe" + f"Complete {report_path.stem} report".encode("utf-16-le")
                )
                return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

            with mock.patch("core.system_information.platform.system", return_value="Windows"):
                with mock.patch("core.system_information.subprocess.run", side_effect=create_report) as run:
                    reports = collect_system_information_reports(
                        output_dir=output_directory,
                        system_root=system_root,
                    )

            self.assertEqual(set(reports), {"msinfo32", "dxdiag"})
            self.assertEqual(read_system_information_report(reports["msinfo32"]), "Complete msinfo32 report")
            self.assertEqual(read_system_information_report(reports["dxdiag"]), "Complete dxdiag report")
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[0].args[0][1], "/report")
            self.assertEqual(run.call_args_list[1].args[0][1], "/t")

    def test_missing_windows_utility_reports_explicit_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with mock.patch("core.system_information.platform.system", return_value="Windows"):
                with self.assertRaises(FileNotFoundError):
                    collect_system_information_reports(
                        output_dir=Path(temporary_directory) / "reports",
                        system_root=temporary_directory,
                    )

    def test_report_paths_are_named_for_both_tools(self):
        paths = get_system_information_report_paths("reports")
        self.assertEqual(paths["msinfo32"].name, "msinfo32.txt")
        self.assertEqual(paths["dxdiag"].name, "dxdiag.txt")

    def test_packaged_reports_use_persistent_local_app_data(self):
        with mock.patch("core.system_information.sys.frozen", True, create=True):
            with mock.patch.dict(
                "core.system_information.os.environ",
                {"LOCALAPPDATA": r"C:\Users\tester\AppData\Local"},
            ):
                reports_dir = get_system_information_reports_dir()

        self.assertEqual(
            reports_dir,
            Path(r"C:\Users\tester\AppData\Local\RayhanWindowsToolkit\reports"),
        )
        self.assertNotIn("_MEI", str(reports_dir))

    def test_report_timeout_is_reported_clearly(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "report.txt"
            with mock.patch(
                "core.system_information.subprocess.run",
                side_effect=subprocess.TimeoutExpired("msinfo32", REPORT_TIMEOUT_SECONDS),
            ):
                with self.assertRaisesRegex(TimeoutError, "did not finish"):
                    _run_report("MSInfo32", Path("msinfo32.exe"), ["/report"], output_path)

    @unittest.skipUnless(os.name == "nt", "Windows process startup options only")
    def test_windows_report_runs_without_showing_modal_windows(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "report.txt"

            def create_report(command, **kwargs):
                output_path.write_text("System information", encoding="utf-8")
                self.assertEqual(kwargs["startupinfo"].wShowWindow, subprocess.SW_HIDE)
                return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

            with mock.patch("core.system_information.subprocess.run", side_effect=create_report):
                _run_report("MSInfo32", Path("msinfo32.exe"), ["/report"], output_path)


if __name__ == "__main__":
    unittest.main()
