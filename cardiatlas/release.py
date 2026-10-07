from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .models import DatasetRecord, EvidenceRecord, Record
from .schema import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ReleaseManifest:
    version: str
    schema_version: str
    created_at: str
    record_count: int
    record_types: dict[str, int]
    digest: str
    # release-checklist item 8: "the exact release version, schema version,
    # and source inventory are recorded". version/schema_version are the
    # fields above; these two cover the source-inventory half.
    dataset_accessions: tuple[str, ...] = ()
    evidence_sources: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "record_count": self.record_count,
            "record_types": dict(sorted(self.record_types.items())),
            "digest": self.digest,
            "dataset_accessions": list(self.dataset_accessions),
            "evidence_sources": list(self.evidence_sources),
        }


def canonical_payload(records: Iterable[Record]) -> bytes:
    payload = [record.to_dict() for record in records]
    payload.sort(key=lambda item: (str(item.get("record_type", "")), str(item.get("id", ""))))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest_records(records: Iterable[Record]) -> str:
    return hashlib.sha256(canonical_payload(records)).hexdigest()


def create_manifest(records: Iterable[Record], version: str, schema_version: str = SCHEMA_VERSION) -> ReleaseManifest:
    materialized = list(records)
    counts: dict[str, int] = {}
    for record in materialized:
        counts[record.record_type] = counts.get(record.record_type, 0) + 1
    dataset_accessions = tuple(sorted({r.accession for r in materialized if isinstance(r, DatasetRecord) and r.accession}))
    evidence_sources = tuple(sorted({
        f"{r.source_type}:{r.source_identifier}"
        for r in materialized
        if isinstance(r, EvidenceRecord) and r.source_identifier
    }))
    return ReleaseManifest(
        version=version,
        schema_version=schema_version,
        created_at=datetime.now(timezone.utc).isoformat(),
        record_count=len(materialized),
        record_types=counts,
        digest=digest_records(materialized),
        dataset_accessions=dataset_accessions,
        evidence_sources=evidence_sources,
    )


def verify_digest(records: Iterable[Record], expected: str) -> bool:
    return digest_records(records) == expected


def digest_relations(relations) -> str:
    """Hash exact edge content without changing the historical record digest."""
    payload = []
    for relation in relations:
        item = relation.to_dict()
        item['evidence_ids'] = sorted(set(item['evidence_ids']))
        payload.append(item)
    payload.sort(key=lambda item: json.dumps(item, sort_keys=True, allow_nan=False))
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()
