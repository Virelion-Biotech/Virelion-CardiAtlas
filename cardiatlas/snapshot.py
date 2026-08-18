from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from .models import Record
from .schema import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class SnapshotManifest:
    version: str
    schema_version: str
    created_at: str
    record_count: int
    record_types: dict[str, int]
    digest: str

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "record_count": self.record_count,
            "record_types": dict(sorted(self.record_types.items())),
            "digest": self.digest,
        }


def _canonical_payload(records: Iterable[Record]) -> bytes:
    payload = [record.to_dict() for record in records]
    payload.sort(key=lambda item: (item.get("record_type", ""), item.get("id", "")))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def create_snapshot(records: Iterable[Record], version: str = "0.4.0") -> SnapshotManifest:
    values = list(records)
    digest = hashlib.sha256(_canonical_payload(values)).hexdigest()
    counts: dict[str, int] = {}
    for record in values:
        counts[record.record_type] = counts.get(record.record_type, 0) + 1
    return SnapshotManifest(
        version=version,
        schema_version=SCHEMA_VERSION,
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        record_count=len(values),
        record_types=counts,
        digest=digest,
    )
