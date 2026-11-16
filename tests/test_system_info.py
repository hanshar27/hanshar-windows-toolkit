import unittest
from unittest.mock import Mock, patch

from core.system_info import (
    _get_windows_system_specs,
    _get_windows_cpu_temperature,
    get_gpu_name,
    get_gpu_temperature,
    get_system_summary,
)


class TestSystemInfo(unittest.TestCase):
    def test_get_system_summary_returns_expected_keys(self):
        values = get_system_summary()
        self.assertIn("os_name", values)
        self.assertIn("hostname", values)

    def test_windows_system_summary_uses_friendly_cim_names(self):
        specs = {
            "OsCaption": "Microsoft Windows 11 Pro",
            "OsVersion": "10.0.26200",
            "OsBuild": "26200",
            "OsArchitecture": "64-bit",
            "Processor": "AMD Ryzen 5 5600X 6-Core Processor",
            "GpuNames": ["NVIDIA GeForce GTX 1080"],
        }
        with patch("core.system_info.platform.system", return_value="Windows"), patch(
            "core.system_info.subprocess.run",
            return_value=Mock(
                stdout='{"OsCaption":"Microsoft Windows 11 Pro"}',
            ),
        ) as run:
            with patch(
                "core.system_info.json.loads", return_value=specs
            ):
                _get_windows_system_specs.cache_clear()
                summary = get_system_summary()
                gpu_name = get_gpu_name()
            _get_windows_system_specs.cache_clear()

        self.assertEqual(summary["os_release"], "11 Pro")
        self.assertEqual(summary["processor"], "AMD Ryzen 5 5600X 6-Core Processor")
        self.assertEqual(summary["os_version"], "10.0.26200 (Build 26200)")
        self.assertEqual(gpu_name, "NVIDIA GeForce GTX 1080")
        run.assert_called_once()

    def test_reads_cpu_temperature_from_libre_hardware_monitor(self):
        with patch("core.system_info.platform.system", return_value="Windows"), patch(
            "core.system_info.time.monotonic", return_value=100
        ), patch(
            "core.system_info.subprocess.run",
            return_value=Mock(stdout="62.4\r\n"),
        ) as run:
            from core import system_info

            system_info._cpu_temperature_cached_at = 0
            system_info._cpu_temperature_cached_value = None
            self.assertEqual(_get_windows_cpu_temperature(), 62.4)
            self.assertEqual(_get_windows_cpu_temperature(), 62.4)

        run.assert_called_once()
        command = run.call_args.args[0][-1]
        self.assertIn("Parent -match 'CPU|Ryzen|Intel'", command)
        self.assertNotIn("Identifier -match '/(amdcpu|intelcpu|cpu)/'", command)
        system_info._cpu_temperature_cached_at = 0
        system_info._cpu_temperature_cached_value = None

    def test_temperature_is_unavailable_without_a_sensor_provider(self):
        with patch(
            "core.system_info.psutil.sensors_temperatures",
            return_value={},
            create=True,
        ), patch(
            "core.system_info.platform.system", return_value="Windows"
        ), patch("core.system_info.time.monotonic", return_value=200), patch(
            "core.system_info.subprocess.run",
            side_effect=OSError("LibreHardwareMonitor is not running"),
        ):
            from core import system_info

            system_info._cpu_temperature_cached_at = 0
            system_info._cpu_temperature_cached_value = None
            self.assertIsNone(system_info.get_cpu_temperature())
            system_info._cpu_temperature_cached_at = 0
            system_info._cpu_temperature_cached_value = None

    def test_reads_nvidia_gpu_temperature_from_nvidia_smi(self):
        from core import system_info

        with patch("core.system_info.platform.system", return_value="Windows"), patch(
            "core.system_info.time.monotonic", return_value=300
        ), patch(
            "core.system_info.subprocess.run",
            return_value=Mock(stdout="47\r\n"),
        ) as run:
            system_info._gpu_temperature_cached_at = 0
            system_info._gpu_temperature_cached_value = None
            self.assertEqual(get_gpu_temperature(), 47.0)

        self.assertIn("nvidia-smi", run.call_args.args[0][0])
        run.assert_called_once()
        system_info._gpu_temperature_cached_at = 0
        system_info._gpu_temperature_cached_value = None

    def test_falls_back_to_hardware_monitor_for_gpu_temperature(self):
        from core import system_info

        with patch("core.system_info.platform.system", return_value="Windows"), patch(
            "core.system_info.time.monotonic", return_value=400
        ), patch(
            "core.system_info.subprocess.run",
            side_effect=[
                FileNotFoundError("nvidia-smi not found"),
                FileNotFoundError("nvidia-smi not found"),
                Mock(stdout="52.5\r\n"),
            ],
        ) as run:
            system_info._gpu_temperature_cached_at = 0
            system_info._gpu_temperature_cached_value = None
            self.assertEqual(get_gpu_temperature(), 52.5)

        self.assertIn("GPU", run.call_args.args[0][-1])
        system_info._gpu_temperature_cached_at = 0
        system_info._gpu_temperature_cached_value = None

    def test_dashboard_gpu_temperature_card_never_substitutes_cpu_load(self):
        from modules.dashboard import DashboardPanel

        class FakeCard:
            def __init__(self):
                self.value = None
                self.detail = None

            def set_value(self, value, detail):
                self.value = value
                self.detail = detail

        dashboard = object.__new__(DashboardPanel)
        card = FakeCard()
        dashboard.metric_cards = {
            name: FakeCard()
            for name in (
                "GPU TEMPERATURE",
                "DOWNLOAD",
                "DISK FREE",
                "GRAPHICS",
                "PROCESSES",
                "UPLOAD",
                "WINDOWS",
                "DEVICE",
            )
        }
        dashboard.metric_cards["GPU TEMPERATURE"] = card
        dashboard.summary_info = {
            "os_name": "Windows",
            "os_release": "11 Pro",
            "processor": "AMD Ryzen 5 5600X",
            "hostname": "test",
        }
        dashboard.gpu_name = "NVIDIA GeForce GTX 1080"
        dashboard.disk_path = "C:\\"
        dashboard.disk_label = "C:"
        dashboard._previous_network = Mock(bytes_recv=0, bytes_sent=0)
        dashboard._previous_network_time = 1.0
        dashboard._last_refresh_error = None
        dashboard.status_label = Mock()
        dashboard.load_value = Mock()
        dashboard.load_bar = Mock()
        dashboard.os_value = Mock()
        dashboard.processor_value = Mock()
        dashboard.uptime_value = Mock()
        dashboard.cpu_gauge = Mock()
        dashboard.ram_gauge = Mock()
        dashboard.performance_chart = Mock()

        with patch("modules.dashboard.get_cpu_usage", return_value=37.5), patch(
            "modules.dashboard.get_memory_usage",
            return_value={"used_percent": 50, "used_gb": 8, "total_gb": 16},
        ), patch(
            "modules.dashboard.get_disk_usage",
            return_value={"free_gb": 100, "percent_used": 20},
        ), patch("modules.dashboard.get_gpu_temperature", return_value=None), patch(
            "modules.dashboard.get_uptime_human_readable", return_value="1 day"
        ), patch(
            "modules.dashboard.psutil.net_io_counters",
            return_value=Mock(bytes_recv=0, bytes_sent=0),
        ), patch("modules.dashboard.get_process_count", return_value=10), patch(
            "modules.dashboard.time.monotonic", return_value=2.0
        ), patch.object(DashboardPanel, "after"):
            dashboard.refresh_dashboard()

        self.assertEqual(card.value, "Unavailable")
        self.assertNotIn("% load", card.value)
        self.assertEqual(card.detail, "NVIDIA driver or LHM required")


if __name__ == "__main__":
    unittest.main()
