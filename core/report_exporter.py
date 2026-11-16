import csv
import json
from pathlib import Path

from core.activity_log import read_logs

EXPORT_DIR = Path(__file__).resolve().parents[1] / "exports"


def export_activity_csv(path: str | Path | None = None):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(path) if path else EXPORT_DIR / "activity_log.csv"
    rows = read_logs(500)
    fieldnames = ["timestamp", "event", "detail"]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "timestamp": row.get("timestamp", ""),
                "event": row.get("event", ""),
                "detail": row.get("detail", ""),
            })
    return str(out_path)


def export_activity_json(path: str | Path | None = None):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(path) if path else EXPORT_DIR / "activity_log.json"
    rows = read_logs(500)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)
    return str(out_path)
