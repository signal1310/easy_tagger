import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class UndoResult:
    """Encapsulates the result of reverting the most recent batch rename action."""
    reverted_count: int = 0
    reverted_targets: List[str] = field(default_factory=list)
    path_map: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class UndoService:
    """Manages multi-file batch rename undo history and filesystem rollback."""

    def __init__(self, stack_ref: Optional[List[List[Tuple[str, str]]]] = None):
        self.stack: List[List[Tuple[str, str]]] = stack_ref if stack_ref is not None else []

    @property
    def can_undo(self) -> bool:
        return len(self.stack) > 0

    @property
    def count(self) -> int:
        return len(self.stack)

    def push(self, batch: List[Tuple[str, str]]) -> None:
        if batch:
            self.stack.append(batch)

    def undo_last(self) -> Optional[UndoResult]:
        if not self.stack:
            return None

        last_batch = self.stack.pop()
        result = UndoResult()

        for old_path, new_path in reversed(last_batch):
            if os.path.exists(new_path):
                if os.path.exists(old_path) and os.path.normcase(old_path) != os.path.normcase(new_path):
                    result.errors.append(f"원래 파일명이 이미 존재함: {os.path.basename(old_path)}")
                    continue
                try:
                    os.rename(new_path, old_path)
                    result.reverted_count += 1
                    result.reverted_targets.append(old_path)
                    result.path_map[os.path.normcase(new_path)] = old_path
                except Exception as e:
                    result.errors.append(f"복원 실패: {e}")
            else:
                result.errors.append(f"파일 없음: {new_path}")

        return result

