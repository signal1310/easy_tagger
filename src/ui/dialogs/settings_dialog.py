from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from src.core.defaults import APP_NAME, APP_VERSION
from src.ui.icons import icon_factory
from src.ui.styles.theme_manager import ThemeManager


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

        group = QGroupBox("태그 및 외형 설정")
        form = QFormLayout(group)
        form.setSpacing(12)
        form.setContentsMargins(12, 14, 12, 12)

        self.combo_theme = QComboBox()
        eff = self.effective_theme
        self.combo_theme.addItem(icon_factory.get_icon("monitor", theme=eff, size=15), "시스템 적응 (OS 설정 동기화)", "system")
        self.combo_theme.addItem(icon_factory.get_icon("moon", theme=eff, size=15), "다크 모드 (Dark)", "dark")
        self.combo_theme.addItem(icon_factory.get_icon("sun", theme=eff, size=15), "라이트 모드 (Light)", "light")
        self._select_combo_data(self.combo_theme, self.config.get("theme", "system"))
        form.addRow("화면 테마:", self.combo_theme)

        self.combo_position = QComboBox()
        self.combo_position.addItem("뒤에 추가 (Suffix) - 예: 파일 [태그].mp4", "suffix")
        self.combo_position.addItem("앞에 추가 (Prefix) - 예: [태그] 파일.mp4", "prefix")
        self._select_combo_data(self.combo_position, self.config.get("position", "suffix"))
        form.addRow("태그 위치:", self.combo_position)

        self.combo_style = QComboBox()
        self.combo_style.addItem("통합형 - 예: [태그A 태그B]", "merged")
        self.combo_style.addItem("개별형 - 예: [태그A] [태그B]", "separate")
        self._select_combo_data(self.combo_style, self.config.get("style", "merged"))
        form.addRow("대괄호 결합 방식:", self.combo_style)

        self.combo_format = QComboBox()
        self.combo_format.addItem("[태그]", "bracket")
        self.combo_format.addItem("#태그", "hashtag")
        self._select_combo_data(self.combo_format, self.config.get("tag_format", "bracket"))
        form.addRow("기본 태그 형태:", self.combo_format)

        self.combo_indicator_style = QComboBox()
        self.combo_indicator_style.addItem("퍼즐형 모서리 (비대칭 곡면)", "puzzle")
        self.combo_indicator_style.addItem("포인트 테두리 (좌/우 에지)", "edge")
        self.combo_indicator_style.addItem("표시 안 함 (기본 둥근 모서리)", "none")
        self._select_combo_data(self.combo_indicator_style, self.config.get("tag_position_indicator_style", "puzzle"))
        form.addRow("위치 표시 스타일:", self.combo_indicator_style)

        self.spin_height = QSpinBox()
        self.spin_height.setRange(28, 60)
        self.spin_height.setValue(int(self.config.get("button_height", 38)))
        self.spin_height.setSuffix(" px")
        self.spin_height.setToolTip("모든 태그 버튼의 상하 고정 높이입니다. (가로는 글자 길이에 맞춰 자동 조절됨)")
        form.addRow("버튼 높이:", self.spin_height)

        self.chk_always_on_top = QCheckBox("프로그램을 항상 위에 고정")
        self.chk_always_on_top.setChecked(bool(self.config.get("always_on_top", False)))
        form.addRow("", self.chk_always_on_top)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        subtle_color = "#71717a" if eff == "dark" else "#a1a1aa"
        self.lbl_version = QLabel(f"{APP_NAME} {APP_VERSION}")
        self.lbl_version.setStyleSheet(f"color: {subtle_color}; font-size: 11px;")
        btn_layout.addWidget(self.lbl_version)
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

    @staticmethod
    def _select_combo_data(combo: QComboBox, value):
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _save_and_accept(self):
        self.config["theme"] = self.combo_theme.currentData()
        self.config["position"] = self.combo_position.currentData()
        self.config["style"] = self.combo_style.currentData()
        self.config["tag_format"] = self.combo_format.currentData()
        self.config["tag_position_indicator_style"] = self.combo_indicator_style.currentData()
        self.config["button_height"] = self.spin_height.value()
        self.config["always_on_top"] = self.chk_always_on_top.isChecked()
        self.accept()

    def get_updated_config(self) -> dict:
        return self.config

