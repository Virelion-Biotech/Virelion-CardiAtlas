from __future__ import annotations

from collections import defaultdict

from .models import AtlasRecord, Record
from .validation import require_valid


class AtlasRegistry:
    """Small deterministic registry used by the foundation layer and tests.

    A future backend can implement the same conceptual operations without
    changing the record contract used by downstream Virelion components.
    """

    def __init__(self) -> None:
        self._records: dict[str, Record] = {}
        self._types: dict[str, set[str]] = defaultdict(set)

    def add(self, record: Record) -> None:
        require_valid(record)
        if record.id in self._records:
            raise ValueError(f"record already exists: {record.id}")
        self._records[record.id] = record
        self._types[record.record_type].add(record.id)

    def upsert(self, record: Record) -> None:
        require_valid(record)
        old = self._records.get(record.id)
        if old is not None:
            self._types[old.record_type].discard(record.id)
        self._records[record.id] = record
        self._types[record.record_type].add(record.id)

    def get(self, record_id: str) -> Record | None:
        return self._records.get(record_id)

    def all(self, record_type: str | None = None) -> list[Record]:
        if record_type is None:
            return list(self._records.values())
        return [self._records[rid] for rid in self._types.get(record_type, set())]

    def remove(self, record_id: str) -> bool:
        record = self._records.pop(record_id, None)
        if record is None:
            return False
        self._types[record.record_type].discard(record_id)
        return True

    def __len__(self) -> int:
        return len(self._records)
