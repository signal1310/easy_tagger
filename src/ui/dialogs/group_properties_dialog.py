from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolTip,
    QVBoxLayout,
)

from src.ui.styles.theme_manager import ThemeManager


class GroupPropertiesDialog(QDialog):
    """Integrated dialog to configure group name and group-level tag attributes override."""

    def __init__(self, group_data: dict, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.setWindowTitle("그룹 설정")
        self.setMinimumWidth(400)
        self.effective_theme = effective_theme
        self.group_data = dict(group_data)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # 1. Group info groupbox
        info_box = QGroupBox("그룹 기본 정보")
        info_form = QFormLayout(info_box)
        info_form.setSpacing(10)
        info_form.setContentsMargins(12, 14, 12, 12)

        self.edit_name = QLineEdit(self.group_data.get("name", ""))
        self.edit_name.setMinimumHeight(32)
        self.edit_name.returnPressed.connect(self._save_and_accept)
        info_form.addRow("그룹 이름:", self.edit_name)
        layout.addWidget(info_box)

        # 2. Tag attribute override groupbox
        prop_box = QGroupBox("그룹 태그 속성 통일")
        form = QFormLayout(prop_box)
        form.setSpacing(12)
        form.setContentsMargins(12, 14, 12, 12)

        self.chk_override = QCheckBox("이 그룹 내 모든 태그 속성 강제 통일")
        self.chk_override.setChecked(bool(self.group_data.get("override_tags", False)))
        self.chk_override.toggled.connect(self._on_override_toggled)
        form.addRow("", self.chk_override)

        self.combo_position = QComboBox()
        self.combo_position.addItem("접미 (Suffix) — 파일명 뒤", "suffix")
        self.combo_position.addItem("접두 (Prefix) — 파일명 앞", "prefix")
        idx_pos = self.combo_position.findData(self.group_data.get("tag_position", "suffix"))
        if idx_pos >= 0:
            self.combo_position.setCurrentIndex(idx_pos)
        form.addRow("통일 위치:", self.combo_position)

        self.combo_format = QComboBox()
        self.combo_format.addItem("[태그]", "bracket")
        self.combo_format.addItem("#태그", "hashtag")
        idx_fmt = self.combo_format.findData(self.group_data.get("tag_format", "bracket"))
        if idx_fmt >= 0:
            self.combo_format.setCurrentIndex(idx_fmt)
        form.addRow("통일 형태:", self.combo_format)

        hint_color = "#a1a1aa" if self.effective_theme == "dark" else "#64748b"
        self.lbl_guide = QLabel("※ 체크 시 개별 태그 설정을 무시하고 이 그룹의 모든 태그가 동일한 위치/형태로 동작합니다.")
        self.lbl_guide.setWordWrap(True)
        self.lbl_guide.setStyleSheet(f"color: {hint_color}; font-size: 11px;")
        form.addRow(self.lbl_guide)
        layout.addWidget(prop_box)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.setDefault(True)
        self.btn_save.setAutoDefault(True)
        self.btn_save.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)
        self._on_override_toggled(self.chk_override.isChecked())

    def _on_override_toggled(self, checked: bool):
        self.combo_position.setEnabled(checked)
        self.combo_format.setEnabled(checked)

    def _save_and_accept(self):
        new_name = self.edit_name.text().strip()
        if not new_name:
            self.edit_name.setFocus()
            QToolTip.showText(self.edit_name.mapToGlobal(self.edit_name.rect().bottomLeft()), "그룹 이름을 입력해주세요.", self.edit_name)
            return
        self.group_data["name"] = new_name
        self.group_data["override_tags"] = self.chk_override.isChecked()
        self.group_data["tag_position"] = self.combo_position.currentData()
        self.group_data["tag_format"] = self.combo_format.currentData()
        self.accept()

    def get_group_name(self) -> str:
        return self.group_data.get("name", "")

    def get_data(self) -> dict:
        return dict(self.group_data)
