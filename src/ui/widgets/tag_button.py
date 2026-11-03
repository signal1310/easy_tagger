import json
import os

from PyQt6.QtCore import QMimeData, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QMenu, QPushButton

from src.core.defaults import MIME_TAG
from src.core.tag_parser import get_tag_name, parse_tag_definition
from src.ui.icons import icon_factory
from src.ui.styles.theme_manager import ThemeManager


def format_display_label(raw_label: str, tag_state: str) -> str:
    if tag_state == "on":
        return f"✓ {raw_label}"
    if tag_state == "partial":
        return f"◐ {raw_label}"
    return raw_label


def build_tag_tooltip(description: str, tag_state: str) -> str:
    """Builds concise tooltip containing only essential description and active file toggle status."""
    lines = []
    desc = description.strip()
    if desc:
        lines.append(desc)

    if tag_state == "on":
        lines.append("✓ 적용됨 (클릭 시 제거)")
    elif tag_state == "partial":
        lines.append("◐ 일부 적용됨 (클릭 시 전체 추가)")
    elif tag_state == "off":
        lines.append("+ 미적용 (클릭 시 추가)")

    return "\n".join(lines) if lines else ""


def compute_tag_button_width(text: str, base_font: QFont, is_bold: bool = False) -> int:
    """Calculates precise button width based on actual font metrics without awkward excess margins."""
    if not text:
        return 24
    calc_font = QFont(base_font)
    calc_font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
    calc_font.setPixelSize(13)
    calc_font.setWeight(QFont.Weight.Bold if is_bold else QFont.Weight.DemiBold)
    adv = QFontMetrics(calc_font).horizontalAdvance(text)
    return max(24, adv + 20)


def compute_tag_button_qss(
    bg_hex: str, effective_theme: str, tag_state: str = "none", is_drag_over: bool = False
) -> str:
    """Computes dynamic QSS for TagButton across states ('none', 'on', 'partial', 'off', drag_over)."""
    adapted_bg, contrast_text = ThemeManager.adapt_color_for_theme(bg_hex, effective_theme)
    base_color = QColor(adapted_bg)
    is_dark = effective_theme == "dark"

    if is_drag_over:
        bg = base_color.lighter(150).name() if is_dark else base_color.darker(128).name()
        bdr_c = base_color.lighter(165).name() if is_dark else base_color.darker(140).name()
        fg = "#ffffff" if is_dark else ThemeManager.get_contrast_text_color(bg)
        border, hover, pressed, weight = f"2px dashed {bdr_c}", bg, base_color.darker(115).name(), "700"
    elif tag_state == "on":
        bg = base_color.lighter(138).name() if is_dark else base_color.darker(122).name()
        bdr_c = base_color.lighter(155).name() if is_dark else base_color.darker(135).name()
        fg = "#ffffff" if is_dark else ThemeManager.get_contrast_text_color(bg)
        hover = base_color.lighter(150).name() if is_dark else base_color.darker(130).name()
        pressed = base_color.lighter(125).name() if is_dark else base_color.darker(138).name()
        border, weight = f"2px solid {bdr_c}", "700"
    elif tag_state == "partial":
        bg = base_color.lighter(110).name() if is_dark else base_color.darker(108).name()
        bdr_c = base_color.lighter(140).name() if is_dark else base_color.darker(128).name()
        fg = "#ffffff" if is_dark else ThemeManager.get_contrast_text_color(bg)
        hover = base_color.lighter(125).name() if is_dark else base_color.darker(118).name()
        pressed = base_color.lighter(105).name() if is_dark else base_color.darker(126).name()
        border, weight = f"2px dashed {bdr_c}", "600"
    elif tag_state == "off":
        bdr_c = base_color.lighter(135).name() if is_dark else base_color.darker(118).name()
        bg = "#1c1c22" if is_dark else "#ffffff"
        fg = "#ededed" if is_dark else "#18181b"
        hover = base_color.name() if is_dark else base_color.lighter(112).name()
        pressed = base_color.lighter(115).name() if is_dark else base_color.darker(112).name()
        border, weight = f"2px solid {bdr_c}", "600"
    else:
        bdr_c = base_color.lighter(120).name() if is_dark else base_color.darker(110).name()
        bg, fg = adapted_bg, contrast_text
        hover = base_color.lighter(118).name() if is_dark else base_color.darker(108).name()
        pressed = base_color.darker(110).name() if is_dark else base_color.darker(118).name()
        border, weight = f"1.5px solid {bdr_c}", "600"

    style = f"""
        QPushButton {{
            background-color: {bg}; color: {fg};
            font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            font-size: 13px; font-weight: {weight};
            border: {border}; border-radius: 8px;
            padding: 2px 6px; text-align: center;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
    """
    return style + "\n" + ThemeManager.get_tooltip_style(effective_theme)


