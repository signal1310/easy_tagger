from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QCheckBox, QSpinBox, QPushButton, QGroupBox, QLabel
)
import icon_factory
from theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """
    Global settings dialog for Easy Tagger.
    Configures theme, tag position, bracket style, button height, and always-on-top.
    """
    def __init__(self, current_config: dict, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.setWindowTitle("환경 설정")
        self.setMinimumWidth(380)
        self.effective_theme = effective_theme
        self.config = dict(current_config)

        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        # General Group
        group = QGroupBox("태그 및 외형 설정")
        form = QFormLayout(group)
        form.setSpacing(12)
        form.setContentsMargins(12, 14, 12, 12)

        # 1. Theme
        self.combo_theme = QComboBox()
        self.combo_theme.addItem(icon_factory.get_icon("monitor", theme=self.effective_theme, size=15), "시스템 적응 (OS 설정 동기화)", "system")
        self.combo_theme.addItem(icon_factory.get_icon("moon", theme=self.effective_theme, size=15), "다크 모드 (Dark)", "dark")
        self.combo_theme.addItem(icon_factory.get_icon("sun", theme=self.effective_theme, size=15), "라이트 모드 (Light)", "light")
        idx_theme = self.combo_theme.findData(self.config.get("theme", "system"))
        if idx_theme >= 0:
            self.combo_theme.setCurrentIndex(idx_theme)
        form.addRow("화면 테마:", self.combo_theme)

        # 2. Tag Position
        self.combo_position = QComboBox()
        self.combo_position.addItem("뒤에 추가 (Suffix) - 예: 파일 [태그].mp4", "suffix")
        self.combo_position.addItem("앞에 추가 (Prefix) - 예: [태그] 파일.mp4", "prefix")
        idx_pos = self.combo_position.findData(self.config.get("position", "suffix"))
        if idx_pos >= 0:
            self.combo_position.setCurrentIndex(idx_pos)
        form.addRow("태그 위치:", self.combo_position)

        # 3. Bracket Style
        self.combo_style = QComboBox()
        self.combo_style.addItem("통합형 - 예: [태그A 태그B]", "merged")
        self.combo_style.addItem("개별형 - 예: [태그A] [태그B]", "separate")
        idx_style = self.combo_style.findData(self.config.get("style", "merged"))
        if idx_style >= 0:
            self.combo_style.setCurrentIndex(idx_style)
        form.addRow("태그 포맷:", self.combo_style)

        # 4. Button Height (Fixed height for all buttons)
        self.spin_height = QSpinBox()
        self.spin_height.setRange(28, 60)
        self.spin_height.setValue(int(self.config.get("button_height", 38)))
        self.spin_height.setSuffix(" px")
        self.spin_height.setToolTip("모든 태그 버튼의 상하 고정 높이입니다. (가로는 글자 길이에 맞춰 자동 조절)")
        form.addRow("버튼 높이 (고정):", self.spin_height)

        # 5. Always on Top
        self.chk_always_on_top = QCheckBox("프로그램 항상 위에 표시 (Always on Top)")
        self.chk_always_on_top.setChecked(bool(self.config.get("always_on_top", False)))
        form.addRow("", self.chk_always_on_top)

        layout.addWidget(group)

        # Action Buttons
        btn_layout = QHBoxLayout()
        subtle_color = "#71717a" if self.effective_theme == "dark" else "#a1a1aa"
        lbl_version = QLabel("Easy Tagger v1.0.0")
        lbl_version.setStyleSheet(f"color: {subtle_color}; font-size: 11px;")
        btn_layout.addWidget(lbl_version)
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _save_and_accept(self):
        self.config["theme"] = self.combo_theme.currentData()
        self.config["position"] = self.combo_position.currentData()
        self.config["style"] = self.combo_style.currentData()
        self.config["button_height"] = self.spin_height.value()
        self.config["always_on_top"] = self.chk_always_on_top.isChecked()
        self.accept()

    def get_updated_config(self) -> dict:
        return self.config

