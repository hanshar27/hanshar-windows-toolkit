import os
import sys
import time
from collections import deque
from pathlib import Path
import tkinter as tk

import customtkinter as ctk
import psutil

from core.activity_log import append_log
from core.report_exporter import export_activity_csv, export_activity_json
from core.system_info import (
    get_cpu_usage,
    get_disk_usage,
    get_gpu_name,
    get_gpu_temperature,
    get_memory_usage,
    get_system_summary,
    get_uptime_human_readable,
)
from core.system_monitor import get_process_count
from core.system_report import generate_system_report


CARD_COLOR = "#22201e"
CARD_BORDER = "#363330"
TEXT_COLOR = "#e6e5e3"
MUTED_COLOR = "#a7a29c"
CPU_COLOR = "#f97316"
RAM_COLOR = "#0ea5e9"
GREEN_COLOR = "#22c55e"
YELLOW_COLOR = "#f59e0b"
PURPLE_COLOR = "#a855f7"


class CircularGauge(ctk.CTkCanvas):
    def __init__(self, master, color, **kwargs):
        super().__init__(
            master,
            height=158,
            bg=CARD_COLOR,
            highlightthickness=0,
            **kwargs,
        )
        self.color = color
        self.value = 0.0
        self.bind("<Configure>", self._draw)

    def set(self, value):
        self.value = max(0.0, min(100.0, float(value)))
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = max(self.winfo_width(), 100)
        height = max(self.winfo_height(), 100)
        diameter = min(width - 28, height - 20)
        left = (width - diameter) / 2
        top = (height - diameter) / 2
        box = (left, top, left + diameter, top + diameter)
        self.create_arc(
            *box,
            start=135,
            extent=270,
            style="arc",
            outline="#3b3834",
            width=11,
        )
        self.create_arc(
            *box,
            start=135,
            extent=270 * self.value / 100,
            style="arc",
            outline=self.color,
            width=11,
        )
        center_x = width / 2
        center_y = height / 2
        self.create_text(
            center_x,
            center_y - 4,
            text=f"{self.value:.1f}%",
            fill=TEXT_COLOR,
            font=("Segoe UI", 25, "bold"),
        )
        self.create_text(
            center_x,
            center_y + 22,
            text="USAGE",
            fill=MUTED_COLOR,
            font=("Segoe UI", 10, "bold"),
        )


class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title, icon, color, value="—", detail=""):
        super().__init__(
            master,
            corner_radius=16,
            fg_color=CARD_COLOR,
            border_width=1,
            border_color=CARD_BORDER,
        )
        self.grid_columnconfigure(1, weight=1)
        badge = ctk.CTkFrame(
            self,
            width=34,
            height=34,
            corner_radius=17,
            fg_color=color,
        )
        badge.grid(row=0, column=0, padx=(12, 8), pady=(12, 8), sticky="nw")
        badge.grid_propagate(False)
        ctk.CTkLabel(
            badge,
            text=icon,
            text_color="#ffffff",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=120,
        )
        self.title_label.grid(row=0, column=1, padx=(0, 8), pady=(13, 0), sticky="ew")
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=21, weight="bold"),
            anchor="w",
            justify="left",
            wraplength=140,
        )
        self.value_label.grid(row=1, column=0, columnspan=2, padx=12, sticky="ew")
        self.detail_label = ctk.CTkLabel(
            self,
            text=detail,
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11),
            anchor="w",
            wraplength=140,
        )
        self.detail_label.grid(
            row=2, column=0, columnspan=2, padx=12, pady=(0, 10), sticky="ew"
        )
        self.bind("<Configure>", self._update_text_wrap)
        self._last_wrap_width = 0

    def _update_text_wrap(self, _event=None):
        width = self.winfo_width()
        if width <= 1 or width == self._last_wrap_width:
            return
        self._last_wrap_width = width
        self.title_label.configure(wraplength=max(70, width - 68))
        value_wrap = max(80, width - 24)
        self.value_label.configure(wraplength=value_wrap)
        self.detail_label.configure(wraplength=value_wrap)

    def set_value(self, value, detail=""):
        self.value_label.configure(text=value)
        self.detail_label.configure(text=detail)


