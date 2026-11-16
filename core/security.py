import ctypes


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except AttributeError:
        return False


def require_admin_for_action(action_name: str) -> None:
    if not is_admin():
        raise PermissionError(f"{action_name} requires administrator privileges on Windows.")
