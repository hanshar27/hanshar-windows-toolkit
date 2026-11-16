import ctypes
import os
import platform
import subprocess
import sys
from pathlib import Path

SYSTEM_MEMORY_LIST_INFORMATION = 80
MEMORY_PURGE_STANDBY_LIST = 4
ELEVATED_ACTION_ARGUMENT = "--clear-standby-cache"
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_ENABLED = 0x0002
ERROR_NOT_ALL_ASSIGNED = 1300


class _Luid(ctypes.Structure):
    _fields_ = [("LowPart", ctypes.c_ulong), ("HighPart", ctypes.c_long)]


class _LuidAndAttributes(ctypes.Structure):
    _fields_ = [("Luid", _Luid), ("Attributes", ctypes.c_ulong)]


class _TokenPrivileges(ctypes.Structure):
    _fields_ = [("PrivilegeCount", ctypes.c_ulong), ("Privileges", _LuidAndAttributes)]


def is_administrator() -> bool:
    if os.name != "nt":
        return False
    return bool(ctypes.windll.shell32.IsUserAnAdmin())


def _purge_standby_list() -> None:
    _enable_privilege("SeProfileSingleProcessPrivilege")
    ntdll = ctypes.WinDLL("ntdll")
    set_system_information = ntdll.NtSetSystemInformation
    set_system_information.argtypes = [
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_ulong,
    ]
    set_system_information.restype = ctypes.c_long

    command = ctypes.c_ulong(MEMORY_PURGE_STANDBY_LIST)
    status = set_system_information(
        SYSTEM_MEMORY_LIST_INFORMATION,
        ctypes.byref(command),
        ctypes.sizeof(command),
    )
    if status < 0:
        raise OSError(f"Windows rejected the standby-memory purge (NTSTATUS 0x{status & 0xFFFFFFFF:08X}).")


def _enable_privilege(privilege_name: str) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    token = ctypes.c_void_p()
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    advapi32.OpenProcessToken.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi32.LookupPrivilegeValueW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.POINTER(_Luid),
    ]
    advapi32.AdjustTokenPrivileges.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.POINTER(_TokenPrivileges),
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(token),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        luid = _Luid()
        if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
            raise ctypes.WinError(ctypes.get_last_error())

        privileges = _TokenPrivileges(
            1,
            _LuidAndAttributes(luid, SE_PRIVILEGE_ENABLED),
        )
        ctypes.set_last_error(0)
        if not advapi32.AdjustTokenPrivileges(
            token,
            False,
            ctypes.byref(privileges),
            0,
            None,
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == ERROR_NOT_ALL_ASSIGNED:
            raise PermissionError(f"The {privilege_name} privilege is not available.")
    finally:
        kernel32.CloseHandle(token)


def clear_standby_memory() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("Standby memory can only be cleared on Windows.")
    if not is_administrator():
        raise PermissionError("Administrator permission is required to clear standby memory.")
    _purge_standby_list()


def build_elevation_parameters(
    executable: str | Path,
    frozen: bool | None = None,
) -> str:
    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))
    if frozen:
        command_arguments = [ELEVATED_ACTION_ARGUMENT]
    else:
        script_path = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path("main.py")
        command_arguments = [str(script_path), ELEVATED_ACTION_ARGUMENT]
    return subprocess.list2cmdline(command_arguments)


def request_elevated_standby_memory_clear() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("Standby memory can only be cleared on Windows.")

    executable = str(Path(sys.executable).resolve())
    parameters = build_elevation_parameters(executable)
    shell_execute = ctypes.windll.shell32.ShellExecuteW
    shell_execute.restype = ctypes.c_ssize_t
    shell_execute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]
    result = shell_execute(None, "runas", executable, parameters, None, 0)
    if result <= 32:
        raise RuntimeError(
            "Windows could not start the administrator task. The UAC request may have been cancelled."
        )
