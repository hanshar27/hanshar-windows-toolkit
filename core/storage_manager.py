import glob
import ctypes
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

PROTECTED_PATHS = (
    r"C:\Windows\System32",
    r"C:\Windows\WinSxS",
    r"C:\pagefile.sys",
    r"C:\hiberfil.sys",
    r"C:\Users\*\Downloads",
    r"C:\Users\*\Desktop",
    r"C:\Users\*\Documents",
    r"C:\Users\*\Pictures",
    r"C:\Users\*\Videos",
)

SAFE_CACHE_CATEGORIES = {
    "%TEMP% User Temp": [
        "{TEMP}",
    ],
    "Windows Temp": [
        "{WINDIR}\\Temp",
    ],
    "Prefetch": [
        "{WINDIR}\\Prefetch",
    ],
    "Thumbnail Cache": [
        "{LOCALAPPDATA}\\Microsoft\\Windows\\Explorer",
    ],
    "DirectX Shader Cache": [
        "{LOCALAPPDATA}\\D3DSCache",
        "{LOCALAPPDATA}\\AMD\\DxCache",
    ],
    "Windows Error Reporting": [
        "{LOCALAPPDATA}\\Microsoft\\Windows\\WER",
    ],
    "Google Chrome Cache": [
        "{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\Cache",
        "{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\GPUCache",
        "{LOCALAPPDATA}\\Google\\Chrome\\User Data\\Default\\Code Cache",
    ],
    "Microsoft Edge Cache": [
        "{LOCALAPPDATA}\\Microsoft\\Edge\\User Data\\Default\\Cache",
        "{LOCALAPPDATA}\\Microsoft\\Edge\\User Data\\Default\\GPUCache",
        "{LOCALAPPDATA}\\Microsoft\\Edge\\User Data\\Default\\Code Cache",
    ],
    "Mozilla Firefox Cache": [
        "{LOCALAPPDATA}\\Mozilla\\Firefox\\Profiles\\*\\cache2",
        "{LOCALAPPDATA}\\Mozilla\\Firefox\\Profiles\\*\\startupCache",
    ],
}

DEEP_CACHE_CATEGORIES = {
    "Windows Temporary Data": [
        "{LOCALAPPDATA}\\Microsoft\\Windows\\INetCache",
        "{LOCALAPPDATA}\\Microsoft\\Windows\\Temporary Internet Files",
    ],
    "App Cache": [
        "{LOCALAPPDATA}\\Microsoft\\Windows\\Explorer\\ThumbCache",
        "{LOCALAPPDATA}\\Microsoft\\Windows\\Explorer\\IconCache",
    ],
    "Runtime Cache": [
        "{LOCALAPPDATA}\\Microsoft\\CLR_v4.0_32",
    ],
}


def _expand_path(raw_path: str, base_dir: Optional[str] = None) -> List[str]:
    if not raw_path:
        return []
    expanded = raw_path
    env = {
        "LOCALAPPDATA": base_dir if base_dir is not None else (os.environ.get("LOCALAPPDATA") or r"C:\Users\Default\AppData\Local"),
        "WINDIR": os.environ.get("WINDIR") or r"C:\Windows",
        "USERPROFILE": os.environ.get("USERPROFILE") or r"C:\Users\Default",
        "TEMP": os.path.join(base_dir, "Temp") if base_dir is not None else (os.environ.get("TEMP") or os.path.join(os.environ.get("LOCALAPPDATA") or r"C:\Users\Default\AppData\Local", "Temp")),
    }
    for key, value in env.items():
        expanded = expanded.replace(f"{{{key}}}", value)

    if "*" in expanded:
        matches = sorted(glob.glob(expanded))
        return matches if matches else [expanded]
    return [expanded]


def _is_protected(path: str) -> bool:
    normalized = os.path.normcase(os.path.normpath(path))
    extraction_path = getattr(sys, "_MEIPASS", None)
    if extraction_path:
        extraction_root = os.path.normcase(os.path.normpath(extraction_path))
        try:
            if os.path.commonpath((normalized, extraction_root)) == extraction_root:
                return True
        except ValueError:
            pass

    temp_roots = {
        os.path.normcase(os.path.normpath(root))
        for root in (
            os.environ.get("TEMP"),
            os.environ.get("TMP"),
            tempfile.gettempdir(),
        )
        if root
    }
    for temp_root in temp_roots:
        try:
            if os.path.commonpath((normalized, temp_root)) != temp_root:
                continue
        except ValueError:
            continue
        relative_path = os.path.relpath(normalized, temp_root)
        extraction_folder = relative_path.split(os.sep, 1)[0]
        if extraction_folder.upper().startswith("_MEI"):
            return True

    windows_dir = os.path.normcase(os.path.normpath(os.environ.get("WINDIR") or r"C:\Windows"))
    allowed_windows_cache_dirs = {
        os.path.normcase(os.path.normpath(os.path.join(windows_dir, "Temp"))),
        os.path.normcase(os.path.normpath(os.path.join(windows_dir, "Prefetch"))),
    }
    try:
        inside_windows = os.path.commonpath((normalized, windows_dir)) == windows_dir
    except ValueError:
        inside_windows = False
    if inside_windows:
        return not any(
            normalized == allowed or normalized.startswith(allowed + os.sep)
            for allowed in allowed_windows_cache_dirs
        )

    for protected in PROTECTED_PATHS:
        if protected.startswith("C:\\Users\\*"):
            if "\\Downloads" in normalized or "\\Desktop" in normalized or "\\Documents" in normalized or "\\Pictures" in normalized or "\\Videos" in normalized:
                return True
        elif protected.endswith("pagefile.sys") and normalized.endswith("pagefile.sys"):
            return True
        elif protected.endswith("hiberfil.sys") and normalized.endswith("hiberfil.sys"):
            return True
    return False


