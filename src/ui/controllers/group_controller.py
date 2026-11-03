from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip

from src.core.tag_parser import get_tag_name
from src.services.group_model_service import GroupModelService
from src.ui.dialogs.group_dialog import GroupDialog
from src.ui.dialogs.message_box import ThemedMessageBox
from src.ui.dialogs.tag_dialog import TagDialog


class GroupController:
    """Coordinates group & tag CRUD dialogs and drag-reordering with GroupModelService."""

    def __init__(self, window):
        self.win = window

    def on_group_collapse_toggled(self, group_id: str, collapsed: bool) -> None:
        if GroupModelService.set_group_collapsed(self.win.config, group_id, collapsed):
            self.win.save_config()

    def add_new_group(self) -> None:
        dlg = GroupDialog(
            title="새 그룹 추가",
            initial_name="",
            effective_theme=self.win.get_effective_theme(),
            parent=self.win,
        )
        if dlg.exec() and dlg.get_group_name():
            name = dlg.get_group_name()
            GroupModelService.add_group(self.win.config, name)
            self._commit_and_refresh(f"새 그룹 '{name}' 생성됨")

    def rename_group(self, group_id: str) -> None:
        target = GroupModelService.find_group(self.win.config, group_id)
        if not target:
            return
        dlg = GroupDialog(
            title="그룹 이름 변경",
            initial_name=target.get("name", ""),
            effective_theme=self.win.get_effective_theme(),
            parent=self.win,
        )
        if dlg.exec() and dlg.get_group_name():
            name = dlg.get_group_name()
            if GroupModelService.rename_group(self.win.config, group_id, name):
                self._commit_and_refresh(f"그룹 이름이 '{name}'(으)로 변경됨")

    def delete_group(self, group_id: str) -> None:
        target = GroupModelService.find_group(self.win.config, group_id)
        if not target:
            return
        if ThemedMessageBox.question(
            self.win,
            "그룹 삭제",
            f"'{target.get('name')}' 그룹과 포함된 모든 태그를 삭제하시겠습니까?",
            effective_theme=self.win.get_effective_theme(),
        ):
            deleted_name = GroupModelService.delete_group(self.win.config, group_id)
            if deleted_name:
                self._commit_and_refresh(f"그룹 '{deleted_name}' 삭제됨")

    def add_tag_to_group(self, group_id: str) -> None:
        target_group = GroupModelService.find_group(self.win.config, group_id)
        if not target_group:
            return
        btn_height = int(self.win.config.get("button_height", 38))
        dlg = TagDialog(button_height=btn_height, effective_theme=self.win.get_effective_theme(), parent=self.win)
        if dlg.exec():
            new_data = dlg.get_data()
            group_name = GroupModelService.add_tag(self.win.config, group_id, new_data)
            if group_name:
                tag_name = get_tag_name(new_data, "태그")
                self._commit_and_refresh(f"'{group_name}'에 '{tag_name}' 태그 추가됨")

    def edit_tag_button(self, btn_data: dict) -> None:
        btn_height = int(self.win.config.get("button_height", 38))
        dlg = TagDialog(
            initial_data=btn_data,
            button_height=btn_height,
            effective_theme=self.win.get_effective_theme(),
            parent=self.win,
        )
        if dlg.exec():
            updated = dlg.get_data()
            GroupModelService.update_tag(self.win.config, updated)
            self._commit_and_refresh(f"태그 '{get_tag_name(updated, '태그')}' 수정됨")

    def duplicate_tag_button(self, btn_data: dict) -> None:
        dup = GroupModelService.duplicate_tag(self.win.config, btn_data)
        if dup:
            self._commit_and_refresh(f"태그 '{dup['name']}' 복제됨")

    def delete_tag_button(self, btn_data: dict) -> None:
        target_name = get_tag_name(btn_data, "태그")
        if ThemedMessageBox.question(
            self.win,
            "태그 삭제",
            f"'{target_name}' 태그를 삭제하시겠습니까?",
            effective_theme=self.win.get_effective_theme(),
        ):
            GroupModelService.delete_tag(self.win.config, btn_data.get("id", ""))
            self._commit_and_refresh(f"태그 '{target_name}' 삭제됨")

    def reorder_tag(self, source_tag_id: str, target_tag_id: str, drop_pos: str) -> None:
        tag_name = GroupModelService.reorder_tag(self.win.config, source_tag_id, target_tag_id, drop_pos)
        if tag_name:
            self._commit_and_refresh(f"태그 '{tag_name}' 순서 변경 완료")

    def move_tag_to_group(self, source_tag_id: str, target_group_id: str) -> None:
        moved = GroupModelService.move_tag_to_group(self.win.config, source_tag_id, target_group_id)
        if moved:
            tag_name, group_name = moved
            self._commit_and_refresh(f"태그 '{tag_name}' ➔ '{group_name}' 이동 완료")

    def reorder_group(self, source_group_id: str, target_group_id: str, drop_pos: str) -> None:
        group_name = GroupModelService.reorder_group(self.win.config, source_group_id, target_group_id, drop_pos)
        if group_name:
            self._commit_and_refresh(f"그룹 '{group_name}' 순서 변경 완료")

    def _commit_and_refresh(self, tooltip_msg: str) -> None:
        self.win.save_config()
        self.win.refresh_groups()
        QToolTip.showText(QCursor.pos(), tooltip_msg, self.win)

