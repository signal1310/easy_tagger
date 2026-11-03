import os
from dataclasses import dataclass, field
from typing import List, Tuple

from src.core.filename_builder import (
    apply_tag_to_tags_list,
    assemble_filename,
    extract_tags_and_base,
    remove_tag_from_tags_list,
)
from src.core.tag_parser import is_tag_in_tags


@dataclass
class BatchRenameResult:
    """Encapsulates the outcome of a batch tag application or removal."""
    rename_batch: List[Tuple[str, str]] = field(default_factory=list)
    resulting_paths: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    already_tagged_count: int = 0


def normalize_existing_paths(file_paths: List[str]) -> List[str]:
    """Deduplicates and normalizes paths, returning only files that currently exist on disk."""
    valid_paths: List[str] = []
    seen_norm = set()
    for p in file_paths:
        if not p:
            continue
        norm_path = os.path.normpath(os.path.abspath(p))
        norm_case = os.path.normcase(norm_path)
        if os.path.exists(norm_path) and norm_case not in seen_norm:
            seen_norm.add(norm_case)
            valid_paths.append(norm_path)
    return valid_paths


def extract_files_tags(valid_paths: List[str]) -> List[List[str]]:
    """Extracts the list of existing tags for each file path."""
    return [
        extract_tags_and_base(os.path.splitext(os.path.basename(p))[0])[1]
        for p in valid_paths
    ]


def compute_button_tag_state(file_tags_list: List[List[str]], btn_data: dict) -> str:
    """Computes button state ('none', 'on', 'partial', 'off') relative to active files."""
    if not file_tags_list:
        return "none"
    total = len(file_tags_list)
    match_count = sum(1 for tags in file_tags_list if is_tag_in_tags(tags, btn_data))
    if match_count == total:
        return "on"
    if match_count > 0:
        return "partial"
    return "off"


def _is_same_file_path(src_path: str, dst_path: str) -> bool:
    if os.path.normcase(src_path) == os.path.normcase(dst_path):
        return True
    if os.path.exists(dst_path):
        try:
            return os.path.samefile(src_path, dst_path)
        except Exception:
            return False
    return False


def apply_tag_batch(
    file_paths: List[str],
    tag_to_apply: str,
    position: str = "suffix",
    style: str = "merged",
) -> BatchRenameResult:
    """Applies `tag_to_apply` across `file_paths` on disk and records renamed pairs."""
    res = BatchRenameResult()
    for raw_fpath in file_paths:
        fpath = os.path.normpath(os.path.abspath(raw_fpath))
        if not os.path.exists(fpath):
            res.errors.append(f"파일 없음: {raw_fpath}")
            continue

        folder, filename = os.path.split(fpath)
        basename, ext = os.path.splitext(filename)
        cleaned_base, existing_tags = extract_tags_and_base(basename)
        new_tags = apply_tag_to_tags_list(existing_tags, tag_to_apply)
        new_basename = assemble_filename(cleaned_base, new_tags, position=position, style=style)
        new_filename = f"{new_basename}{ext}"
        new_path = os.path.normpath(os.path.join(folder, new_filename))

        if _is_same_file_path(fpath, new_path):
            res.already_tagged_count += 1
            res.resulting_paths.append(fpath)
            continue

        if os.path.exists(new_path):
            res.errors.append(f"이미 존재하는 파일명: {new_filename}")
            res.resulting_paths.append(fpath)
            continue

        try:
            os.rename(fpath, new_path)
            res.rename_batch.append((fpath, new_path))
            res.resulting_paths.append(new_path)
        except Exception as e:
            res.errors.append(f"변경 실패 ({os.path.basename(fpath)}): {e}")
            res.resulting_paths.append(fpath)

    return res


def remove_tag_batch(
    valid_paths: List[str],
    tag_to_remove: str,
    position: str = "suffix",
    style: str = "merged",
) -> BatchRenameResult:
    """Removes `tag_to_remove` from all `valid_paths` on disk and records renamed pairs."""
    res = BatchRenameResult()
    for fpath in valid_paths:
        folder, filename = os.path.split(fpath)
        basename, ext = os.path.splitext(filename)
        cleaned_base, existing_tags = extract_tags_and_base(basename)
        new_tags = remove_tag_from_tags_list(existing_tags, tag_to_remove)
        new_basename = assemble_filename(cleaned_base, new_tags, position=position, style=style)
        new_filename = f"{new_basename}{ext}"
        new_path = os.path.normpath(os.path.join(folder, new_filename))

        if os.path.normcase(new_path) != os.path.normcase(fpath):
            if os.path.exists(new_path):
                res.errors.append(f"이미 존재하는 파일명이 있습니다: {new_filename}")
                res.resulting_paths.append(fpath)
                continue
            try:
                os.rename(fpath, new_path)
                res.rename_batch.append((fpath, new_path))
                res.resulting_paths.append(new_path)
            except Exception as e:
                res.errors.append(f"파일 이름 변경 오류 ({filename}): {e}")
                res.resulting_paths.append(fpath)
        else:
            res.resulting_paths.append(fpath)

    return res

