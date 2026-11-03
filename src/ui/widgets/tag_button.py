import json
import os

from PyQt6.QtCore import QEvent, QMimeData, QPoint, QPropertyAnimation, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QFrame, QGraphicsOpacityEffect, QMenu, QPushButton, QToolTip

from src.core.defaults import MIME_TAG
from src.core.tag_parser import get_tag_name, parse_tag_definition
from src.ui.animation import MotionConstants, MotionHelper
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
    bg_hex: str, effective_theme: str, tag_state: str = "none", is_drag_over: bool = False, is_live_dragging: bool = False
) -> str:
    """Computes dynamic QSS for TagButton across states ('none', 'on', 'partial', 'off', drag_over, live_dragging)."""
    adapted_bg, contrast_text = ThemeManager.adapt_color_for_theme(bg_hex, effective_theme)
    base_color = QColor(adapted_bg)
    is_dark = effective_theme == "dark"

    if is_drag_over:
        bg = base_color.lighter(150).name() if is_dark else base_color.darker(128).name()
        bdr_c = base_color.lighter(165).name() if is_dark else base_color.darker(140).name()
        fg = "#ffffff" if is_dark else ThemeManager.get_contrast_text_color(bg)
        border, hover, pressed, weight = f"2px dashed {bdr_c}", bg, base_color.darker(115).name(), "700"
    elif is_live_dragging:
        bg, fg = adapted_bg, contrast_text
        hover = base_color.lighter(118).name() if is_dark else base_color.darker(108).name()
        pressed = base_color.darker(110).name() if is_dark else base_color.darker(118).name()
        border, weight = "2px solid #38bdf8", "700"
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


