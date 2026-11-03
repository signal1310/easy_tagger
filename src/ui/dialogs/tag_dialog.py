import uuid
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.core.defaults import PRESET_COLORS
from src.core.tag_parser import get_tag_name, parse_tag_definition
from src.ui.styles.theme_manager import ThemeManager
from src.ui.widgets.tag_button import compute_tag_button_qss, compute_tag_button_width


class PastelColorPicker(QGroupBox):
    """Reusable group box offering preset pastel color swatches and a custom QColorDialog trigger."""

    colorSelected = pyqtSignal(str)

    def __init__(self, initial_color: str = "#bae6fd", effective_theme: str = "dark", parent=None):
        super().__init__("버튼 파스텔 색상", parent)
        self.effective_theme = effective_theme
        self._current_color = initial_color
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("파스텔 프리셋:"))

        border_color = "rgba(255, 255, 255, 0.2)" if effective_theme == "dark" else "rgba(0, 0, 0, 0.15)"
        hover_border = "#93c5fd" if effective_theme == "dark" else "#2563eb"
        for hex_code, name in PRESET_COLORS:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            disp_color, _ = ThemeManager.adapt_color_for_theme(hex_code, self.effective_theme)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {disp_color}; border-radius: 11px; border: 1px solid {border_color}; }}"
                f"QPushButton:hover {{ border: 2px solid {hover_border}; }}"
            )
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, c=hex_code: self._emit_color(c))
            layout.addWidget(btn)

        self.btn_custom_color = QPushButton("직접 선택...")
        self.btn_custom_color.setObjectName("btnSecondary")
        self.btn_custom_color.clicked.connect(self._pick_custom_color)
        layout.addWidget(self.btn_custom_color)
        layout.addStretch()

    def set_current_color(self, hex_code: str) -> None:
        self._current_color = hex_code

    def _emit_color(self, hex_code: str) -> None:
        self._current_color = hex_code
        self.colorSelected.emit(hex_code)

    def _pick_custom_color(self) -> None:
        dlg = QColorDialog(QColor(self._current_color), self)
        dlg.setWindowTitle("배경색 선택")
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))
        ThemeManager.apply_titlebar_theme(dlg, self.effective_theme)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            picked = dlg.selectedColor()
            if picked.isValid():
                self._emit_color(picked.name())


