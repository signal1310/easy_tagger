import os
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCursor, QDragEnterEvent, QDropEvent, QGuiApplication, QIcon, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QScrollArea, QToolTip, QVBoxLayout, QWidget

from src.core.config_manager import load_config, save_config
from src.core.paths import CONFIG_FILE, get_resource_path
from src.services.undo_service import UndoService
from src.ui.controllers.file_controller import FileController
from src.ui.controllers.group_controller import GroupController
from src.ui.dialogs.help_dialog import HelpDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.styles.theme_manager import ThemeManager
from src.ui.widgets.action_bar import ActionBar
from src.ui.widgets.group_widget import GroupWidget
from src.ui.widgets.tag_button import TagButton


class MainWindow(QMainWindow):
    """Main application window wiring ActionBar, group cards, and controllers."""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Easy Tagger")
        self.config_path = config_path or CONFIG_FILE
        self.config = load_config(self.config_path)

        self.resize(self.config.get("window_width", 380), self.config.get("window_height", 340))
        if "window_x" in self.config and "window_y" in self.config:
            self.move(int(self.config["window_x"]), int(self.config["window_y"]))
        self.setMinimumSize(140, 70)

        self.undo_stack: List[List[Tuple[str, str]]] = []
        self.undo_service = UndoService(self.undo_stack)
        self.file_ctrl = FileController(self, self.undo_service)
        self.group_ctrl = GroupController(self)
        self.group_widgets: List[GroupWidget] = []
        self.all_tag_buttons: List[TagButton] = []

        icon_path = get_resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self._init_shortcuts()
        self._init_theme_listener()
        self.apply_window_flags()
        self.apply_theme()
        self.refresh_groups()

    @property
    def active_file_paths(self) -> List[str]:
        return self.file_ctrl.active_file_paths

    @active_file_paths.setter
    def active_file_paths(self, paths: List[str]):
        self.file_ctrl.active_file_paths = list(paths)

    @property
    def active_file_path(self) -> Optional[str]:
        return self.active_file_paths[-1] if self.active_file_paths else None

    @active_file_path.setter
    def active_file_path(self, value: Optional[str]):
        self.file_ctrl.active_file_paths = [value] if value else []

    def get_effective_theme(self) -> str:
        return ThemeManager.resolve_effective_theme(self.config.get("theme", "system"))

    def save_config(self) -> None:
        save_config(self.config, self.config_path)

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        self.action_bar = ActionBar(effective_theme=self.get_effective_theme(), parent=self)
        self.btn_add_group, self.btn_menu = self.action_bar.btn_add_group, self.action_bar.btn_menu
        self.action_bar.clearFilesRequested.connect(self.file_ctrl.clear_active_files)
        self.action_bar.addGroupRequested.connect(self.group_ctrl.add_new_group)
        self.action_bar.undoRequested.connect(self.undo_last_action)
        self.action_bar.togglePinRequested.connect(self.toggle_pin)
        self.action_bar.openSettingsRequested.connect(self.open_settings_dialog)
        self.action_bar.openHelpRequested.connect(self.open_help_dialog)
        self.btn_menu.clicked.connect(lambda: self.action_bar.show_hamburger_menu(
            self.get_effective_theme(), self.undo_service.count, bool(self.config.get("always_on_top", False))
        ))
        vbox.addWidget(self.action_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAcceptDrops(True)
        self.groups_container = QWidget()
        self.groups_container.setObjectName("groupsContainer")
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setContentsMargins(0, 0, 0, 0)
        self.groups_layout.setSpacing(10)
        self.groups_layout.addStretch()
        self.scroll_area.setWidget(self.groups_container)
        vbox.addWidget(self.scroll_area)

        self.setAcceptDrops(True)
        for w in (self, self.scroll_area, self.groups_container):
            w.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def _init_shortcuts(self) -> None:
        for text, seq, slot in (
            ("실행 취소", "Ctrl+Z", self.undo_last_action),
            ("설정", "Ctrl+,", self.open_settings_dialog),
            ("도움말", "F1", self.open_help_dialog),
        ):
            act = QAction(text, self)
            act.setShortcut(QKeySequence(seq))
            act.triggered.connect(slot)
            self.addAction(act)

    def _init_theme_listener(self) -> None:
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(
                lambda: self.apply_theme() if self.config.get("theme", "system") == "system" else None
            )

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.get_effective_theme())

    def apply_theme(self) -> None:
        eff = self.get_effective_theme()
        ThemeManager.apply_theme_to_app(eff)
        self.setStyleSheet(ThemeManager.get_main_style(eff))
        ThemeManager.apply_titlebar_theme(self, eff)
        for gw in self.group_widgets:
            gw.set_effective_theme(eff)
        self.action_bar.update_icons(eff, active_count=len(self.active_file_paths))

    def apply_window_flags(self) -> None:
        on_top = bool(self.config.get("always_on_top", False))
        cur = self.windowFlags()
        new_f = (cur | Qt.WindowType.WindowStaysOnTopHint) if on_top else (cur & ~Qt.WindowType.WindowStaysOnTopHint)
        if new_f != cur:
            self.setWindowFlags(new_f)
            self.show()

    def toggle_pin(self) -> None:
        new_state = not self.config.get("always_on_top", False)
        self.config["always_on_top"] = new_state
        self.save_config()
        self.apply_window_flags()
        msg = "항상 위에 고정되었습니다." if new_state else "항상 위에 고정이 해제되었습니다."
        QToolTip.showText(QCursor.pos(), msg, self)

    def open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self.config, effective_theme=self.get_effective_theme(), parent=self)
        if dlg.exec():
            self.config.update(dlg.get_updated_config())
            self.save_config()
            self.apply_theme()
            self.apply_window_flags()
            self.refresh_groups()
            QToolTip.showText(QCursor.pos(), "설정이 저장되었습니다.", self)

    def open_help_dialog(self) -> None:
        HelpDialog(effective_theme=self.get_effective_theme(), parent=self).exec()

    def undo_last_action(self) -> None:
        self.file_ctrl.undo_last_action()

    def refresh_groups(self) -> None:
        for gw in self.group_widgets:
            gw.deleteLater()
        self.group_widgets.clear()
        self.all_tag_buttons.clear()
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        eff, btn_h = self.get_effective_theme(), int(self.config.get("button_height", 38))
        for gdata in self.config.get("groups", []):
            gw = GroupWidget(gdata, fixed_height=btn_h, effective_theme=eff, parent=self.groups_container)
            gw.addTagRequested.connect(self.group_ctrl.add_tag_to_group)
            gw.renameGroupRequested.connect(self.group_ctrl.rename_group)
            gw.editGroupSettingsRequested.connect(self.group_ctrl.edit_group_settings)
            gw.deleteGroupRequested.connect(self.group_ctrl.delete_group)
            gw.collapseToggled.connect(self.group_ctrl.on_group_collapse_toggled)
            gw.groupReorderRequested.connect(self.group_ctrl.reorder_group)
            gw.tagMovedToGroupRequested.connect(self.group_ctrl.move_tag_to_group)
            gw.filesDropped.connect(self._handle_dropped_files)

            for bdata in gdata.get("buttons", []):
                btn = TagButton(bdata, fixed_height=btn_h, effective_theme=eff, parent=gw.body_container)
                btn.filesDropped.connect(self.file_ctrl.on_files_dropped_on_button)
                btn.clicked.connect(lambda _, b=btn: self.file_ctrl.on_tag_button_clicked(b))
                btn.editRequested.connect(self.group_ctrl.edit_tag_button)
                btn.duplicateRequested.connect(self.group_ctrl.duplicate_tag_button)
                btn.deleteRequested.connect(self.group_ctrl.delete_tag_button)
                btn.tagReorderRequested.connect(self.group_ctrl.reorder_tag)
                gw.add_tag_button(btn)
                self.all_tag_buttons.append(btn)

            self.groups_layout.addWidget(gw)
            self.group_widgets.append(gw)

        self.groups_layout.addStretch()
        for btn in self.all_tag_buttons:
            btn.update_appearance()
        self.file_ctrl.update_highlights()

    def _handle_dropped_files(self, paths: list):
        if paths:
            self.file_ctrl.set_active_files(paths)
            first = os.path.basename(paths[0])
            msg = f"'{first}' 편집 준비 완료" if len(paths) == 1 else f"'{first}' 외 {len(paths) - 1}개 파일 편집 준비 완료"
            QToolTip.showText(QCursor.pos(), msg, self)

    def dragEnterEvent(self, event: QDragEnterEvent):
        event.acceptProposedAction() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            paths = [os.path.normpath(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                event.acceptProposedAction()
                self._handle_dropped_files(paths)

    def closeEvent(self, event):
        self.config["window_width"], self.config["window_height"] = self.width(), self.height()
        self.config["window_x"], self.config["window_y"] = self.pos().x(), self.pos().y()
        self.save_config()
        super().closeEvent(event)
