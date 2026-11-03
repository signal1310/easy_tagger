from PyQt6.QtWidgets import QDialog, QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.core.defaults import APP_NAME, APP_VERSION
from src.ui.styles.theme_manager import ThemeManager


class HelpDialog(QDialog):
    """Themed dialog explaining mouse gestures, keyboard shortcuts, and tag tips."""

    def __init__(self, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.setWindowTitle("도움말")
        self.setMinimumWidth(390)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))
        self._init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    @staticmethod
    def _build_section(title: str, items: list) -> QGroupBox:
        box = QGroupBox(title)
        vbox = QVBoxLayout(box)
        vbox.setSpacing(6)
        for text in items:
            vbox.addWidget(QLabel(text))
        return box

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        layout.addWidget(
            self._build_section(
                "마우스 제스처",
                [
                    "• Ctrl + 드래그 (태그): 태그 순서 변경 및 다른 그룹으로 이동",
                    "• Ctrl + 드래그 (그룹 바): 그룹 상/하 순서 변경",
                    "• 파일 드롭: 탐색기에서 파일을 창에 드롭하여 즉시 편집",
                    "• 태그 클릭: 파일 편집 중 해당 태그 추가/제거 토글",
                    "• 우클릭: 태그 수정/복제/삭제 및 그룹 메뉴",
                ],
            )
        )
        layout.addWidget(
            self._build_section(
                "키보드 단축키",
                [
                    "• Ctrl + Z: 실행 취소 (마지막 태그 작업 전 파일명 복원)",
                    "• Ctrl + ,: 환경 설정 열기",
                    "• F1: 도움말 열기",
                ],
            )
        )
        layout.addWidget(
            self._build_section(
                "태그 활용 팁",
                [
                    "• 고정 속성 (예: -fps 60): 동일 키가 있을 경우 자동 교체",
                    "• 입력형 속성 (예: -score ?): 클릭 시 실시간 값 입력 프롬프트",
                ],
            )
        )

        btn_layout = QHBoxLayout()
        subtle_color = "#71717a" if self.effective_theme == "dark" else "#a1a1aa"
        self.lbl_version = QLabel(f"{APP_NAME} {APP_VERSION}")
        self.lbl_version.setStyleSheet(f"color: {subtle_color}; font-size: 11px;")
        btn_layout.addWidget(self.lbl_version)
        btn_layout.addStretch()

        self.btn_ok = QPushButton("확인")
        self.btn_ok.setObjectName("btnSave")
        self.btn_ok.setFixedWidth(80)
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)

