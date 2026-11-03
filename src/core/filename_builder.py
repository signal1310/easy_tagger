import re
from typing import Any, Dict, List, Optional, Tuple, Union

from src.core.tag_parser import PARAM_KEY_RE, PARAM_TAG_RE, parse_bracket_content

_BRACKET_RE = re.compile(r'\[([^\]]+)\]')
# Standalone hashtags surrounded by whitespace or string boundaries
# e.g., "트랙 #1" matches "1", while "C#_강의", "C# 강의", "트랙#1" do NOT match.
_HASHTAG_RE = re.compile(r'(?:(?<=^)|(?<=\s))#([^\s#\[\]]+)(?=(?:\s|$))')
_HASHTAG_SUB_RE = re.compile(r'(?:(?<=^)|(?<=\s))#[^\s#\[\]]+(?=(?:\s|$))')
_WHITESPACE_RE = re.compile(r'\s+')


def extract_tags_and_base(filename_without_ext: str) -> Tuple[str, List[str]]:
    """
    Extracts all existing tags (both bracketed [tag] and standalone #tag) from filename
    and returns (cleaned_base_name, list_of_tags).
    Accurately avoids mistaking words with embedded hashes like 'C#' or '트랙#1' for tags.
    """
    tags: List[str] = []

    # 1. Extract bracketed tags: [taga] [tagb] or [taga tagb]
    raw_blocks = _BRACKET_RE.findall(filename_without_ext)
    for block in raw_blocks:
        for st in parse_bracket_content(block):
            st_clean = st.strip()
            if st_clean and st_clean not in tags:
                tags.append(st_clean)

    # 2. Extract standalone hashtags: e.g. " #태그 "
    raw_hashes = _HASHTAG_RE.findall(filename_without_ext)
    for ht in raw_hashes:
        ht_clean = ht.strip()
        if ht_clean and ht_clean not in tags:
            tags.append(ht_clean)

    # 3. Clean filename base by removing brackets and standalone hashtags
    cleaned_base = _BRACKET_RE.sub("", filename_without_ext)
    cleaned_base = _HASHTAG_SUB_RE.sub("", cleaned_base)
    cleaned_base = _WHITESPACE_RE.sub(" ", cleaned_base).strip(" _-")
    if not cleaned_base:
        cleaned_base = "file"

    return cleaned_base, tags


def format_tag_for_bracket(tag: str) -> str:
    """Ensures parameter tag format, e.g. -fps 60 -> -fps 60, or normal tag -> tag."""
    return tag.strip().strip("[]#")


def assemble_filename(
    base_name: str,
    tags: List[Union[str, Dict[str, Any]]],
    position: str = "suffix",
    style: str = "merged",
    default_format: str = "bracket",
    tag_specs: Optional[Dict[str, Dict[str, Any]]] = None,
) -> str:
    """
    Assembles filename without extension according to position and format:
    - Position: 'prefix' (before base_name) or 'suffix' (after base_name)
    - Style: 'merged' ([tag1 tag2]) or 'separate' ([tag1] [tag2]) for brackets
    - Format: 'bracket' ([tag]) or 'hashtag' (#tag)
    Supports heterogeneous tags: prefix brackets, prefix hashtags, suffix brackets, suffix hashtags.
    """
    if not tags:
        return base_name

    prefix_brackets: List[str] = []
    prefix_hashtags: List[str] = []
    suffix_brackets: List[str] = []
    suffix_hashtags: List[str] = []

    for item in tags:
        if isinstance(item, dict):
            tag_name = item.get("name", "")
            t_pos = item.get("position", position)
            t_fmt = item.get("format", default_format)
        else:
            tag_name = str(item)
            spec = (tag_specs or {}).get(tag_name, {})
            t_pos = spec.get("position", position)
            t_fmt = spec.get("format", default_format)

        clean_name = format_tag_for_bracket(tag_name)
        if not clean_name:
            continue

        if t_pos == "auto":
            t_pos = position
        if t_fmt == "auto":
            t_fmt = default_format

        if t_pos == "prefix":
            if t_fmt == "hashtag":
                prefix_hashtags.append(clean_name)
            else:
                prefix_brackets.append(clean_name)
        else:
            if t_fmt == "hashtag":
                suffix_hashtags.append(clean_name)
            else:
                suffix_brackets.append(clean_name)

    # Build prefix segment: [brackets] #hashtags
    prefix_parts: List[str] = []
    if prefix_brackets:
        if style == "merged":
            prefix_parts.append(f"[{' '.join(prefix_brackets)}]")
        else:
            prefix_parts.append(" ".join(f"[{t}]" for t in prefix_brackets))
    if prefix_hashtags:
        prefix_parts.append(" ".join(f"#{t}" for t in prefix_hashtags))
    prefix_str = " ".join(prefix_parts).strip()

    # Build suffix segment: [brackets] #hashtags
    suffix_parts: List[str] = []
    if suffix_brackets:
        if style == "merged":
            suffix_parts.append(f"[{' '.join(suffix_brackets)}]")
        else:
            suffix_parts.append(" ".join(f"[{t}]" for t in suffix_brackets))
    if suffix_hashtags:
        suffix_parts.append(" ".join(f"#{t}" for t in suffix_hashtags))
    suffix_str = " ".join(suffix_parts).strip()

    # Assemble: [prefix] base_name [suffix]
    result_parts: List[str] = []
    if prefix_str:
        result_parts.append(prefix_str)
    result_parts.append(base_name)
    if suffix_str:
        result_parts.append(suffix_str)

    return " ".join(result_parts).strip()


def apply_tag_to_tags_list(existing_tags: List[str], new_tag: str) -> List[str]:
    """
    Appends or updates tag in the list.
    If new_tag is of form '-key value' or '[-key value]', replaces any existing '-key ...'.
    Otherwise, if new_tag already exists, keeps it without duplicate.
    """
    new_tag = new_tag.strip().strip("[]#")
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
    tag_to_remove = tag_to_remove.strip().strip("[]#")
    param_match = PARAM_KEY_RE.match(tag_to_remove)
    param_key = f"-{param_match.group(1)}" if param_match else None

    result: List[str] = []
    for t in existing_tags:
        clean_t = t.strip().strip("[]#")
        if param_key and (clean_t.startswith(f"{param_key} ") or clean_t == param_key):
            continue
        if clean_t == tag_to_remove:
            continue
        result.append(t)
    return result
