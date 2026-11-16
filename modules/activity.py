import customtkinter as ctk

from core.activity_log import read_logs
from core.report_exporter import export_activity_csv, export_activity_json


class ActivityLogPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")

        title = ctk.CTkLabel(self, text="Activity Log", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self, text="Recent application events and status changes", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.toolbar = ctk.CTkFrame(self, fg_color="transparent")
        self.toolbar.pack(fill="x", padx=20, pady=(0, 8))
        self.export_csv = ctk.CTkButton(self.toolbar, text="Export CSV", command=self._export_csv, corner_radius=12)
        self.export_csv.pack(side="left")
        self.export_json = ctk.CTkButton(self.toolbar, text="Export JSON", command=self._export_json, corner_radius=12)
        self.export_json.pack(side="left", padx=(10, 0))
        self.status_label = ctk.CTkLabel(self.toolbar, text="Ready", text_color="#A0A0B0")
        self.status_label.pack(side="left", padx=(12, 0))

        self.log_view = ctk.CTkTextbox(self, height=420, wrap="word")
        self.log_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_view.configure(state="disabled")

        self.refresh_logs()

    def _export_csv(self):
        path = export_activity_csv()
        self.status_label.configure(text=f"Exported CSV: {path}")

    def _export_json(self):
        path = export_activity_json()
        self.status_label.configure(text=f"Exported JSON: {path}")

    def refresh_logs(self):
        records = read_logs(50)
        self.log_view.configure(state="normal")
        self.log_view.delete("0.0", "end")
        if not records:
            self.log_view.insert("0.0", "No activity recorded yet.\n")
        else:
            for record in records:
                stamp = record.get("timestamp", "Unknown")
                event = record.get("event", "event")
                detail = record.get("detail", "")
                line = f"[{stamp}] {event}"
                if detail:
                    line += f" - {detail}"
                self.log_view.insert("end", line + "\n")
        self.log_view.configure(state="disabled")
