import os
from typing import Dict

from src.core.paths import get_resource_path


def _get_icon_url(filename: str) -> str:
    return get_resource_path(os.path.join("assets", "icons", filename)).replace("\\", "/")


_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "win_bg": "#141416", "fg": "#ededed", "bar_bg": "#1e1e23", "bar_fg": "#d4d4d4",
        "close_fg": "#888888", "close_hover": "#f87171",
        "hdr_btn_fg": "#d4d4d4", "hdr_btn_hover_bg": "#2e2e36", "hdr_btn_hover_fg": "#ffffff",
        "hdr_btn_disabled": "#55555c", "pin_checked_bg": "#383844", "pin_checked_fg": "#93c5fd",
        "card_bg": "#1f1f25", "ghdr_bg": "#2e2e38", "ghdr_hover": "#383844",
        "gtitle_fg": "#ededed", "gind_fg": "#9ca3af", "gadd_hover": "#434352",
        "combo_bg": "#27272a", "combo_border": "#3f3f48", "combo_sel_bg": "#3f3f48", "combo_sel_fg": "#ffffff",
        "menu_bg": "#26262a", "menu_border": "#3f3f48", "menu_sel_bg": "#3b3b44", "menu_sel_fg": "#ffffff",
        "menu_sep": "#34343a",
        "dlg_bg": "#1f1f23", "lbl_fg": "#d4d4d4", "lbl_weight": "500",
        "input_bg": "#2a2a30", "input_fg": "#ffffff", "border": "#3f3f48", "focus_border": "#6366f1",
        "group_border": "#34343a", "group_fg": "#a1a1aa",
        "btn_bg": "#2a2a30", "btn_hover": "#34343c", "btn_pressed": "#222228",
        "btn_disabled_fg": "#55555c", "btn_disabled_bg": "#1c1c20",
        "arrow_down": _get_icon_url("chevron-down-dark.svg"),
        "arrow_up": _get_icon_url("chevron-up-dark.svg"),
        "spin_btn_hover": "rgba(255, 255, 255, 0.08)",
        "save_hover": "#3b82f6",
        "tip_bg": "#26262a", "tip_fg": "#ededed", "tip_border": "#3f3f48",
    },
    "light": {
        "win_bg": "#ffffff", "fg": "#18181b", "bar_bg": "#f2f4f7", "bar_fg": "#27272a",
        "close_fg": "#71717a", "close_hover": "#ef4444",
        "hdr_btn_fg": "#52525b", "hdr_btn_hover_bg": "#e2e5ec", "hdr_btn_hover_fg": "#18181b",
        "hdr_btn_disabled": "#a1a1aa", "pin_checked_bg": "#e2e8f0", "pin_checked_fg": "#2563eb",
        "card_bg": "#eaedf2", "ghdr_bg": "#d6dae2", "ghdr_hover": "#ccd1db",
        "gtitle_fg": "#18181b", "gind_fg": "#4b5563", "gadd_hover": "#c0c6d2",
        "combo_bg": "#ffffff", "combo_border": "#d4d4d8", "combo_sel_bg": "#e4e4e7", "combo_sel_fg": "#18181b",
        "menu_bg": "#ffffff", "menu_border": "#e4e4e7", "menu_sel_bg": "#f4f4f5", "menu_sel_fg": "#18181b",
        "menu_sep": "#e4e4e7",
        "dlg_bg": "#ffffff", "lbl_fg": "#27272a", "lbl_weight": "600",
        "input_bg": "#fcfcfc", "input_fg": "#18181b", "border": "#d4d4d8", "focus_border": "#2563eb",
        "group_border": "#e4e4e7", "group_fg": "#52525b",
        "btn_bg": "#f4f4f5", "btn_hover": "#e4e4e7", "btn_pressed": "#d4d4d8",
        "btn_disabled_fg": "#a1a1aa", "btn_disabled_bg": "#f4f4f5",
        "arrow_down": _get_icon_url("chevron-down-light.svg"),
        "arrow_up": _get_icon_url("chevron-up-light.svg"),
        "spin_btn_hover": "rgba(0, 0, 0, 0.06)",
        "save_hover": "#1d4ed8",
        "tip_bg": "#ffffff", "tip_fg": "#18181b", "tip_border": "#d4d4d8",
    },
}


def get_tooltip_qss(effective_theme: str) -> str:
    p = _PALETTES["dark" if effective_theme == "dark" else "light"]
    return f"""
        QToolTip {{
            background-color: {p['tip_bg']};
            color: {p['tip_fg']};
            border: 1px solid {p['tip_border']};
            border-radius: 6px;
            padding: 6px 10px;
            font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif;
            font-size: 12px;
        }}
    """


