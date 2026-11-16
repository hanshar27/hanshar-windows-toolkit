import threading

import customtkinter as ctk
from core.ui_style import BORDER_COLOR, PANEL_COLOR

from core.network_tools import (
    dns_lookup,
    flush_dns,
    get_ip_config,
    get_local_ip,
    get_network_adapters,
    internet_connected,
    ping_host,
    release_ip,
    renew_ip,
    validate_host,
)
from ui.cards import InfoCard


class NetworkToolsPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="Network Tools", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Ping, DNS, adapter diagnostics, and connectivity checks", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "Ping", "--", "Latency"),
            InfoCard(self.cards_container, "DNS", "--", "Resolver status"),
            InfoCard(self.cards_container, "Internet", "--", "Connectivity"),
            InfoCard(self.cards_container, "IP", "--", "Local address"),
        ]

        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")

        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        action_panel = ctk.CTkFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        action_panel.pack(fill="both", expand=True, padx=18, pady=(12, 20))

        ctk.CTkLabel(action_panel, text="Diagnostic actions", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 10))

        row = ctk.CTkFrame(action_panel, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 18))

        self.ping_button = ctk.CTkButton(row, text="Ping Test", width=130, height=38, corner_radius=12, command=lambda: self.run_network_action("ping"))
        self.ping_button.pack(side="left", padx=(0, 12), pady=(0, 10))

        self.dns_button = ctk.CTkButton(row, text="DNS Lookup", width=130, height=38, corner_radius=12, command=lambda: self.run_network_action("dns"))
        self.dns_button.pack(side="left", padx=(0, 12), pady=(0, 10))

        self.flush_button = ctk.CTkButton(row, text="Flush DNS", width=130, height=38, corner_radius=12, command=lambda: self.run_network_action("flush"))
        self.flush_button.pack(side="left", padx=(0, 12), pady=(0, 10))

        self.renew_button = ctk.CTkButton(row, text="Renew IP", width=130, height=38, corner_radius=12, command=lambda: self.run_network_action("renew"))
        self.renew_button.pack(side="left", padx=(0, 12), pady=(0, 10))

        self.release_button = ctk.CTkButton(row, text="Release IP", width=130, height=38, corner_radius=12, command=lambda: self.run_network_action("release"))
        self.release_button.pack(side="left", pady=(0, 10))

        self.output = ctk.CTkTextbox(self, height=200, wrap="word", corner_radius=18)
        self.output.pack(fill="both", expand=True, padx=18, pady=(0, 20))
        self.output.insert("0.0", "Ready for network diagnostics.\n")
        self.output.configure(state="disabled")

        self.refresh_summary()

    def _append_output(self, text: str):
        self.output.configure(state="normal")
        self.output.insert("end", text + "\n")
        self.output.configure(state="disabled")
        self.output.see("end")

    def refresh_summary(self):
        self.cards[0].label_value.configure(text="Checking...")
        self.cards[1].label_value.configure(text="Checking...")
        self.cards[2].label_value.configure(text="Checking...")
        self.cards[3].label_value.configure(text=get_local_ip())

        def worker():
            ping_result = ping_host("8.8.8.8")
            dns_result = dns_lookup("google.com")
            connectivity = internet_connected()
            self.after(0, lambda: self._populate_summary(ping_result, dns_result, connectivity))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_summary(self, ping_result, dns_result, connectivity):
        if ping_result.get("success"):
            self.cards[0].label_value.configure(text="Healthy")
            self.cards[0].label_subtitle.configure(text="Ping OK")
        else:
            self.cards[0].label_value.configure(text="Retry")
            self.cards[0].label_subtitle.configure(text="Ping failed")

        if dns_result.get("success"):
            self.cards[1].label_value.configure(text="Healthy")
            self.cards[1].label_subtitle.configure(text="DNS OK")
        else:
            self.cards[1].label_value.configure(text="Fail")
            self.cards[1].label_subtitle.configure(text="DNS issue")

        self.cards[2].label_value.configure(text="Online" if connectivity else "Offline")
        self.cards[2].label_subtitle.configure(text="Internet status")
        self.cards[3].label_value.configure(text=get_local_ip())
        self.cards[3].label_subtitle.configure(text="Local address")

    def run_network_action(self, action: str):
        if action == "ping":
            self._append_output("Running ping test against 8.8.8.8...")
            result = ping_host("8.8.8.8")
            self._append_output(result.get("output", "No output returned"))
        elif action == "dns":
            self._append_output("Running DNS lookup for google.com...")
            result = dns_lookup("google.com")
            self._append_output(str(result))
        elif action == "flush":
            self._append_output("Running DNS flush...")
            result = flush_dns()
            self._append_output(str(result))
        elif action == "renew":
            self._append_output("Running IP renew...")
            result = renew_ip()
            self._append_output(str(result))
        elif action == "release":
            self._append_output("Running IP release...")
            result = release_ip()
            self._append_output(str(result))

        self.refresh_summary()
