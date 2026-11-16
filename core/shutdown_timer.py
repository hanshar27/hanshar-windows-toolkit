import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

STATE_PATH = Path(__file__).resolve().parents[1] / "logs" / "shutdown_timer_state.json"


def format_duration(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def validate_timer_input(hours: int, minutes: int, seconds: int) -> int:
    try:
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("Timer values must be numeric") from exc

    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError("Timer duration must be greater than zero")
    return total_seconds


def save_timer_state(state: Dict[str, object]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state), encoding="utf-8")


def load_timer_state() -> Optional[Dict[str, object]]:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def clear_timer_state() -> None:
    if STATE_PATH.exists():
        try:
            STATE_PATH.unlink()
        except OSError:
            pass


def schedule_windows_shutdown(total_seconds: int) -> Dict[str, object]:
    total_seconds = max(1, int(total_seconds))
    started_at = time.time()
    result = subprocess.run(["shutdown", "/s", "/t", str(total_seconds)], capture_output=True, text=True, check=False)
    state = {
        "status": "active",
        "started_at": started_at,
        "total_seconds": total_seconds,
        "deadline": started_at + total_seconds,
        "result_stdout": result.stdout,
        "result_stderr": result.stderr,
        "returncode": result.returncode,
    }
    save_timer_state(state)
    return state


def cancel_windows_shutdown() -> Dict[str, object]:
    result = subprocess.run(["shutdown", "/a"], capture_output=True, text=True, check=False)
    state = {
        "status": "cancelled",
        "cancelled_at": time.time(),
        "returncode": result.returncode,
        "result_stdout": result.stdout,
        "result_stderr": result.stderr,
    }
    save_timer_state(state)
    return state


def get_remaining_seconds() -> Optional[int]:
    state = load_timer_state()
    if not state or state.get("status") != "active":
        return None
    deadline = float(state.get("deadline", 0))
    remaining = int(deadline - time.time())
    return max(0, remaining)


def describe_timer_state() -> str:
    state = load_timer_state()
    if not state:
        return "No timer scheduled"
    if state.get("status") == "cancelled":
        return "Timer Cancelled"
    if state.get("status") == "active":
        deadline = float(state.get("deadline", 0))
        remaining = max(0, int(deadline - time.time()))
        return f"Scheduled Shutdown ({format_duration(remaining)} remaining)"
    return "Timer Active"
