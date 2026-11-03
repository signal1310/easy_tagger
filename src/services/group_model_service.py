import uuid
from typing import Any, Dict, Optional, Tuple

from src.core.tag_parser import get_tag_name


class GroupModelService:
    """Pure domain service for CRUD and drag-reorder operations on groups and tag buttons."""

    @staticmethod
    def find_group(config: Dict[str, Any], group_id: str) -> Optional[Dict[str, Any]]:
        return next((g for g in config.get("groups", []) if g.get("id") == group_id), None)

    @staticmethod
    def find_tag_and_group(
        config: Dict[str, Any], tag_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        for g in config.get("groups", []):
            for b in g.get("buttons", []):
                if b.get("id") == tag_id:
                    return g, b
        return None, None

    @staticmethod
    def add_group(config: Dict[str, Any], name: str) -> Dict[str, Any]:
        new_group = {
            "id": str(uuid.uuid4()),
            "name": name,
            "collapsed": False,
            "buttons": [],
        }
        config.setdefault("groups", []).append(new_group)
        return new_group

    @classmethod
    def rename_group(cls, config: Dict[str, Any], group_id: str, new_name: str) -> bool:
        target = cls.find_group(config, group_id)
        if not target or not new_name:
            return False
        target["name"] = new_name
        return True

    @classmethod
    def delete_group(cls, config: Dict[str, Any], group_id: str) -> Optional[str]:
        target = cls.find_group(config, group_id)
        if not target:
            return None
        name = target.get("name", "그룹")
        config["groups"] = [g for g in config.get("groups", []) if g.get("id") != group_id]
        return name

    @classmethod
    def set_group_collapsed(cls, config: Dict[str, Any], group_id: str, collapsed: bool) -> bool:
        target = cls.find_group(config, group_id)
        if target is None:
            return False
        target["collapsed"] = collapsed
        return True

    @classmethod
    def add_tag(cls, config: Dict[str, Any], group_id: str, tag_data: Dict[str, Any]) -> Optional[str]:
        group = cls.find_group(config, group_id)
        if not group:
            return None
        group.setdefault("buttons", []).append(tag_data)
        return group.get("name", "그룹")

    @classmethod
    def update_tag(cls, config: Dict[str, Any], updated_data: Dict[str, Any]) -> bool:
        group, old_btn = cls.find_tag_and_group(config, updated_data.get("id", ""))
        if not group or not old_btn:
            return False
        buttons = group.get("buttons", [])
        buttons[buttons.index(old_btn)] = updated_data
        return True

    @classmethod
    def duplicate_tag(cls, config: Dict[str, Any], btn_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        group, orig_btn = cls.find_tag_and_group(config, btn_data.get("id", ""))
        if not group or not orig_btn:
            return None
        dup = dict(btn_data)
        dup["id"] = str(uuid.uuid4())
        dup["name"] = f"{get_tag_name(dup, '태그')} (복사)"
        dup.pop("label", None)
        dup.pop("tag_text", None)

        buttons = group.get("buttons", [])
        buttons.insert(buttons.index(orig_btn) + 1, dup)
        return dup

    @staticmethod
    def delete_tag(config: Dict[str, Any], tag_id: str) -> None:
        for g in config.get("groups", []):
            g["buttons"] = [b for b in g.get("buttons", []) if b.get("id") != tag_id]

    @classmethod
    def reorder_tag(
        cls, config: Dict[str, Any], source_tag_id: str, target_tag_id: str, drop_pos: str
    ) -> Optional[str]:
        if not source_tag_id or not target_tag_id or source_tag_id == target_tag_id:
            return None
        src_group, src_btn = cls.find_tag_and_group(config, source_tag_id)
        dst_group, dst_btn = cls.find_tag_and_group(config, target_tag_id)
        if not src_btn or not dst_btn or not src_group or not dst_group:
            return None

        src_group["buttons"].remove(src_btn)
        target_idx = dst_group["buttons"].index(dst_btn)
        insert_idx = target_idx if drop_pos == "before" else target_idx + 1
        dst_group["buttons"].insert(insert_idx, src_btn)
        return get_tag_name(src_btn, "태그")

    @classmethod
    def reorder_tag_to_index(
        cls, config: Dict[str, Any], source_tag_id: str, target_group_id: str, target_index: int
    ) -> Optional[str]:
        if not source_tag_id or not target_group_id:
            return None
        src_group, src_btn = cls.find_tag_and_group(config, source_tag_id)
        dst_group = cls.find_group(config, target_group_id)
        if not src_btn or not src_group or not dst_group:
            return None

        src_group["buttons"].remove(src_btn)
        btns = dst_group.setdefault("buttons", [])
        idx = max(0, min(target_index, len(btns)))
        btns.insert(idx, src_btn)
        return get_tag_name(src_btn, "태그")

    @classmethod
    def move_tag_to_group(
        cls, config: Dict[str, Any], source_tag_id: str, target_group_id: str
    ) -> Optional[Tuple[str, str]]:
        if not source_tag_id or not target_group_id:
            return None
        src_group, src_btn = cls.find_tag_and_group(config, source_tag_id)
        dst_group = cls.find_group(config, target_group_id)
        if not src_btn or not src_group or not dst_group or src_group == dst_group:
            return None

        src_group["buttons"].remove(src_btn)
        dst_group.setdefault("buttons", []).append(src_btn)
        return get_tag_name(src_btn, "태그"), dst_group.get("name", "그룹")

    @classmethod
    def reorder_group(
        cls, config: Dict[str, Any], source_group_id: str, target_group_id: str, drop_pos: str
    ) -> Optional[str]:
        if not source_group_id or not target_group_id or source_group_id == target_group_id:
            return None
        groups = config.get("groups", [])
        src_group = cls.find_group(config, source_group_id)
        dst_group = cls.find_group(config, target_group_id)
        if not src_group or not dst_group:
            return None

        groups.remove(src_group)
        target_idx = groups.index(dst_group)
        insert_idx = target_idx if drop_pos == "before" else target_idx + 1
        groups.insert(insert_idx, src_group)
        return src_group.get("name", "그룹")

