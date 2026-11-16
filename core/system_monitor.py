import time
from typing import Dict

import psutil

from core.system_info import (
    get_cpu_usage,
    get_disk_usage,
    get_gpu_temperature,
    get_memory_usage,
    get_uptime_human_readable,
)


def get_network_usage() -> Dict[str, float]:
    net = psutil.net_io_counters()
    return {
        "bytes_sent": float(net.bytes_sent),
        "bytes_recv": float(net.bytes_recv),
    }


def get_process_count() -> int:
    return len(psutil.pids())


def get_system_snapshot() -> Dict[str, object]:
    memory = get_memory_usage()
    disk = get_disk_usage("C:\\")
    cpu_usage = get_cpu_usage()
    gpu_temp = get_gpu_temperature()
    update = get_network_usage()
    return {
        "cpu_usage": round(cpu_usage, 1),
        "ram_usage": round(memory["used_percent"], 1),
        "disk_usage": round(disk["percent_used"], 1),
        "gpu_temperature": gpu_temp,
        "uptime": get_uptime_human_readable(),
        "process_count": get_process_count(),
        "network_sent": round(update["bytes_sent"] / (1024 * 1024), 2),
        "network_recv": round(update["bytes_recv"] / (1024 * 1024), 2),
    }
