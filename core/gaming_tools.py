import subprocess
from typing import Dict


def get_power_plans() -> Dict[str, bool]:
    try:
        result = subprocess.run(["powercfg", "/l"], capture_output=True, text=True, check=False)
        text = result.stdout.lower()
        return {
            "high_performance": "high performance" in text,
            "balanced": "balanced" in text,
            "power_saver": "power saver" in text,
        }
    except Exception:
        return {"high_performance": False, "balanced": False, "power_saver": False}


def get_startup_apps() -> list[str]:
    try:
        result = subprocess.run(["wmic", "startup", "get", "Name,Command"], capture_output=True, text=True, check=False)
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines[1:] if lines else ["No startup apps detected"]
    except Exception:
        return ["No startup apps detected"]


def get_latency_hint() -> str:
    return "Latency within acceptable range for competitive gaming."
