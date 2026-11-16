import customtkinter as ctk

from core.gaming_tools import get_latency_hint, get_power_plans, get_startup_apps
from core.ui_style import ACCENT_PURPLE, BORDER_COLOR, PANEL_COLOR
from ui.cards import InfoCard


class GamingPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="Gaming & Performance", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Performance mode, process awareness, and network checks", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "Gaming Mode", "Enabled", "Optimized profile"),
            InfoCard(self.cards_container, "CPU", "--%", "During gameplay"),
            InfoCard(self.cards_container, "RAM", "--%", "Current usage"),
            InfoCard(self.cards_container, "Ping", "-- ms", "Network quality"),
        ]

        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")

        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        utility_panel = ctk.CTkFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        utility_panel.pack(fill="both", expand=True, padx=18, pady=(12, 18))

        ctk.CTkLabel(utility_panel, text="Gaming utilities", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 12))

        buttons = ctk.CTkFrame(utility_panel, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(0, 18))
        for label in ["Performance Profile", "Startup Overview", "Latency Test", "FPS Monitor"]:
            ctk.CTkButton(
                buttons,
                text=label,
                width=150,
                height=38,
                corner_radius=12,
                fg_color=ACCENT_PURPLE,
                hover_color="#C779FF",
            ).pack(side="left", padx=(0, 12), pady=4)

        self.summary = ctk.CTkTextbox(self, height=180, wrap="word")
        self.summary.pack(fill="both", expand=True, padx=18, pady=(0, 20))
        self.summary.configure(state="disabled")

        self.refresh_stats()

    def refresh_stats(self):
        power_plans = get_power_plans()
        startup = get_startup_apps()
        summary_lines = [
            "Game mode: available",
            f"Power plan available: High Performance={power_plans.get('high_performance', False)}, Balanced={power_plans.get('balanced', False)}",
            f"Latency guidance: {get_latency_hint()}",
            f"Startup apps: {len(startup)} item(s) listed",
            "Background apps: non-critical tasks should be minimized during gameplay",
        ]

        self.cards[1].label_value.configure(text="42%")
        self.cards[2].label_value.configure(text="61%")
        self.cards[3].label_value.configure(text="18 ms")

        self.summary.configure(state="normal")
        self.summary.delete("0.0", "end")
        self.summary.insert("0.0", "\n".join(summary_lines))
        self.summary.configure(state="disabled")
