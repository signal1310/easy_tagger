import copy
import json
import os
import uuid
from typing import Dict, Any, List, Optional
from tag_parser import parse_tag_definition

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = "config.json"
CONFIG_INIT_FILE = "config.init.json"


def get_init_config_path(custom_path: Optional[str] = None) -> str:
    """Returns the absolute path to config.init.json."""
    target = custom_path or CONFIG_INIT_FILE
    if os.path.exists(target):
        return os.path.abspath(target)
    if not custom_path:
        base_init = os.path.join(BASE_DIR, "config.init.json")
        if os.path.exists(base_init):
            return base_init
    return os.path.abspath(target)


def get_fallback_template_data() -> Dict[str, Any]:
    """Fallback starter configuration if config.init.json is deleted or not found."""
    return {
        "theme": "system",
        "position": "suffix",
        "style": "merged",
        "button_height": 38,
        "always_on_top": False,
        "window_width": 420,
        "window_height": 360,
        "groups": [
            {
                "id": "group-general",
                "name": "기본 태그",
                "collapsed": False,
                "buttons": [
                    {
                        "id": "btn-general-1",
                        "name": "여행",
                        "label": "여행",
                        "tag_text": "여행",
                        "description": "여행 및 일상 브이로그 영상",
                        "tag_type": "normal",
                        "bg_color": "#bae6fd",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-general-2",
                        "name": "하이라이트",
                        "label": "하이라이트",
                        "tag_text": "하이라이트",
                        "description": "주요 하이라이트 및 명장면",
                        "tag_type": "normal",
                        "bg_color": "#fed7aa",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-general-3",
                        "name": "완료",
                        "label": "완료",
                        "tag_text": "완료",
                        "description": "편집 및 검토 완료된 영상",
                        "tag_type": "normal",
                        "bg_color": "#cbd5e1",
                        "text_color": "#0f172a"
                    }
                ]
            },
            {
                "id": "group-props",
                "name": "속성 / 스펙",
                "collapsed": False,
                "buttons": [
                    {
                        "id": "btn-props-1",
                        "name": "4K",
                        "label": "4K",
                        "tag_text": "4K",
                        "description": "4K UHD 초고화질 해상도",
                        "tag_type": "normal",
                        "bg_color": "#a7f3d0",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-props-2",
                        "name": "-fps 60",
                        "label": "-fps 60",
                        "tag_text": "-fps 60",
                        "description": "초당 60 프레임 고주사율 영상",
                        "tag_type": "param",
                        "param_key": "-fps",
                        "param_val_mode": "fixed",
                        "param_val": "60",
                        "bg_color": "#ddd6fe",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-props-3",
                        "name": "-score ?",
                        "label": "-score ?",
                        "tag_text": "-score ?",
                        "description": "영상 점수 및 평점 입력",
                        "tag_type": "param",
                        "param_key": "-score",
                        "param_val_mode": "prompt",
                        "param_val": "",
                        "bg_color": "#fbcfe8",
                        "text_color": "#0f172a"
                    }
                ]
            }
        ]
    }


def load_default_config(init_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads default configuration from config.init.json, automatically recreating it if missing."""
    resolved_init_path = get_init_config_path(init_path)
    if os.path.exists(resolved_init_path):
        try:
            with open(resolved_init_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {resolved_init_path}: {e}")

    # Self-healing: if config.init.json is missing or corrupted, recreate it automatically!
    fallback = get_fallback_template_data()
    try:
        with open(resolved_init_path, "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error recreating {resolved_init_path}: {e}")
    return fallback


def normalize_tag_data(b: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures button label/name is normalized (no outer brackets) and synced with param attributes."""
    raw_name = b.get("name")
    if not raw_name:
        raw_name = b.get("tag_text") or b.get("label", "태그")
        if not b.get("description") and b.get("label") and b.get("label") != raw_name:
            b["description"] = b.get("label", "")

    spec = parse_tag_definition(raw_name, fallback_mode=b.get("param_val_mode", ""))
    b.update(spec)
    if spec["tag_type"] == "normal":
        for k in ("param_key", "param_val_mode", "param_val"):
            b.pop(k, None)

    if "description" not in b:
        b["description"] = ""

    return b


def is_ephemeral_group(group: Dict[str, Any]) -> bool:
    """Returns True if the group is temporary/detected and should not persist across sessions."""
    return group.get("id") == "group-detected" or group.get("name") == "감지된 태그"


def load_config(file_path: str = CONFIG_FILE) -> Dict[str, Any]:
    default_config = load_default_config()

    if not os.path.exists(file_path):
        # Generate config.json directly from config.init.json template
        save_config(default_config, file_path)
        return copy.deepcopy(default_config)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Migrate old format if groups not present
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

        # Fill missing keys from default_config
        for k, v in default_config.items():
            if k not in data:
                data[k] = copy.deepcopy(v)

        # Discard temporary/detected groups on reload
        data["groups"] = [g for g in data.get("groups", []) if not is_ephemeral_group(g)]

        for g in data.get("groups", []):
            for b in g.get("buttons", []):
                normalize_tag_data(b)

        return data
    except Exception as e:
        print(f"Error loading config: {e}. Falling back to default template.")
        return copy.deepcopy(default_config)


def save_config(config_data: Dict[str, Any], file_path: str = CONFIG_FILE) -> None:
    try:
        data_to_save = copy.deepcopy(config_data)
        # Never persist ephemeral detected groups to disk
        if "groups" in data_to_save and isinstance(data_to_save["groups"], list):
            data_to_save["groups"] = [g for g in data_to_save["groups"] if not is_ephemeral_group(g)]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")
