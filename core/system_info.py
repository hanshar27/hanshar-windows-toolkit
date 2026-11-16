import json
import os
import platform
import re
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import psutil

_CPU_TEMPERATURE_CACHE_SECONDS = 5
_cpu_temperature_cached_at = 0.0
_cpu_temperature_cached_value: Optional[float] = None
_gpu_temperature_cached_at = 0.0
_gpu_temperature_cached_value: Optional[float] = None


@lru_cache(maxsize=1)
def _get_windows_system_specs() -> Optional[Dict[str, object]]:
    if platform.system() != "Windows":
        return None

    script = (
        "$os = Get-CimInstance Win32_OperatingSystem; "
        "$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; "
        "$gpus = @(Get-CimInstance Win32_VideoController | "
        "ForEach-Object { $_.Name }); "
        "[PSCustomObject]@{ "
        "OsCaption = $os.Caption; OsVersion = $os.Version; "
        "OsBuild = $os.BuildNumber; OsArchitecture = $os.OSArchitecture; "
        "Processor = $cpu.Name; GpuNames = $gpus "
        "} | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=12,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        specs = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None

    if not isinstance(specs, dict):
        return None
    return specs


def get_system_summary() -> Dict[str, str]:
    windows_specs = _get_windows_system_specs()
    if windows_specs:
        caption = str(windows_specs.get("OsCaption") or "Windows").strip()
        caption = re.sub(r"^Microsoft\s+", "", caption)
        os_release = re.sub(r"^Windows\s+", "", caption) or platform.release()
        os_version = str(windows_specs.get("OsVersion") or platform.version())
        build = windows_specs.get("OsBuild")
        if build:
            os_version = f"{os_version} (Build {build})"
        processor = str(windows_specs.get("Processor") or "").strip()
        architecture = str(
            windows_specs.get("OsArchitecture") or platform.machine()
        ).strip()
        if processor:
            return {
                "os_name": "Windows",
                "os_release": os_release,
                "os_version": os_version,
                "processor": processor,
                "architecture": architecture,
                "hostname": platform.node(),
            }

    return {
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "processor": platform.processor() or "Unknown",
        "architecture": platform.machine(),
        "hostname": platform.node(),
    }


def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=None)


def get_memory_usage() -> Dict[str, float]:
    memory = psutil.virtual_memory()
    return {
        "used_percent": memory.percent,
        "used_gb": round(memory.used / (1024 ** 3), 2),
        "total_gb": round(memory.total / (1024 ** 3), 2),
    }


def get_disk_usage(path: str = "C:\\") -> Dict[str, float]:
    disk = psutil.disk_usage(path)
    return {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "free_gb": round(disk.free / (1024 ** 3), 2),
        "percent_used": disk.percent,
    }


def get_uptime_seconds() -> float:
    try:
        return float(psutil.boot_time())
    except Exception:
        return 0.0