def get_main_qss(effective_theme: str) -> str:
    p = _PALETTES["dark" if effective_theme == "dark" else "light"]
    base = f"""
        QMainWindow {{ background-color: {p['win_bg']}; }}
        QWidget {{ color: {p['fg']}; font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif; }}
        QScrollArea, QWidget#groupsContainer {{ border: none; background-color: transparent; }}
        QFrame#activeFileBar {{ background-color: {p['bar_bg']}; border: none; border-radius: 6px; }}
        QLabel#lblActiveFile {{ color: {p['bar_fg']}; font-size: 11px; font-weight: 600; }}
        QPushButton#btnCloseActiveFile {{
            background-color: transparent; color: {p['close_fg']}; border: none;
            font-weight: 700; font-size: 12px; padding: 0 4px;
        }}
        QPushButton#btnCloseActiveFile:hover {{ color: {p['close_hover']}; }}
        QPushButton#btnHeaderAction, QPushButton#btnHeaderPin {{
            background-color: transparent; color: {p['hdr_btn_fg']}; border: none;
            border-radius: 4px; font-size: 11px; font-weight: 600; padding: 2px 6px;
        }}
        QPushButton#btnHeaderAction:hover, QPushButton#btnHeaderPin:hover {{
            background-color: {p['hdr_btn_hover_bg']}; color: {p['hdr_btn_hover_fg']};
        }}
        QPushButton#btnHeaderAction:disabled {{ color: {p['hdr_btn_disabled']}; }}
        QPushButton#btnHeaderPin:checked {{
            background-color: {p['pin_checked_bg']}; color: {p['pin_checked_fg']};
        }}
        QFrame#groupCard {{ background-color: {p['card_bg']}; border: none; border-radius: 8px; }}
        QFrame#groupHeader {{
            background-color: {p['ghdr_bg']}; border: none;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;
        }}
        QFrame#groupHeader[collapsed="true"] {{
            border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;
        }}
        QFrame#groupHeader:hover {{ background-color: {p['ghdr_hover']}; }}
        QFrame#groupHeader[live_dragging="true"] {{
            background-color: {p['ghdr_hover']};
            border: 1.5px solid #38bdf8;
        }}
        QLabel#lblGroupTitle {{ color: {p['gtitle_fg']}; font-weight: 700; font-size: 12px; }}
        QLabel#lblGroupIndicator {{
            color: {p['gind_fg']}; font-weight: 700; font-size: 10px;
            padding-left: 2px; padding-right: 2px;
        }}
        QPushButton#btnGroupAdd {{
            background-color: {p['ghdr_bg']}; color: {p['gtitle_fg']};
            font-weight: 700; font-size: 13px; border-radius: 4px; border: none; padding: 0;
        }}
        QPushButton#btnGroupAdd:hover {{ background-color: {p['gadd_hover']}; }}
        QComboBox {{
            background-color: {p['combo_bg']}; border: 1px solid {p['combo_border']};
            border-radius: 6px; padding: 5px 28px 5px 12px; color: {p['fg']}; font-size: 13px; font-weight: 500;
        }}
        QComboBox:hover {{ border-color: {p['focus_border']}; }}
        QComboBox:focus {{ border-color: {p['focus_border']}; }}
        QComboBox::drop-down {{
            subcontrol-origin: padding; subcontrol-position: top right;
            width: 24px; border: none; background: transparent;
        }}
        QComboBox::down-arrow {{
            image: url("{p['arrow_down']}");
            width: 12px; height: 12px;
            margin-right: 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {p['combo_bg']}; color: {p['fg']};
            selection-background-color: {p['combo_sel_bg']}; selection-color: {p['combo_sel_fg']};
            border: 1px solid {p['combo_border']}; border-radius: 6px; padding: 4px; outline: none;
        }}
    """
    return base + "\n" + get_tooltip_qss(effective_theme)


def get_context_menu_qss(effective_theme: str) -> str:
    p = _PALETTES["dark" if effective_theme == "dark" else "light"]
    return f"""
        QMenu {{
            background-color: {p['menu_bg']}; color: {p['fg']};
            border: 1px solid {p['menu_border']}; border-radius: 8px;
            padding: 6px 4px; font-size: 13px;
        }}
        QMenu::item {{
            padding: 6px 20px 6px 10px; border-radius: 5px; margin: 1px 3px;
        }}
        QMenu::item:selected {{
            background-color: {p['menu_sel_bg']}; color: {p['menu_sel_fg']};
        }}
        QMenu::icon {{
            padding-left: 10px; margin-right: 6px;
        }}
        QMenu::separator {{
            height: 1px; background: {p['menu_sep']}; margin: 4px 6px;
        }}
    """


