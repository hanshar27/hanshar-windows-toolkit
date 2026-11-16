import json
import os
import sys
from pathlib import Path

from core.ui_style import DEFAULT_BLUR_INTENSITY

DEFAULT_SETTINGS = {
    "app_name": "Hanshar Windows Toolkit",
    "app_version": "1.0.0",
    "blur_intensity": DEFAULT_BLUR_INTENSITY,
    "log_directory": "logs",
    "startup_on_login": False,
    "require_confirmation": True,
}


def _candidate_config_paths():
    candidates = []
    project_root = Path(__file__).resolve().parents[1]
    if getattr(sys, "frozen", False):
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        candidates.append(
            local_app_data / "Hanshar Windows Toolkit" / "config.json"
        )
        candidates.append(Path(sys.executable).resolve().parent / "config.json")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "config.json")
    else:
        candidates.append(project_root / "config.json")
    return [path for path in candidates if path]


def _resolve_config_path(path=None):
    if path is not None:
        return Path(path)
    if getattr(sys, "frozen", False):
        return _candidate_config_paths()[0]
    for config_path in _candidate_config_paths():
        if config_path.exists():
            return config_path
    return _candidate_config_paths()[0]


def load_settings(path: str | Path | None = None):
    config = DEFAULT_SETTINGS.copy()
    config_paths = [Path(path)] if path is not None else _candidate_config_paths()
    for config_path in config_paths:
        if not config_path.exists():
            continue
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
                if isinstance(loaded, dict):
                    config.update(loaded)
                    break
        except (json.JSONDecodeError, OSError):
            return config
    config.pop("theme", None)
    try:
        config["blur_intensity"] = max(
            0, min(100, int(config.get("blur_intensity", DEFAULT_BLUR_INTENSITY)))
        )
    except (TypeError, ValueError):
        config["blur_intensity"] = DEFAULT_BLUR_INTENSITY
    return config


def save_settings(settings: dict, path: str | Path | None = None):
    config_path = _resolve_config_path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    saved_settings = {
        key: value for key, value in settings.items() if key != "theme"
    }
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(saved_settings, handle, indent=2)
    return saved_settings