class SystemActivityBar(tk.Canvas):
    def __init__(self, master):
        super().__init__(
            master,
            height=12,
            bg=CARD_COLOR,
            highlightthickness=0,
        )
        self.value = 0.0
        self.bind("<Configure>", self._draw)

    def set(self, value):
        self.value = max(0.0, min(100.0, float(value)))
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return
        radius = height / 2
        self.create_rounded_rectangle(0, 0, width, height, radius, fill="#393632")
        fill_width = max(height, width * self.value / 100)
        if self.value <= 0:
            return
        colors = ("#fb923c", "#f97316", "#ea580c", "#c2410c")
        segment_width = fill_width / len(colors)
        for index, color in enumerate(colors):
            left = index * segment_width
            right = min(fill_width, (index + 1) * segment_width + 1)
            self.create_rectangle(left, 1, right, height - 1, fill=color, outline="")

    def create_rounded_rectangle(self, left, top, right, bottom, radius, **kwargs):
        points = (
            left + radius, top,
            right - radius, top,
            right, top,
            right, top + radius,
            right, bottom - radius,
            right, bottom,
            right - radius, bottom,
            left + radius, bottom,
            left, bottom,
            left, bottom - radius,
            left, top + radius,
            left, top,
        )
        self.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


class PerformanceChart(tk.Canvas):
    def __init__(self, master):
        super().__init__(
            master,
            height=170,
            bg=CARD_COLOR,
            highlightthickness=0,
        )
        self.cpu_values = deque([0.0] * 24, maxlen=24)
        self.ram_values = deque([0.0] * 24, maxlen=24)
        self.bind("<Configure>", self._draw)

    def add_sample(self, cpu, ram):
        self.cpu_values.append(max(0.0, min(100.0, float(cpu))))
        self.ram_values.append(max(0.0, min(100.0, float(ram))))
        self._draw()

    def _draw(self, _event=None):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        if width <= 1 or height <= 1:
            return
        left, right, top, bottom = 10, width - 10, 12, height - 12
        for step in range(1, 4):
            y = top + (bottom - top) * step / 4
            self.create_line(left, y, right, y, fill="#393632", dash=(2, 4))

        for values, color in (
            (self.cpu_values, CPU_COLOR),
            (self.ram_values, RAM_COLOR),
        ):
            points = []
            for index, value in enumerate(values):
                x = left + (right - left) * index / (len(values) - 1)
                y = bottom - (bottom - top) * value / 100
                points.extend((x, y))
            if len(points) >= 4:
                self.create_line(
                    *points,
                    fill=color,
                    width=2,
                    smooth=True,
                    splinesteps=12,
                )


class DashboardPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.summary_info = get_system_summary()
        self.gpu_name = get_gpu_name() or "Not detected"
        app_location = sys.executable if getattr(sys, "frozen", False) else __file__
        self.disk_path = (
            Path(app_location).resolve().anchor or os.environ.get("SystemDrive", "C:\\")
        )
        self.disk_label = self.disk_path.rstrip("\\/")
        self._previous_network = psutil.net_io_counters()
        self._previous_network_time = time.monotonic()
        self._last_refresh_error = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_COLOR,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Your device at a glance",
            font=ctk.CTkFont(size=14),
            text_color=MUTED_COLOR,
        ).pack(anchor="w", pady=(2, 0))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.body.grid_columnconfigure(0, weight=5, uniform="bento")
        self.body.grid_columnconfigure(1, weight=7, uniform="bento")
        self.body.grid_columnconfigure(2, weight=9, uniform="bento")
        self.body.grid_rowconfigure(0, weight=1)

        self._build_system_column()
        self._build_metrics_column()
        self._build_performance_column()
        self.after(500, self.refresh_dashboard)

    def _make_card(self, master, fg_color=CARD_COLOR, **kwargs):
        return ctk.CTkFrame(
            master,
            fg_color=fg_color,
            corner_radius=16,
            border_width=1,
            border_color=CARD_BORDER,
            **kwargs,
        )

    def _build_system_column(self):
        column = ctk.CTkFrame(self.body, fg_color="transparent")
        column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        column.grid_columnconfigure(0, weight=1)
        column.grid_rowconfigure(0, weight=7)
        column.grid_rowconfigure(1, weight=4)

        self.system_card = self._make_card(column, fg_color=CARD_COLOR)
        self.system_card.grid(row=0, column=0, sticky="nsew", pady=(0, 7))

        identity = ctk.CTkFrame(self.system_card, fg_color="transparent")
        identity.pack(fill="x", padx=14, pady=(15, 13))
        icon = ctk.CTkFrame(
            identity, width=48, height=48, corner_radius=15, fg_color="#3c2a1e"
        )
        icon.pack(side="left", padx=(0, 11))
        icon.pack_propagate(False)
        ctk.CTkLabel(
            icon,
            text="▣",
            text_color=CPU_COLOR,
            font=ctk.CTkFont(size=29, weight="bold"),
        ).place(relx=0.5, rely=0.5, anchor="center")
        heading = ctk.CTkFrame(identity, fg_color="transparent")
        heading.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            heading,
            text="System overview",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            heading,
            text="WINDOWS DEVICE",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        self.os_value = self._add_system_detail(self.system_card, "OPERATING SYSTEM")
        self.processor_value = self._add_system_detail(self.system_card, "PROCESSOR")
        self.uptime_value = self._add_system_detail(self.system_card, "UPTIME")

        load_row = ctk.CTkFrame(self.system_card, fg_color="transparent")
        load_row.pack(fill="x", padx=14, pady=(9, 4))
        ctk.CTkLabel(
            load_row,
            text="SYSTEM LOAD",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")
        self.load_value = ctk.CTkLabel(
            load_row,
            text="0%",
            text_color=CPU_COLOR,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.load_value.pack(side="right")
        self.load_bar = SystemActivityBar(self.system_card)
        self.load_bar.pack(fill="x", padx=14, pady=(0, 14))

        self.quick_card = self._make_card(column, fg_color=CARD_COLOR)
        self.quick_card.grid(row=1, column=0, sticky="nsew", pady=(7, 0))
        ctk.CTkLabel(
            self.quick_card,
            text="Quick actions",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(13, 9))
        self.action_bar = ctk.CTkFrame(self.quick_card, fg_color="transparent")
        self.action_bar.pack(fill="both", expand=True, padx=10, pady=(0, 11))
        for index in range(3):
            self.action_bar.grid_columnconfigure(index, weight=1, uniform="actions")
        actions = (
            ("⇩ CSV", self._export_csv, CPU_COLOR),
            ("⇩ JSON", self._export_json, RAM_COLOR),
            ("Report", self._generate_report, PURPLE_COLOR),
        )
        for index, (label, command, color) in enumerate(actions):
            ctk.CTkButton(
                self.action_bar,
                text=label,
                command=command,
                height=44,
                corner_radius=12,
                fg_color="#302e2a",
                hover_color="#403c36",
                text_color=color,
                font=ctk.CTkFont(size=10, weight="bold"),
            ).grid(row=0, column=index, sticky="ew", padx=2)
        self.status_label = ctk.CTkLabel(
            self.quick_card,
            text="Ready",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11),
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 10))

    def _add_system_detail(self, master, title):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(
            row,
            text=title,
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        value = ctk.CTkLabel(
            row,
            text="Loading...",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=12),
            anchor="w",
            justify="left",
            wraplength=155,
        )
        value.pack(fill="x", anchor="w", pady=(2, 0))
        return value

    def _build_metrics_column(self):
        column = ctk.CTkFrame(self.body, fg_color="transparent")
        column.grid(row=0, column=1, sticky="nsew", padx=7)
        for index in (0, 1):
            column.grid_columnconfigure(index, weight=1, uniform="metric-columns")
        for index in range(4):
            column.grid_rowconfigure(index, weight=1, uniform="metric-rows")

        definitions = (
            ("GPU TEMPERATURE", "°", RAM_COLOR, "—", "GPU sensor"),
            ("DOWNLOAD", "↓", RAM_COLOR, "0 KB/s", "Network"),
            ("DISK FREE", "▤", GREEN_COLOR, "—", "Drive C:"),
            ("GRAPHICS", "◈", PURPLE_COLOR, "—", "GPU"),
            ("PROCESSES", "◉", PURPLE_COLOR, "—", "Running"),
            ("UPLOAD", "↑", YELLOW_COLOR, "0 KB/s", "Network"),
            ("WINDOWS", "⊞", RAM_COLOR, "—", "Version"),
            ("DEVICE", "⌂", GREEN_COLOR, "—", "Hostname"),
        )
        self.metric_cards = {}
        for index, (title, icon, color, value, detail) in enumerate(definitions):
            card = MetricCard(column, title, icon, color, value, detail)
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=4,
                pady=4,
            )
            self.metric_cards[title] = card

    def _build_performance_column(self):
        column = ctk.CTkFrame(self.body, fg_color="transparent")
        column.grid(row=0, column=2, sticky="nsew", padx=(7, 0))
        column.grid_columnconfigure(0, weight=1)
        column.grid_rowconfigure(0, weight=5)
        column.grid_rowconfigure(1, weight=4)

        gauges = ctk.CTkFrame(column, fg_color="transparent")
        gauges.grid(row=0, column=0, sticky="nsew", pady=(0, 7))
        for index in (0, 1):
            gauges.grid_columnconfigure(index, weight=1, uniform="gauge-columns")
        gauges.grid_rowconfigure(0, weight=1)
        self.cpu_gauge_card, self.cpu_gauge = self._make_gauge_card(
            gauges, "Processor", "LIVE", CPU_COLOR, 0
        )
        self.ram_gauge_card, self.ram_gauge = self._make_gauge_card(
            gauges, "Memory", "LIVE", RAM_COLOR, 1
        )

        chart_card = self._make_card(column)
        chart_card.grid(row=1, column=0, sticky="nsew", pady=(7, 0))
        chart_header = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_header.pack(fill="x", padx=14, pady=(12, 1))
        ctk.CTkLabel(
            chart_header,
            text="Performance activity",
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            chart_header,
            text="LIVE",
            text_color=GREEN_COLOR,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="right")
        legend = ctk.CTkFrame(chart_card, fg_color="transparent")
        legend.pack(fill="x", padx=14, pady=(5, 0))
        self._add_legend(legend, "CPU", CPU_COLOR)
        self._add_legend(legend, "RAM", RAM_COLOR)
        self.performance_chart = PerformanceChart(chart_card)
        self.performance_chart.pack(fill="both", expand=True, padx=8, pady=(2, 8))

    def _make_gauge_card(self, master, title, state, color, column):
        card = self._make_card(master)
        card.grid(row=0, column=column, sticky="nsew", padx=4)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(13, 0))
        ctk.CTkLabel(
            header,
            text=title,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="• " + state,
            text_color=color,
            font=ctk.CTkFont(size=10, weight="bold"),
        ).pack(side="right")
        gauge = CircularGauge(card, color)
        gauge.pack(fill="both", expand=True, padx=4, pady=(0, 0))
        ctk.CTkLabel(
            card,
            text="Updated every 1.5 sec",
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=10),
        ).pack(pady=(0, 11))
        return card, gauge

    @staticmethod
    def _add_legend(master, text, color):
        item = ctk.CTkFrame(master, fg_color="transparent")
        item.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(
            item,
            text="●",
            text_color=color,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(0, 4))
        ctk.CTkLabel(
            item,
            text=text,
            text_color=MUTED_COLOR,
            font=ctk.CTkFont(size=11),
        ).pack(side="left")

    def _export_csv(self):
        self._run_action("CSV export", export_activity_csv, "export_csv")

    def _export_json(self):
        self._run_action("JSON export", export_activity_json, "export_json")

    def _generate_report(self):
        try:
            generate_system_report()
            report_path = Path(__file__).resolve().parents[1] / "reports" / "system_report.json"
            self.status_label.configure(text=f"Report saved: {report_path.name}")
            append_log("system_report_generated", str(report_path))
            if hasattr(os, "startfile"):
                os.startfile(str(report_path))
        except Exception as exc:
            self._show_action_error("Report", exc)

    def _run_action(self, name, action, log_event):
        try:
            path = action()
            self.status_label.configure(text=f"{name} saved: {Path(path).name}")
            append_log(log_event, str(path))
        except Exception as exc:
            self._show_action_error(name, exc)

    def _show_action_error(self, name, error):
        self.status_label.configure(text=f"{name} failed: {error}")
        append_log("dashboard_action_failed", f"{name}: {error}")

    def refresh_dashboard(self):
        try:
            cpu_usage = get_cpu_usage()
            ram = get_memory_usage()
            disk = get_disk_usage(self.disk_path)
            gpu_temp = get_gpu_temperature()
            uptime = get_uptime_human_readable()
            network = psutil.net_io_counters()
            now = time.monotonic()
            elapsed = max(now - self._previous_network_time, 0.001)
            download_rate = max(
                0.0, (network.bytes_recv - self._previous_network.bytes_recv) / elapsed
            )
            upload_rate = max(
                0.0, (network.bytes_sent - self._previous_network.bytes_sent) / elapsed
            )
            self._previous_network = network
            self._previous_network_time = now

            self.cpu_gauge.set(cpu_usage)
            self.ram_gauge.set(ram["used_percent"])
            self.performance_chart.add_sample(cpu_usage, ram["used_percent"])
            self.load_value.configure(text=f"{cpu_usage:.1f}%")
            self.load_bar.set(cpu_usage)

            self.os_value.configure(
                text=f"{self.summary_info['os_name']} {self.summary_info['os_release']}"
            )
            self.processor_value.configure(text=self.summary_info["processor"] or "Unknown")
            self.uptime_value.configure(text=uptime)

            self.metric_cards["GPU TEMPERATURE"].set_value(
                f"{gpu_temp:.1f}°C" if gpu_temp is not None else "Unavailable",
                "GPU temperature"
                if gpu_temp is not None
                else "NVIDIA driver or LHM required",
            )
            self.metric_cards["DOWNLOAD"].set_value(
                self._format_rate(download_rate), "Network"
            )
            self.metric_cards["DISK FREE"].set_value(
                f"{disk['free_gb']:.1f} GB",
                f"{self.disk_label} · {disk['percent_used']:.0f}% used",
            )
            self.metric_cards["GRAPHICS"].set_value(
                self.gpu_name, "GPU"
            )
            self.metric_cards["PROCESSES"].set_value(
                f"{get_process_count():,}", "Running"
            )
            self.metric_cards["UPLOAD"].set_value(
                self._format_rate(upload_rate), "Network"
            )
            self.metric_cards["WINDOWS"].set_value(
                f"{self.summary_info['os_name']} {self.summary_info['os_release']}",
                "Version",
            )
            self.metric_cards["DEVICE"].set_value(
                self._shorten(self.summary_info["hostname"], 18), "Hostname"
            )
        except Exception as exc:
            error = str(exc)
            self.status_label.configure(text=f"Dashboard update failed: {error}")
            if error != self._last_refresh_error:
                append_log("dashboard_refresh_failed", error)
            self._last_refresh_error = error
        else:
            self._last_refresh_error = None

        self.after(1500, self.refresh_dashboard)

    @staticmethod
    def _format_rate(bytes_per_second):
        if bytes_per_second >= 1024 * 1024:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
        return f"{bytes_per_second / 1024:.0f} KB/s"

    @staticmethod
    def _shorten(value, max_length):
        value = str(value or "Unavailable")
        if len(value) <= max_length:
            return value
        return value[: max_length - 1] + "…"
