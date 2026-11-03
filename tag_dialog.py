import uuid
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontMetrics
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QColorDialog, QGroupBox
)
from tag_parser import get_tag_name, parse_tag_definition
from theme_manager import ThemeManager

# Soft, elegant pastel preset colors
PRESET_COLORS = [
    ("#bae6fd", "스카이"),
    ("#a7f3d0", "민트"),
    ("#fde68a", "레몬"),
    ("#fed7aa", "피치"),
    ("#fca5a5", "코랄"),
    ("#ddd6fe", "라벤더"),
    ("#fbcfe8", "핑크"),
    ("#99f6e4", "아쿠아"),
    ("#cbd5e1", "슬레이트"),
]


class TagDialog(QDialog):
    """
    Dialog to Add or Edit a Tag Button.
    Unified tag input:
      - Normal tag: '여행', '4K'
      - Fixed attribute tag: '-fps 60'
      - Prompt attribute tag: '-score ?'
    """
    def __init__(self, initial_data: dict = None, button_height: int = 38, effective_theme: str = "dark", parent=None):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.button_height = button_height
        self.setWindowTitle("태그 상세 설정" if initial_data else "새 태그 추가")
        self.setMinimumWidth(420)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

        self.data = dict(initial_data) if initial_data else {
            "id": str(uuid.uuid4()),
            "name": "새태그",
            "label": "새태그",
            "tag_text": "새태그",
            "description": "",
            "tag_type": "normal",
            "bg_color": "#bae6fd",
            "text_color": "#0f172a",
        }

        self._init_ui()
        self._load_data()
        self._update_preview()

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.effective_theme)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # 1. Tag Name & Description (Unified input)
        form_group = QGroupBox("태그 정보")
        form = QFormLayout(form_group)
        form.setSpacing(10)
        form.setContentsMargins(12, 14, 12, 12)

        self.edit_name = QLineEdit()
        self.edit_name.setMinimumHeight(32)
        self.edit_name.setPlaceholderText("예: 여행, 4K, -fps 60, -score ?")
        self.edit_name.textChanged.connect(self._on_input_changed)
        form.addRow("태그 이름:", self.edit_name)

        self.edit_desc = QLineEdit()
        self.edit_desc.setMinimumHeight(32)
        self.edit_desc.setPlaceholderText("마우스 호버 시 툴팁으로 표시될 설명")
        self.edit_desc.textChanged.connect(self._on_input_changed)
        form.addRow("태그 설명:", self.edit_desc)

        # Syntax guide & live recognition status
        hint_color = "#a1a1aa" if self.effective_theme == "dark" else "#64748b"
        self.lbl_syntax_guide = QLabel(
            "💡 일반: <b>여행</b>  |  고정 속성: <b>-fps 60</b>  |  입력형 속성: <b>-score ?</b>"
        )
        self.lbl_syntax_guide.setStyleSheet(f"color: {hint_color}; font-size: 11px;")
        self.lbl_syntax_guide.setFixedHeight(18)
        form.addRow(self.lbl_syntax_guide)

        self.lbl_detected_type = QLabel()
        self.lbl_detected_type.setStyleSheet("font-size: 12px; font-weight: 600;")
        self.lbl_detected_type.setFixedHeight(20)
        form.addRow(self.lbl_detected_type)

        main_layout.addWidget(form_group)

        # 2. Appearance (Pastel Color Palette)
        style_group = QGroupBox("버튼 파스텔 색상")
        style_layout = QVBoxLayout(style_group)

        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("파스텔 프리셋:"))
        for hex_code, name in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(f"background-color: {hex_code}; border-radius: 11px; border: 1px solid rgba(0,0,0,0.15);")
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, c=hex_code: self._set_color(c))
            preset_layout.addWidget(btn)

        self.btn_custom_color = QPushButton("직접 선택...")
        self.btn_custom_color.setObjectName("btnSecondary")
        self.btn_custom_color.clicked.connect(self._pick_custom_color)
        preset_layout.addWidget(self.btn_custom_color)
        preset_layout.addStretch()
        style_layout.addLayout(preset_layout)

        main_layout.addWidget(style_group)

        # 3. Live Preview Area
        preview_group = QGroupBox("실제 버튼 미리보기 (호버 시 툴팁 확인 가능)")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_btn = QPushButton("미리보기")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_font = QFont("Segoe UI")
        preview_font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
        preview_font.setPixelSize(13)
        preview_font.setWeight(QFont.Weight.DemiBold)
        self.preview_btn.setFont(preview_font)
        preview_layout.addWidget(self.preview_btn)
        main_layout.addWidget(preview_group)

        # 4. Dialog Actions
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(self.btn_save)

        main_layout.addLayout(btn_layout)

    def _load_data(self):
        spec = parse_tag_definition(
            get_tag_name(self.data),
            fallback_mode=self.data.get("param_val_mode", "")
        )
        self.edit_name.setText(spec["name"])
        self.edit_desc.setText(self.data.get("description", ""))

    def _set_color(self, hex_code: str):
        self.data["bg_color"] = hex_code
        self.data["text_color"] = ThemeManager.get_contrast_text_color(hex_code)
        self._update_preview()

    def _pick_custom_color(self):
        cur = QColor(self.data.get("bg_color", "#bae6fd"))
        picked = QColorDialog.getColor(cur, self, "배경색 선택")
        if picked.isValid():
            self._set_color(picked.name())

    def _on_input_changed(self):
        self._update_preview()

    def _update_preview(self):
        raw_input = self.edit_name.text().strip() or "미리보기"
        spec = parse_tag_definition(raw_input)
        name = spec["name"]
        desc = self.edit_desc.text().strip()

        # Update real-time type detection hint
        if spec["tag_type"] == "param":
            if spec["param_val_mode"] == "prompt":
                self.lbl_detected_type.setText(
                    f"입력형 속성 (키: {spec['param_key']}) — 적용 시 값을 직접 입력"
                )
            else:
                val_disp = spec["param_val"] or "(빈 값)"
                self.lbl_detected_type.setText(
                    f"고정 속성 (키: {spec['param_key']}, 값: {val_disp}) — 동일 키 값 교체"
                )
        else:
            self.lbl_detected_type.setText(
                f"일반 태그 — 파일명에 [{name}] 형태로 추가"
            )

        bg = self.data.get("bg_color", "#bae6fd")
        adapted_bg, fg = ThemeManager.adapt_color_for_theme(bg, self.effective_theme)

        self.preview_btn.setText(name)
        calc_font = QFont(self.preview_btn.font())
        calc_font.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
        calc_font.setPixelSize(13)
        calc_font.setWeight(QFont.Weight.DemiBold)
        fm = QFontMetrics(calc_font)
        w = max(24, fm.horizontalAdvance(name) + 20)
        self.preview_btn.setFixedSize(w, self.button_height)
        preview_style = f"""
            QPushButton {{
                background-color: {adapted_bg};
                color: {fg};
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
                font-size: 13px;
                font-weight: 600;
                border: 2px solid transparent;
                border-radius: 8px;
                padding: 2px 6px;
                text-align: center;
            }}
        """
        preview_style += "\n" + ThemeManager.get_tooltip_style(self.effective_theme)
        self.preview_btn.setStyleSheet(preview_style)

        tip_parts = []
        if desc:
            tip_parts.append(f"[설명] {desc}")
        tip_parts.append(f"태그: [{name}]")
        tip_parts.append("• 호버링 툴팁 미리보기")
        self.preview_btn.setToolTip("\n".join(tip_parts))

    def _save_and_accept(self):
        raw_name = self.edit_name.text().strip() or "태그"
        desc = self.edit_desc.text().strip()

        spec = parse_tag_definition(raw_name)
        self.data.update(spec)
        if spec["tag_type"] == "normal":
            for k in ("param_key", "param_val_mode", "param_val"):
                self.data.pop(k, None)

        self.data["description"] = desc
        bg = self.data.get("bg_color", "#bae6fd")
        self.data["text_color"] = ThemeManager.get_contrast_text_color(bg)

        self.accept()

    def get_data(self) -> dict:
        return dict(self.data)
