import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "activity_log.jsonl"


def ensure_log_dir():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def append_log(event: str, detail: str = ""):
    ensure_log_dir()
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "detail": detail,
    }
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def read_logs(limit: int = 20):
    ensure_log_dir()
    if not LOG_FILE.exists():
        return []
    records = []
    with LOG_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(records) >= limit:
                break
    return records