def get_uptime_human_readable() -> str:
    try:
        uptime_seconds = time.time() - psutil.boot_time()
        total_seconds = int(uptime_seconds)
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{days} day(s), {hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return "Unavailable"


def get_cpu_temperature() -> Optional[float]:
    temperatures = {}
    try:
        temperatures = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        pass

    preferred_sensor_names = ("package", "tctl", "tdie")
    for sensors in temperatures.values():
        for sensor in sensors:
            if sensor.current is None:
                continue
            if any(
                name in (sensor.label or "").lower()
                for name in preferred_sensor_names
            ):
                return round(sensor.current, 1)

    for key in ("coretemp", "k10temp", "cpu_thermal"):
        sensors = temperatures.get(key, [])
        if sensors and sensors[0].current is not None:
            return round(sensors[0].current, 1)

    for sensors in temperatures.values():
        if sensors and sensors[0].current is not None:
            return round(sensors[0].current, 1)

    return _get_windows_cpu_temperature()


def _get_windows_cpu_temperature() -> Optional[float]:
    global _cpu_temperature_cached_at, _cpu_temperature_cached_value

    now = time.monotonic()
    if now - _cpu_temperature_cached_at < _CPU_TEMPERATURE_CACHE_SECONDS:
        return _cpu_temperature_cached_value

    if platform.system() != "Windows":
        _cpu_temperature_cached_at = now
        _cpu_temperature_cached_value = None
        return None

    script = (
        "$sensors = @(); "
        "foreach ($namespace in @('root/LibreHardwareMonitor', "
        "'root/OpenHardwareMonitor')) { "
        "try { $sensors = @(Get-CimInstance -Namespace $namespace "
        "-ClassName Sensor -ErrorAction Stop | "
        "Where-Object { $_.SensorType -eq 'Temperature' }); "
        "if ($sensors.Count -gt 0) { break } } catch { } }; "
        "$cpuSensors = $sensors | Where-Object { "
        "$_.Identifier -match 'amdcpu|intelcpu|/cpu/' -or "
        "$_.Parent -match 'CPU|Ryzen|Intel' -or "
        "$_.Name -match 'CPU|Core|Tctl|Tdie' }; "
        "$sensor = $cpuSensors | Where-Object { "
        "$_.Name -match 'Package|Tctl|Tdie' } | "
        "Sort-Object Value -Descending | Select-Object -First 1; "
        "if (-not $sensor) { $sensor = $sensors | "
        "Where-Object { $_.Identifier -match 'amdcpu|intelcpu|/cpu/' -and "
        "$_.Name -match 'Core' } | "
        "Sort-Object Value -Descending | Select-Object -First 1 }; "
        "if ($sensor) { "
        "[string]::Format([Globalization.CultureInfo]::InvariantCulture, "
        "'{0:F1}', [double]$sensor.Value) }"
    )
    value = None
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        output = result.stdout.strip()
        if output:
            candidate = float(output.splitlines()[-1])
            if 0 <= candidate <= 125:
                value = round(candidate, 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        value = None

    _cpu_temperature_cached_at = now
    _cpu_temperature_cached_value = value
    return value


def get_gpu_temperature() -> Optional[float]:
    global _gpu_temperature_cached_at, _gpu_temperature_cached_value

    now = time.monotonic()
    if now - _gpu_temperature_cached_at < _CPU_TEMPERATURE_CACHE_SECONDS:
        return _gpu_temperature_cached_value

    value = None
    if platform.system() == "Windows":
        value = _get_nvidia_gpu_temperature()
        if value is None:
            value = _get_windows_gpu_temperature()

    _gpu_temperature_cached_at = now
    _gpu_temperature_cached_value = value
    return value


def _get_nvidia_gpu_temperature() -> Optional[float]:
    commands = [["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"]]
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    commands.append(
        [
            str(
                Path(program_files)
                / "NVIDIA Corporation"
                / "NVSMI"
                / "nvidia-smi.exe"
            ),
            "--query-gpu=temperature.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3,
                check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError):
            continue

        for line in result.stdout.splitlines():
            try:
                temperature = float(line.strip())
            except ValueError:
                continue
            if 0 <= temperature <= 125:
                return round(temperature, 1)
    return None


def _get_windows_gpu_temperature() -> Optional[float]:
    script = (
        "$sensors = @(); "
        "foreach ($namespace in @('root/LibreHardwareMonitor', "
        "'root/OpenHardwareMonitor')) { "
        "try { $sensors = @(Get-CimInstance -Namespace $namespace "
        "-ClassName Sensor -ErrorAction Stop | "
        "Where-Object { $_.SensorType -eq 'Temperature' }); "
        "if ($sensors.Count -gt 0) { break } } catch { } }; "
        "$gpuSensors = $sensors | Where-Object { "
        "$_.Identifier -match 'gpu|nvidia|radeon|intelgpu' -or "
        "$_.Parent -match 'GPU|GeForce|NVIDIA|Radeon|Arc' -or "
        "$_.Name -match 'GPU|GeForce|NVIDIA|Radeon|Graphics' }; "
        "$sensor = $gpuSensors | Where-Object { "
        "$_.Name -match 'GPU Core|GPU Temperature|Core' } | "
        "Select-Object -First 1; "
        "if (-not $sensor) { $sensor = $gpuSensors | "
        "Select-Object -First 1 }; "
        "if ($sensor) { "
        "[string]::Format([Globalization.CultureInfo]::InvariantCulture, "
        "'{0:F1}', [double]$sensor.Value) }"
    )
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None

    try:
        temperature = float(result.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError):
        return None
    if 0 <= temperature <= 125:
        return round(temperature, 1)
    return None


def get_gpu_name() -> Optional[str]:
    windows_specs = _get_windows_system_specs()
    if windows_specs:
        gpu_names = windows_specs.get("GpuNames")
        if isinstance(gpu_names, str):
            return gpu_names.strip() or None
        if isinstance(gpu_names, list):
            names = [str(name).strip() for name in gpu_names if str(name).strip()]
            if names:
                return ", ".join(names)

    try:
        import wmi  # type: ignore

        computer = wmi.WMI()
        for gpu in computer.Win32_VideoController():
            name = getattr(gpu, "Name", None)
            if name:
                return str(name)
    except Exception:
        return None
    return None
