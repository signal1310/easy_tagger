import os
from typing import List

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QPushButton

from src.ui.icons import icon_factory
from src.ui.styles.theme_manager import ThemeManager


class ActionBar(QFrame):
    """
    Top status & action bar displaying the active file(s), '[+ 새 그룹]' button,
    and '[☰ 메뉴]' hamburger menu.
    """

    clearFilesRequested = pyqtSignal()
    addGroupRequested = pyqtSignal()
    undoRequested = pyqtSignal()
    togglePinRequested = pyqtSignal()
    openSettingsRequested = pyqtSignal()
    openHelpRequested = pyqtSignal()

    def __init__(self, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.setObjectName("activeFileBar")
        self.setFixedHeight(28)
        self._init_ui(effective_theme)

    def _init_ui(self, eff: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 6, 2)
        layout.setSpacing(6)

        self.lbl_active_icon = QLabel()
        self.lbl_active_icon.setObjectName("lblActiveFileIcon")
        layout.addWidget(self.lbl_active_icon)

        self.lbl_active_file = QLabel("파일을 드롭하여 태그 편집")
        self.lbl_active_file.setObjectName("lblActiveFile")
        layout.addWidget(self.lbl_active_file)

        self.btn_close_active_file = QPushButton()
        self.btn_close_active_file.setObjectName("btnCloseActiveFile")
        self.btn_close_active_file.setToolTip("편집 모드 해제 (활성 파일 닫기)")
        self.btn_close_active_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_active_file.setVisible(False)
        self.btn_close_active_file.clicked.connect(self.clearFilesRequested.emit)
        layout.addWidget(self.btn_close_active_file)

        layout.addStretch()

        self.btn_add_group = QPushButton()
        self.btn_add_group.setObjectName("btnHeaderAction")
        self.btn_add_group.setToolTip("새 그룹 추가...")
        self.btn_add_group.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_group.clicked.connect(self.addGroupRequested.emit)
        layout.addWidget(self.btn_add_group)

        self.btn_menu = QPushButton()
        self.btn_menu.setObjectName("btnHeaderAction")
        self.btn_menu.setToolTip("메뉴")
        self.btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_menu)

        self.update_icons(eff, active_count=0)

    def update_icons(self, eff: str, active_count: int = 0):
        icon_size = QSize(15, 15)
        self.btn_add_group.setIcon(icon_factory.get_icon("folder-plus", theme=eff, size=15))
        self.btn_add_group.setIconSize(icon_size)
        self.btn_menu.setIcon(icon_factory.get_icon("menu", theme=eff, size=15))
        self.btn_menu.setIconSize(icon_size)
        self.btn_close_active_file.setIcon(icon_factory.get_icon("x", theme=eff, size=12))
        self.btn_close_active_file.setIconSize(QSize(12, 12))
        file_icon = "files" if active_count > 1 else "file"
        self.lbl_active_icon.setPixmap(icon_factory.get_pixmap(file_icon, theme=eff, size=14))

    def update_active_files_display(self, valid_paths: List[str], eff: str) -> str:
        """Updates bar text/icons for `valid_paths` and returns the corresponding window title."""
        total = len(valid_paths)
        self.update_icons(eff, active_count=total)
        if total == 0:
            self.lbl_active_file.setText("파일을 드롭하여 태그 편집")
            self.lbl_active_file.setToolTip("윈도우 탐색기에서 파일을 창 또는 버튼으로 드래그 & 드롭하세요.")
            self.btn_close_active_file.setVisible(False)
            return "Easy Tagger"

        self.btn_close_active_file.setVisible(True)
        if total == 1:
            filename = os.path.basename(valid_paths[0])
            self.lbl_active_file.setText(filename)
            self.lbl_active_file.setToolTip(f"현재 편집 중: {valid_paths[0]}\n태그 버튼을 클릭하여 추가/제거하세요.")
            return f"Easy Tagger - [{filename}]"

        first_name = os.path.basename(valid_paths[0])
        self.lbl_active_file.setText(f"{first_name} 외 {total - 1}개 ({total}개 파일)")
        preview = "\n".join(f"• {os.path.basename(p)}" for p in valid_paths[:15])
        if total > 15:
            preview += f"\n... 외 {total - 15}개"
        self.lbl_active_file.setToolTip(
            f"현재 다중 편집 중 ({total}개 파일):\n{preview}\n\n태그 버튼을 클릭하여 일괄 추가/제거하세요."
        )
        return f"Easy Tagger - [{first_name} 외 {total - 1}개]"

    def build_hamburger_menu(self, eff: str, undo_count: int, is_pinned: bool) -> QMenu:
        """Constructs the styled hamburger QMenu with natural labels, icons, and shortcuts."""
        menu = QMenu(self)
        menu.setStyleSheet(ThemeManager.get_context_menu_style(eff))

        undo_lbl = f"실행 취소 ({undo_count})" if undo_count > 0 else "실행 취소"
        act_undo = menu.addAction(icon_factory.get_icon("undo", theme=eff), f"{undo_lbl}\tCtrl+Z")
        act_undo.setEnabled(undo_count > 0)
        act_undo.triggered.connect(self.undoRequested.emit)
        menu.addSeparator()

        pin_color = "#2563eb" if (eff == "light" and is_pinned) else ("#93c5fd" if is_pinned else None)
        act_pin = menu.addAction(icon_factory.get_icon("pin", color=pin_color, theme=eff), "항상 위에 고정")
        act_pin.setCheckable(True)
        act_pin.setChecked(is_pinned)
        act_pin.triggered.connect(self.togglePinRequested.emit)

        act_settings = menu.addAction(icon_factory.get_icon("settings", theme=eff), "환경 설정...\tCtrl+,")
        act_settings.triggered.connect(self.openSettingsRequested.emit)
        menu.addSeparator()

        act_help = menu.addAction(icon_factory.get_icon("help", theme=eff), "도움말\tF1")
        act_help.triggered.connect(self.openHelpRequested.emit)
        return menu

    def show_hamburger_menu(self, eff: str, undo_count: int, is_pinned: bool):
        menu = self.build_hamburger_menu(eff, undo_count, is_pinned)
        menu.exec(self.btn_menu.mapToGlobal(self.btn_menu.rect().bottomLeft()))

