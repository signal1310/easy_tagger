import json
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize
from PyQt6.QtGui import QCursor, QDrag
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QMenu, QApplication
)

import icon_factory
from flow_layout import FlowLayout
from tag_button import TagButton, MIME_TAG
from theme_manager import ThemeManager

MIME_GROUP = "application/x-easytagger-group"


class ClickableHeaderFrame(QFrame):
    """Header frame that emits clicked/rightClicked signals and initiates Ctrl + Drag for group reordering."""
    clicked = pyqtSignal()
    rightClicked = pyqtSignal(object)
    startGroupDrag = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit(event.globalPosition().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if self._drag_start_pos is not None:
                if (event.pos() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                    self.startGroupDrag.emit()
                    self._drag_start_pos = None
                    return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            # If Ctrl was not held, normal click toggles collapse
            if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.clicked.emit()
            self._drag_start_pos = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class GroupWidget(QWidget):
    """
    Collapsible group container.
    Displays:
      [▼ / ▲] [그룹명]               [+]
    When clicked, toggles body visibility (expanded: '▼', collapsed: '▲').
    Supports Ctrl + Drag to reorder groups and accept tags moved from other groups.
    """
    SYMBOL_EXPANDED = "▼"
    SYMBOL_COLLAPSED = "▲"

    addTagRequested = pyqtSignal(str)                  # group_id
    renameGroupRequested = pyqtSignal(str)             # group_id
    deleteGroupRequested = pyqtSignal(str)             # group_id
    collapseToggled = pyqtSignal(str, bool)            # group_id, is_collapsed
    groupReorderRequested = pyqtSignal(str, str, str)  # (src_group_id, target_group_id, 'before'/'after')
    tagMovedToGroupRequested = pyqtSignal(str, str)    # (src_tag_id, target_group_id)
    emptyAreaRightClicked = pyqtSignal(object)         # global_pos

    def __init__(self, group_data: dict, fixed_height: int = 38, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.group_data = dict(group_data)
        self.group_id = self.group_data.get("id", "")
        self.group_name = self.group_data.get("name", "그룹")
        self.collapsed = bool(self.group_data.get("collapsed", False))
        self.fixed_height = fixed_height
        self.effective_theme = effective_theme

        self.setAcceptDrops(True)
        self._init_ui()
        self.set_collapsed(self.collapsed, notify=False)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Enclosing Card Frame for the entire group (borderless, differentiated by surface color)
        self.group_card = QFrame()
        self.group_card.setObjectName("groupCard")
        self.group_card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.group_card.customContextMenuRequested.connect(lambda _: self._show_context_menu())

        card_layout = QVBoxLayout(self.group_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 1. Header Frame (fills 100% of the top of group card)
        self.header_frame = ClickableHeaderFrame()
        self.header_frame.setObjectName("groupHeader")
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.setFixedHeight(28)
        self.header_frame.setToolTip(f"'{self.group_name}' (클릭: 접기/펼치기 | Ctrl+드래그: 그룹 순서 변경)")
        self.header_frame.clicked.connect(self.toggle_collapse)
        self.header_frame.rightClicked.connect(self._show_context_menu)
        self.header_frame.startGroupDrag.connect(self._start_group_drag)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(8, 2, 8, 2)
        header_layout.setSpacing(6)

        # Symmetrical Indicator: '▼' when open, '▲' when closed
        self.lbl_indicator = QLabel(self.SYMBOL_EXPANDED if not self.collapsed else self.SYMBOL_COLLAPSED)
        self.lbl_indicator.setObjectName("lblGroupIndicator")
        self.lbl_indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(self.lbl_indicator)

        # Group Name
        self.lbl_title = QLabel(self.group_name)
        self.lbl_title.setObjectName("lblGroupTitle")
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_layout.addWidget(self.lbl_title)

        header_layout.addStretch()

        # '+' Button on the far right to add a tag into this group
        self.btn_add_tag = QPushButton()
        self.btn_add_tag.setObjectName("btnGroupAdd")
        self.btn_add_tag.setFixedSize(22, 22)
        self.btn_add_tag.setToolTip(f"'{self.group_name}' 그룹에 새 태그 추가")
        self.btn_add_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_tag.setIcon(icon_factory.get_icon("plus", theme=self.effective_theme, size=12))
        self.btn_add_tag.setIconSize(QSize(12, 12))
        self.btn_add_tag.clicked.connect(lambda: self.addTagRequested.emit(self.group_id))
        header_layout.addWidget(self.btn_add_tag)

        card_layout.addWidget(self.header_frame)

        # 2. Body Container with FlowLayout (padding on sides/bottom so tags sit nicely inside card)
        self.body_container = QWidget()
        self.body_container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.body_container.customContextMenuRequested.connect(lambda _: self._show_context_menu())

        self.flow_layout = FlowLayout(self.body_container, margin=6, h_spacing=8, v_spacing=8)
        card_layout.addWidget(self.body_container)

        main_layout.addWidget(self.group_card)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda _: self._show_context_menu())

    def _emit_empty_right_click(self, _pos=None):
        self._show_context_menu()

    def _start_group_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_GROUP, json.dumps({"group_id": self.group_id}).encode("utf-8"))
        drag.setMimeData(mime)
        pix = self.header_frame.grab()
        drag.setPixmap(pix)
        drag.setHotSpot(self.header_frame.rect().center())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_GROUP) or event.mimeData().hasFormat(MIME_TAG):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME_GROUP) or event.mimeData().hasFormat(MIME_TAG):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat(MIME_TAG):
            try:
                raw_bytes = bytes(event.mimeData().data(MIME_TAG))
                payload = json.loads(raw_bytes.decode("utf-8"))
                src_tag_id = payload.get("tag_id")
                if src_tag_id:
                    event.acceptProposedAction()
                    self.tagMovedToGroupRequested.emit(src_tag_id, self.group_id)
                    return
            except Exception as e:
                print(f"Error dropping tag on group: {e}")
        elif event.mimeData().hasFormat(MIME_GROUP):
            try:
                raw_bytes = bytes(event.mimeData().data(MIME_GROUP))
                payload = json.loads(raw_bytes.decode("utf-8"))
                src_group_id = payload.get("group_id")
                if src_group_id and src_group_id != self.group_id:
                    pos_y = event.position().y()
                    drop_pos = "before" if pos_y < self.height() / 2 else "after"
                    event.acceptProposedAction()
                    self.groupReorderRequested.emit(src_group_id, self.group_id, drop_pos)
                    return
            except Exception as e:
                print(f"Error dropping group: {e}")
        event.ignore()

    def set_effective_theme(self, theme: str):
        self.effective_theme = theme
        self.btn_add_tag.setIcon(icon_factory.get_icon("plus", theme=theme, size=12))
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TagButton):
                item.widget().set_effective_theme(theme)

    def set_fixed_height(self, h: int):
        self.fixed_height = h
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), TagButton):
                item.widget().set_fixed_height(h)

    def toggle_collapse(self):
        self.set_collapsed(not self.collapsed, notify=True)

    def set_collapsed(self, collapsed: bool, notify: bool = True):
        self.collapsed = collapsed
        self.lbl_indicator.setText(self.SYMBOL_COLLAPSED if self.collapsed else self.SYMBOL_EXPANDED)
        self.body_container.setVisible(not self.collapsed)
        self.header_frame.setProperty("collapsed", "true" if self.collapsed else "false")
        self.header_frame.style().unpolish(self.header_frame)
        self.header_frame.style().polish(self.header_frame)
        if notify:
            self.collapseToggled.emit(self.group_id, self.collapsed)

    def add_tag_button(self, btn: TagButton):
        self.flow_layout.addWidget(btn)

    def _show_context_menu(self, global_pos=None):
        eff = self.effective_theme
        menu = QMenu(self)
        menu.setStyleSheet(ThemeManager.get_context_menu_style(eff))

        action_add_tag = menu.addAction(icon_factory.get_icon("plus", theme=eff), "태그 추가...")
        menu.addSeparator()
        action_rename = menu.addAction(icon_factory.get_icon("edit", theme=eff), "그룹 이름 변경...")
        action_delete = menu.addAction(icon_factory.get_icon("trash", theme=eff), "그룹 삭제")

        pos = global_pos or QCursor.pos()
        chosen = menu.exec(pos)
        if chosen == action_add_tag:
            self.addTagRequested.emit(self.group_id)
        elif chosen == action_rename:
            self.renameGroupRequested.emit(self.group_id)
        elif chosen == action_delete:
            self.deleteGroupRequested.emit(self.group_id)