def build_scan_targets(mode: str = "safe", base_dir: Optional[str] = None) -> List[str]:
    selected = SAFE_CACHE_CATEGORIES if mode == "safe" else {**SAFE_CACHE_CATEGORIES, **DEEP_CACHE_CATEGORIES}
    targets: List[str] = []
    for group in selected.values():
        for raw in group:
            targets.extend(_expand_path(raw, base_dir=base_dir))
    unique = []
    seen = set()
    for item in targets:
        norm = os.path.normcase(os.path.normpath(item))
        if norm not in seen:
            unique.append(item)
            seen.add(norm)
    return unique


def _scan_directory(directory: str, category: str) -> List[Dict[str, object]]:
    if not directory or not os.path.isdir(directory):
        return []
    results: List[Dict[str, object]] = []
    for root, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not _is_protected(os.path.join(root, d))]
        for name in filenames:
            full_path = os.path.join(root, name)
            if _is_protected(full_path):
                continue
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue
            results.append({
                "category": category,
                "path": full_path,
                "size_bytes": size,
                "name": name,
            })
    return results


def _query_recycle_bin() -> Dict[str, int]:
    if os.name != "nt":
        raise OSError("Recycle Bin scanning is only supported on Windows.")

    class SHQueryRecycleBinInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("i64Size", ctypes.c_longlong),
            ("i64NumItems", ctypes.c_longlong),
        ]

    info = SHQueryRecycleBinInfo()
    info.cbSize = ctypes.sizeof(info)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    result = shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
    if result != 0:
        raise OSError(f"Could not scan Recycle Bin (HRESULT 0x{result & 0xFFFFFFFF:08X}).")
    return {"size_bytes": int(info.i64Size), "item_count": int(info.i64NumItems)}


def _empty_recycle_bin() -> None:
    if os.name != "nt":
        raise OSError("Recycle Bin cleanup is only supported on Windows.")

    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    shell32.SHEmptyRecycleBinW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_ulong]
    shell32.SHEmptyRecycleBinW.restype = ctypes.c_long
    result = shell32.SHEmptyRecycleBinW(None, None, 0x1 | 0x2 | 0x4)
    if result != 0:
        raise OSError(f"Could not empty Recycle Bin (HRESULT 0x{result & 0xFFFFFFFF:08X}).")


def scan_cache_locations(mode: str = "safe", base_dir: Optional[str] = None) -> Dict[str, object]:
    categories = SAFE_CACHE_CATEGORIES if mode == "safe" else {**SAFE_CACHE_CATEGORIES, **DEEP_CACHE_CATEGORIES}
    grouped: Dict[str, List[Dict[str, object]]] = {}
    scan_errors: List[str] = []
    for category, paths in categories.items():
        files: List[Dict[str, object]] = []
        for raw in paths:
            for candidate in _expand_path(raw, base_dir=base_dir):
                files.extend(_scan_directory(candidate, category))
        grouped[category] = files

    recycle_bin_category = "Recycle Bin"
    try:
        recycle_bin = _query_recycle_bin()
        if recycle_bin["item_count"]:
            grouped[recycle_bin_category] = [{
                "category": recycle_bin_category,
                "name": "Empty Recycle Bin",
                "size_bytes": recycle_bin["size_bytes"],
                "item_count": recycle_bin["item_count"],
                "action": "empty_recycle_bin",
            }]
        else:
            grouped[recycle_bin_category] = []
    except OSError as exc:
        grouped[recycle_bin_category] = []
        scan_errors.append(str(exc))

    flat = []
    seen_paths: set[str] = set()
    for entries in grouped.values():
        for entry in entries:
            path = str(entry.get("path", entry.get("action")))
            if path not in seen_paths:
                flat.append(entry)
                seen_paths.add(path)

    total_bytes = sum(int(item["size_bytes"]) for item in flat)
    file_count = sum(int(item.get("item_count", 1)) for item in flat)
    return {
        "mode": mode,
        "entries": flat,
        "categories": {
            category: sum(int(item.get("item_count", 1)) for item in entries)
            for category, entries in grouped.items()
        },
        "file_count": file_count,
        "total_size_bytes": total_bytes,
        "total_size_mb": round(total_bytes / (1024 * 1024), 2),
        "scan_errors": scan_errors,
    }


def delete_entries(entries: Iterable[Dict[str, object]]) -> Tuple[int, List[str]]:
    deleted = 0
    errors: List[str] = []
    for entry in entries:
        if entry.get("action") == "empty_recycle_bin":
            try:
                _empty_recycle_bin()
                deleted += int(entry.get("item_count", 0))
            except OSError as exc:
                errors.append(f"Recycle Bin: {exc}")
            continue

        path = str(entry["path"])
        try:
            if _is_protected(path):
                errors.append(f"{path}: protected temporary runtime file")
                continue
            file_obj = Path(path)
            if file_obj.exists() and file_obj.is_file():
                file_obj.unlink()
                deleted += 1
        except OSError as exc:
            errors.append(f"{path}: {exc}")
    return deleted, errors
