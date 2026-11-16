import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - only available on Windows
    winreg = None

APP_NAME = "Hanshar Windows Toolkit"
LEGACY_APP_NAME = "Rayhan Windows Toolkit"


def get_current_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    if sys.argv and sys.argv[0]:
        return Path(sys.argv[0]).resolve()
    return Path.cwd() / "main.py"


def build_startup_command(app_path=None):
    target = Path(app_path).resolve() if app_path is not None else get_current_app_path()
    return f'"{str(target)}"'


def is_startup_enabled(app_name=APP_NAME):
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
            names = [app_name]
            if app_name == APP_NAME:
                names.append(LEGACY_APP_NAME)
            for name in names:
                try:
                    value, _ = winreg.QueryValueEx(key, name)
                    if value:
                        return True
                except FileNotFoundError:
                    continue
            return False
    except OSError:
        return False


def set_startup_enabled(enabled: bool, app_name=APP_NAME, app_path=None):
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE) as key:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, build_startup_command(app_path))
                if app_name == APP_NAME:
                    try:
                        winreg.DeleteValue(key, LEGACY_APP_NAME)
                    except FileNotFoundError:
                        pass
            else:
                names = [app_name]
                if app_name == APP_NAME:
                    names.append(LEGACY_APP_NAME)
                for name in names:
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
        return True
    except OSError:
        return False
