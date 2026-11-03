import re
from typing import List

TOKEN_RE = re.compile(r'(-\w+\s+(?:"[^"]+"|\'[^\']+\'|\S+)|"[^"]+"|\'[^\']+\'|\S+)')
PARAM_TAG_RE = re.compile(r'^-(\w+)\s*(.*)')
PARAM_KEY_RE = re.compile(r'^-(\w+)')


def get_tag_name(btn_data: dict, default: str = "") -> str:
    """Consistently retrieves the tag name (without outer brackets or leading hashtag) from button configuration data."""
    raw = btn_data.get("name") or btn_data.get("tag_text") or btn_data.get("label") or default
    clean = str(raw).strip()
    if clean.startswith("[") and clean.endswith("]"):
        clean = clean[1:-1].strip()
    elif clean.startswith("#"):
        clean = clean.lstrip("#").strip()
    return clean


def parse_tag_definition(raw_name: str, fallback_mode: str = "") -> dict:
    """
    Parses a single tag name string into a unified tag specification dict.
    - Normal tag: '여행', '4K' -> tag_type='normal'
    - Fixed attribute tag: '-fps 60' -> tag_type='param', param_key='-fps', param_val_mode='fixed', param_val='60'
    - Prompt attribute tag: '-score ?' -> tag_type='param', param_key='-score', param_val_mode='prompt', param_val=''
    """
    clean = str(raw_name).strip()
    if clean.startswith("[") and clean.endswith("]"):
        clean = clean[1:-1].strip()
    elif clean.startswith("#"):
        clean = clean.lstrip("#").strip()

    param_match = PARAM_TAG_RE.match(clean)
    if param_match:
        key = f"-{param_match.group(1)}"
        val = param_match.group(2).strip()
        if val == "?" or (not val and fallback_mode == "prompt"):
            return {
                "name": f"{key} ?",
                "tag_type": "param",
                "param_key": key,
                "param_val_mode": "prompt",
                "param_val": "",
            }
        return {
            "name": f"{key} {val}".strip(),
            "tag_type": "param",
            "param_key": key,
            "param_val_mode": "fixed",
            "param_val": val,
        }

    return {
        "name": clean,
        "tag_type": "normal",
    }


def parse_bracket_content(content: str) -> List[str]:
    """
    Parses space-separated tags inside a bracket, respecting [-param value] pairs.
    Example: 'taga tagb -fps 60 -author "John Doe"' -> ['taga', 'tagb', '-fps 60', '-author "John Doe"']
    """
    content = content.strip()
    if not content:
        return []

    tokens: List[str] = []
    for match in TOKEN_RE.findall(content):
        clean = match.strip()
        if len(clean) >= 2 and clean[0] == clean[-1] and clean[0] in ('"', "'"):
            clean = clean[1:-1].strip()
        if clean:
            tokens.append(clean)
    return tokens


def is_tag_in_tags(existing_tags: List[str], btn_data: dict) -> bool:
    """Checks whether the tag defined by btn_data is currently present in existing_tags."""
    clean_existing = [t.strip().strip("[]#") for t in existing_tags]
    spec = parse_tag_definition(get_tag_name(btn_data), fallback_mode=btn_data.get("param_val_mode", ""))
    if spec["tag_type"] == "param":
        key = spec["param_key"].strip().strip("[]#")
        if spec["param_val_mode"] == "prompt":
            return any(t.startswith(f"{key} ") or t == key for t in clean_existing)
        return spec["name"].strip().strip("[]#") in clean_existing
    return spec["name"].strip().strip("[]#") in clean_existing
