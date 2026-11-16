import ipaddress
import socket
import subprocess
import urllib.request
from typing import Dict, List


def ping_host(hostname: str = "8.8.8.8", timeout: int = 4) -> Dict[str, object]:
    try:
        result = subprocess.run(["ping", "-n", "4", hostname], capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        return {
            "success": result.returncode == 0,
            "hostname": hostname,
            "output": output,
            "returncode": result.returncode,
        }
    except Exception as exc:
        return {"success": False, "hostname": hostname, "output": str(exc), "returncode": 1}


def dns_lookup(hostname: str = "google.com") -> Dict[str, object]:
    try:
        addresses = socket.gethostbyname_ex(hostname)
        return {"success": True, "hostname": hostname, "addresses": addresses[2]}
    except Exception as exc:
        return {"success": False, "hostname": hostname, "error": str(exc)}


def get_ip_config() -> str:
    try:
        result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=False)
        return result.stdout
    except Exception as exc:
        return str(exc)


def get_network_adapters() -> List[str]:
    try:
        result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, check=False)
        lines = result.stdout.splitlines()
        adapters = []
        for line in lines:
            if line.strip().startswith("Wireless LAN adapter") or line.strip().startswith("Ethernet adapter"):
                adapters.append(line.strip())
        return adapters or ["No adapters detected"]
    except Exception:
        return ["No adapters detected"]


def flush_dns() -> Dict[str, object]:
    try:
        result = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, text=True, check=False)
        return {"success": result.returncode == 0, "output": (result.stdout + result.stderr).strip()}
    except Exception as exc:
        return {"success": False, "output": str(exc)}


def renew_ip() -> Dict[str, object]:
    try:
        result = subprocess.run(["ipconfig", "/renew"], capture_output=True, text=True, check=False)
        return {"success": result.returncode == 0, "output": (result.stdout + result.stderr).strip()}
    except Exception as exc:
        return {"success": False, "output": str(exc)}


def release_ip() -> Dict[str, object]:
    try:
        result = subprocess.run(["ipconfig", "/release"], capture_output=True, text=True, check=False)
        return {"success": result.returncode == 0, "output": (result.stdout + result.stderr).strip()}
    except Exception as exc:
        return {"success": False, "output": str(exc)}


def internet_connected() -> bool:
    try:
        with urllib.request.urlopen("https://www.google.com", timeout=5):
            return True
    except Exception:
        return False


def get_local_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "127.0.0.1"


def validate_host(hostname: str) -> bool:
    if not hostname or not hostname.strip():
        return False
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
