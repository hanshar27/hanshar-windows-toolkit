import os
import sys
from pathlib import Path

try:
    import win32api
    import win32con
    import win32gui
    import win32gui_struct
except ImportError:  # pragma: no cover - Windows-only feature
    win32api = win32con = win32gui = win32gui_struct = None


class TrayManager:
    def __init__(self, app, icon_path=None):
        self.app = app
        self.icon_path = Path(icon_path) if icon_path else Path(__file__).resolve().parents[1] / "assets" / "app_icon.ico"
        self.hwnd = None
        self._visible = False

    def create(self):
        if win32api is None:
            return False
        if self.hwnd is not None:
            return True
        try:
            self.hwnd = win32gui.CreateWindowEx(
                0,
                "STATIC",
                "TrayIcon",
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                None,
                None,
            )
            return True
        except Exception:
            return False

    def minimize_to_tray(self):
        if self.app is not None:
            self.app.withdraw()
            self._visible = False
        return True

    def restore_from_tray(self):
        if self.app is not None:
            self.app.deiconify()
            self.app.focus_set()
            self._visible = True
        return True
