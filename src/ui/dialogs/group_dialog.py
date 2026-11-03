from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.ui.styles.theme_manager import ThemeManager


class GroupDialog(QDialog):
    """
    Themed dialog to Add or Rename a Group.
    Fully integrated with the app's Dark / Light themes and Windows native titlebars.
    """

    def __init__(
        self, title: str = "새 그룹 추가", initial_name: str = "", effective_theme: str = "dark", parent=None
    ):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.setWindowTitle(title)
        self.setMinimumWidth(320)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

        self.group_name = initial_name
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)
        QTimer.singleShot(0, self._focus_input)

    def _focus_input(self):
        self.activateWindow()
        self.raise_()
        self.edit_name.setFocus()
        self.edit_name.selectAll()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        group_box = QGroupBox("그룹 정보")
        form = QFormLayout(group_box)
        form.setSpacing(10)

        self.edit_name = QLineEdit()
        self.edit_name.setText(self.group_name)
        self.edit_name.returnPressed.connect(self._save_and_accept)
        form.addRow("그룹 이름:", self.edit_name)
        layout.addWidget(group_box)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("확인")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)
        self.edit_name.selectAll()
        self.edit_name.setFocus()

    def _save_and_accept(self):
        val = self.edit_name.text().strip()
        if not val:
            return
        self.group_name = val
        self.accept()

    def get_group_name(self) -> str:
        return self.group_name