class TagPlaceholder(QFrame):
    """Visual preview slot inserted into target groups during cross-group live drag."""

    def __init__(self, size: QSize, bg_hex: str = "#bae6fd", effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.setObjectName("tagPlaceholder")
        self.setFixedSize(size)
        self._is_live_dragging = True
        is_dark = effective_theme == "dark"
        adapted_bg, _ = ThemeManager.adapt_color_for_theme(bg_hex, effective_theme)
        col = QColor(adapted_bg)
        r, g, b = col.red(), col.green(), col.blue()
        bg = f"rgba({r}, {g}, {b}, 0.22)" if is_dark else f"rgba({r}, {g}, {b}, 0.28)"
        bdr = col.lighter(135).name() if is_dark else col.darker(120).name()
        self.setStyleSheet(f"""
            QFrame#tagPlaceholder {{
                background-color: {bg};
                border: 2px dashed {bdr};
                border-radius: 8px;
            }}
        """)


class TagButton(QPushButton):
    """
    Custom PushButton representing a tag.
    Accepts dragged files from Explorer, supports Ctrl + Drag reordering/moving across groups,
    and displays active/inactive highlights for edited files.
    """

    _active_drag_tag = None

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
        is_live = getattr(self, "_is_live_dragging", False)
        w = compute_tag_button_width(display_label, self.font(), is_bold=(self.tag_state == "on" or is_drag_over or is_live))
        self.setFixedSize(w, self.fixed_height)
        self.updateGeometry()
        self.setToolTip(build_tag_tooltip(self.data.get("description", ""), self.tag_state))
        bg = self.data.get("bg_color", "#bae6fd")
        self.setStyleSheet(compute_tag_button_qss(bg, self.effective_theme, self.tag_state, is_drag_over, is_live))

    def mousePressEvent(self, event):
        is_ctrl_left = event.button() == Qt.MouseButton.LeftButton and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        self._drag_start_pos = event.pos() if is_ctrl_left else None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if self._drag_start_pos is not None:
                dist = (event.pos() - self._drag_start_pos).manhattanLength()
                if dist >= QApplication.startDragDistance():
                    if not getattr(self, "_is_live_dragging", False):
                        self._start_live_tag_drag()
                    self._handle_live_tag_move(event.globalPosition().toPoint())
                    return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if getattr(self, "_is_live_dragging", False):
                self._finish_live_tag_drag()
                self._drag_start_pos = None
                event.accept()
                return
            if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.clicked.emit()
            self._drag_start_pos = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def eventFilter(self, obj, event):
        if getattr(self, "_is_live_dragging", False):
            if event.type() == QEvent.Type.MouseButtonRelease:
                self._finish_live_tag_drag()
                return True
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        TagButton._active_drag_tag = None
        if getattr(self, "_is_live_dragging", False):
            self._finish_live_tag_drag()
        super().hideEvent(event)

    def _start_live_tag_drag(self):
        TagButton._active_drag_tag = self
        self._is_live_dragging = True
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setProperty("live_dragging", "true")
        self.update_appearance()
        self._origin_gw = self._get_parent_group_widget()
        self._placeholder_gw = None
        self._placeholder = None
        self._target_gw = None
        self._target_idx = -1
        self._last_swap_pos = None
        try:
            self.grabMouse()
        except Exception:
            pass
        QApplication.instance().installEventFilter(self)
        MotionHelper.fade_opacity(self, MotionConstants.OPACITY_FULL, MotionConstants.OPACITY_DRAGGING)

    def _get_parent_group_widget(self):
        p = self.parent()
        while p:
            if hasattr(p, "group_id") and hasattr(p, "flow_layout"):
                return p
            p = p.parent()
        return None

    def _handle_live_tag_move(self, global_pos: QPoint):
        main_win = self.window()
        origin_gw = getattr(self, "_origin_gw", None) or self._get_parent_group_widget()
        self._origin_gw = origin_gw
        if not origin_gw or not hasattr(main_win, "config") or not hasattr(main_win, "group_widgets"):
            return

        target_gw = None
        for gw in main_win.group_widgets:
            if gw.isVisible():
                gw_rect = QRect(gw.mapToGlobal(QPoint(0, 0)), gw.size())
                if gw_rect.contains(global_pos):
                    target_gw = gw
                    break

        if not target_gw:
            for gw in getattr(main_win, "group_widgets", []):
                gw._cancel_auto_expand()
            if hasattr(self, "_placeholder") and self._placeholder and self._placeholder_gw:
                self._placeholder_gw.flow_layout.removeWidget(self._placeholder, animate=True)
                self._placeholder_gw = None
                self._target_gw = None
                self._target_idx = -1
            return

        # Cancel auto-expand on any group that is not the current hover target
        for gw in main_win.group_widgets:
            if gw != target_gw:
                gw._cancel_auto_expand()

        if target_gw.collapsed:
            target_gw._start_auto_expand()
            # Do not insert placeholder into a collapsed group while hovering over it
            if hasattr(self, "_placeholder") and self._placeholder and self._placeholder_gw:
                self._placeholder_gw.flow_layout.removeWidget(self._placeholder, animate=True)
                self._placeholder_gw = None
                self._target_gw = None
                self._target_idx = -1
            return
        else:
            target_gw._cancel_auto_expand()

        if target_gw == origin_gw:
            # Hovering within original group: clean up placeholder in other groups
            if hasattr(self, "_placeholder") and self._placeholder and self._placeholder_gw:
                self._placeholder_gw.flow_layout.removeWidget(self._placeholder, animate=True)
                self._placeholder_gw = None
                self._target_gw = None
                self._target_idx = -1

            other_buttons = []
            for i in range(origin_gw.flow_layout.count()):
                it = origin_gw.flow_layout.itemAt(i)
                if it and it.widget() and it.widget() != self and isinstance(it.widget(), TagButton):
                    other_buttons.append(it.widget())

            curr_idx = origin_gw.flow_layout.indexOf(self)
            target_idx = len(other_buttons)
            for idx, btn in enumerate(other_buttons):
                b_rect = QRect(btn.mapToGlobal(QPoint(0, 0)), btn.size())
                if global_pos.y() < b_rect.top():
                    target_idx = idx
                    break
                elif b_rect.top() <= global_pos.y() <= b_rect.bottom() + 6:
                    if curr_idx >= 0 and curr_idx <= idx:
                        threshold_x = b_rect.left() + min(8, int(b_rect.width() * 0.2))
                        if global_pos.x() < threshold_x:
                            target_idx = idx
                            break
                    else:
                        threshold_x = b_rect.right() - min(8, int(b_rect.width() * 0.2))
                        if global_pos.x() < threshold_x:
                            target_idx = idx
                            break

            if curr_idx != target_idx:
                # Apply hysteresis to prevent rapid vibration on slow movements near boundaries
                if getattr(self, "_last_swap_pos", None) is not None:
                    if (global_pos - self._last_swap_pos).manhattanLength() < MotionConstants.DEADBAND_TAG_SWAP_PX:
                        target_idx = curr_idx

            if curr_idx != target_idx:
                self._last_swap_pos = global_pos
                origin_gw.flow_layout.moveWidget(self, target_idx, animate=True)
                self._target_gw = origin_gw
                self._target_idx = target_idx
        else:
            # Hovering over another group: use visual preview placeholder matching tag color
            if hasattr(self, "_placeholder") and self._placeholder and self._placeholder_gw and self._placeholder_gw != target_gw:
                self._placeholder_gw.flow_layout.removeWidget(self._placeholder, animate=True)
                self._placeholder_gw = None

            if not hasattr(self, "_placeholder") or self._placeholder is None:
                tag_bg = self.data.get("bg_color", "#bae6fd")
                self._placeholder = TagPlaceholder(self.size(), tag_bg, self.effective_theme)

            other_buttons = []
            for i in range(target_gw.flow_layout.count()):
                it = target_gw.flow_layout.itemAt(i)
                if it and it.widget() and it.widget() != self._placeholder and isinstance(it.widget(), TagButton):
                    other_buttons.append(it.widget())

            curr_p_idx = target_gw.flow_layout.indexOf(self._placeholder) if self._placeholder_gw == target_gw else -1
            target_idx = len(other_buttons)
            for idx, btn in enumerate(other_buttons):
                b_rect = QRect(btn.mapToGlobal(QPoint(0, 0)), btn.size())
                if global_pos.y() < b_rect.top():
                    target_idx = idx
                    break
                elif b_rect.top() <= global_pos.y() <= b_rect.bottom() + 6:
                    if curr_p_idx >= 0 and curr_p_idx <= idx:
                        threshold_x = b_rect.left() + min(8, int(b_rect.width() * 0.2))
                        if global_pos.x() < threshold_x:
                            target_idx = idx
                            break
                    else:
                        threshold_x = b_rect.right() - min(8, int(b_rect.width() * 0.2))
                        if global_pos.x() < threshold_x:
                            target_idx = idx
                            break

            if self._placeholder_gw != target_gw:
                self._placeholder.setParent(target_gw.body_container)
                target_gw.flow_layout.insertWidget(target_idx, self._placeholder, animate=True)
                self._placeholder.show()
                self._placeholder_gw = target_gw
                self._target_gw = target_gw
                self._target_idx = target_idx
                self._last_swap_pos = global_pos
            else:
                if curr_p_idx != target_idx:
                    # Apply hysteresis to prevent rapid placeholder vibration
                    if getattr(self, "_last_swap_pos", None) is not None:
                        if (global_pos - self._last_swap_pos).manhattanLength() < MotionConstants.DEADBAND_TAG_SWAP_PX:
                            target_idx = curr_p_idx
                if curr_p_idx != target_idx:
                    self._last_swap_pos = global_pos
                    target_gw.flow_layout.moveWidget(self._placeholder, target_idx, animate=True)
                    self._target_idx = target_idx

        main_win.groups_container.layout().activate()

    def _finish_live_tag_drag(self):
        TagButton._active_drag_tag = None
        try:
            QApplication.instance().removeEventFilter(self)
        except Exception:
            pass
        try:
            if self.mouseGrabber() == self:
                self.releaseMouse()
        except Exception:
            pass
        self._is_live_dragging = False
        self.unsetCursor()
        self.setProperty("live_dragging", "false")
        self.update_appearance()

        main_win = self.window()
        target_gw = getattr(self, "_target_gw", None)
        target_idx = getattr(self, "_target_idx", -1)
        origin_gw = getattr(self, "_origin_gw", None)
        placeholder = getattr(self, "_placeholder", None)
        placeholder_gw = getattr(self, "_placeholder_gw", None)

        if placeholder:
            if placeholder_gw:
                placeholder_gw.flow_layout.removeWidget(placeholder, animate=False)
            placeholder.deleteLater()
            self._placeholder = None
            self._placeholder_gw = None

        if target_gw and origin_gw and target_gw != origin_gw and target_idx >= 0:
            if hasattr(main_win, "config"):
                from src.services.group_model_service import GroupModelService
                GroupModelService.reorder_tag_to_index(main_win.config, self.data["id"], target_gw.group_id, target_idx)
            origin_gw.flow_layout.removeWidget(self, animate=True)
            target_gw.flow_layout.insertWidget(target_idx, self, animate=True)
            self.setParent(target_gw.body_container)
            self.show()
            self.update_appearance()
        elif origin_gw:
            if hasattr(main_win, "config"):
                from src.services.group_model_service import GroupModelService
                final_idx = origin_gw.flow_layout.indexOf(self)
                if final_idx >= 0:
                    GroupModelService.reorder_tag_to_index(main_win.config, self.data["id"], origin_gw.group_id, final_idx)

        self._target_gw = None
        self._target_idx = -1
        self._origin_gw = None
        self._last_swap_pos = None

        for gw in getattr(main_win, "group_widgets", []):
            gw._cancel_auto_expand()

        MotionHelper.fade_opacity(self, MotionConstants.OPACITY_DRAGGING, MotionConstants.OPACITY_FULL)

        if hasattr(main_win, "groups_container"):
            main_win.groups_container.layout().activate()
        if hasattr(main_win, "file_ctrl"):
            main_win.file_ctrl.update_highlights()
        if hasattr(main_win, "save_config"):
            main_win.save_config()

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
