import sys
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

from core.activity_log import append_log
from core.app_state import load_app_state, save_app_state
from core.memory_tools import ELEVATED_ACTION_ARGUMENT, clear_standby_memory
from core.settings_manager import load_settings
from core.tray_manager import TrayManager
from core.ui_style import (
    DEFAULT_BLUR_INTENSITY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WINDOW_BACKGROUND,
)
from core.window_effects import apply_window_backdrop
from modules.activity import ActivityLogPanel
from modules.dashboard import DashboardPanel
from modules.gaming import GamingPanel
from modules.maintenance import MaintenancePanel
from modules.monitor import SystemMonitorPanel
from modules.network import NetworkToolsPanel
from modules.power import PowerManagerPanel
from modules.settings import SettingsPanel
from modules.storage import StorageCleanerPanel
from modules.system_information import SystemInformationPanel
from ui.sidebar import Sidebar

try:
    from pystray import Icon, Menu, MenuItem
except ImportError:  # pragma: no cover
    Icon = None
    Menu = None
    MenuItem = None


class HansharWindowsToolkitApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.app_state = load_app_state()
        self.blur_intensity = self.settings.get(
            "blur_intensity", DEFAULT_BLUR_INTENSITY
        )
        self.title("Hanshar Windows Toolkit")
        self.geometry("1280x760")
        self.minsize(980, 620)
        self.configure(fg_color=WINDOW_BACKGROUND)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        icon_path = Path(__file__).resolve().parent / "assets" / "app_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.sidebar = Sidebar(self, command=self.show_page)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.footer = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0, height=28)
        self.footer.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_columnconfigure(1, weight=0)

        self.status_label = ctk.CTkLabel(
            self.footer,
            text=self.app_state.get("status", "Ready"),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=(12, 0), sticky="w")

        self.version_label = ctk.CTkLabel(
            self.footer,
            text=f"v{self.settings.get('app_version', '1.0.0')}",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
        )
        self.version_label.grid(row=0, column=1, padx=(0, 12), sticky="e")

        self.tray = TrayManager(self)
        self.bind("<Unmap>", self._handle_minimize)
        self.bind("<Map>", self._handle_restore)
        self._setup_tray_icon()

        self.pages = {
            "Dashboard": DashboardPanel(self.content),
            "System Monitor": SystemMonitorPanel(self.content),
            "System Information": SystemInformationPanel(self.content),
            "Storage Cleaner": StorageCleanerPanel(self.content),
            "Power Manager": PowerManagerPanel(self.content),
            "Network Tools": NetworkToolsPanel(self.content),
            "Gaming": GamingPanel(self.content),
            "Maintenance": MaintenancePanel(self.content),
            "Activity Log": ActivityLogPanel(self.content),
            "Settings": SettingsPanel(
                self.content,
                on_blur_change=self.set_blur_intensity,
                initial_blur_intensity=self.blur_intensity,
            ),
        }

        for frame in self.pages.values():
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()

        self.after(
            150,
            lambda: self.set_blur_intensity(self.blur_intensity, persist=False),
        )
        append_log("app_started", "Hanshar Windows Toolkit launched")
        self.show_page(self.app_state.get("last_page", "Dashboard"))

    def set_blur_intensity(self, intensity: int, persist: bool = False) -> bool:
        self.blur_intensity = max(0, min(100, int(intensity)))
        self.settings["blur_intensity"] = self.blur_intensity
        applied = apply_window_backdrop(self, self.blur_intensity)
        if persist:
            save_settings(self.settings)
        if not applied:
            append_log(
                "backdrop_unavailable",
                f"Windows acrylic backdrop could not be applied at {self.blur_intensity}%.",
            )
        return applied

    def show_page(self, page_name: str):
        for name, frame in self.pages.items():
            if name == page_name:
                frame.grid()
                self.sidebar.set_active(page_name)
                self.set_status(f"{page_name} active")
            else:
                frame.grid_remove()
        self.app_state["last_page"] = page_name
        save_app_state(self.app_state)
        append_log("page_viewed", page_name)

    def set_status(self, message: str):
        self.status_label.configure(text=message)
        self.app_state["status"] = message
        save_app_state(self.app_state)
        append_log("status_changed", message)

    def _setup_tray_icon(self):
        if Icon is None or Menu is None or MenuItem is None:
            return
        try:
            icon_path = Path(__file__).resolve().parent / "assets" / "app_icon.ico"
            app_menu = Menu(
                MenuItem("Restore", self._restore_from_tray),
                MenuItem("Exit", self._exit_app),
            )
            self.pystray_icon = Icon("Hanshar Windows Toolkit", str(icon_path), menu=app_menu)
        except Exception:
            self.pystray_icon = None

    def _restore_from_tray(self):
        if self.pystray_icon is not None:
            try:
                self.pystray_icon.stop()
            except Exception:
                pass
        self.tray.restore_from_tray()

    def _exit_app(self):
        try:
            if self.pystray_icon is not None:
                self.pystray_icon.stop()
        except Exception:
            pass
        self.destroy()

    def _handle_minimize(self, event=None):
        if self.state() == "iconic" and self.pystray_icon is not None:
            self.tray.minimize_to_tray()
            try:
                self.pystray_icon.run()
            except Exception:
                pass

    def _handle_restore(self, event=None):
        self.tray.restore_from_tray()


def main():
    if ELEVATED_ACTION_ARGUMENT in sys.argv[1:]:
        try:
            clear_standby_memory()
        except Exception as exc:
            messagebox.showerror(
                "Hanshar Windows Toolkit",
                f"Could not clear standby memory:\n{exc}",
            )
            raise SystemExit(1)
        messagebox.showinfo(
            "Hanshar Windows Toolkit",
            "Windows cleared the standby memory cache.",
        )
        return

    app = HansharWindowsToolkitApp()
    app.mainloop()


if __name__ == "__main__":
    main()
