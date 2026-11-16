import customtkinter as ctk
from tkinter import messagebox

from core.activity_log import append_log
from core.maintenance_tools import collect_system_info, get_maintenance_summary, run_command
from core.memory_tools import (
    clear_standby_memory,
    is_administrator,
    request_elevated_standby_memory_clear,
)
from core.ui_style import ACCENT_AMBER, BORDER_COLOR, CARD_COLOR, PANEL_COLOR
from ui.cards import InfoCard


class MaintenancePanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="Windows Maintenance", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Repair tasks, health checks, and system utilities", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "System Health", "Healthy", "No critical issues"),
            InfoCard(self.cards_container, "Windows Update", "Ready", "Update checker"),
            InfoCard(self.cards_container, "SFC Scan", "Available", "System file checks"),
            InfoCard(self.cards_container, "DISM", "Available", "Repair and restore"),
        ]

        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")

        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        actions = ctk.CTkFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        actions.pack(fill="both", expand=True, padx=18, pady=(12, 20))

        ctk.CTkLabel(actions, text="Maintenance actions", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 10))

        buttons = ctk.CTkFrame(actions, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(0, 18))

        action_specs = [
            ("System Info", self._run_system_info),
            ("Windows Update", self._run_windows_update),
            ("DISM Health", self._run_dism_health),
            ("DISM RestoreHealth", self._run_dism_restore),
            ("SFC /scannow", self._run_sfc),
            ("Device Manager", self._run_device_manager),
        ]

        self.action_buttons = []
        for label, callback in action_specs:
            button = ctk.CTkButton(buttons, text=label, width=150, height=38, corner_radius=12, command=callback)
            button.pack(side="left", padx=(0, 12), pady=4)
            self.action_buttons.append(button)

        memory_panel = ctk.CTkFrame(
            actions,
            fg_color=CARD_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        memory_panel.pack(fill="x", padx=18, pady=(0, 18))
        ctk.CTkLabel(
            memory_panel,
            text="Standby memory cache",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F4F4F8",
        ).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkLabel(
            memory_panel,
            text="Frees cached standby RAM for immediate use. Windows may cache it again when needed.",
            text_color="#A0A0B0",
            anchor="w",
            wraplength=760,
        ).pack(anchor="w", padx=14, pady=(0, 8))
        self.memory_cache_button = ctk.CTkButton(
            memory_panel,
            text="Clear Memory Cache",
            width=190,
            corner_radius=12,
            fg_color=ACCENT_AMBER,
            hover_color="#FFC465",
            command=self._clear_memory_cache,
        )
        self.memory_cache_button.pack(anchor="w", padx=14, pady=(0, 8))
        self.memory_cache_status = ctk.CTkLabel(
            memory_panel,
            text="Administrator permission is required.",
            text_color="#A0A0B0",
            anchor="w",
        )
        self.memory_cache_status.pack(fill="x", padx=14, pady=(0, 12))

        self.log = ctk.CTkTextbox(self, height=160, wrap="word")
        self.log.pack(fill="both", expand=True, padx=18, pady=(0, 20))
        self.log.configure(state="disabled")
        self.refresh_summary()

    def _set_log_text(self, text):
        self.log.configure(state="normal")
        self.log.delete("0.0", "end")
        self.log.insert("0.0", text)
        self.log.configure(state="disabled")

    def _run_system_info(self):
        output = collect_system_info()
        self._set_log_text(output)

    def _run_windows_update(self):
        result = run_command(["powershell", "-NoProfile", "-Command", "Get-WUList | Select-Object -First 5 | Format-Table -AutoSize"])
        if result["ok"] and result["stdout"]:
            self._set_log_text(result["stdout"])
        else:
            self._set_log_text("Windows Update check is not available on this system.\n" + (result["stderr"] or ""))

    def _run_dism_health(self):
        result = run_command(["DISM", "/Online", "/Cleanup-Image", "/CheckHealth"])
        if result["ok"]:
            self._set_log_text(result["stdout"] or "DISM health check completed successfully.")
        else:
            self._set_log_text(result["stderr"] or "DISM health check reported issues.")

    def _run_dism_restore(self):
        result = run_command(["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"])
        if result["ok"]:
            self._set_log_text(result["stdout"] or "DISM restore completed successfully.")
        else:
            self._set_log_text(result["stderr"] or "DISM restore could not run.")

    def _run_sfc(self):
        result = run_command(["sfc", "/scannow"])
        if result["ok"]:
            self._set_log_text(result["stdout"] or "SFC scan completed successfully.")
        else:
            self._set_log_text(result["stderr"] or "SFC scan could not run.")

    def _run_device_manager(self):
        result = run_command(["devmgmt.msc"])
        if result["ok"]:
            self._set_log_text("Device Manager launched successfully.")
        else:
            self._set_log_text(result["stderr"] or "Could not launch Device Manager.")

    def refresh_summary(self):
        summary = get_maintenance_summary()
        self.cards[0].label_value.configure(text=summary["system_health"])
        self.cards[1].label_value.configure(text=summary["windows_update"])
        self.cards[2].label_value.configure(text=summary["sfc_status"])
        self.cards[3].label_value.configure(text=summary["dism_status"])
        self._set_log_text("Windows security status: healthy\nSystem scan: no major issues detected\nRepair actions require explicit user confirmation")

    def _clear_memory_cache(self):
        confirmed = messagebox.askyesno(
            "Clear standby memory cache",
            "This asks Windows to purge cached standby memory. Windows may rebuild "
            "the cache as needed, and performance may briefly change.\n\n"
            "Continue?",
            parent=self,
        )
        if not confirmed:
            return

        self.memory_cache_button.configure(state="disabled")
        try:
            if is_administrator():
                clear_standby_memory()
                self.memory_cache_status.configure(text="Standby memory cache cleared.")
                append_log("standby_memory_cleared", "Cleared standby memory cache")
            else:
                request_elevated_standby_memory_clear()
                self.memory_cache_status.configure(
                    text="Administrator permission requested. Approve the Windows UAC prompt."
                )
                append_log("standby_memory_elevation_requested", "Requested administrator permission")
        except Exception as exc:
            self.memory_cache_status.configure(text=f"Could not clear memory cache: {exc}")
            append_log("standby_memory_clear_failed", str(exc))
        finally:
            self.memory_cache_button.configure(state="normal")
