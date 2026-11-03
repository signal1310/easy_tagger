import re
from typing import List, Tuple

from src.core.tag_parser import PARAM_KEY_RE, PARAM_TAG_RE, parse_bracket_content

_BRACKET_RE = re.compile(r'\[([^\]]+)\]')
_WHITESPACE_RE = re.compile(r'\s+')


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

    cleaned_base = _BRACKET_RE.sub("", filename_without_ext)
    cleaned_base = _WHITESPACE_RE.sub(" ", cleaned_base).strip(" _-")
    if not cleaned_base:
        cleaned_base = "file"

    return cleaned_base, tags


def format_tag_for_bracket(tag: str) -> str:
    """Ensures parameter tag format, e.g. -fps 60 -> -fps 60, or normal tag -> tag."""
    return tag.strip()


def assemble_filename(
    base_name: str, tags: List[str], position: str = "suffix", style: str = "merged"
) -> str:
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
    else:
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
    new_tag = new_tag.strip().strip("[]")
    if not new_tag:
        return list(existing_tags)

    tags = list(existing_tags)
    param_match = PARAM_TAG_RE.match(new_tag)
    if param_match:
        param_key = f"-{param_match.group(1)}"
        for i, t in enumerate(tags):
            if t.startswith(f"{param_key} ") or t == param_key:
                tags[i] = new_tag
                return tags
        tags.append(new_tag)
    elif new_tag not in tags:
        tags.append(new_tag)

    return tags


def remove_tag_from_tags_list(existing_tags: List[str], tag_to_remove: str) -> List[str]:
    """Removes a tag (normal or parameter) from existing tags."""
    tag_to_remove = tag_to_remove.strip().strip("[]")
    param_match = PARAM_KEY_RE.match(tag_to_remove)
    param_key = f"-{param_match.group(1)}" if param_match else None

    result: List[str] = []
    for t in existing_tags:
        if param_key and (t.startswith(f"{param_key} ") or t == param_key):
            continue
        if t == tag_to_remove:
            continue
        result.append(t)
    return result

