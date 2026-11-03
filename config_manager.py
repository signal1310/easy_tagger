import copy
import json
import os
import sys
import uuid
from typing import Dict, Any, List, Optional
from tag_parser import parse_tag_definition


def get_app_dir() -> str:
    """Returns the persistent directory of the executable or main script (where user configs live)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_bundle_dir() -> str:
    """Returns the bundled resources directory (supports PyInstaller _MEIPASS)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path: str) -> str:
    """Resolves resource path for both development and bundled PyInstaller environments."""
    bundle_path = os.path.join(get_bundle_dir(), relative_path)
    if os.path.exists(bundle_path):
        return bundle_path
    app_path = os.path.join(get_app_dir(), relative_path)
    if os.path.exists(app_path):
        return app_path
    return bundle_path


BASE_DIR = get_app_dir()
BUNDLE_DIR = get_bundle_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CONFIG_INIT_FILE = os.path.join(BASE_DIR, "config.init.json")


def get_init_config_path(custom_path: Optional[str] = None) -> str:
    """Returns the absolute path to config.init.json."""
    if custom_path:
        return os.path.abspath(custom_path)

    # 1. First priority: look for config.init.json next to executable/script
    app_init = os.path.join(BASE_DIR, "config.init.json")
    if os.path.exists(app_init):
        return app_init

    # 2. Second priority: look in bundle directory if running from PyInstaller
    bundle_init = os.path.join(BUNDLE_DIR, "config.init.json")
    if os.path.exists(bundle_init):
        return bundle_init

    # 3. Default to BASE_DIR so self-healing creates it next to executable
    return app_init


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
                        "description": "여행 및 일상 브이로그 영상",
                        "tag_type": "normal",
                        "bg_color": "#bae6fd",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-general-2",
                        "name": "하이라이트",
                        "description": "주요 하이라이트 및 명장면",
                        "tag_type": "normal",
                        "bg_color": "#fed7aa",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-general-3",
                        "name": "완료",
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
                        "description": "4K UHD 초고화질 해상도",
                        "tag_type": "normal",
                        "bg_color": "#a7f3d0",
                        "text_color": "#0f172a"
                    },
                    {
                        "id": "btn-props-2",
                        "name": "-fps 60",
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
    # Strip redundant duplicate properties
    b.pop("label", None)
    b.pop("tag_text", None)

    if spec["tag_type"] == "normal":
        for k in ("param_key", "param_val_mode", "param_val"):
            b.pop(k, None)

    if "description" not in b:
        b["description"] = ""

    return b


def is_ephemeral_group(group: Dict[str, Any]) -> bool:
    """Returns True if the group is temporary/detected and should not persist across sessions."""
    return group.get("id") == "group-detected" or group.get("name") == "감지된 태그"


def load_config(file_path: Optional[str] = None) -> Dict[str, Any]:
    target_path = file_path or CONFIG_FILE
    default_config = load_default_config()

    if not os.path.exists(target_path):
        # Generate config.json directly from config.init.json template
        save_config(default_config, target_path)
        return copy.deepcopy(default_config)

    try:
        with open(target_path, "r", encoding="utf-8") as f:
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


def save_config(config_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
    target_path = file_path or CONFIG_FILE
    try:
        data_to_save = copy.deepcopy(config_data)
        # Never persist ephemeral detected groups to disk
        if "groups" in data_to_save and isinstance(data_to_save["groups"], list):
            data_to_save["groups"] = [g for g in data_to_save["groups"] if not is_ephemeral_group(g)]

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")
