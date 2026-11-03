import os
import uuid
from typing import List, Tuple, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QGuiApplication, QCursor, QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QMenu, QToolTip, QFrame, QLabel, QPushButton
)

import icon_factory
from config_manager import load_config, save_config, CONFIG_FILE, get_resource_path
from tag_button import TagButton
from tag_dialog import TagDialog, PRESET_COLORS
from settings_dialog import SettingsDialog
from group_widget import GroupWidget
from dialog_utils import GroupDialog, ThemedPromptDialog, ThemedMessageBox
from tag_parser import (
    get_tag_name,
    parse_tag_definition,
    extract_tags_and_base,
    assemble_filename,
    apply_tag_to_tags_list,
    remove_tag_from_tags_list,
    is_tag_in_tags
)
from theme_manager import ThemeManager


class MainWindow(QMainWindow):
    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Easy Tagger")
        self.config_path = config_path or CONFIG_FILE
        self.config = load_config(self.config_path)

        w = self.config.get("window_width", 380)
        h = self.config.get("window_height", 340)
        self.resize(w, h)
        if "window_x" in self.config and "window_y" in self.config:
            self.move(int(self.config["window_x"]), int(self.config["window_y"]))
        # Extreme minimal resize allowed
        self.setMinimumSize(140, 70)

        # Active file(s) being edited
        self.active_file_paths: List[str] = []

        # Undo stack: list of lists: [ [ (old_path, new_path), ... ], ... ]
        self.undo_stack: List[List[Tuple[str, str]]] = []
        self.group_widgets: List[GroupWidget] = []
        self.all_tag_buttons: List[TagButton] = []

        # Window & Taskbar Icon
        icon_path = get_resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._init_ui()
        self._init_shortcuts()
        self._init_theme_listener()
        self._apply_window_flags()
        self._apply_theme()
        self._refresh_groups()
        self._update_action_bar_state()

    @property
    def active_file_path(self) -> Optional[str]:
        return self.active_file_paths[-1] if self.active_file_paths else None

    @active_file_path.setter
    def active_file_path(self, value: Optional[str]):
        if value:
            self.active_file_paths = [value]
        else:
            self.active_file_paths = []

    def _save_config(self):
        save_config(self.config, self.config_path)

    def _find_group(self, group_id: str) -> Optional[dict]:
        return next((g for g in self.config.get("groups", []) if g.get("id") == group_id), None)

    def _find_tag_and_group(self, tag_id: str) -> Tuple[Optional[dict], Optional[dict]]:
        for g in self.config.get("groups", []):
            for b in g.get("buttons", []):
                if b.get("id") == tag_id:
                    return g, b
        return None, None

    def _resolve_tag_to_apply(self, btn_data: dict) -> Optional[str]:
        """Resolves the tag string to apply (prompting user if param_val_mode == 'prompt')."""
        spec = parse_tag_definition(get_tag_name(btn_data), fallback_mode=btn_data.get("param_val_mode", ""))
        if spec["tag_type"] == "param":
            key = spec["param_key"]
            if spec["param_val_mode"] == "prompt":
                dlg = ThemedPromptDialog(
                    "속성값 입력",
                    f"[{key} <값>] 에 들어갈 값을 입력하세요:\n(예: 60, 4K, 5)",
                    initial_text=btn_data.get("param_val", ""),
                    effective_theme=self.get_effective_theme(),
                    parent=self
                )
                if not dlg.exec():
                    return None
                val = dlg.get_text()
                if not val:
                    return None
                return f"{key} {val}"

            return spec["name"]

        return spec["name"] if spec["name"] else None

    def get_effective_theme(self) -> str:
        return ThemeManager.resolve_effective_theme(self.config.get("theme", "system"))

    def _apply_theme(self):
        eff = self.get_effective_theme()
        ThemeManager.apply_theme_to_app(eff)
        self.setStyleSheet(ThemeManager.get_main_style(eff))
        ThemeManager.apply_titlebar_theme(self, eff)
        for gw in self.group_widgets:
            gw.set_effective_theme(eff)
        for btn in self.all_tag_buttons:
            btn.set_effective_theme(eff)
        self._update_action_bar_icons()

    def _update_action_bar_icons(self):
        eff = self.get_effective_theme()
        btn_icon_size = QSize(15, 15)

        if hasattr(self, "btn_add_group"):
            self.btn_add_group.setIcon(icon_factory.get_icon("folder-plus", theme=eff, size=15))
            self.btn_add_group.setIconSize(btn_icon_size)

        if hasattr(self, "btn_undo"):
            self.btn_undo.setIcon(icon_factory.get_icon("undo", theme=eff, size=15))
            self.btn_undo.setIconSize(btn_icon_size)

        if hasattr(self, "btn_pin"):
            pin_active = self.btn_pin.isChecked()
            pin_color = "#2563eb" if (eff == "light" and pin_active) else ("#93c5fd" if pin_active else None)
            self.btn_pin.setIcon(icon_factory.get_icon("pin", color=pin_color, theme=eff, size=15))
            self.btn_pin.setIconSize(btn_icon_size)

        if hasattr(self, "btn_settings"):
            self.btn_settings.setIcon(icon_factory.get_icon("settings", theme=eff, size=15))
            self.btn_settings.setIconSize(btn_icon_size)

        if hasattr(self, "btn_close_active_file"):
            self.btn_close_active_file.setIcon(icon_factory.get_icon("x", theme=eff, size=12))
            self.btn_close_active_file.setIconSize(QSize(12, 12))

        if hasattr(self, "lbl_active_icon"):
            if not self.active_file_paths:
                self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("file", theme=eff, size=14))
            elif len(self.active_file_paths) == 1:
                self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("file", theme=eff, size=14))
            else:
                self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("files", theme=eff, size=14))

    def showEvent(self, event):
        super().showEvent(event)
        ThemeManager.apply_titlebar_theme(self, self.get_effective_theme())

    def _update_action_bar_state(self):
        if hasattr(self, "btn_undo"):
            self.btn_undo.setEnabled(len(self.undo_stack) > 0)
        if hasattr(self, "btn_pin"):
            is_pinned = bool(self.config.get("always_on_top", False))
            self.btn_pin.setChecked(is_pinned)
            self.btn_pin.setToolTip(f"항상 위에 고정 ({'켜짐' if is_pinned else '꺼짐'})")

    def _apply_window_flags(self):
        is_on_top = bool(self.config.get("always_on_top", False))
        current_flags = self.windowFlags()
        if is_on_top:
            new_flags = current_flags | Qt.WindowType.WindowStaysOnTopHint
        else:
            new_flags = current_flags & ~Qt.WindowType.WindowStaysOnTopHint

        if new_flags != current_flags:
            self.setWindowFlags(new_flags)
            self.show()
        self._update_action_bar_state()

    def _init_theme_listener(self):
        hints = QGuiApplication.styleHints()
        if hasattr(hints, 'colorSchemeChanged'):
            hints.colorSchemeChanged.connect(self._on_system_color_scheme_changed)

    def _on_system_color_scheme_changed(self):
        if self.config.get("theme", "system") == "system":
            self._apply_theme()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(8, 8, 8, 8)
        main_vbox.setSpacing(6)

        # 1. Sleek Active File & Action Bar (borderless, color-differentiated)
        self.active_file_bar = QFrame()
        self.active_file_bar.setObjectName("activeFileBar")
        self.active_file_bar.setFixedHeight(28)
        bar_layout = QHBoxLayout(self.active_file_bar)
        bar_layout.setContentsMargins(8, 2, 6, 2)
        bar_layout.setSpacing(6)

        self.lbl_active_icon = QLabel()
        self.lbl_active_icon.setObjectName("lblActiveFileIcon")
        bar_layout.addWidget(self.lbl_active_icon)

        self.lbl_active_file = QLabel("파일을 드롭하여 태그 편집")
        self.lbl_active_file.setObjectName("lblActiveFile")
        bar_layout.addWidget(self.lbl_active_file)

        self.btn_close_active_file = QPushButton()
        self.btn_close_active_file.setObjectName("btnCloseActiveFile")
        self.btn_close_active_file.setToolTip("편집 모드 해제 (활성 파일 닫기)")
        self.btn_close_active_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_active_file.setVisible(False)
        self.btn_close_active_file.clicked.connect(self._clear_active_file)
        bar_layout.addWidget(self.btn_close_active_file)

        bar_layout.addStretch()

        # Visible Standard GUI Actions (modern vector icons)
        self.btn_add_group = QPushButton()
        self.btn_add_group.setObjectName("btnHeaderAction")
        self.btn_add_group.setToolTip("새 그룹 추가...")
        self.btn_add_group.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_group.clicked.connect(self._add_new_group)
        bar_layout.addWidget(self.btn_add_group)

        self.btn_undo = QPushButton()
        self.btn_undo.setObjectName("btnHeaderAction")
        self.btn_undo.setToolTip("실행 취소 (Ctrl+Z)")
        self.btn_undo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_undo.clicked.connect(self.undo_last_action)
        bar_layout.addWidget(self.btn_undo)

        self.btn_pin = QPushButton()
        self.btn_pin.setObjectName("btnHeaderPin")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setToolTip("항상 위에 고정 (클릭하여 토글)")
        self.btn_pin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pin.clicked.connect(self._toggle_pin)
        bar_layout.addWidget(self.btn_pin)

        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("btnHeaderAction")
        self.btn_settings.setToolTip("환경 설정... (Ctrl+,)")
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self._open_settings_dialog)
        bar_layout.addWidget(self.btn_settings)

        self._update_action_bar_icons()

        main_vbox.addWidget(self.active_file_bar)

        # 2. Scroll Area holding the Groups
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setAcceptDrops(True)

        self.groups_container = QWidget()
        self.groups_container.setObjectName("groupsContainer")
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setContentsMargins(0, 0, 0, 0)
        self.groups_layout.setSpacing(10)
        self.groups_layout.addStretch()

        self.scroll_area.setWidget(self.groups_container)
        main_vbox.addWidget(self.scroll_area)

        # Enable drop on window & scroll area to load files
        self.setAcceptDrops(True)

        # Disable context menus on window and background areas (top action bar houses all actions)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.scroll_area.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.groups_container.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def _init_shortcuts(self):
        undo_action = QAction("실행 취소", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo_last_action)
        self.addAction(undo_action)

        settings_action = QAction("설정", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings_dialog)
        self.addAction(settings_action)

    # ------------------ Drag and Drop onto Window (Load Active File) ------------------

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            paths = [os.path.normpath(u.toLocalFile()) for u in urls if u.isLocalFile()]
            if paths:
                event.acceptProposedAction()
                self._set_active_files(paths)
                if len(paths) == 1:
                    QToolTip.showText(QCursor.pos(), f"📄 '{os.path.basename(paths[0])}' 편집 준비 완료", self)
                else:
                    QToolTip.showText(QCursor.pos(), f"📚 '{os.path.basename(paths[0])}' 외 {len(paths) - 1}개 파일 편집 준비 완료", self)

    # ------------------ Active File Management & Tag Highlighting ------------------

    def _set_active_file(self, file_path: Optional[str]):
        self._set_active_files([file_path] if file_path else [])

    def _set_active_files(self, file_paths: List[str]):
        if not file_paths:
            self._clear_active_file()
            return

        valid_paths: List[str] = []
        seen_norm = set()
        for p in file_paths:
            if not p:
                continue
            norm_path = os.path.normpath(os.path.abspath(p))
            norm_case = os.path.normcase(norm_path)
            if os.path.exists(norm_path) and norm_case not in seen_norm:
                seen_norm.add(norm_case)
                valid_paths.append(norm_path)

        if not valid_paths:
            self._clear_active_file()
            return

        self.active_file_paths = valid_paths
        self._detect_and_register_tags_from_files(valid_paths)
        self._update_tag_buttons_highlight()

    def _detect_and_register_tags_from_files(self, file_paths: List[str]):
        """
        Analyzes filenames and automatically adds any unknown tags (tags not present in the program)
        into the '감지된 태그' group so that they are visible and editable in the program.
        """
        if not file_paths:
            return

        groups = self.config.get("groups", [])
        discovered_tags = []

        for fpath in file_paths:
            if not os.path.exists(fpath):
                continue
            filename = os.path.basename(fpath)
            basename, _ = os.path.splitext(filename)
            _, existing_tags = extract_tags_and_base(basename)

            for t in existing_tags:
                t_clean = t.strip()
                if not t_clean:
                    continue

                # Check if t_clean is matched by any button in any group
                matched = False
                for g in groups:
                    for b in g.get("buttons", []):
                        if is_tag_in_tags([t_clean], b):
                            matched = True
                            break
                    if matched:
                        break

                if not matched and t_clean not in discovered_tags:
                    discovered_tags.append(t_clean)

        if not discovered_tags:
            return

        # Find or create group "감지된 태그"
        detected_group = next(
            (g for g in groups if g.get("id") == "group-detected" or g.get("name") == "감지된 태그"),
            None
        )
        if not detected_group:
            detected_group = {
                "id": "group-detected",
                "name": "감지된 태그",
                "collapsed": False,
                "buttons": []
            }
            # Put at index 0 (top) for immediate visibility
            groups.insert(0, detected_group)

        existing_count = len(detected_group.get("buttons", []))

        for idx, tag_str in enumerate(discovered_tags):
            color_hex, _ = PRESET_COLORS[(existing_count + idx) % len(PRESET_COLORS)]
            spec = parse_tag_definition(tag_str)
            new_btn = {
                "id": str(uuid.uuid4()),
                "description": "파일에서 감지된 태그",
                "bg_color": color_hex,
                "text_color": "#0f172a",
            }
            new_btn.update(spec)
            detected_group.setdefault("buttons", []).append(new_btn)

        self._save_config()
        self._refresh_groups()
        QToolTip.showText(QCursor.pos(), f"파일에서 새 태그 감지: {', '.join(discovered_tags)}", self)

    def _clear_active_file(self):
        self.active_file_paths = []
        self._update_tag_buttons_highlight()

    def _update_tag_buttons_highlight(self):
        valid_paths = [p for p in self.active_file_paths if os.path.exists(p)]
        if valid_paths:
            self.active_file_paths = valid_paths
            file_tags_list = [
                extract_tags_and_base(os.path.splitext(os.path.basename(p))[0])[1]
                for p in valid_paths
            ]
            total = len(valid_paths)

            # Highlight matching buttons ('on' if all have tag, 'partial' if some have tag, 'off' if none)
            for btn in self.all_tag_buttons:
                match_count = sum(1 for tags in file_tags_list if is_tag_in_tags(tags, btn.data))
                if match_count == total:
                    btn.set_tag_state("on")
                elif match_count > 0:
                    btn.set_tag_state("partial")
                else:
                    btn.set_tag_state("off")

            # Update active file bar
            eff = self.get_effective_theme()
            if total == 1:
                filename = os.path.basename(valid_paths[0])
                self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("file", theme=eff, size=14))
                self.lbl_active_file.setText(filename)
                self.lbl_active_file.setToolTip(f"현재 편집 중: {valid_paths[0]}\n태그 버튼을 클릭하여 추가/제거하세요.")
                self.setWindowTitle(f"Easy Tagger - [{filename}]")
            else:
                first_name = os.path.basename(valid_paths[0])
                self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("files", theme=eff, size=14))
                self.lbl_active_file.setText(f"{first_name} 외 {total - 1}개 ({total}개 파일)")
                files_preview = "\n".join(f"• {os.path.basename(p)}" for p in valid_paths[:15])
                if total > 15:
                    files_preview += f"\n... 외 {total - 15}개"
                self.lbl_active_file.setToolTip(
                    f"현재 다중 편집 중 ({total}개 파일):\n{files_preview}\n\n태그 버튼을 클릭하여 일괄 추가/제거하세요."
                )
                self.setWindowTitle(f"Easy Tagger - [{first_name} 외 {total - 1}개]")
            self.btn_close_active_file.setVisible(True)
        else:
            self.active_file_paths = []
            for btn in self.all_tag_buttons:
                btn.set_tag_state("none")

            eff = self.get_effective_theme()
            self.lbl_active_icon.setPixmap(icon_factory.get_pixmap("file", theme=eff, size=14))
            self.lbl_active_file.setText("파일을 드롭하여 태그 편집")
            self.lbl_active_file.setToolTip("윈도우 탐색기에서 파일을 창 또는 버튼으로 드래그 & 드롭하세요.")
            self.btn_close_active_file.setVisible(False)
            self.setWindowTitle("Easy Tagger")

    # ------------------ Tag Button Click (Toggle Tag on Active File(s)) ------------------

    def _on_tag_button_clicked(self, btn: TagButton):
        valid_paths = [p for p in self.active_file_paths if os.path.exists(p)]
        if not valid_paths:
            QToolTip.showText(QCursor.pos(), "먼저 탐색기에서 파일을 드래그 & 드롭해주세요.", self)
            return

        file_tags_list = [
            extract_tags_and_base(os.path.splitext(os.path.basename(p))[0])[1]
            for p in valid_paths
        ]
        all_have_tag = all(is_tag_in_tags(tags, btn.data) for tags in file_tags_list)
        position = self.config.get("position", "suffix")
        style = self.config.get("style", "merged")
        btn_name = get_tag_name(btn.data, "태그")

        if all_have_tag:
            # TOGGLE OFF: Remove this tag from all active files
            spec = parse_tag_definition(get_tag_name(btn.data), fallback_mode=btn.data.get("param_val_mode", ""))
            tag_to_remove = spec["param_key"] if spec["tag_type"] == "param" else spec["name"]

            rename_batch: List[Tuple[str, str]] = []
            updated_paths: List[str] = []
            errors = []

            for fpath in valid_paths:
                folder, filename = os.path.split(fpath)
                basename, ext = os.path.splitext(filename)
                cleaned_base, existing_tags = extract_tags_and_base(basename)
                new_tags = remove_tag_from_tags_list(existing_tags, tag_to_remove)
                new_basename = assemble_filename(cleaned_base, new_tags, position=position, style=style)
                new_filename = f"{new_basename}{ext}"
                new_path = os.path.normpath(os.path.join(folder, new_filename))

                if os.path.normcase(new_path) != os.path.normcase(fpath):
                    if os.path.exists(new_path):
                        errors.append(f"이미 존재하는 파일명이 있습니다: {new_filename}")
                        updated_paths.append(fpath)
                        continue
                    try:
                        os.rename(fpath, new_path)
                        rename_batch.append((fpath, new_path))
                        updated_paths.append(new_path)
                    except Exception as e:
                        errors.append(f"파일 이름 변경 오류 ({filename}): {e}")
                        updated_paths.append(fpath)
                else:
                    updated_paths.append(fpath)

            if rename_batch:
                self.undo_stack.append(rename_batch)
                self._update_action_bar_state()
                self.active_file_paths = updated_paths
                self._update_tag_buttons_highlight()
                if len(rename_batch) == 1:
                    QToolTip.showText(QCursor.pos(), f"[{btn_name}] 제거됨 ➔ '{os.path.basename(rename_batch[0][1])}'", self)
                else:
                    QToolTip.showText(QCursor.pos(), f"[{btn_name}] 일괄 제거됨 ({len(rename_batch)}개 파일)", self)
            if errors:
                ThemedMessageBox.warning(self, "태그 제거 실패", "\n".join(errors[:5]), effective_theme=self.get_effective_theme())
        else:
            # TOGGLE ON (from 'off' or 'partial'): Add this tag to all active files
            tag_to_apply = self._resolve_tag_to_apply(btn.data)
            if not tag_to_apply:
                return
            self._apply_tag_to_files(valid_paths, tag_to_apply)

    def _toggle_pin(self):
        new_state = not self.config.get("always_on_top", False)
        self.config["always_on_top"] = new_state
        self._save_config()
        self._apply_window_flags()
        self._update_action_bar_state()
        self._update_action_bar_icons()
        tip = "항상 위에 고정되었습니다." if new_state else "항상 위에 고정이 해제되었습니다."
        QToolTip.showText(QCursor.pos(), tip, self)

    def _open_settings_dialog(self):
        dlg = SettingsDialog(self.config, effective_theme=self.get_effective_theme(), parent=self)
        if dlg.exec():
            updated = dlg.get_updated_config()
            self.config.update(updated)
            self._save_config()

            self._apply_theme()
            self._apply_window_flags()
            self._refresh_groups()
            QToolTip.showText(QCursor.pos(), "설정이 저장되었습니다.", self)

    def closeEvent(self, event):
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        pos = self.pos()
        self.config["window_x"] = pos.x()
        self.config["window_y"] = pos.y()
        self._save_config()
        super().closeEvent(event)

    # ------------------ Groups & Tag Buttons Management ------------------

    def _refresh_groups(self):
        # Clear existing group widgets and button references
        for gw in self.group_widgets:
            gw.deleteLater()
        self.group_widgets.clear()
        self.all_tag_buttons.clear()

        # Remove stretch if present
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        eff_theme = self.get_effective_theme()
        btn_height = int(self.config.get("button_height", 38))
        groups_data = self.config.get("groups", [])

        for gdata in groups_data:
            gw = GroupWidget(gdata, fixed_height=btn_height, effective_theme=eff_theme, parent=self.groups_container)
            gw.addTagRequested.connect(self._add_tag_to_group)
            gw.renameGroupRequested.connect(self._rename_group)
            gw.deleteGroupRequested.connect(self._delete_group)
            gw.collapseToggled.connect(self._on_group_collapse_toggled)
            gw.groupReorderRequested.connect(self._on_group_reorder)
            gw.tagMovedToGroupRequested.connect(self._on_tag_moved_to_group)

            # Add buttons to group
            for bdata in gdata.get("buttons", []):
                btn = TagButton(bdata, fixed_height=btn_height, effective_theme=eff_theme, parent=gw.body_container)
                btn.filesDropped.connect(self._on_files_dropped_on_button)
                btn.clicked.connect(lambda _, b=btn: self._on_tag_button_clicked(b))
                btn.editRequested.connect(self._on_edit_tag_button)
                btn.duplicateRequested.connect(self._on_duplicate_tag_button)
                btn.deleteRequested.connect(self._on_delete_tag_button)
                btn.tagReorderRequested.connect(self._on_tag_reorder)

                gw.add_tag_button(btn)
                self.all_tag_buttons.append(btn)

            self.groups_layout.addWidget(gw)
            self.group_widgets.append(gw)

        self.groups_layout.addStretch()
        self._update_tag_buttons_highlight()

    def _on_group_collapse_toggled(self, group_id: str, collapsed: bool):
        target = self._find_group(group_id)
        if target is not None:
            target["collapsed"] = collapsed
            self._save_config()

    def _add_new_group(self):
        dlg = GroupDialog(
            title="새 그룹 추가",
            initial_name="",
            effective_theme=self.get_effective_theme(),
            parent=self
        )
        if dlg.exec():
            name = dlg.get_group_name()
            if name:
                new_group = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "collapsed": False,
                    "buttons": [],
                }
                self.config.setdefault("groups", []).append(new_group)
                self._save_config()
                self._refresh_groups()
                QToolTip.showText(QCursor.pos(), f"새 그룹 '{name}' 생성됨", self)

    def _rename_group(self, group_id: str):
        target = self._find_group(group_id)
        if not target:
            return

        dlg = GroupDialog(
            title="그룹 이름 변경",
            initial_name=target.get("name", ""),
            effective_theme=self.get_effective_theme(),
            parent=self
        )
        if dlg.exec():
            name = dlg.get_group_name()
            if name:
                target["name"] = name
                self._save_config()
                self._refresh_groups()
                QToolTip.showText(QCursor.pos(), f"그룹 이름이 '{name}'(으)로 변경됨", self)

    def _delete_group(self, group_id: str):
        target = self._find_group(group_id)
        if not target:
            return

        if ThemedMessageBox.question(
            self,
            "그룹 삭제",
            f"'{target.get('name')}' 그룹과 포함된 모든 태그를 삭제하시겠습니까?",
            effective_theme=self.get_effective_theme()
        ):
            self.config["groups"] = [g for g in self.config.get("groups", []) if g.get("id") != group_id]
            self._save_config()
            self._refresh_groups()
            QToolTip.showText(QCursor.pos(), f"그룹 '{target.get('name')}' 삭제됨", self)

    def _add_tag_to_group(self, group_id: str):
        target_group = self._find_group(group_id)
        if not target_group:
            return

        btn_height = int(self.config.get("button_height", 38))
        dlg = TagDialog(button_height=btn_height, effective_theme=self.get_effective_theme(), parent=self)
        if dlg.exec():
            new_data = dlg.get_data()
            target_group.setdefault("buttons", []).append(new_data)
            self._save_config()
            self._refresh_groups()
            tag_name = get_tag_name(new_data, "태그")
            QToolTip.showText(QCursor.pos(), f"'{target_group['name']}'에 '{tag_name}' 태그 추가됨", self)

    def _on_edit_tag_button(self, btn_data: dict):
        btn_height = int(self.config.get("button_height", 38))
        dlg = TagDialog(initial_data=btn_data, button_height=btn_height, effective_theme=self.get_effective_theme(), parent=self)
        if dlg.exec():
            updated = dlg.get_data()
            group, old_btn = self._find_tag_and_group(updated.get("id", ""))
            if group and old_btn:
                buttons = group.get("buttons", [])
                idx = buttons.index(old_btn)
                buttons[idx] = updated
            self._save_config()
            self._refresh_groups()
            tag_name = get_tag_name(updated, "태그")
            QToolTip.showText(QCursor.pos(), f"태그 '{tag_name}' 수정됨", self)

    def _on_duplicate_tag_button(self, btn_data: dict):
        dup = dict(btn_data)
        dup["id"] = str(uuid.uuid4())
        base_name = get_tag_name(dup, "태그")
        new_name = f"{base_name} (복사)"
        dup["name"] = new_name
        dup["label"] = new_name
        dup["tag_text"] = new_name

        group, orig_btn = self._find_tag_and_group(btn_data.get("id", ""))
        if group and orig_btn:
            buttons = group.get("buttons", [])
            idx = buttons.index(orig_btn)
            buttons.insert(idx + 1, dup)

        self._save_config()
        self._refresh_groups()
        QToolTip.showText(QCursor.pos(), f"태그 '{dup['name']}' 복제됨", self)

    def _on_delete_tag_button(self, btn_data: dict):
        target_name = get_tag_name(btn_data, "태그")
        if ThemedMessageBox.question(
            self,
            "태그 삭제",
            f"'{target_name}' 태그를 삭제하시겠습니까?",
            effective_theme=self.get_effective_theme()
        ):
            for g in self.config.get("groups", []):
                g["buttons"] = [b for b in g.get("buttons", []) if b.get("id") != btn_data.get("id")]
            self._save_config()
            self._refresh_groups()
            QToolTip.showText(QCursor.pos(), f"태그 '{target_name}' 삭제됨", self)

    # ------------------ Tag & Group Reordering & Moving via Ctrl+Drag ------------------

    def _on_tag_reorder(self, source_tag_id: str, target_tag_id: str, drop_pos: str):
        if not source_tag_id or not target_tag_id or source_tag_id == target_tag_id:
            return

        source_group, source_btn = self._find_tag_and_group(source_tag_id)
        target_group, target_btn = self._find_tag_and_group(target_tag_id)
        if not source_btn or not target_btn or not source_group or not target_group:
            return

        source_group["buttons"].remove(source_btn)
        target_idx = target_group["buttons"].index(target_btn)
        insert_idx = target_idx if drop_pos == "before" else target_idx + 1
        target_group["buttons"].insert(insert_idx, source_btn)

        self._save_config()
        self._refresh_groups()

        tag_name = get_tag_name(source_btn, "태그")
        QToolTip.showText(QCursor.pos(), f"태그 '{tag_name}' 순서 변경 완료", self)

    def _on_tag_moved_to_group(self, source_tag_id: str, target_group_id: str):
        if not source_tag_id or not target_group_id:
            return

        source_group, source_btn = self._find_tag_and_group(source_tag_id)
        target_group = self._find_group(target_group_id)
        if not source_btn or not source_group or not target_group or source_group == target_group:
            return

        source_group["buttons"].remove(source_btn)
        target_group.setdefault("buttons", []).append(source_btn)

        self._save_config()
        self._refresh_groups()

        tag_name = get_tag_name(source_btn, "태그")
        group_name = target_group.get("name", "그룹")
        QToolTip.showText(QCursor.pos(), f"태그 '{tag_name}' ➔ '{group_name}' 이동 완료", self)

    def _on_group_reorder(self, source_group_id: str, target_group_id: str, drop_pos: str):
        if not source_group_id or not target_group_id or source_group_id == target_group_id:
            return

        groups = self.config.get("groups", [])
        source_group = self._find_group(source_group_id)
        target_group = self._find_group(target_group_id)
        if not source_group or not target_group:
            return

        groups.remove(source_group)
        target_idx = groups.index(target_group)
        insert_idx = target_idx if drop_pos == "before" else target_idx + 1
        groups.insert(insert_idx, source_group)

        self._save_config()
        self._refresh_groups()

        source_name = source_group.get("name", "그룹")
        QToolTip.showText(QCursor.pos(), f"그룹 '{source_name}' 순서 변경 완료", self)

    # ------------------ Tag Application via Drop ------------------

    def _on_files_dropped_on_button(self, btn_data: dict, file_paths: List[str]):
        # Activate app window immediately after drop so modal dialog gains active window focus
        self.activateWindow()
        self.raise_()
        tag_to_apply = self._resolve_tag_to_apply(btn_data)
        if not tag_to_apply:
            return
        self._apply_tag_to_files(file_paths, tag_to_apply)

    def _apply_tag_to_files(self, file_paths: List[str], tag_to_apply: str):
        # Auto-detect any unknown tags in dropped files and register them
        self._detect_and_register_tags_from_files(file_paths)

        position = self.config.get("position", "suffix")
        style = self.config.get("style", "merged")

        rename_batch: List[Tuple[str, str]] = []
        resulting_paths: List[str] = []
        errors = []
        already_tagged_count = 0

        for raw_fpath in file_paths:
            fpath = os.path.normpath(os.path.abspath(raw_fpath))
            if not os.path.exists(fpath):
                errors.append(f"파일 없음: {raw_fpath}")
                continue

            folder, filename = os.path.split(fpath)
            basename, ext = os.path.splitext(filename)

            cleaned_base, existing_tags = extract_tags_and_base(basename)
            new_tags = apply_tag_to_tags_list(existing_tags, tag_to_apply)
            new_basename = assemble_filename(cleaned_base, new_tags, position=position, style=style)
            new_filename = f"{new_basename}{ext}"
            new_path = os.path.normpath(os.path.join(folder, new_filename))

            # Check if file is already identical in name/path (already has this tag)
            is_same = (os.path.normcase(new_path) == os.path.normcase(fpath))
            if not is_same and os.path.exists(new_path):
                try:
                    if os.path.samefile(fpath, new_path):
                        is_same = True
                except Exception:
                    pass

            if is_same:
                already_tagged_count += 1
                resulting_paths.append(fpath)
                continue

            if os.path.exists(new_path):
                errors.append(f"이미 존재하는 파일명: {new_filename}")
                resulting_paths.append(fpath)
                continue

            try:
                os.rename(fpath, new_path)
                rename_batch.append((fpath, new_path))
                resulting_paths.append(new_path)
            except Exception as e:
                errors.append(f"변경 실패 ({os.path.basename(fpath)}): {e}")
                resulting_paths.append(fpath)

        if rename_batch:
            self.undo_stack.append(rename_batch)
            self._update_action_bar_state()
            first_old = os.path.basename(rename_batch[0][0])
            first_new = os.path.basename(rename_batch[0][1])
            count = len(rename_batch)

            if count == 1:
                msg = f"'{first_old}' ➔ '{first_new}'"
            else:
                msg = f"'{first_old}' 외 {count - 1}개 완료"
            QToolTip.showText(QCursor.pos(), msg, self)
        elif already_tagged_count > 0 and not errors:
            target_name = os.path.basename(resulting_paths[-1]) if resulting_paths else "파일"
            QToolTip.showText(QCursor.pos(), f"이미 [{tag_to_apply}] 태그가 적용되어 있습니다. ('{target_name}')", self)

        # Keep all manipulated files as active files for continued batch editing
        if resulting_paths:
            self._set_active_files(resulting_paths)

        if errors:
            ThemedMessageBox.warning(self, "일부 파일 처리 오류", "\n".join(errors[:5]), effective_theme=self.get_effective_theme())

    # ------------------ Undo Logic ------------------

    def undo_last_action(self):
        if not self.undo_stack:
            QToolTip.showText(QCursor.pos(), "실행 취소할 작업이 없습니다.", self)
            return

        last_batch = self.undo_stack.pop()
        self._update_action_bar_state()
        reverted_count = 0
        errors = []
        path_map = {}

        reverted_targets: List[str] = []
        for old_path, new_path in reversed(last_batch):
            if os.path.exists(new_path):
                try:
                    os.rename(new_path, old_path)
                    reverted_count += 1
                    reverted_targets.append(old_path)
                    path_map[os.path.normcase(new_path)] = old_path
                except Exception as e:
                    errors.append(f"복원 실패: {e}")
            else:
                errors.append(f"파일 없음: {new_path}")

        if self.active_file_paths:
            updated_active = [
                path_map.get(os.path.normcase(p), p)
                for p in self.active_file_paths
            ]
            self._set_active_files(updated_active)
        elif reverted_targets:
            self._set_active_files(list(reversed(reverted_targets)))
        else:
            self._update_tag_buttons_highlight()

        if reverted_count > 0:
            QToolTip.showText(QCursor.pos(), f"{reverted_count}개 파일 복원 완료", self)
        if errors:
            ThemedMessageBox.warning(self, "실행 취소 오류", "\n".join(errors[:5]), effective_theme=self.get_effective_theme())
