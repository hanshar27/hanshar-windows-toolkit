import threading

import customtkinter as ctk

from core.storage_manager import delete_entries, scan_cache_locations
from core.ui_style import (
    ACCENT_COLOR,
    ACCENT_PURPLE,
    BORDER_COLOR,
    CARD_COLOR,
    PANEL_COLOR,
)
from ui.cards import InfoCard


class StorageCleanerPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.configure(fg_color="transparent")
        self.mode = "safe"
        self.results = []
        self.category_checkboxes = {}

        self.content_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.content_frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(self.content_frame, text="Storage Cleaner", font=ctk.CTkFont(size=28, weight="bold"), text_color="#F4F4F8")
        title.pack(anchor="w", padx=20, pady=(18, 8))

        subtitle = ctk.CTkLabel(self.content_frame, text="Safe scan and preview for temporary files and verified cache", font=ctk.CTkFont(size=12), text_color="#A0A0B0")
        subtitle.pack(anchor="w", padx=20, pady=(0, 14))

        self.cards_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.cards_container.pack(fill="x", padx=20, pady=(0, 8))

        self.cards = [
            InfoCard(self.cards_container, "Files", "0", "Scanned items"),
            InfoCard(self.cards_container, "Size", "0 MB", "Estimated cleanup"),
            InfoCard(self.cards_container, "Categories", "0", "Safe groups"),
            InfoCard(self.cards_container, "State", "Idle", "Waiting"),
        ]
        for idx, card in enumerate(self.cards):
            card.grid(row=0, column=idx, padx=18, pady=8, sticky="nsew")
        for i in range(4):
            self.cards_container.grid_columnconfigure(i, weight=1)

        mode_frame = ctk.CTkFrame(self.content_frame, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        mode_frame.pack(fill="x", padx=18, pady=(12, 18))

        ctk.CTkLabel(mode_frame, text="Cleanup modes", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 8))

        self.safe_btn = ctk.CTkButton(mode_frame, text="SAFE CLEANUP", width=180, height=40, corner_radius=12, fg_color=ACCENT_PURPLE, hover_color="#C779FF", command=lambda: self.set_mode("safe"))
        self.safe_btn.pack(side="left", padx=18, pady=(0, 18))

        self.deep_btn = ctk.CTkButton(mode_frame, text="DEEP CLEANUP", width=180, height=40, corner_radius=12, fg_color=ACCENT_PURPLE, hover_color="#C779FF", command=lambda: self.set_mode("deep"))
        self.deep_btn.pack(side="left", padx=(0, 18), pady=(0, 18))

        self.scan_btn = ctk.CTkButton(mode_frame, text="SCAN", width=120, height=40, corner_radius=12, fg_color=ACCENT_COLOR, hover_color="#70A4FF", command=self.scan_selected_mode)
        self.scan_btn.pack(side="left", padx=(0, 10), pady=(0, 18))

        self.clean_btn = ctk.CTkButton(mode_frame, text="DELETE SELECTED", width=160, height=40, corner_radius=12, command=self.confirm_cleanup)
        self.clean_btn.pack(side="left", padx=(0, 12), pady=(0, 18))

        category_frame = ctk.CTkFrame(self.content_frame, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        category_frame.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(category_frame, text="Cleanup categories", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 8))
        self.category_container = ctk.CTkScrollableFrame(
            category_frame, fg_color="transparent", height=160
        )
        self.category_container.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        preview_frame = ctk.CTkFrame(self.content_frame, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        preview_frame.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(preview_frame, text="Scan preview", font=ctk.CTkFont(size=18, weight="bold"), text_color="#F4F4F8").pack(anchor="w", padx=18, pady=(18, 8))
        self.preview_box = ctk.CTkTextbox(preview_frame, height=180, wrap="word")
        self.preview_box.pack(fill="x", padx=18, pady=(0, 18))

        self.log_box = ctk.CTkTextbox(self.content_frame, height=110, wrap="word")
        self.log_box.insert("0.0", "Ready for a safe cleanup scan.\n")
        self.log_box.configure(state="disabled")
        self.log_box.pack(fill="x", padx=18, pady=(0, 20))

        self.set_mode("safe")
        self.scan_selected_mode()

    def set_mode(self, mode: str):
        self.mode = mode
        active_color = ACCENT_COLOR
        inactive_color = CARD_COLOR
        self.safe_btn.configure(fg_color=active_color if mode == "safe" else inactive_color)
        self.deep_btn.configure(fg_color=active_color if mode == "deep" else inactive_color)
        self.cards[3].label_value.configure(text=("SAFE" if mode == "safe" else "DEEP"))
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"Mode switched to {mode.upper()} cleanup.\n")
        self.log_box.configure(state="disabled")

    def _set_category_filters(self, categories):
        for child in self.category_container.winfo_children():
            child.destroy()
        self.category_checkboxes = {}
        for category in categories:
            checkbox = ctk.CTkCheckBox(self.category_container, text=category, onvalue=True, offvalue=False, checkbox_height=16, checkbox_width=16)
            if category != "Recycle Bin":
                checkbox.select()
            checkbox.pack(anchor="w", padx=18, pady=4)
            self.category_checkboxes[category] = checkbox

    def _selected_categories(self):
        return [category for category, checkbox in self.category_checkboxes.items() if checkbox.get()]

    def scan_selected_mode(self):
        self.cards[3].label_value.configure(text="SCANNING")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"Scanning {self.mode.upper()} cleanup candidates...\n")
        self.log_box.configure(state="disabled")

        def worker():
            summary = scan_cache_locations(mode=self.mode)
            self.after(0, lambda: self._populate_scan_results(summary))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_scan_results(self, summary):
        self.results = summary.get("entries", [])
        self.cards[0].label_value.configure(text=str(summary.get("file_count", 0)))
        self.cards[1].label_value.configure(text=f"{summary.get('total_size_mb', 0):.2f} MB")
        self.cards[2].label_value.configure(text=str(len(summary.get("categories", {}))))
        self.cards[3].label_value.configure(text="READY")

        categories = list(summary.get("categories", {}).keys())
        self._set_category_filters(categories)

        text = []
        if not self.results:
            text.append("No verified cache files found in the selected scan mode.")
        else:
            for item in self.results[:25]:
                folder = item.get("category")
                size_mb = int(item.get("size_bytes", 0)) / (1024 * 1024)
                item_count = int(item.get("item_count", 1))
                count_text = f" ({item_count} items)" if item.get("action") == "empty_recycle_bin" else ""
                text.append(f"[{folder}] {item.get('name')}{count_text} - {size_mb:.2f} MB")
        self.preview_box.configure(state="normal")
        self.preview_box.delete("0.0", "end")
        self.preview_box.insert("0.0", "\n".join(text))
        self.preview_box.configure(state="disabled")

        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"Scan complete: {summary.get('file_count', 0)} item(s), {summary.get('total_size_mb', 0):.2f} MB.\n")
        for error in summary.get("scan_errors", []):
            self.log_box.insert("end", f"Scan warning: {error}\n")
        self.log_box.configure(state="disabled")

    def confirm_cleanup(self):
        selected_categories = self._selected_categories()
        if not selected_categories:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", "Select at least one cleanup category first.\n")
            self.log_box.configure(state="disabled")
            return

        entries = [item for item in self.results if item.get("category") in selected_categories]
        if not entries:
            self.log_box.configure(state="normal")
            self.log_box.insert("end", "Nothing to delete in the selected categories.\n")
            self.log_box.configure(state="disabled")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm cleanup")
        dialog.geometry("480x180")
        dialog.transient(self)
        dialog.grab_set()


        item_count = sum(int(item.get("item_count", 1)) for item in entries)
        empties_recycle_bin = any(item.get("action") == "empty_recycle_bin" for item in entries)
        warning = " This permanently empties the Recycle Bin on all drives." if empties_recycle_bin else ""
        ctk.CTkLabel(dialog, text="Clean the selected locations?", font=ctk.CTkFont(size=18, weight="bold")).pack(padx=20, pady=(18, 8))
        ctk.CTkLabel(
            dialog,
            text=f"This will remove up to {item_count} item(s) from the selected temporary/cache locations.{warning} Windows may recreate some cache files.",
            wraplength=420,
        ).pack(padx=20, pady=(0, 10))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(padx=20, pady=(0, 18))

        def proceed():
            dialog.destroy()
            self.execute_cleanup(entries)

        def cancel():
            dialog.destroy()
            self.log_box.configure(state="normal")
            self.log_box.insert("end", "Cleanup cancelled by user.\n")
            self.log_box.configure(state="disabled")

        ctk.CTkButton(btn_row, text="Yes, delete", command=proceed, width=120, corner_radius=12).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_row, text="Cancel", command=cancel, width=120, corner_radius=12).pack(side="left")

    def execute_cleanup(self, entries):
        self.cards[3].label_value.configure(text="DELETING")
        self.log_box.configure(state="normal")
        item_count = sum(int(item.get("item_count", 1)) for item in entries)
        self.log_box.insert("end", f"Cleaning {item_count} item(s)...\n")
        self.log_box.configure(state="disabled")

        def worker():
            deleted, errors = delete_entries(entries)
            self.after(0, lambda: self._cleanup_complete(deleted, errors))

        threading.Thread(target=worker, daemon=True).start()

    def _cleanup_complete(self, deleted, errors):
        self.cards[3].label_value.configure(text="DONE")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"Cleanup complete: {deleted} item(s) removed.\n")
        if errors:
            self.log_box.insert("end", "Skipped locked or protected files:\n")
            for error in errors[:5]:
                self.log_box.insert("end", f"- {error}\n")
        self.log_box.configure(state="disabled")
        self.scan_selected_mode()
