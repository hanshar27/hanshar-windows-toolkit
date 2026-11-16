import customtkinter as ctk

from core.system_info import get_gpu_name
from core.system_monitor import get_system_snapshot
from core.system_report import generate_system_report
from ui.cards import InfoCard


class SystemMonitorPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="System Monitor", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Real-time performance and health overview", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "CPU", "0%", "Current utilization"),
            InfoCard(self.cards_container, "RAM", "0%", "Memory in use"),
            InfoCard(self.cards_container, "Disk", "0%", "Drive workload"),
            InfoCard(self.cards_container, "Network", "0 MB", "Bytes transferred"),
        ]

        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")

        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", padx=18, pady=(10, 6))
        self.export_button = ctk.CTkButton(self.action_bar, text="Export Report", command=self.export_report, corner_radius=12)
        self.export_button.pack(side="left")
        self.report_status = ctk.CTkLabel(self.action_bar, text="No report generated yet", text_color="#A0A0B0")
        self.report_status.pack(side="left", padx=(12, 0))

        self.display = ctk.CTkTextbox(self, height=220, wrap="word", corner_radius=18)
        self.display.pack(fill="both", expand=True, padx=18, pady=(10, 20))
        self.display.configure(state="disabled")

        self.after(500, self.refresh_monitor)

    def export_report(self):
        report = generate_system_report()
        self.report_status.configure(text=f"Report saved: reports/system_report.json")
        self.display.configure(state="normal")
        self.display.insert("end", f"\n--- System report exported ---\nGenerated at: {report.get('generated_at', 'Unknown')}\n")
        self.display.configure(state="disabled")

    def refresh_monitor(self):
        snapshot = get_system_snapshot()
        self.cards[0].label_value.configure(text=f"{snapshot['cpu_usage']:.1f}%")
        self.cards[1].label_value.configure(text=f"{snapshot['ram_usage']:.1f}%")
        self.cards[2].label_value.configure(text=f"{snapshot['disk_usage']:.1f}%")
        self.cards[3].label_value.configure(text=f"{snapshot['network_sent']:.1f} MB")

        gpu_name = get_gpu_name() or "GPU not detected"
        self.display.configure(state="normal")
        self.display.delete("0.0", "end")
        self.display.insert("0.0", f"CPU Usage: {snapshot['cpu_usage']:.1f}%\n")
        self.display.insert("end", f"RAM Usage: {snapshot['ram_usage']:.1f}%\n")
        self.display.insert("end", f"Disk Usage: {snapshot['disk_usage']:.1f}%\n")
        self.display.insert("end", f"GPU: {gpu_name}\n")
        gpu_temperature = snapshot["gpu_temperature"]
        self.display.insert(
            "end",
            "GPU Temperature: "
            f"{gpu_temperature:.1f}°C\n"
            if gpu_temperature is not None
            else "GPU Temperature: Unavailable\n",
        )
        self.display.insert("end", f"Processes: {snapshot['process_count']}\n")
        self.display.insert("end", f"Uptime: {snapshot['uptime']}\n")
        self.display.insert("end", f"Network Sent: {snapshot['network_sent']:.2f} MB\n")
        self.display.insert("end", f"Network Received: {snapshot['network_recv']:.2f} MB\n")
        self.display.configure(state="disabled")
        self.after(1500, self.refresh_monitor)
