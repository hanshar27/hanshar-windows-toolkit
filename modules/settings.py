import customtkinter as ctk

from core.settings_manager import load_settings, save_settings
from core.startup_manager import is_startup_enabled, set_startup_enabled
from core.ui_style import (
    ACCENT_COLOR,
    ACCENT_PURPLE,
    BORDER_COLOR,
    DEFAULT_BLUR_INTENSITY,
    PANEL_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, master, on_blur_change=None, initial_blur_intensity=None):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.settings = load_settings()
        self.on_blur_change = on_blur_change
        self.blur_intensity = max(
            0,
            min(
                100,
                int(
                    self.settings.get("blur_intensity", DEFAULT_BLUR_INTENSITY)
                    if initial_blur_intensity is None
                    else initial_blur_intensity
                ),
            ),
        )
        self._save_after_id = None

        ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(18, 8))

        ctk.CTkLabel(
            self,
            text="Personalize the glass effect and application behavior",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.panel = ctk.CTkFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self.panel.pack(fill="both", expand=True, padx=20, pady=(8, 20))

        ctk.CTkLabel(
            self.panel,
            text="Glass appearance",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=22, pady=(22, 8))

        ctk.CTkLabel(
            self.panel,
            text=(
                "Adjust how strongly the Windows acrylic backdrop shows through the app. "
                "The blur radius itself is controlled by Windows."
            ),
            text_color=TEXT_SECONDARY,
            wraplength=700,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 14))

        self.blur_value_label = ctk.CTkLabel(
            self.panel,
            text=f"Blur strength  {self.blur_intensity}%",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.blur_value_label.pack(anchor="w", padx=22, pady=(0, 8))

        self.blur_slider = ctk.CTkSlider(
            self.panel,
            from_=0,
            to=100,
            number_of_steps=20,
            command=self._apply_blur,
            progress_color=ACCENT_PURPLE,
            button_color=ACCENT_PURPLE,
            button_hover_color="#FFC465",
            width=460,
        )
        self.blur_slider.pack(anchor="w", padx=22, pady=(0, 8))
        self.blur_slider.set(self.blur_intensity)

        ctk.CTkLabel(
            self.panel,
            text="Off",
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=22, pady=(0, 20))

        self.confirmation = ctk.CTkSwitch(
            self.panel,
            text="Require confirmation for destructive actions",
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT_COLOR,
        )
        self.confirmation.pack(anchor="w", padx=22, pady=(0, 14))
        if self.settings.get("require_confirmation", True):
            self.confirmation.select()
        else:
            self.confirmation.deselect()

        self.startup = ctk.CTkSwitch(
            self.panel,
            text="Launch with Windows startup",
            onvalue=True,
            offvalue=False,
            command=self._toggle_startup,
            progress_color=ACCENT_COLOR,
        )
        self.startup.pack(anchor="w", padx=22, pady=(0, 22))
        self.settings["startup_on_login"] = self.settings.get(
            "startup_on_login", is_startup_enabled()
        )
        if self.settings["startup_on_login"]:
            self.startup.select()
        else:
            self.startup.deselect()

        ctk.CTkLabel(
            self.panel,
            text="Application details",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=22, pady=(0, 10))
        self.info = ctk.CTkLabel(
            self.panel,
            text=self._details_text(),
            text_color=TEXT_SECONDARY,
            justify="left",
        )
        self.info.pack(anchor="w", padx=22, pady=(0, 18))

        self.save_button = ctk.CTkButton(
            self.panel,
            text="Save Settings",
            command=self.save_settings,
            fg_color=ACCENT_COLOR,
            hover_color="#343744",
            corner_radius=12,
        )
        self.save_button.pack(anchor="w", padx=22, pady=(0, 22))

    def _details_text(self):
        return (
            f"Version {self.settings.get('app_version', '1.0.0')}\n"
            f"Log directory: {self.settings.get('log_directory', 'logs')}\n"
            "Appearance: Hanshar Glass\n"
            "About: Hanshar Windows Toolkit"
        )

    def _apply_blur(self, value):
        self.blur_intensity = max(0, min(100, int(round(float(value)))))
        self.blur_value_label.configure(text=f"Blur strength  {self.blur_intensity}%")
        self.settings["blur_intensity"] = self.blur_intensity

        if self.on_blur_change is not None:
            applied = self.on_blur_change(self.blur_intensity)
            self.info.configure(
                text=(
                    self._details_text()
                    if applied
                    else self._details_text()
                    + "\nWindows acrylic backdrop is unavailable on this system."
                )
            )

        if self._save_after_id is not None:
            self.after_cancel(self._save_after_id)
        self._save_after_id = self.after(350, self._save_blur_setting)

    def _save_blur_setting(self):
        self._save_after_id = None
        try:
            save_settings(self.settings)
        except OSError as exc:
            self.info.configure(text=f"{self._details_text()}\nCould not save blur setting: {exc}")

    def _toggle_startup(self):
        enabled = bool(self.startup.get())
        self.settings["startup_on_login"] = enabled
        set_startup_enabled(enabled)

    def save_settings(self):
        self.settings["blur_intensity"] = self.blur_intensity
        self.settings["require_confirmation"] = bool(self.confirmation.get())
        self.settings["startup_on_login"] = bool(self.startup.get())
        try:
            set_startup_enabled(self.settings["startup_on_login"])
            save_settings(self.settings)
        except OSError as exc:
            self.info.configure(text=f"{self._details_text()}\nCould not save settings: {exc}")
            return
        self.info.configure(text=f"{self._details_text()}\nSettings saved.")
