import sys
from typing import Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QPalette, QColor
from PyQt6.QtWidgets import QApplication


class ThemeManager:
    """
    Manages application theming for Dark, Light, and System adaptive modes.
    Pure neutral dark (comfortable lightness, zero hue/tint) and high-contrast light mode,
    ensuring perfect legibility across all widgets, tooltips, and Windows titlebars.
    """

    THEMES = {
        "dark": "🌙 다크 모드",
        "light": "☀️ 라이트 모드",
        "system": "💻 시스템 적응",
    }

    @staticmethod
    def is_system_dark() -> bool:
        hints = QGuiApplication.styleHints()
        if hasattr(hints, 'colorScheme'):
            return hints.colorScheme() == Qt.ColorScheme.Dark
        return False

    @classmethod
    def resolve_effective_theme(cls, theme_mode: str) -> str:
        """Returns 'dark' or 'light' given the mode ('dark', 'light', or 'system')."""
        if theme_mode == "system":
            return "dark" if cls.is_system_dark() else "light"
        return theme_mode if theme_mode in ("dark", "light") else "dark"

    @staticmethod
    def get_contrast_text_color(hex_color: str) -> str:
        """Returns high-contrast text color ('#0f172a' or '#ffffff') based on luminance."""
        c = QColor(hex_color)
        if not c.isValid():
            return "#0f172a"
        lum = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255
        return "#0f172a" if lum > 0.55 else "#ffffff"

    @classmethod
    def adapt_color_for_theme(cls, hex_color: str, theme: str) -> Tuple[str, str]:
        """
        Adapts a tag color for the active theme.
        In dark mode, bright pastels are automatically toned down into elegant,
        eye-comfortable deep muted tones (preventing harsh blinding glare).
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

        return (hex_color, cls.get_contrast_text_color(hex_color))

    @classmethod
    def get_tooltip_style(cls, effective_theme: str) -> str:
        if effective_theme == "dark":
            return """
                QToolTip {
                    background-color: #26262a;
                    color: #ededed;
                    border: 1px solid #3f3f48;
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif;
                    font-size: 12px;
                }
            """
        return """
            QToolTip {
                background-color: #ffffff;
                color: #18181b;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif;
                font-size: 12px;
            }
        """

    @classmethod
    def apply_theme_to_app(cls, effective_theme: str):
        """Applies global palette and tooltip styling to QApplication instance."""
        app = QApplication.instance()
        if not app:
            return

        app.setStyleSheet(cls.get_tooltip_style(effective_theme))

        palette = app.palette()
        if effective_theme == "dark":
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#26262a"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#ededed"))
        else:
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#18181b"))
        app.setPalette(palette)

    @classmethod
    def apply_titlebar_theme(cls, widget, effective_theme: str):
        """
        Synchronizes the native Windows titlebar (minimize, maximize, close buttons and caption)
        with the app's Dark / Light mode and theme colors.
        """
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = int(widget.winId())
            use_dark = 1 if effective_theme == "dark" else 0
            value = ctypes.c_int(use_dark)

            # 1. DWMWA_USE_IMMERSIVE_DARK_MODE (20 on Win11/Win10 20H1+, 19 on older Win10)
            hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
            )
            if hr != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 19, ctypes.byref(value), ctypes.sizeof(value)
                )

            # 2. On Windows 11 (build 22000+), customize titlebar background & text color
            # DWMWA_CAPTION_COLOR = 35 (BGR hex: 0x00BBGGRR), DWMWA_TEXT_COLOR = 36
            if effective_theme == "dark":
                caption_color = ctypes.c_int(0x00161414)  # #141416
                caption_text = ctypes.c_int(0x00ededed)   # #ededed
            else:
                caption_color = ctypes.c_int(0x00ffffff)  # #ffffff
                caption_text = ctypes.c_int(0x0018181b)   # #18181b

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
            )
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 36, ctypes.byref(caption_text), ctypes.sizeof(caption_text)
            )
        except Exception:
            pass

    @classmethod
    def get_main_style(cls, effective_theme: str) -> str:
        if effective_theme == "dark":
            base = """
                QMainWindow {
                    background-color: #141416;
                }
                QWidget {
                    color: #ededed;
                    font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif;
                }
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QWidget#groupsContainer {
                    background-color: transparent;
                    border: none;
                }
                QFrame#activeFileBar {
                    background-color: #1e1e23;
                    border: none;
                    border-radius: 6px;
                }
                QLabel#lblActiveFile {
                    color: #d4d4d4;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton#btnCloseActiveFile {
                    background-color: transparent;
                    color: #888888;
                    border: none;
                    font-weight: 700;
                    font-size: 12px;
                    padding: 0 4px;
                }
                QPushButton#btnCloseActiveFile:hover {
                    color: #f87171;
                }
                QPushButton#btnHeaderAction {
                    background-color: transparent;
                    color: #d4d4d4;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 6px;
                }
                QPushButton#btnHeaderAction:hover {
                    background-color: #2e2e36;
                    color: #ffffff;
                }
                QPushButton#btnHeaderAction:disabled {
                    color: #55555c;
                }
                QPushButton#btnHeaderPin {
                    background-color: transparent;
                    color: #d4d4d4;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton#btnHeaderPin:hover {
                    background-color: #2e2e36;
                    color: #ffffff;
                }
                QPushButton#btnHeaderPin:checked {
                    background-color: #383844;
                    color: #93c5fd;
                }
                QFrame#groupCard {
                    background-color: #1f1f25;
                    border: none;
                    border-radius: 8px;
                }
                QFrame#groupHeader {
                    background-color: #2e2e38;
                    border: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }
                QFrame#groupHeader[collapsed="true"] {
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                }
                QFrame#groupHeader:hover {
                    background-color: #383844;
                }
                QLabel#lblGroupTitle {
                    color: #ededed;
                    font-weight: 700;
                    font-size: 12px;
                }
                QLabel#lblGroupIndicator {
                    color: #9ca3af;
                    font-weight: 700;
                    font-size: 10px;
                    padding-left: 2px;
                    padding-right: 2px;
                }
                QPushButton#btnGroupAdd {
                    background-color: #2e2e38;
                    color: #ededed;
                    font-weight: 700;
                    font-size: 13px;
                    border-radius: 4px;
                    border: none;
                    padding: 0;
                }
                QPushButton#btnGroupAdd:hover {
                    background-color: #434352;
                }
                QComboBox {
                    background-color: #27272a;
                    border: 1px solid #3f3f48;
                    border-radius: 6px;
                    padding: 5px 12px;
                    color: #ededed;
                    font-size: 13px;
                    font-weight: 500;
                }
                QComboBox QAbstractItemView {
                    background-color: #27272a;
                    color: #ededed;
                    selection-background-color: #3f3f48;
                    selection-color: #ffffff;
                    border: 1px solid #3f3f48;
                    padding: 4px;
                }
            """
        else:  # light
            base = """
                QMainWindow {
                    background-color: #ffffff;
                }
                QWidget {
                    color: #18181b;
                    font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif;
                }
                QScrollArea {
                    border: none;
                    background-color: transparent;
                }
                QWidget#groupsContainer {
                    background-color: transparent;
                    border: none;
                }
                QFrame#activeFileBar {
                    background-color: #f2f4f7;
                    border: none;
                    border-radius: 6px;
                }
                QLabel#lblActiveFile {
                    color: #27272a;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton#btnCloseActiveFile {
                    background-color: transparent;
                    color: #71717a;
                    border: none;
                    font-weight: 700;
                    font-size: 12px;
                    padding: 0 4px;
                }
                QPushButton#btnCloseActiveFile:hover {
                    color: #ef4444;
                }
                QPushButton#btnHeaderAction {
                    background-color: transparent;
                    color: #52525b;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 6px;
                }
                QPushButton#btnHeaderAction:hover {
                    background-color: #e2e5ec;
                    color: #18181b;
                }
                QPushButton#btnHeaderAction:disabled {
                    color: #a1a1aa;
                }
                QPushButton#btnHeaderPin {
                    background-color: transparent;
                    color: #52525b;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 6px;
                }
                QPushButton#btnHeaderPin:hover {
                    background-color: #e2e5ec;
                    color: #18181b;
                }
                QPushButton#btnHeaderPin:checked {
                    background-color: #e2e8f0;
                    color: #2563eb;
                }
                QFrame#groupCard {
                    background-color: #eaedf2;
                    border: none;
                    border-radius: 8px;
                }
                QFrame#groupHeader {
                    background-color: #d6dae2;
                    border: none;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }
                QFrame#groupHeader[collapsed="true"] {
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                }
                QFrame#groupHeader:hover {
                    background-color: #ccd1db;
                }
                QLabel#lblGroupTitle {
                    color: #18181b;
                    font-weight: 700;
                    font-size: 12px;
                }
                QLabel#lblGroupIndicator {
                    color: #4b5563;
                    font-weight: 700;
                    font-size: 10px;
                    padding-left: 2px;
                    padding-right: 2px;
                }
                QPushButton#btnGroupAdd {
                    background-color: #d6dae2;
                    color: #18181b;
                    font-weight: 700;
                    font-size: 13px;
                    border-radius: 4px;
                    border: none;
                    padding: 0;
                }
                QPushButton#btnGroupAdd:hover {
                    background-color: #c0c6d2;
                }
                QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #d4d4d8;
                    border-radius: 6px;
                    padding: 5px 12px;
                    color: #18181b;
                    font-size: 13px;
                    font-weight: 500;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #18181b;
                    selection-background-color: #e4e4e7;
                    selection-color: #18181b;
                    border: 1px solid #d4d4d8;
                    padding: 4px;
                }
            """
        return base + "\n" + cls.get_tooltip_style(effective_theme)

    @classmethod
    def get_context_menu_style(cls, effective_theme: str) -> str:
        if effective_theme == "dark":
            return """
                QMenu {
                    background-color: #26262a;
                    color: #ededed;
                    border: 1px solid #3f3f48;
                    border-radius: 6px;
                    padding: 4px;
                    font-size: 13px;
                }
                QMenu::item {
                    padding: 6px 20px 6px 12px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #3b3b44;
                    color: #ffffff;
                }
                QMenu::separator {
                    height: 1px;
                    background: #34343a;
                    margin: 4px 6px;
                }
            """
        return """
            QMenu {
                background-color: #ffffff;
                color: #18181b;
                border: 1px solid #e4e4e7;
                border-radius: 6px;
                padding: 4px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f4f4f5;
                color: #18181b;
            }
            QMenu::separator {
                height: 1px;
                background: #e4e4e7;
                margin: 4px 6px;
            }
        """

    @classmethod
    def get_dialog_style(cls, effective_theme: str) -> str:
        if effective_theme == "dark":
            base = """
                QDialog {
                    background-color: #1f1f23;
                    color: #ededed;
                }
                QLabel {
                    color: #d4d4d4;
                    font-size: 13px;
                    font-weight: 500;
                }
                QLineEdit, QSpinBox {
                    background-color: #2a2a30;
                    border: 1px solid #3f3f48;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #ffffff;
                    font-size: 13px;
                }
                QLineEdit:focus, QSpinBox:focus {
                    border-color: #6366f1;
                }
                QGroupBox {
                    border: 1px solid #34343a;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 14px;
                    font-weight: 600;
                    color: #a1a1aa;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QRadioButton, QCheckBox {
                    color: #ededed;
                    font-size: 13px;
                }
                QComboBox {
                    background-color: #2a2a30;
                    border: 1px solid #3f3f48;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #ffffff;
                    font-size: 13px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2a2a30;
                    color: #ffffff;
                    selection-background-color: #3b3b44;
                    border: 1px solid #3f3f48;
                }
                QPushButton#btnSecondary {
                    background-color: #2a2a30;
                    color: #ededed;
                    border: 1px solid #3f3f48;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                }
                QPushButton#btnSecondary:hover {
                    background-color: #34343c;
                }
                QPushButton#btnCancel {
                    background-color: #2a2a30;
                    color: #ededed;
                    border: 1px solid #3f3f48;
                    padding: 7px 16px;
                    border-radius: 6px;
                }
                QPushButton#btnCancel:hover {
                    background-color: #34343c;
                }
                QPushButton#btnSave {
                    background-color: #2563eb;
                    color: #ffffff;
                    padding: 7px 20px;
                    font-weight: 600;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton#btnSave:hover {
                    background-color: #3b82f6;
                }
                QMessageBox QPushButton {
                    background-color: #2a2a30;
                    color: #ededed;
                    border: 1px solid #3f3f48;
                    padding: 6px 14px;
                    border-radius: 6px;
                    min-width: 60px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #34343c;
                }
            """
        else:
            base = """
                QDialog {
                    background-color: #ffffff;
                    color: #18181b;
                }
                QLabel {
                    color: #27272a;
                    font-size: 13px;
                    font-weight: 600;
                }
                QLineEdit, QSpinBox {
                    background-color: #fcfcfc;
                    border: 1px solid #d4d4d8;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #18181b;
                    font-size: 13px;
                }
                QLineEdit:focus, QSpinBox:focus {
                    border-color: #2563eb;
                }
                QGroupBox {
                    border: 1px solid #e4e4e7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 14px;
                    font-weight: 600;
                    color: #52525b;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                }
                QRadioButton, QCheckBox {
                    color: #18181b;
                    font-size: 13px;
                }
                QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #d4d4d8;
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: #18181b;
                    font-size: 13px;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #18181b;
                    selection-background-color: #f4f4f5;
                    border: 1px solid #d4d4d8;
                }
                QPushButton#btnSecondary {
                    background-color: #f4f4f5;
                    color: #18181b;
                    border: 1px solid #d4d4d8;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                }
                QPushButton#btnSecondary:hover {
                    background-color: #e4e4e7;
                }
                QPushButton#btnCancel {
                    background-color: #f4f4f5;
                    color: #18181b;
                    border: 1px solid #d4d4d8;
                    padding: 7px 16px;
                    border-radius: 6px;
                }
                QPushButton#btnCancel:hover {
                    background-color: #e4e4e7;
                }
                QPushButton#btnSave {
                    background-color: #2563eb;
                    color: #ffffff;
                    padding: 7px 20px;
                    font-weight: 600;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton#btnSave:hover {
                    background-color: #1d4ed8;
                }
                QMessageBox QPushButton {
                    background-color: #f4f4f5;
                    color: #18181b;
                    border: 1px solid #d4d4d8;
                    padding: 6px 14px;
                    border-radius: 6px;
                    min-width: 60px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #e4e4e7;
                }
            """
        return base + "\n" + cls.get_tooltip_style(effective_theme)
