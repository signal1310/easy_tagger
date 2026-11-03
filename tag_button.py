import os
import json
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QColor, QDrag, QFont, QFontMetrics
from PyQt6.QtWidgets import QPushButton, QMenu, QApplication

import icon_factory
from tag_parser import get_tag_name, parse_tag_definition
from theme_manager import ThemeManager

MIME_TAG = "application/x-easytagger-tag"

# Alias for backward compatibility
adapt_color_for_theme = ThemeManager.adapt_color_for_theme


class TagButton(QPushButton):
    """
    Custom PushButton representing a tag.
    Accepts dragged files from Windows Explorer,
    supports Ctrl + Drag reordering/moving across groups,
    and displays active/inactive highlights for the currently edited file.
    """
    filesDropped = pyqtSignal(dict, list)
    tagReorderRequested = pyqtSignal(str, str, str)  # (src_tag_id, target_tag_id, 'before'/'after')
    editRequested = pyqtSignal(dict)
    deleteRequested = pyqtSignal(dict)
    duplicateRequested = pyqtSignal(dict)

    def __init__(self, data: dict, fixed_height: int = 38, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.data = dict(data)
        self.fixed_height = fixed_height
        self.effective_theme = effective_theme
        self.tag_state = "none"  # "none" = no file active, "on" = tagged, "off" = not tagged
        self._drag_start_pos = None

        # Standardize button font for consistent cross-platform metrics
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
        """Sets tag highlight state: 'none', 'on' (all have tag), 'partial' (some have tag), 'off' (none have tag)."""
        if self.tag_state != state:
            self.tag_state = state
            self.update_appearance()

    def _format_display_label(self, raw_label: str) -> str:
        if self.tag_state == "on":
            return f"✓ {raw_label}"
        if self.tag_state == "partial":
            return f"◐ {raw_label}"
        return raw_label

    def _calculate_width(self, text: str) -> int:
        """Calculates precise button width based on actual font metrics without awkward excess margins or truncation."""
        if not text:
            return 24
        # Use Bold (700) weight if state is 'on' or in drag over, otherwise DemiBold (600)
        weight = QFont.Weight.Bold if self.tag_state == "on" else QFont.Weight.DemiBold
        calc_font = QFont(self.font())
        calc_font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
        calc_font.setPixelSize(13)
        calc_font.setWeight(weight)
        fm = QFontMetrics(calc_font)
        adv = fm.horizontalAdvance(text)
        # 12px padding (6px left + 6px right) + 4px border (2px each side) + 4px safety buffer = 20px
        return max(24, adv + 20)

    def sizeHint(self) -> QSize:
        label = get_tag_name(self.data, "Tag")
        display_text = self._format_display_label(label)
        w = self._calculate_width(display_text)
        return QSize(w, self.fixed_height)

    def update_data(self, new_data: dict):
        self.data.update(new_data)
        self.update_appearance()

    def update_appearance(self, is_drag_over: bool = False):
        spec = parse_tag_definition(get_tag_name(self.data, "Tag"), fallback_mode=self.data.get("param_val_mode", ""))
        self.data.update(spec)
        raw_label = spec["name"]

        bg = self.data.get("bg_color", "#bae6fd")

        display_label = self._format_display_label(raw_label)
        self.setText(display_label)
        w = self._calculate_width(display_label)
        self.setFixedSize(w, self.fixed_height)
        self.updateGeometry()

        # Build tooltip: Description on hover as requested
        desc = self.data.get("description", "").strip()
        tip_lines = []
        if desc:
            tip_lines.append(f"[설명] {desc}")
        tip_lines.append(f"태그: [{raw_label}]")

        if self.tag_state == "on":
            tip_lines.append("• 현재 파일에 적용됨 (클릭하여 제거)")
        elif self.tag_state == "partial":
            tip_lines.append("• 일부 파일에만 적용됨 (클릭하여 전체 추가)")
        elif self.tag_state == "off":
            tip_lines.append("• 현재 파일에 미적용 (클릭하여 추가)")
        else:
            tip_lines.append("• 파일을 드래그 & 드롭하여 태그 적용")

        tip_lines.append("(우클릭: 수정 / 복제 / 삭제)")
        self.setToolTip("\n".join(tip_lines))

        # Style computation based on tag_state and theme
        adapted_bg, contrast_text = ThemeManager.adapt_color_for_theme(bg, self.effective_theme)
        base_color = QColor(adapted_bg)

        if is_drag_over:
            if self.effective_theme == "dark":
                bg_render = base_color.lighter(150).name()
                border_style = f"2px dashed {base_color.lighter(165).name()}"
                fg_render = "#ffffff"
            else:
                bg_render = base_color.darker(128).name()
                border_style = f"2px dashed {base_color.darker(140).name()}"
                fg_render = ThemeManager.get_contrast_text_color(bg_render)
            hover_color = bg_render
            pressed_color = base_color.darker(115).name()
            font_weight = "700"

        elif self.tag_state == "on":
            # Tag is APPLIED to all active files: Solid filled with vibrant tag color + checkmark
            if self.effective_theme == "dark":
                bg_render = base_color.lighter(138).name()
                border_style = f"2px solid {base_color.lighter(155).name()}"
                fg_render = "#ffffff"
                hover_color = base_color.lighter(150).name()
                pressed_color = base_color.lighter(125).name()
            else:
                bg_render = base_color.darker(122).name()
                border_style = f"2px solid {base_color.darker(135).name()}"
                fg_render = ThemeManager.get_contrast_text_color(bg_render)
                hover_color = base_color.darker(130).name()
                pressed_color = base_color.darker(138).name()
            font_weight = "700"

        elif self.tag_state == "partial":
            # Tag is APPLIED to some active files: Dashed outline with tag color + soft fill
            if self.effective_theme == "dark":
                bg_render = base_color.lighter(110).name()
                border_style = f"2px dashed {base_color.lighter(140).name()}"
                fg_render = "#ffffff"
                hover_color = base_color.lighter(125).name()
                pressed_color = base_color.lighter(105).name()
            else:
                bg_render = base_color.darker(108).name()
                border_style = f"2px dashed {base_color.darker(128).name()}"
                fg_render = ThemeManager.get_contrast_text_color(bg_render)
                hover_color = base_color.darker(118).name()
                pressed_color = base_color.darker(126).name()
            font_weight = "600"

        elif self.tag_state == "off":
            # Tag is NOT applied to active files: Outlined pill with border in the TAG'S COLOR!
            if self.effective_theme == "dark":
                border_color = base_color.lighter(135).name()
                border_style = f"2px solid {border_color}"
                bg_render = "#1c1c22"
                fg_render = "#ededed"
                hover_color = base_color.name()
                pressed_color = base_color.lighter(115).name()
            else:
                border_color = base_color.darker(118).name()
                border_style = f"2px solid {border_color}"
                bg_render = "#ffffff"
                fg_render = "#18181b"
                hover_color = base_color.lighter(112).name()
                pressed_color = base_color.darker(112).name()
            font_weight = "600"

        else:  # "none" (no active files: clean solid pills with subtle colored border)
            if self.effective_theme == "dark":
                border_style = f"1.5px solid {base_color.lighter(120).name()}"
                bg_render = adapted_bg
                fg_render = contrast_text
                hover_color = base_color.lighter(118).name()
                pressed_color = base_color.darker(110).name()
            else:
                border_style = f"1.5px solid {base_color.darker(110).name()}"
                bg_render = adapted_bg
                fg_render = contrast_text
                hover_color = base_color.darker(108).name()
                pressed_color = base_color.darker(118).name()
            font_weight = "600"

        style = f"""
            QPushButton {{
                background-color: {bg_render};
                color: {fg_render};
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 13px;
                font-weight: {font_weight};
                border: {border_style};
                border-radius: 8px;
                padding: 2px 6px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """
        # Append QToolTip style so local button stylesheet doesn't shadow/isolate the tooltip style
        style += "\n" + ThemeManager.get_tooltip_style(self.effective_theme)
        self.setStyleSheet(style)

    # ------------------ Mouse & Drag Events (Ctrl + Drag to Move/Reorder) ------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._drag_start_pos = event.pos()
        else:
            self._drag_start_pos = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if self._drag_start_pos is not None:
                if (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                    self._start_tag_drag()
                    self._drag_start_pos = None
                    return
        super().mouseMoveEvent(event)

    def _start_tag_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        tag_id = self.data.get("id")
        mime.setData(MIME_TAG, json.dumps({"tag_id": tag_id}).encode("utf-8"))
        drag.setMimeData(mime)

        pix = self.grab()
        drag.setPixmap(pix)
        drag.setHotSpot(self.rect().center())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(MIME_TAG) or event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.update_appearance(is_drag_over=True)
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME_TAG) or event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.update_appearance(is_drag_over=False)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.update_appearance(is_drag_over=False)
        # 1. Tag Reorder / Move between groups
        if event.mimeData().hasFormat(MIME_TAG):
            try:
                raw_bytes = bytes(event.mimeData().data(MIME_TAG))
                payload = json.loads(raw_bytes.decode("utf-8"))
                src_id = payload.get("tag_id")
                target_id = self.data.get("id")
                if src_id and target_id and src_id != target_id:
                    pos_x = event.position().x()
                    drop_pos = "before" if pos_x < self.width() / 2 else "after"
                    event.acceptProposedAction()
                    self.tagReorderRequested.emit(src_id, target_id, drop_pos)
                    return
            except Exception as e:
                print(f"Error handling tag drop: {e}")
            event.ignore()
            return

        # 2. File drop from Explorer
        if event.mimeData().hasUrls():
            file_paths = [
                os.path.normpath(u.toLocalFile())
                for u in event.mimeData().urls()
                if u.isLocalFile()
            ]
            if file_paths:
                event.acceptProposedAction()
                self.filesDropped.emit(self.data, file_paths)
                return
        event.ignore()

    # ------------------ Context Menu (Simplified: Edit, Duplicate, Delete) ------------------

    def _show_context_menu(self, pos):
        eff = self.effective_theme
        menu = QMenu(self)
        menu.setStyleSheet(ThemeManager.get_context_menu_style(eff))

        action_edit = menu.addAction(icon_factory.get_icon("edit", theme=eff), "태그 수정...")
        action_duplicate = menu.addAction(icon_factory.get_icon("copy", theme=eff), "태그 복제")
        menu.addSeparator()
        action_delete = menu.addAction(icon_factory.get_icon("trash", theme=eff), "태그 삭제")

        chosen = menu.exec(self.mapToGlobal(pos))
        if chosen == action_edit:
            self.editRequested.emit(self.data)
        elif chosen == action_duplicate:
            self.duplicateRequested.emit(self.data)
        elif chosen == action_delete:
            self.deleteRequested.emit(self.data)