def get_dialog_qss(effective_theme: str) -> str:
    p = _PALETTES["dark" if effective_theme == "dark" else "light"]
    base = f"""
        QDialog {{ background-color: {p['dlg_bg']}; color: {p['fg']}; font-family: 'Segoe UI', 'Malgun Gothic', -apple-system, sans-serif; }}
        QLabel {{ color: {p['lbl_fg']}; font-size: 13px; font-weight: {p['lbl_weight']}; }}
        QLineEdit {{
            background-color: {p['input_bg']}; border: 1px solid {p['border']};
            border-radius: 6px; padding: 6px 10px; color: {p['input_fg']}; font-size: 13px;
        }}
        QLineEdit:focus {{ border-color: {p['focus_border']}; }}
        QSpinBox {{
            background-color: {p['input_bg']}; border: 1px solid {p['border']};
            border-radius: 6px; padding: 5px 24px 5px 10px; color: {p['input_fg']}; font-size: 13px;
            min-height: 20px;
        }}
        QSpinBox:hover {{ border-color: {p['focus_border']}; }}
        QSpinBox:focus {{ border-color: {p['focus_border']}; }}
        QSpinBox::up-button {{
            subcontrol-origin: border; subcontrol-position: top right;
            width: 18px; border: none; background: transparent;
            border-top-right-radius: 5px; margin-right: 2px; margin-top: 2px;
        }}
        QSpinBox::up-button:hover {{ background-color: {p['spin_btn_hover']}; }}
        QSpinBox::up-arrow {{
            image: url("{p['arrow_up']}");
            width: 10px; height: 10px;
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border; subcontrol-position: bottom right;
            width: 18px; border: none; background: transparent;
            border-bottom-right-radius: 5px; margin-right: 2px; margin-bottom: 2px;
        }}
        QSpinBox::down-button:hover {{ background-color: {p['spin_btn_hover']}; }}
        QSpinBox::down-arrow {{
            image: url("{p['arrow_down']}");
            width: 10px; height: 10px;
        }}
        QGroupBox {{
            border: 1px solid {p['group_border']}; border-radius: 8px;
            margin-top: 10px; padding-top: 14px; font-weight: 600; color: {p['group_fg']};
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        QRadioButton, QCheckBox {{ color: {p['fg']}; font-size: 13px; }}
        QComboBox {{
            background-color: {p['input_bg']}; border: 1px solid {p['border']};
            border-radius: 6px; padding: 6px 28px 6px 12px; color: {p['input_fg']}; font-size: 13px;
            min-height: 20px;
        }}
        QComboBox:hover {{ border-color: {p['focus_border']}; }}
        QComboBox:focus {{ border-color: {p['focus_border']}; }}
        QComboBox::drop-down {{
            subcontrol-origin: padding; subcontrol-position: top right;
            width: 24px; border: none; background: transparent;
        }}
        QComboBox::down-arrow {{
            image: url("{p['arrow_down']}");
            width: 12px; height: 12px;
            margin-right: 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {p['dlg_bg']}; color: {p['input_fg']};
            selection-background-color: {p['combo_sel_bg']}; selection-color: {p['combo_sel_fg']};
            border: 1px solid {p['border']}; border-radius: 6px; padding: 4px; outline: none;
        }}
        QPushButton {{
            background-color: {p['btn_bg']}; color: {p['fg']};
            border: 1px solid {p['border']}; border-radius: 6px; padding: 6px 14px;
            font-size: 13px; font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {p['btn_hover']}; border-color: {p['focus_border']}; }}
        QPushButton:pressed {{ background-color: {p['btn_pressed']}; }}
        QPushButton:disabled {{
            color: {p['btn_disabled_fg']}; background-color: {p['btn_disabled_bg']}; border-color: {p['border']};
        }}
        QPushButton#btnSecondary {{
            background-color: {p['btn_bg']}; color: {p['fg']};
            border: 1px solid {p['border']}; border-radius: 4px; padding: 3px 8px; font-size: 11px;
        }}
        QPushButton#btnSecondary:hover {{ background-color: {p['btn_hover']}; }}
        QPushButton#btnCancel {{
            background-color: {p['btn_bg']}; color: {p['fg']};
            border: 1px solid {p['border']}; padding: 7px 16px; border-radius: 6px;
        }}
        QPushButton#btnCancel:hover {{ background-color: {p['btn_hover']}; }}
        QPushButton#btnSave {{
            background-color: #2563eb; color: #ffffff;
            padding: 7px 20px; font-weight: 600; border-radius: 6px; border: none;
        }}
        QPushButton#btnSave:hover {{ background-color: {p['save_hover']}; }}
        QMessageBox QPushButton {{
            background-color: {p['btn_bg']}; color: {p['fg']};
            border: 1px solid {p['border']}; padding: 6px 14px; border-radius: 6px; min-width: 60px;
        }}
        QMessageBox QPushButton:hover {{ background-color: {p['btn_hover']}; }}
    """
    return base + "\n" + get_tooltip_qss(effective_theme)