class TagDialog(QDialog):
    """Dialog to Add or Edit a Tag Button via unified tag syntax ('여행', '-fps 60', '-score ?')."""

    def __init__(
        self, initial_data: Optional[dict] = None, button_height: int = 38, effective_theme: str = "dark", parent=None
    ):
        super().__init__(parent)
        self.effective_theme = effective_theme
        self.button_height = button_height
        self.setWindowTitle("태그 상세 설정" if initial_data else "새 태그 추가")
        self.setMinimumWidth(420)
        self.setStyleSheet(ThemeManager.get_dialog_style(self.effective_theme))

        self.data = dict(initial_data) if initial_data else {
            "id": str(uuid.uuid4()),
            "name": "새태그",
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
        QTimer.singleShot(0, self._focus_input)

    def _focus_input(self):
        self.activateWindow()
        self.raise_()
        self.edit_name.setFocus()
        self.edit_name.selectAll()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._save_and_accept()
            event.accept()
            return
        super().keyPressEvent(event)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)

        form_group = QGroupBox("태그 정보")
        form = QFormLayout(form_group)
        form.setSpacing(10)
        form.setContentsMargins(12, 14, 12, 12)

        self.edit_name = QLineEdit()
        self.edit_name.setMinimumHeight(32)
        self.edit_name.setPlaceholderText("예: 여행, 4K, -fps 60, -score ?")
        self.edit_name.textChanged.connect(self._update_preview)
        self.edit_name.returnPressed.connect(self._save_and_accept)
        form.addRow("태그 이름:", self.edit_name)

        self.edit_desc = QLineEdit()
        self.edit_desc.setMinimumHeight(32)
        self.edit_desc.setPlaceholderText("마우스 호버 시 툴팁으로 표시될 설명")
        self.edit_desc.textChanged.connect(self._update_preview)
        self.edit_desc.returnPressed.connect(self._save_and_accept)
        form.addRow("태그 설명:", self.edit_desc)

        hint_color = "#a1a1aa" if self.effective_theme == "dark" else "#64748b"
        self.lbl_syntax_guide = QLabel("일반: 여행  |  고정 속성: -fps 60  |  입력형 속성: -score ?")
        self.lbl_syntax_guide.setStyleSheet(f"color: {hint_color}; font-size: 11px;")
        form.addRow(self.lbl_syntax_guide)

        self.lbl_detected_type = QLabel()
        self.lbl_detected_type.setStyleSheet("font-size: 12px; font-weight: 600;")
        form.addRow(self.lbl_detected_type)
        main_layout.addWidget(form_group)

        self.color_picker = PastelColorPicker(
            self.data.get("bg_color", "#bae6fd"), effective_theme=self.effective_theme, parent=self
        )
        self.color_picker.colorSelected.connect(self._set_color)
        self.btn_custom_color = self.color_picker.btn_custom_color
        main_layout.addWidget(self.color_picker)

        preview_group = QGroupBox("실제 버튼 미리보기 (호버 시 툴팁 확인 가능)")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_btn = QPushButton("미리보기")
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pfont = QFont("Segoe UI")
        pfont.setFamilies(["Segoe UI", "Malgun Gothic", "sans-serif"])
        pfont.setPixelSize(13)
        pfont.setWeight(QFont.Weight.DemiBold)
        self.preview_btn.setFont(pfont)
        preview_layout.addWidget(self.preview_btn)
        main_layout.addWidget(preview_group)

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
        main_layout.addLayout(btn_layout)

    def _load_data(self):
        spec = parse_tag_definition(get_tag_name(self.data), fallback_mode=self.data.get("param_val_mode", ""))
        self.edit_name.setText(spec["name"])
        self.edit_desc.setText(self.data.get("description", ""))

    def _set_color(self, hex_code: str):
        self.data["bg_color"] = hex_code
        self.data["text_color"] = ThemeManager.get_contrast_text_color(hex_code)
        self._update_preview()

    def _update_preview(self):
        spec = parse_tag_definition(self.edit_name.text().strip() or "미리보기")
        name, desc = spec["name"], self.edit_desc.text().strip()
        if spec["tag_type"] == "param":
            val_disp = spec["param_val"] or "(빈 값)"
            self.lbl_detected_type.setText(
                f"입력형 속성 (키: {spec['param_key']}) — 적용 시 값을 직접 입력"
                if spec["param_val_mode"] == "prompt"
                else f"고정 속성 (키: {spec['param_key']}, 값: {val_disp}) — 동일 키 값 교체"
            )
        else:
            self.lbl_detected_type.setText(f"일반 태그 — 파일명에 [{name}] 형태로 추가")

        bg = self.data.get("bg_color", "#bae6fd")
        self.preview_btn.setText(name)
        self.preview_btn.setFixedSize(compute_tag_button_width(name, self.preview_btn.font()), self.button_height)
        self.preview_btn.setStyleSheet(compute_tag_button_qss(bg, self.effective_theme, tag_state="none"))
        self.preview_btn.setToolTip(desc if desc else "")

    def _save_and_accept(self):
        spec = parse_tag_definition(self.edit_name.text().strip() or "태그")
        self.data.update(spec)
        if spec["tag_type"] == "normal":
            for k in ("param_key", "param_val_mode", "param_val"):
                self.data.pop(k, None)
        self.data["description"] = self.edit_desc.text().strip()
        self.data["text_color"] = ThemeManager.get_contrast_text_color(self.data.get("bg_color", "#bae6fd"))
        self.accept()

    def get_data(self) -> dict:
        return dict(self.data)
