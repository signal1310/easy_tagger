import os
from typing import List, Optional

from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip

from src.core.tag_parser import get_tag_name, is_tag_in_tags, parse_tag_definition
from src.services.file_rename_service import (
    apply_tag_batch,
    compute_button_tag_state,
    extract_files_tags,
    normalize_existing_paths,
    remove_tag_batch,
)
from src.services.tag_detection_service import detect_and_register_unknown_tags
from src.services.undo_service import UndoService
from src.ui.dialogs.message_box import ThemedMessageBox
from src.ui.dialogs.prompt_dialog import ThemedPromptDialog
from src.ui.widgets.tag_button import TagButton


class FileController:
    """Coordinates active file selection, batch tag toggling/application, tag detection, and undo."""

    def __init__(self, window, undo_service: UndoService):
        self.win = window
        self.undo_service = undo_service
        self.active_file_paths: List[str] = []

    def set_active_files(self, file_paths: List[str]) -> None:
        valid_paths = normalize_existing_paths(file_paths)
        if not valid_paths:
            self.clear_active_files()
            return
        self.active_file_paths = valid_paths
        self._detect_unknown_tags(valid_paths)
        self.update_highlights()

    def clear_active_files(self) -> None:
        self.active_file_paths = []
        self.update_highlights()

    def _detect_unknown_tags(self, file_paths: List[str]) -> None:
        discovered = detect_and_register_unknown_tags(self.win.config, file_paths)
        if discovered:
            self.win.save_config()
            self.win.refresh_groups()
            QToolTip.showText(QCursor.pos(), f"파일에서 새 태그 감지: {', '.join(discovered)}", self.win)

    def update_highlights(self) -> None:
        valid_paths = [p for p in self.active_file_paths if os.path.exists(p)]
        self.active_file_paths = valid_paths
        file_tags_list = extract_files_tags(valid_paths) if valid_paths else []
        for btn in self.win.all_tag_buttons:
            btn.set_tag_state(compute_button_tag_state(file_tags_list, btn.data))
        self.win.setWindowTitle(self.win.action_bar.update_active_files_display(valid_paths, self.win.get_effective_theme()))

    def resolve_tag_to_apply(self, btn_data: dict) -> Optional[str]:
        spec = parse_tag_definition(get_tag_name(btn_data), fallback_mode=btn_data.get("param_val_mode", ""))
        if spec["tag_type"] == "param" and spec["param_val_mode"] == "prompt":
            key = spec["param_key"]
            dlg = ThemedPromptDialog(
                "속성값 입력", f"[{key} <값>] 에 들어갈 값을 입력하세요:\n(예: 60, 4K, 5)",
                initial_text=btn_data.get("param_val", ""), effective_theme=self.win.get_effective_theme(), parent=self.win,
            )
            return f"{key} {dlg.get_text()}" if (dlg.exec() and dlg.get_text()) else None
        return spec["name"] if spec["name"] else None

    def on_tag_button_clicked(self, btn: TagButton) -> None:
        valid_paths = [p for p in self.active_file_paths if os.path.exists(p)]
        if not valid_paths:
            QToolTip.showText(QCursor.pos(), "먼저 탐색기에서 파일을 드래그 & 드롭해주세요.", self.win)
            return

        if all(is_tag_in_tags(tags, btn.data) for tags in extract_files_tags(valid_paths)):
            spec = parse_tag_definition(get_tag_name(btn.data), fallback_mode=btn.data.get("param_val_mode", ""))
            tag_to_remove = spec["param_key"] if spec["tag_type"] == "param" else spec["name"]
            res = remove_tag_batch(
                valid_paths, tag_to_remove, self.win.config.get("position", "suffix"), self.win.config.get("style", "merged")
            )
            if res.rename_batch:
                self.undo_service.push(res.rename_batch)
                self.active_file_paths = res.resulting_paths
                self.update_highlights()
                bname = get_tag_name(btn.data, "태그")
                msg = f"[{bname}] 제거됨 ➔ '{os.path.basename(res.rename_batch[0][1])}'" if len(res.rename_batch) == 1 else f"[{bname}] 일괄 제거됨 ({len(res.rename_batch)}개 파일)"
                QToolTip.showText(QCursor.pos(), msg, self.win)
            if res.errors:
                ThemedMessageBox.warning(self.win, "태그 제거 실패", "\n".join(res.errors[:5]), self.win.get_effective_theme())
            return

        tag_to_apply = self.resolve_tag_to_apply(btn.data)
        if tag_to_apply:
            self.apply_tag_to_files(valid_paths, tag_to_apply)

    def on_files_dropped_on_button(self, btn_data: dict, file_paths: List[str]) -> None:
        self.win.activateWindow()
        self.win.raise_()
        tag_to_apply = self.resolve_tag_to_apply(btn_data)
        if tag_to_apply:
            self.apply_tag_to_files(file_paths, tag_to_apply)

    def apply_tag_to_files(self, file_paths: List[str], tag_to_apply: str) -> None:
        self._detect_unknown_tags(file_paths)
        res = apply_tag_batch(
            file_paths, tag_to_apply, self.win.config.get("position", "suffix"), self.win.config.get("style", "merged")
        )
        if res.rename_batch:
            self.undo_service.push(res.rename_batch)
            old_n, new_n = os.path.basename(res.rename_batch[0][0]), os.path.basename(res.rename_batch[0][1])
            msg = f"'{old_n}' ➔ '{new_n}'" if len(res.rename_batch) == 1 else f"'{old_n}' 외 {len(res.rename_batch) - 1}개 완료"
            QToolTip.showText(QCursor.pos(), msg, self.win)
        elif res.already_tagged_count > 0 and not res.errors:
            target_name = os.path.basename(res.resulting_paths[-1]) if res.resulting_paths else "파일"
            QToolTip.showText(QCursor.pos(), f"이미 [{tag_to_apply}] 태그가 적용되어 있습니다. ('{target_name}')", self.win)

        if res.resulting_paths:
            self.set_active_files(res.resulting_paths)
        if res.errors:
            ThemedMessageBox.warning(self.win, "일부 파일 처리 오류", "\n".join(res.errors[:5]), self.win.get_effective_theme())

    def undo_last_action(self) -> None:
        res = self.undo_service.undo_last()
        if res is None:
            QToolTip.showText(QCursor.pos(), "실행 취소할 작업이 없습니다.", self.win)
            return

        if self.active_file_paths:
            self.set_active_files([res.path_map.get(os.path.normcase(p), p) for p in self.active_file_paths])
        elif res.reverted_targets:
            self.set_active_files(list(reversed(res.reverted_targets)))
        else:
            self.update_highlights()

        if res.reverted_count > 0:
            QToolTip.showText(QCursor.pos(), f"{res.reverted_count}개 파일 복원 완료", self.win)
        if res.errors:
            ThemedMessageBox.warning(self.win, "실행 취소 오류", "\n".join(res.errors[:5]), self.win.get_effective_theme())
