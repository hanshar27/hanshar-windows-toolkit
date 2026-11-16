import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict

REPORT_TIMEOUT_SECONDS = 180


def get_system_information_reports_dir() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        return local_app_data / "RayhanWindowsToolkit" / "reports"
    return Path(__file__).resolve().parents[1] / "reports"


def _decode_output(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    if b"\x00" in data[:4096]:
        return data.decode("utf-16-le", errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def get_system_information_report_paths(
    output_dir: str | Path | None = None,
) -> Dict[str, Path]:
    directory = Path(output_dir) if output_dir is not None else get_system_information_reports_dir()
    return {
        "msinfo32": directory / "msinfo32.txt",
        "dxdiag": directory / "dxdiag.txt",
    }


def read_system_information_report(path: str | Path) -> str:
    return _decode_output(Path(path).read_bytes())


def _run_report(
    name: str,
    executable: Path,
    arguments: list[str],
    output_path: Path,
) -> None:
    if output_path.exists():
        output_path.unlink()

    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    try:
        result = subprocess.run(
            [str(executable), *arguments, str(output_path)],
            capture_output=True,
            startupinfo=startupinfo,
            timeout=REPORT_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"{name} did not finish within {REPORT_TIMEOUT_SECONDS} seconds."
        ) from exc
    except OSError as exc:
        raise RuntimeError(f"Could not run {name}: {exc}") from exc

    if result.returncode != 0:
        detail = _decode_output(result.stderr or result.stdout).strip()
        message = f"Windows returned exit code {result.returncode}."
        if detail:
            message = f"{message} {detail}"
        raise RuntimeError(f"Could not generate the {name} report. {message}")

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError(f"{name} finished without creating a report.")


def collect_system_information_reports(
    output_dir: str | Path | None = None,
    system_root: str | Path | None = None,
) -> Dict[str, Path]:
    if platform.system() != "Windows":
        raise RuntimeError("System Information reports are available on Windows only.")

    root_value = system_root or os.environ.get("SystemRoot")
    if not root_value:
        raise RuntimeError("Windows SystemRoot could not be located.")

    system_root_path = Path(root_value)
    system_directory = system_root_path / "System32"
    executables = {
        "msinfo32": system_directory / "msinfo32.exe",
        "dxdiag": system_directory / "dxdiag.exe",
    }
    for name, executable in executables.items():
        if not executable.is_file():
            raise FileNotFoundError(f"Windows utility was not found: {executable}")

    report_paths = get_system_information_report_paths(output_dir)
    for path in report_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    _run_report("MSInfo32", executables["msinfo32"], ["/report"], report_paths["msinfo32"])
    _run_report("DxDiag", executables["dxdiag"], ["/t"], report_paths["dxdiag"])
    return report_paths
