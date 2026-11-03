from typing import Tuple

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from src.ui.styles import palette_utils
from src.ui.styles.qss_templates import (
    get_context_menu_qss,
    get_dialog_qss,
    get_main_qss,
    get_tooltip_qss,
)


class ThemeManager:
    """
    Facade for application theming across Dark, Light, and System adaptive modes.
    Delegates color luminance/adaptation to palette_utils and QSS templates to main_qss/dialog_qss.
    """

    THEMES = {
        "dark": "다크 모드",
        "light": "라이트 모드",
        "system": "시스템 적응",
    }

    @staticmethod
    def is_system_dark() -> bool:
        return palette_utils.is_system_dark()

    @classmethod
    def resolve_effective_theme(cls, theme_mode: str) -> str:
        return palette_utils.resolve_effective_theme(theme_mode)

    @staticmethod
    def get_contrast_text_color(hex_color: str) -> str:
        return palette_utils.get_contrast_text_color(hex_color)

    @classmethod
    def adapt_color_for_theme(cls, hex_color: str, theme: str) -> Tuple[str, str]:
        return palette_utils.adapt_color_for_theme(hex_color, theme)

    @classmethod
    def get_tooltip_style(cls, effective_theme: str) -> str:
        return get_tooltip_qss(effective_theme)

    @classmethod
    def apply_theme_to_app(cls, effective_theme: str) -> None:
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
    def apply_titlebar_theme(cls, widget, effective_theme: str) -> None:
        palette_utils.apply_titlebar_theme(widget, effective_theme)

    @classmethod
    def get_main_style(cls, effective_theme: str) -> str:
        return get_main_qss(effective_theme)

    @classmethod
    def get_context_menu_style(cls, effective_theme: str) -> str:
        return get_context_menu_qss(effective_theme)

    @classmethod
    def get_dialog_style(cls, effective_theme: str) -> str:
        return get_dialog_qss(effective_theme)

