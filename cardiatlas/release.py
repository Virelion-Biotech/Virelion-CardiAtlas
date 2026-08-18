from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from .models import Record


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    version: str
    schema_version: str
    created_at: str
    record_count: int
    record_types: dict[str, int]
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "record_count": self.record_count,
            "record_types": dict(sorted(self.record_types.items())),
            "digest": self.digest,
        }


def canonical_payload(records: Iterable[Record]) -> bytes:
    payload = [record.to_dict() for record in records]
    payload.sort(key=lambda item: (str(item.get("record_type", "")), str(item.get("id", ""))))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_records(records: Iterable[Record]) -> str:
    return hashlib.sha256(canonical_payload(records)).hexdigest()


def create_manifest(records: Iterable[Record], version: str, schema_version: str = "0.2") -> ReleaseManifest:
    materialized = list(records)
    counts: dict[str, int] = {}
    for record in materialized:
        counts[record.record_type] = counts.get(record.record_type, 0) + 1
    return ReleaseManifest(
        version=version,
        schema_version=schema_version,
        created_at=datetime.now(UTC).isoformat(),
        record_count=len(materialized),
        record_types=counts,
        digest=digest_records(materialized),
    )


def verify_digest(records: Iterable[Record], expected: str) -> bool:
    return digest_records(records) == expected
