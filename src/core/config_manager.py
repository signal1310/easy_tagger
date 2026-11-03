import copy
import json
import os
import uuid
from typing import Any, Dict, Optional

from src.core.defaults import get_default_config
from src.core.paths import CONFIG_FILE
from src.core.tag_parser import parse_tag_definition


def load_default_config() -> Dict[str, Any]:
    """Returns a deep copy of the built-in default application configuration."""
    return copy.deepcopy(get_default_config())


def normalize_tag_data(btn: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures button name is normalized (no outer brackets) and stripped of duplicate legacy keys."""
    raw_name = btn.get("name")
    if not raw_name:
        raw_name = btn.get("tag_text") or btn.get("label", "태그")
        if not btn.get("description") and btn.get("label") and btn.get("label") != raw_name:
            btn["description"] = btn.get("label", "")

    spec = parse_tag_definition(raw_name, fallback_mode=btn.get("param_val_mode", ""))
    btn.update(spec)
    btn.pop("label", None)
    btn.pop("tag_text", None)

    if spec["tag_type"] == "normal":
        for k in ("param_key", "param_val_mode", "param_val"):
            btn.pop(k, None)

    if "description" not in btn:
        btn["description"] = ""

    return btn


def is_ephemeral_group(group: Dict[str, Any]) -> bool:
    """Returns True if the group is temporary/detected and should not persist across sessions."""
    return group.get("id") == "group-detected" or group.get("name") == "감지된 태그"


def load_config(file_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads user configuration from disk, migrating legacy fields and filling defaults."""
    target_path = file_path or CONFIG_FILE
    default_config = load_default_config()

    if not os.path.exists(target_path):
        save_config(default_config, target_path)
        return copy.deepcopy(default_config)

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "groups" not in data or not isinstance(data["groups"], list):
            if "buttons" in data and isinstance(data["buttons"], list):
                data["groups"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "기본 그룹",
                        "collapsed": False,
                        "buttons": data["buttons"],
                    }
                ]
            else:
                data["groups"] = copy.deepcopy(default_config.get("groups", []))

        for k, v in default_config.items():
            if k not in data:
                data[k] = copy.deepcopy(v)

        data["groups"] = [g for g in data.get("groups", []) if not is_ephemeral_group(g)]
        for g in data.get("groups", []):
            for b in g.get("buttons", []):
                normalize_tag_data(b)

        return data
    except Exception as e:
        print(f"Error loading config: {e}. Falling back to default template.")
        return copy.deepcopy(default_config)


def save_config(config_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
    """Persists configuration to disk while stripping ephemeral session-only groups."""
    target_path = file_path or CONFIG_FILE
    try:
        data_to_save = copy.deepcopy(config_data)
        if "groups" in data_to_save and isinstance(data_to_save["groups"], list):
            data_to_save["groups"] = [
                g for g in data_to_save["groups"] if not is_ephemeral_group(g)
            ]
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

