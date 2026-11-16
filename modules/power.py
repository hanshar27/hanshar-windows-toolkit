import subprocess
import threading
import time

import customtkinter as ctk
from core.ui_style import ACCENT_AMBER, ACCENT_COLOR, BORDER_COLOR, PANEL_COLOR, TEXT_SECONDARY

from core.shutdown_timer import (
    cancel_windows_shutdown,
    clear_timer_state,
    describe_timer_state,
    format_duration,
    get_remaining_seconds,
    load_timer_state,
    schedule_windows_shutdown,
    validate_timer_input,
)
from ui.cards import InfoCard


class PowerManagerPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="Power Manager", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Shutdown, sleep, hibernate, and power plan control", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "Power Plan", "Balanced", "Current profile"),
            InfoCard(self.cards_container, "Sleep", "Available", "Quick resume"),
            InfoCard(self.cards_container, "Hibernate", "Available", "Low-power state"),
            InfoCard(self.cards_container, "Shutdown Timer", "Idle", "No active timer"),
        ]

        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")

        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        action_panel = ctk.CTkFrame(
            self, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR
        )
        action_panel.pack(fill="both", expand=True, padx=18, pady=(14, 10))

        ctk.CTkLabel(action_panel, text="Quick actions", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 10))

        button_row = ctk.CTkFrame(action_panel, fg_color="transparent")
        button_row.pack(fill="x", padx=18, pady=(0, 18))

        self.shutdown_now = ctk.CTkButton(button_row, text="Shutdown Now", width=140, height=38, corner_radius=12, command=self.handle_shutdown_now)
        self.shutdown_now.pack(side="left", padx=(0, 12))
        self.restart_now = ctk.CTkButton(button_row, text="Restart Now", width=140, height=38, corner_radius=12, command=self.handle_restart_now)
        self.restart_now.pack(side="left", padx=(0, 12))
        self.sleep_now = ctk.CTkButton(button_row, text="Sleep", width=140, height=38, corner_radius=12, command=self.handle_sleep)
        self.sleep_now.pack(side="left", padx=(0, 12))
        self.hibernate_now = ctk.CTkButton(button_row, text="Hibernate", width=140, height=38, corner_radius=12, command=self.handle_hibernate)
        self.hibernate_now.pack(side="left")

        timer_panel = ctk.CTkFrame(
            self, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR
        )
        timer_panel.pack(fill="both", expand=True, padx=18, pady=(0, 20))

        ctk.CTkLabel(timer_panel, text="Shutdown timer", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 10))
        self.timer_label = ctk.CTkLabel(timer_panel, text="00:00:00", font=ctk.CTkFont(size=34, weight="bold"), text_color=ACCENT_COLOR)
        self.timer_label.pack(anchor="w", padx=18, pady=(0, 10))

        preset_frame = ctk.CTkFrame(timer_panel, fg_color="transparent")
        preset_frame.pack(fill="x", padx=18, pady=(0, 12))
        for minutes in [30, 60, 120, 180, 300]:
            label = self._preset_label(minutes)
            btn = ctk.CTkButton(preset_frame, text=label, width=110, height=32, corner_radius=12, command=lambda value=minutes: self.apply_preset(value))
            btn.pack(side="left", padx=(0, 8))

        custom_frame = ctk.CTkFrame(timer_panel, fg_color="transparent")
        custom_frame.pack(fill="x", padx=18, pady=(0, 12))
        self.hours_entry = ctk.CTkEntry(custom_frame, width=70, placeholder_text="Hours")
        self.hours_entry.pack(side="left", padx=(0, 8))
        self.minutes_entry = ctk.CTkEntry(custom_frame, width=70, placeholder_text="Minutes")
        self.minutes_entry.pack(side="left", padx=(0, 8))
        self.seconds_entry = ctk.CTkEntry(custom_frame, width=70, placeholder_text="Seconds")
        self.seconds_entry.pack(side="left")

        controls = ctk.CTkFrame(timer_panel, fg_color="transparent")
        controls.pack(fill="x", padx=18, pady=(0, 18))
        self.start_btn = ctk.CTkButton(controls, text="START TIMER", width=150, height=38, corner_radius=12, fg_color=ACCENT_COLOR, hover_color="#70A4FF", command=self.start_timer)
        self.start_btn.pack(side="left", padx=(0, 12))
        self.cancel_btn = ctk.CTkButton(controls, text="CANCEL TIMER", width=150, height=38, corner_radius=12, fg_color=ACCENT_AMBER, hover_color="#FFC465", command=self.cancel_timer)
        self.cancel_btn.pack(side="left", padx=(0, 12))
        self.reset_btn = ctk.CTkButton(controls, text="RESET TIMER", width=150, height=38, corner_radius=12, command=self.reset_timer)
        self.reset_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(timer_panel, text="Timer Idle", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        self.status_label.pack(anchor="w", padx=18, pady=(0, 18))

        self.remaining_seconds = 0
        self.timer_active = False
        self.after(500, self.refresh_timer_state)

    @staticmethod
    def _preset_label(minutes: int) -> str:
        if minutes >= 60 and minutes % 60 == 0:
            hours = minutes // 60
            unit = "Hour" if hours == 1 else "Hours"
            return f"{hours} {unit}"
        return f"{minutes} Minutes"

    def apply_preset(self, minutes: int):
        total_seconds = max(1, int(minutes) * 60)
        hours = total_seconds // 3600
        minutes_rem = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.hours_entry.delete(0, "end")
        self.minutes_entry.delete(0, "end")
        self.seconds_entry.delete(0, "end")
        self.hours_entry.insert(0, str(hours))
        self.minutes_entry.insert(0, str(minutes_rem))
        self.seconds_entry.insert(0, str(seconds))

    def refresh_timer_state(self):
        state = load_timer_state()
        if state and state.get("status") == "active":
            remaining = max(0, int(float(state.get("deadline", 0)) - time.time()))
            self.remaining_seconds = remaining
            self.timer_active = True
            self.timer_label.configure(text=format_duration(remaining))
            self.status_label.configure(text=describe_timer_state())
            self.cards[3].label_value.configure(text="Active")
            self.after(250, self.refresh_timer_state)
            return

        if state and state.get("status") == "cancelled":
            self.timer_label.configure(text="00:00:00")
            self.status_label.configure(text="Timer Cancelled")
            self.cards[3].label_value.configure(text="Cancelled")
        else:
            self.timer_label.configure(text="00:00:00")
            self.status_label.configure(text="Timer Idle")
            self.cards[3].label_value.configure(text="Idle")
        self.timer_active = False
        self.after(500, self.refresh_timer_state)

    def start_timer(self):
        try:
            hours = int(self.hours_entry.get() or 0)
            minutes = int(self.minutes_entry.get() or 0)
            seconds = int(self.seconds_entry.get() or 0)
            total_seconds = validate_timer_input(hours, minutes, seconds)
        except ValueError:
            self.status_label.configure(text="Invalid timer input")
            return

        self.remaining_seconds = total_seconds
        self.timer_active = True
        self.timer_label.configure(text=format_duration(total_seconds))
        self.status_label.configure(text="Scheduled Shutdown")
        self.cards[3].label_value.configure(text="Active")

        try:
            schedule_windows_shutdown(total_seconds)
        except Exception:
            self.status_label.configure(text="Shutdown could not be scheduled")
            self.cards[3].label_value.configure(text="Error")
            return

        self.after(250, self.refresh_timer_state)

    def cancel_timer(self):
        try:
            cancel_windows_shutdown()
        except Exception:
            self.status_label.configure(text="Unable to cancel shutdown")
            return
        clear_timer_state()
        self.remaining_seconds = 0
        self.timer_active = False
        self.timer_label.configure(text="00:00:00")
        self.status_label.configure(text="Timer Cancelled")
        self.cards[3].label_value.configure(text="Cancelled")

    def reset_timer(self):
        clear_timer_state()
        self.remaining_seconds = 0
        self.timer_active = False
        self.timer_label.configure(text="00:00:00")
        self.status_label.configure(text="Timer Idle")
        self.cards[3].label_value.configure(text="Idle")

    def handle_shutdown_now(self):
        subprocess.run(["shutdown", "/s", "/t", "0"], check=False)

    def handle_restart_now(self):
        subprocess.run(["shutdown", "/r", "/t", "0"], check=False)

    def handle_sleep(self):
        subprocess.run(["rundll32", "powrprof.dll,SetSuspendState", "0", "1", "0"], check=False)

    def handle_hibernate(self):
        subprocess.run(["shutdown", "/h"], check=False)