class TagButton(QPushButton):
    """
    Custom PushButton representing a tag.
    Accepts dragged files from Explorer, supports Ctrl + Drag reordering/moving across groups,
    and displays active/inactive highlights for edited files.
    """

    filesDropped = pyqtSignal(dict, list)
    tagReorderRequested = pyqtSignal(str, str, str)
    editRequested = pyqtSignal(dict)
    deleteRequested = pyqtSignal(dict)
    duplicateRequested = pyqtSignal(dict)

    def __init__(self, data: dict, fixed_height: int = 38, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.data = dict(data)
        self.fixed_height = fixed_height
        self.effective_theme = effective_theme
        self.tag_state = "none"
        self._drag_start_pos = None

        btn_font = QFont("Segoe UI")
        btn_font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
        btn_font.setPixelSize(13)
        btn_font.setWeight(QFont.Weight.DemiBold)
        self.setFont(btn_font)

        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.update_appearance()

    def set_effective_theme(self, theme: str):
        self.effective_theme = theme
        self.update_appearance()

    def set_fixed_height(self, h: int):
        self.fixed_height = h
        self.update_appearance()

    def set_tag_state(self, state: str):
        if self.tag_state != state:
            self.tag_state = state
            self.update_appearance()

    def sizeHint(self) -> QSize:
        display_text = format_display_label(get_tag_name(self.data, "Tag"), self.tag_state)
        return QSize(compute_tag_button_width(display_text, self.font(), self.tag_state == "on"), self.fixed_height)

    def update_data(self, new_data: dict):
        self.data.update(new_data)
        self.update_appearance()

    def update_appearance(self, is_drag_over: bool = False):
        spec = parse_tag_definition(get_tag_name(self.data), fallback_mode=self.data.get("param_val_mode", ""))
        self.data.update(spec)
        display_label = format_display_label(spec["name"], self.tag_state)
        self.setText(display_label)
        w = compute_tag_button_width(display_label, self.font(), is_bold=(self.tag_state == "on" or is_drag_over))
        self.setFixedSize(w, self.fixed_height)
        self.updateGeometry()
        self.setToolTip(build_tag_tooltip(self.data.get("description", ""), self.tag_state))
        bg = self.data.get("bg_color", "#bae6fd")
        self.setStyleSheet(compute_tag_button_qss(bg, self.effective_theme, self.tag_state, is_drag_over))

    def mousePressEvent(self, event):
        is_ctrl_left = event.button() == Qt.MouseButton.LeftButton and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        self._drag_start_pos = event.pos() if is_ctrl_left else None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if self._drag_start_pos is not None and (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                self._drag_start_pos = None
                self._start_tag_drag()
                return
        super().mouseMoveEvent(event)

    def _start_tag_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_TAG, json.dumps({"tag_id": self.data.get("id")}).encode("utf-8"))
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(self.rect().center())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(MIME_TAG) or event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.update_appearance(is_drag_over=True)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction() if (event.mimeData().hasFormat(MIME_TAG) or event.mimeData().hasUrls()) else event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.update_appearance(is_drag_over=False)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.update_appearance(is_drag_over=False)
        if event.mimeData().hasFormat(MIME_TAG):
            try:
                payload = json.loads(bytes(event.mimeData().data(MIME_TAG)).decode("utf-8"))
                src_id = payload.get("tag_id")
                target_id = self.data.get("id")
                if src_id and target_id and src_id != target_id:
                    drop_pos = "before" if event.position().x() < self.width() / 2 else "after"
                    event.acceptProposedAction()
                    self.tagReorderRequested.emit(src_id, target_id, drop_pos)
                    return
            except Exception as e:
                print(f"Error handling tag drop: {e}")
            event.ignore()
            return

        if event.mimeData().hasUrls():
            paths = [os.path.normpath(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                event.acceptProposedAction()
                self.filesDropped.emit(self.data, paths)
                return
        event.ignore()

    def _show_context_menu(self, pos):
        eff = self.effective_theme
        menu = QMenu(self)
        menu.setStyleSheet(ThemeManager.get_context_menu_style(eff))
        act_edit = menu.addAction(icon_factory.get_icon("edit", theme=eff), "태그 수정...")
        act_dup = menu.addAction(icon_factory.get_icon("copy", theme=eff), "태그 복제")
        menu.addSeparator()
        act_del = menu.addAction(icon_factory.get_icon("trash", theme=eff), "태그 삭제")

        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == act_edit:
            self.editRequested.emit(self.data)
        elif chosen == act_dup:
            self.duplicateRequested.emit(self.data)
        elif chosen == act_del:
            self.deleteRequested.emit(self.data)
