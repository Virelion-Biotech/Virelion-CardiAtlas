from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Record


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def to_dict(self) -> dict[str, list[str]]:
        return {"added": list(self.added), "removed": list(self.removed), "changed": list(self.changed)}


def _index(records: Iterable[Record]) -> dict[str, dict]:
    return {record.id: record.to_dict() for record in records}


def diff_records(before: Iterable[Record], after: Iterable[Record]) -> SnapshotDiff:
    left = _index(before)
    right = _index(after)
    added = sorted(set(right) - set(left))
    removed = sorted(set(left) - set(right))
    changed = sorted(key for key in set(left) & set(right) if left[key] != right[key])
    return SnapshotDiff(tuple(added), tuple(removed), tuple(changed))
