import subprocess
from pathlib import Path


def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, shell=False)
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "returncode": 127, "stdout": "", "stderr": "Command not available on this system."}
    except ValueError:
        return {"ok": False, "returncode": 1, "stdout": "", "stderr": "Invalid command arguments."}


def get_windows_update_status():
    result = run_command(["powershell", "-NoProfile", "-Command", "Get-Service -Name wuauserv | Select-Object -ExpandProperty Status"])
    if not result["ok"]:
        return "Status unavailable"
    status = result["stdout"] or "Unknown"
    return status.title()


def get_maintenance_summary():
    status = get_windows_update_status()
    return {
        "system_health": "Healthy",
        "windows_update": status,
        "sfc_status": "Available",
        "dism_status": "Available",
    }


def collect_system_info():
    result = run_command(["systeminfo"])
    if result["stdout"]:
        return result["stdout"]
    return "System information is unavailable on this system."
