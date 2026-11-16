import json
from datetime import datetime
from pathlib import Path

from core.system_info import get_system_summary
from core.system_monitor import get_system_snapshot

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def generate_system_report():
    summary = get_system_summary()
    snapshot = get_system_snapshot()
    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": summary,
        "snapshot": snapshot,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "system_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return payload


def read_system_report(path: str | Path | None = None):
    report_path = Path(path) if path else REPORTS_DIR / "system_report.json"
    if not report_path.exists():
        return {}
    with report_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
