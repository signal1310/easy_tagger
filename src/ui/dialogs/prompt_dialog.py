from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from src.ui.styles.theme_manager import ThemeManager


class ThemedPromptDialog(QDialog):
    """
    Themed text input prompt (replaces QInputDialog.getText).
    Used for parametric tags or single-field input.
    """

    def __init__(
        self, title: str, label_text: str, initial_text: str = "", effective_theme: str = "dark", parent=None
    ):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.setWindowTitle(title)
        self.setMinimumWidth(320)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

        self.value = initial_text
        self._label_text = label_text
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)
        self.activateWindow()
        self.raise_()
        QTimer.singleShot(0, self._focus_input)

    def _focus_input(self):
        self.activateWindow()
        self.raise_()
        self.edit_text.setFocus()
        self.edit_text.selectAll()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        lbl = QLabel(self._label_text)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.edit_text = QLineEdit()
        self.edit_text.setText(self.value)
        self.edit_text.returnPressed.connect(self._save_and_accept)
        layout.addWidget(self.edit_text)

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
        self.edit_text.selectAll()
        self.edit_text.setFocus()

    def _save_and_accept(self):
        self.value = self.edit_text.text().strip()
        self.accept()

    def get_text(self) -> str:
        return self.value

