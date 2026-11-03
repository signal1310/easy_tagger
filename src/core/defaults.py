from typing import Any, Dict, List, Tuple

APP_NAME = "Easy Tagger"
APP_VERSION = "v1.1.0"

MIME_TAG = "application/x-easytagger-tag"
MIME_GROUP = "application/x-easytagger-group"

# Soft, elegant pastel preset colors
PRESET_COLORS: List[Tuple[str, str]] = [
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


def get_default_config() -> Dict[str, Any]:
    """Built-in default starter configuration used to initialize config.json when missing."""
    return {
        "theme": "system",
        "position": "suffix",
        "style": "merged",
        "tag_format": "bracket",
        "tag_position_indicator_style": "puzzle",
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
                        "text_color": "#0f172a",
                    },
                    {
                        "id": "btn-general-2",
                        "name": "하이라이트",
                        "description": "주요 하이라이트 및 명장면",
                        "tag_type": "normal",
                        "bg_color": "#fed7aa",
                        "text_color": "#0f172a",
                    },
                    {
                        "id": "btn-general-3",
                        "name": "완료",
                        "description": "편집 및 검토 완료된 영상",
                        "tag_type": "normal",
                        "bg_color": "#cbd5e1",
                        "text_color": "#0f172a",
                    },
                ],
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
                        "text_color": "#0f172a",
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
                        "text_color": "#0f172a",
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
                        "text_color": "#0f172a",
                    },
                ],
            },
        ],
    }


# Backward-compatible alias
get_fallback_template_data = get_default_config

