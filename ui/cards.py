import customtkinter as ctk

from core.ui_style import BORDER_COLOR, CARD_COLOR, TEXT_PRIMARY, TEXT_SECONDARY


class InfoCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, subtitle: str = "", **kwargs):
        super().__init__(
            master,
            corner_radius=18,
            fg_color=CARD_COLOR,
            border_width=1,
            border_color=BORDER_COLOR,
            **kwargs,
        )

        self.label_title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_SECONDARY)
        self.label_title.pack(anchor="w", padx=16, pady=(16, 4))

        self.label_value = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_PRIMARY)
        self.label_value.pack(anchor="w", padx=16)

        if subtitle:
            self.label_subtitle = ctk.CTkLabel(self, text=subtitle, font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY)
            self.label_subtitle.pack(anchor="w", padx=16, pady=(0, 16))
