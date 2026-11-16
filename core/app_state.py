import json
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parents[1] / "app_state.json"

DEFAULT_STATE = {
    "last_page": "Dashboard",
    "status": "Ready",
}


def load_app_state(path: str | Path = STATE_PATH):
    state = DEFAULT_STATE.copy()
    config_path = Path(path)
    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                state.update(loaded)
                state.pop("theme", None)
        except (json.JSONDecodeError, OSError):
            return state
    return state


def save_app_state(state: dict, path: str | Path = STATE_PATH):
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    saved_state = {key: value for key, value in state.items() if key != "theme"}
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(saved_state, handle, indent=2)
    return saved_state
