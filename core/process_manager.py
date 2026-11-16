import psutil


def list_running_processes(limit: int = 10):
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            processes.append({
                "pid": info.get("pid"),
                "name": info.get("name") or "Unknown",
                "cpu_percent": round(info.get("cpu_percent") or 0.0, 2),
                "memory_percent": round(info.get("memory_percent") or 0.0, 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda item: item["cpu_percent"], reverse=True)
    return processes[:limit]
