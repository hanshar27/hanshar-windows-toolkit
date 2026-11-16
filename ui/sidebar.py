import customtkinter as ctk


SIDEBAR_COLOR = "#21201e"
ACTIVE_COLOR = "#33312e"
HOVER_COLOR = "#2a2825"
TEXT_COLOR = "#e6e5e3"
MUTED_COLOR = "#a7a29c"


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, items=None, command=None, **kwargs):
        super().__init__(
            master,
            width=190,
            corner_radius=0,
            fg_color=SIDEBAR_COLOR,
            **kwargs,
        )
        self.command = command
        self.items = items or [
            "Dashboard",
            "System Monitor",
            "System Information",
            "Storage Cleaner",
            "Power Manager",
            "Network Tools",
            "Gaming",
            "Maintenance",
            "Activity Log",
            "Settings",
        ]
        self.item_icons = {
            "Dashboard": "▦",
            "System Monitor": "◷",
            "System Information": "ⓘ",
            "Storage Cleaner": "▤",
            "Power Manager": "⏻",
            "Network Tools": "⌁",
            "Gaming": "▶",
            "Maintenance": "⚙",
            "Activity Log": "≡",
            "Settings": "⚙",
        }
        self.buttons = {}

        title = ctk.CTkLabel(
            self,
            text="HANSHAR",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_COLOR,
        )
        title.pack(anchor="w", padx=18, pady=(22, 8))

        subtitle = ctk.CTkLabel(
            self,
            text="Windows Toolkit",
            font=ctk.CTkFont(size=13),
            text_color=MUTED_COLOR,
        )
        subtitle.pack(anchor="w", padx=18, pady=(0, 16))

        for item in self.items:
            btn = ctk.CTkButton(
                self,
                text=f"{self.item_icons.get(item, '•')}    {item}",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                hover_color=HOVER_COLOR,
                border_width=0,
                text_color=TEXT_COLOR,
                anchor="w",
                font=ctk.CTkFont(size=14),
                command=lambda value=item: self._handle_click(value),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.buttons[item] = btn

        self.active_item = self.items[0]
        self.set_active(self.active_item)

    def _handle_click(self, item: str):
        self.set_active(item)
        if self.command is not None:
            self.command(item)

    def set_active(self, item: str):
        self.active_item = item
        for key, button in self.buttons.items():
            if key == item:
                button.configure(
                    fg_color=ACTIVE_COLOR,
                    hover_color=ACTIVE_COLOR,
                    text_color="#FFFFFF",
                )
            else:
                button.configure(
                    fg_color="transparent",
                    hover_color=HOVER_COLOR,
                    text_color=TEXT_COLOR,
                )
