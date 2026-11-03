from typing import Optional
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QGroupBox, QLabel, QMessageBox
)
from theme_manager import ThemeManager


class GroupDialog(QDialog):
    """
    Themed dialog to Add or Rename a Group.
    Fully integrated with the app's Dark / Light themes and Windows native titlebars.
    """
    def __init__(self, title: str = "새 그룹 추가", initial_name: str = "", effective_theme: str = "dark", parent=None):
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
        from PyQt6.QtCore import QTimer
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
        self.edit_name.setPlaceholderText("그룹 이름 (예: 기본 태그, 속성 / 스펙)")
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


class ThemedPromptDialog(QDialog):
    """
    Themed text input prompt (replaces QInputDialog.getText).
    Used for parametric tags or single-field input.
    """
    def __init__(self, title: str, label_text: str, initial_text: str = "", effective_theme: str = "dark", parent=None):
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
        from PyQt6.QtCore import QTimer
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


class ThemedMessageBox(QMessageBox):
    """
    Themed message box for warnings and confirmation questions,
    styled with the app's current theme and titlebar.
    """
    def __init__(self, icon, title: str, text: str, buttons, default_button, effective_theme: str = "dark", parent=None):
        super().__init__(icon, title, text, buttons, parent)
        self.effective_theme = effective_theme
        self.setDefaultButton(default_button)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    @classmethod
    def question(cls, parent, title: str, text: str, effective_theme: str = "dark") -> bool:
        box = cls(
            QMessageBox.Icon.Question,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
            effective_theme=effective_theme,
            parent=parent
        )
        return box.exec() == QMessageBox.StandardButton.Yes

    @classmethod
    def warning(cls, parent, title: str, text: str, effective_theme: str = "dark"):
        box = cls(
            QMessageBox.Icon.Warning,
            title,
            text,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok,
            effective_theme=effective_theme,
            parent=parent
        )
        box.exec()


class HelpDialog(QDialog):
    """
    Themed dialog explaining mouse gestures, keyboard shortcuts, and tag tips.
    """
    def __init__(self, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.setWindowTitle("사용 팁 및 단축키 안내")
        self.setMinimumWidth(390)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # 1. Mouse Gestures
        group_mouse = QGroupBox("🖱️ 마우스 제스처")
        mouse_layout = QVBoxLayout(group_mouse)
        mouse_layout.setSpacing(6)
        mouse_layout.addWidget(QLabel("• <b>Ctrl + 드래그 (태그)</b>: 태그 순서 변경 및 다른 그룹으로 이동"))
        mouse_layout.addWidget(QLabel("• <b>Ctrl + 드래그 (그룹 바)</b>: 그룹 상/하 순서 변경"))
        mouse_layout.addWidget(QLabel("• <b>파일 드롭</b>: 탐색기에서 파일을 창에 드롭하여 즉시 편집"))
        mouse_layout.addWidget(QLabel("• <b>태그 클릭 (파일 편집 중)</b>: 해당 태그 추가/제거 토글"))
        mouse_layout.addWidget(QLabel("• <b>우클릭</b>: 태그 수정/복제/삭제 및 그룹 메뉴"))
        layout.addWidget(group_mouse)

        # 2. Keyboard Shortcuts
        group_keys = QGroupBox("⌨️ 키보드 단축키")
        keys_layout = QVBoxLayout(group_keys)
        keys_layout.setSpacing(6)
        keys_layout.addWidget(QLabel("• <b>Ctrl + Z</b>: 실행 취소 (마지막 태그 작업 전 파일명 복원)"))
        keys_layout.addWidget(QLabel("• <b>Ctrl + ,</b>: 환경 설정 열기"))
        keys_layout.addWidget(QLabel("• <b>F1</b>: 이 도움말 창 열기"))
        layout.addWidget(group_keys)

        # 3. Tag Features
        group_tags = QGroupBox("🏷️ 태그 활용 팁")
        tags_layout = QVBoxLayout(group_tags)
        tags_layout.setSpacing(6)
        tags_layout.addWidget(QLabel("• <b>고정 속성 (예: -fps 60)</b>: 동일 키가 있을 경우 자동 교체"))
        tags_layout.addWidget(QLabel("• <b>입력형 속성 (예: -score ?)</b>: 클릭 시 실시간 값 입력 프롬프트"))
        layout.addWidget(group_tags)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("확인")
        btn_ok.setObjectName("btnSave")
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

