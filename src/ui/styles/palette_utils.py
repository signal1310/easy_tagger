import sys
from typing import Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QGuiApplication


def is_system_dark() -> bool:
    hints = QGuiApplication.styleHints()
    if hasattr(hints, "colorScheme"):
        return hints.colorScheme() == Qt.ColorScheme.Dark
    return False


def resolve_effective_theme(theme_mode: str) -> str:
    """Returns 'dark' or 'light' given the mode ('dark', 'light', or 'system')."""
    if theme_mode == "system":
        return "dark" if is_system_dark() else "light"
    return theme_mode if theme_mode in ("dark", "light") else "dark"


def get_contrast_text_color(hex_color: str) -> str:
    """Returns high-contrast text color ('#0f172a' or '#ffffff') based on luminance."""
    c = QColor(hex_color)
    if not c.isValid():
        return "#0f172a"
    lum = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
    return "#0f172a" if lum > 0.55 else "#ffffff"


def adapt_color_for_theme(hex_color: str, theme: str) -> Tuple[str, str]:
    """
    Adapts a tag color for the active theme.
    In dark mode, bright pastels are toned down into deep muted tones.
    In light mode, pastels stay soft and bright with dark text.
    """
    c = QColor(hex_color)
    if not c.isValid():
        return ("#2a2a30", "#ededed") if theme == "dark" else ("#e4e4e7", "#18181b")

    if theme == "dark":
        h, s, l, _ = c.getHsl()
        if l > int(255 * 0.35):
            target_s = int(min(255, s * 0.85))
            target_l = int(255 * 0.26)
            dark_c = QColor.fromHsl(h, target_s, target_l)
            return (dark_c.name(), "#ededed")
        return (hex_color, "#ededed")

    return (hex_color, get_contrast_text_color(hex_color))


def apply_titlebar_theme(widget, effective_theme: str) -> None:
    """Synchronizes native Windows DWM titlebar colors with Dark / Light mode."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hwnd = int(widget.winId())
        use_dark = 1 if effective_theme == "dark" else 0
        value = ctypes.c_int(use_dark)

        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
        if hr != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 19, ctypes.byref(value), ctypes.sizeof(value)
            )

        if effective_theme == "dark":
            caption_color = ctypes.c_int(0x00161414)  # #141416
            caption_text = ctypes.c_int(0x00EDEDED)   # #ededed
        else:
            caption_color = ctypes.c_int(0x00FFFFFF)  # #ffffff
            caption_text = ctypes.c_int(0x001B1818)   # #18181b

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 36, ctypes.byref(caption_text), ctypes.sizeof(caption_text)
        )
    except Exception:
        pass

