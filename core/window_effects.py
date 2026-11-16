import ctypes
import os
from ctypes import wintypes
from tkinter import TclError

from core.ui_style import WINDOW_BACKGROUND

WCA_ACCENT_POLICY = 19
ACCENT_DISABLED = 0
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
ACRYLIC_TINT_RGB = (16, 16, 20)


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("accent_state", ctypes.c_int),
        ("accent_flags", ctypes.c_int),
        ("gradient_color", ctypes.c_uint),
        ("animation_id", ctypes.c_int),
    ]


class _WindowCompositionAttributeData(ctypes.Structure):
    _fields_ = [
        ("attribute", ctypes.c_int),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
    ]


def acrylic_tint_alpha(intensity: int) -> int | None:
    value = max(0, min(100, int(intensity)))
    if value == 0:
        return None
    return 224 - round(value * 176 / 100)


def apply_window_backdrop(window, intensity: int) -> bool:
    alpha = acrylic_tint_alpha(intensity)
    window.configure(fg_color=WINDOW_BACKGROUND)
    if os.name != "nt":
        return False

    try:
        window.wm_attributes("-transparentcolor", "")
    except TclError:
        return False

    if alpha is None:
        accent_state = ACCENT_DISABLED
        gradient_color = 0
    else:
        accent_state = ACCENT_ENABLE_ACRYLICBLURBEHIND
        red, green, blue = ACRYLIC_TINT_RGB
        gradient_color = (alpha << 24) | (red << 16) | (green << 8) | blue

    user32 = ctypes.windll.user32
    get_ancestor = user32.GetAncestor
    get_ancestor.argtypes = [wintypes.HWND, wintypes.UINT]
    get_ancestor.restype = wintypes.HWND
    hwnd = get_ancestor(window.winfo_id(), 2)
    set_attribute = getattr(user32, "SetWindowCompositionAttribute", None)
    if set_attribute is None:
        return False
    set_attribute.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(_WindowCompositionAttributeData),
    ]
    set_attribute.restype = wintypes.BOOL

    accent = _AccentPolicy(accent_state, 2, gradient_color, 0)
    data = _WindowCompositionAttributeData(
        WCA_ACCENT_POLICY,
        ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
        ctypes.sizeof(accent),
    )
    return bool(set_attribute(hwnd, ctypes.byref(data)))
