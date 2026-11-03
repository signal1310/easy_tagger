import json
import os

from PyQt6.QtCore import QMimeData, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QDrag
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from src.core.defaults import MIME_GROUP, MIME_TAG
from src.ui.icons import icon_factory
from src.ui.styles.theme_manager import ThemeManager
from src.ui.widgets.flow_layout import FlowLayout
from src.ui.widgets.tag_button import TagButton


class ClickableHeaderFrame(QFrame):
    """Header frame that emits clicked/rightClicked signals and initiates Ctrl + Drag for group reordering."""

    clicked = pyqtSignal()
    rightClicked = pyqtSignal(object)
    startGroupDrag = pyqtSignal()

    def __init__(self, group_name: str, indicator_text: str, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self._drag_start_pos = None
        self.setObjectName("groupHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(28)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.lbl_indicator = QLabel(indicator_text)
        self.lbl_indicator.setObjectName("lblGroupIndicator")
        self.lbl_indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_indicator)

        self.lbl_title = QLabel(group_name)
        self.lbl_title.setObjectName("lblGroupTitle")
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.lbl_title)

        layout.addStretch()

        self.btn_add_tag = QPushButton()
        self.btn_add_tag.setObjectName("btnGroupAdd")
        self.btn_add_tag.setFixedSize(22, 22)
        self.btn_add_tag.setToolTip(f"'{group_name}' 그룹에 새 태그 추가")
        self.btn_add_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_tag.setIcon(icon_factory.get_icon("plus", theme=effective_theme, size=12))
        self.btn_add_tag.setIconSize(QSize(12, 12))
        layout.addWidget(self.btn_add_tag)

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
            if not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                self.clicked.emit()
            self._drag_start_pos = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class GroupWidget(QWidget):
    """
    Collapsible group container card.
    Supports header toggle, '+' tag addition, group context menu on header & card body,
    and Ctrl + Drag reordering of groups and tags.
    """

    SYMBOL_EXPANDED = "▼"
    SYMBOL_COLLAPSED = "▲"

    addTagRequested = pyqtSignal(str)
    renameGroupRequested = pyqtSignal(str)
    deleteGroupRequested = pyqtSignal(str)
    collapseToggled = pyqtSignal(str, bool)
    groupReorderRequested = pyqtSignal(str, str, str)
    tagMovedToGroupRequested = pyqtSignal(str, str)
    filesDropped = pyqtSignal(list)

    AUTO_EXPAND_HOVER_MS = 600

    def __init__(self, group_data: dict, fixed_height: int = 38, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.group_data = dict(group_data)
        self.group_id = self.group_data.get("id", "")
        self.group_name = self.group_data.get("name", "그룹")
        self.collapsed = bool(self.group_data.get("collapsed", False))
        self.fixed_height = fixed_height
        self.effective_theme = effective_theme

        self._auto_expand_timer = QTimer(self)
        self._auto_expand_timer.setSingleShot(True)
        self._auto_expand_timer.setInterval(self.AUTO_EXPAND_HOVER_MS)
        self._auto_expand_timer.timeout.connect(self._on_auto_expand_timeout)

        self.setAcceptDrops(True)
        self._init_ui()
        self.set_collapsed(self.collapsed, notify=False)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.group_card = QFrame()
        self.group_card.setObjectName("groupCard")
        self.group_card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.group_card.customContextMenuRequested.connect(lambda _: self._show_context_menu())

        card_layout = QVBoxLayout(self.group_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        ind = self.SYMBOL_COLLAPSED if self.collapsed else self.SYMBOL_EXPANDED
        self.header_frame = ClickableHeaderFrame(self.group_name, ind, self.effective_theme)
        self.lbl_indicator = self.header_frame.lbl_indicator
        self.lbl_title = self.header_frame.lbl_title
        self.btn_add_tag = self.header_frame.btn_add_tag

        self.header_frame.clicked.connect(self.toggle_collapse)
        self.header_frame.rightClicked.connect(self._show_context_menu)
        self.header_frame.startGroupDrag.connect(self._start_group_drag)
        self.btn_add_tag.clicked.connect(lambda: self.addTagRequested.emit(self.group_id))
        card_layout.addWidget(self.header_frame)

        self.body_container = QWidget()
        self.body_container.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.body_container.customContextMenuRequested.connect(lambda _: self._show_context_menu())
        self.flow_layout = FlowLayout(self.body_container, margin=6, h_spacing=8, v_spacing=8)
        card_layout.addWidget(self.body_container)

        main_layout.addWidget(self.group_card)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda _: self._show_context_menu())

    def _start_group_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_GROUP, json.dumps({"group_id": self.group_id}).encode("utf-8"))
        drag.setMimeData(mime)
        drag.setPixmap(self.header_frame.grab())
        drag.setHotSpot(self.header_frame.rect().center())
        drag.exec(Qt.DropAction.MoveAction)

    def _on_auto_expand_timeout(self):
        if self.collapsed:
            self.set_collapsed(False, notify=True)

    def _start_auto_expand(self):
        if self.collapsed and not self._auto_expand_timer.isActive():
            self._auto_expand_timer.start()

    def _cancel_auto_expand(self):
        if self._auto_expand_timer.isActive():
            self._auto_expand_timer.stop()

    def dragEnterEvent(self, event):
        has_valid = (
            event.mimeData().hasFormat(MIME_GROUP)
            or event.mimeData().hasFormat(MIME_TAG)
            or event.mimeData().hasUrls()
        )
        if has_valid:
            event.acceptProposedAction()
            if self.collapsed and (event.mimeData().hasUrls() or event.mimeData().hasFormat(MIME_TAG)):
                self._start_auto_expand()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        has_valid = (
            event.mimeData().hasFormat(MIME_GROUP)
            or event.mimeData().hasFormat(MIME_TAG)
            or event.mimeData().hasUrls()
        )
        if has_valid:
            event.acceptProposedAction()
            if self.collapsed and (event.mimeData().hasUrls() or event.mimeData().hasFormat(MIME_TAG)):
                self._start_auto_expand()
        else:
            self._cancel_auto_expand()
            event.ignore()

    def dragLeaveEvent(self, event):
        self._cancel_auto_expand()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._cancel_auto_expand()
        if event.mimeData().hasFormat(MIME_TAG):
            try:
                payload = json.loads(bytes(event.mimeData().data(MIME_TAG)).decode("utf-8"))
                src_tag_id = payload.get("tag_id")
                if src_tag_id:
                    event.acceptProposedAction()
                    self.tagMovedToGroupRequested.emit(src_tag_id, self.group_id)
                    return
            except Exception as e:
                print(f"Error dropping tag: {e}")
        elif event.mimeData().hasFormat(MIME_GROUP):
            try:
                payload = json.loads(bytes(event.mimeData().data(MIME_GROUP)).decode("utf-8"))
                src_group_id = payload.get("group_id")
                if src_group_id and src_group_id != self.group_id:
                    drop_pos = "before" if event.position().y() < self.height() / 2 else "after"
                    event.acceptProposedAction()
                    self.groupReorderRequested.emit(src_group_id, self.group_id, drop_pos)
                    return
            except Exception as e:
                print(f"Error dropping group: {e}")
        elif event.mimeData().hasUrls():
            paths = [os.path.normpath(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                event.acceptProposedAction()
                self.filesDropped.emit(paths)
                return
        event.ignore()

    def set_effective_theme(self, theme: str):
        self.effective_theme = theme
        self.btn_add_tag.setIcon(icon_factory.get_icon("plus", theme=theme, size=12))
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and isinstance(item.widget(), TagButton):
                item.widget().set_effective_theme(theme)

    def set_fixed_height(self, h: int):
        self.fixed_height = h
        for i in range(self.flow_layout.count()):
            item = self.flow_layout.itemAt(i)
            if item and isinstance(item.widget(), TagButton):
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
        act_add = menu.addAction(icon_factory.get_icon("plus", theme=eff), "태그 추가...")
        menu.addSeparator()
        act_rename = menu.addAction(icon_factory.get_icon("edit", theme=eff), "그룹 이름 변경...")
        act_del = menu.addAction(icon_factory.get_icon("trash", theme=eff), "그룹 삭제")

        chosen = menu.exec(global_pos or QCursor.pos())
        if chosen == act_add:
            self.addTagRequested.emit(self.group_id)
        elif chosen == act_rename:
            self.renameGroupRequested.emit(self.group_id)
        elif chosen == act_del:
            self.deleteGroupRequested.emit(self.group_id)
