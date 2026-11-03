import os
import uuid
from typing import Any, Dict, List

from src.core.defaults import PRESET_COLORS
from src.core.filename_builder import extract_tags_and_base
from src.core.tag_parser import is_tag_in_tags, parse_tag_definition


def detect_and_register_unknown_tags(
    config: Dict[str, Any], file_paths: List[str]
) -> List[str]:
    """
    Analyzes filenames and registers any unknown tags into the ephemeral '감지된 태그' group.
    Returns the list of newly discovered tag strings.
    """
    if not file_paths:
        return []

    groups = config.setdefault("groups", [])
    discovered_tags: List[str] = []

    for fpath in file_paths:
        if not os.path.exists(fpath):
            continue
        basename, _ = os.path.splitext(os.path.basename(fpath))
        _, existing_tags = extract_tags_and_base(basename)

        for t in existing_tags:
            t_clean = t.strip()
            if not t_clean:
                continue

            matched = any(
                is_tag_in_tags([t_clean], b)
                for g in groups
                for b in g.get("buttons", [])
            )
            if not matched and t_clean not in discovered_tags:
                discovered_tags.append(t_clean)

    if not discovered_tags:
        return []

    detected_group = next(
        (g for g in groups if g.get("id") == "group-detected" or g.get("name") == "감지된 태그"),
        None,
    )
    if not detected_group:
        detected_group = {
            "id": "group-detected",
            "name": "감지된 태그",
            "collapsed": False,
            "buttons": [],
        }
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

    return discovered_tags

