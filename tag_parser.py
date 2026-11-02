import re
from typing import List, Tuple

_TOKEN_RE = re.compile(r'(-\w+\s+(?:"[^"]+"|\'[^\']+\'|\S+)|"[^"]+"|\'[^\']+\'|\S+)')
_BRACKET_RE = re.compile(r'\[([^\]]+)\]')
_WHITESPACE_RE = re.compile(r'\s+')
_PARAM_TAG_RE = re.compile(r'^-(\w+)\s*(.*)')
_PARAM_KEY_RE = re.compile(r'^-(\w+)')


def get_tag_name(btn_data: dict, default: str = "") -> str:
    """Consistently retrieves the tag name (without outer brackets) from button configuration data."""
    raw = btn_data.get("name") or btn_data.get("tag_text") or btn_data.get("label") or default
    clean = str(raw).strip()
    if clean.startswith("[") and clean.endswith("]"):
        clean = clean[1:-1].strip()
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

    param_match = _PARAM_TAG_RE.match(clean)
    if param_match:
        key = f"-{param_match.group(1)}"
        val = param_match.group(2).strip()
        if val == "?" or (not val and fallback_mode == "prompt"):
            norm_name = f"{key} ?"
            return {
                "name": norm_name,
                "label": norm_name,
                "tag_text": norm_name,
                "tag_type": "param",
                "param_key": key,
                "param_val_mode": "prompt",
                "param_val": "",
            }
        norm_name = f"{key} {val}".strip()
        return {
            "name": norm_name,
            "label": norm_name,
            "tag_text": norm_name,
            "tag_type": "param",
            "param_key": key,
            "param_val_mode": "fixed",
            "param_val": val,
        }

    return {
        "name": clean,
        "label": clean,
        "tag_text": clean,
        "tag_type": "normal",
    }


def parse_bracket_content(content: str) -> List[str]:
    """
    Parses space-separated tags inside a bracket, respecting [-param value] pairs.
    Example:
        'taga tagb -fps 60 -author "John Doe"' -> ['taga', 'tagb', '-fps 60', '-author "John Doe"']
    """
    content = content.strip()
    if not content:
        return []

    tokens = []
    for m in _TOKEN_RE.findall(content):
        clean = m.strip().strip('"\'')
        if clean:
            tokens.append(clean)
    return tokens


def extract_tags_and_base(filename_without_ext: str) -> Tuple[str, List[str]]:
    """
    Extracts all existing tags from filename and returns (cleaned_base_name, list_of_tags).
    Supports both [taga] [tagb] and [taga tagb].
    """
    raw_blocks = _BRACKET_RE.findall(filename_without_ext)

    tags: List[str] = []
    for block in raw_blocks:
        for st in parse_bracket_content(block):
            st_clean = st.strip()
            if st_clean and st_clean not in tags:
                tags.append(st_clean)

    # Remove all [ ... ] blocks to get base name
    cleaned_base = _BRACKET_RE.sub('', filename_without_ext)
    # Clean up excess spaces or underscores
    cleaned_base = _WHITESPACE_RE.sub(' ', cleaned_base).strip(' _-')
    if not cleaned_base:
        cleaned_base = "file"

    return cleaned_base, tags


def format_tag_for_bracket(tag: str) -> str:
    """Ensures parameter tag format, e.g. -fps 60 -> -fps 60, or normal tag -> tag"""
    return tag.strip()


def assemble_filename(base_name: str, tags: List[str], position: str = "suffix", style: str = "merged") -> str:
    """
    Assembles new filename without extension based on position ('prefix' | 'suffix')
    and style ('merged' -> [tag1 tag2] | 'separate' -> [tag1] [tag2]).
    """
    if not tags:
        return base_name

    formatted_tags = [format_tag_for_bracket(t) for t in tags if t.strip()]
    if not formatted_tags:
        return base_name

    if style == "merged":
        tags_str = f"[{' '.join(formatted_tags)}]"
    else:  # separate
        tags_str = " ".join([f"[{t}]" for t in formatted_tags])

    if position == "prefix":
        return f"{tags_str} {base_name}".strip()
    return f"{base_name} {tags_str}".strip()


def apply_tag_to_tags_list(existing_tags: List[str], new_tag: str) -> List[str]:
    """
    Appends or updates tag in the list.
    If new_tag is of form '-key value' or '[-key value]', replaces any existing '-key ...'.
    Otherwise, if new_tag already exists, keeps it without duplicate.
    """
    new_tag = new_tag.strip().strip('[]')
    if not new_tag:
        return list(existing_tags)

    tags = list(existing_tags)

    # Check if new_tag is a parameter tag: e.g. "-fps 60" or "-tagname value"
    param_match = _PARAM_TAG_RE.match(new_tag)
    if param_match:
        param_key = f"-{param_match.group(1)}"
        for i, t in enumerate(tags):
            if t.startswith(f"{param_key} ") or t == param_key:
                tags[i] = new_tag
                return tags
        tags.append(new_tag)
    else:
        if new_tag not in tags:
            tags.append(new_tag)

    return tags


def remove_tag_from_tags_list(existing_tags: List[str], tag_to_remove: str) -> List[str]:
    """Removes a tag (normal or parameter) from existing tags."""
    tag_to_remove = tag_to_remove.strip().strip('[]')
    param_match = _PARAM_KEY_RE.match(tag_to_remove)
    param_key = f"-{param_match.group(1)}" if param_match else None

    result = []
    for t in existing_tags:
        if param_key and (t.startswith(f"{param_key} ") or t == param_key):
            continue
        if t == tag_to_remove:
            continue
        result.append(t)
    return result


def is_tag_in_tags(existing_tags: List[str], btn_data: dict) -> bool:
    """Checks whether the tag defined by btn_data is currently present in existing_tags."""
    spec = parse_tag_definition(get_tag_name(btn_data), fallback_mode=btn_data.get("param_val_mode", ""))
    if spec["tag_type"] == "param":
        key = spec["param_key"]
        if spec["param_val_mode"] == "prompt":
            return any(t.startswith(f"{key} ") or t == key for t in existing_tags)
        return spec["name"] in existing_tags

    return spec["name"] in existing_tags


