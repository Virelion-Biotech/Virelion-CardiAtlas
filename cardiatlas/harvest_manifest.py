from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

from .harvest import HarvestItem
from .harvest_qc import HarvestQC, assess_harvest


@dataclass(frozen=True, slots=True)
class HarvestManifest:
    version: str
    created_at: str
    item_count: int
    source_count: int
    digest: str
    qc: HarvestQC
    query_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "item_count": self.item_count,
            "source_count": self.source_count,
            "digest": self.digest,
            "qc": self.qc.to_dict(),
            "query_ids": list(self.query_ids),
        }


def _digest(items: Iterable[HarvestItem]) -> str:
    payload = [item.to_dict() for item in items]
    payload.sort(key=lambda item: (str(item.get("source", "")), str(item.get("external_id", ""))))
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def create_harvest_manifest(items: Iterable[HarvestItem], version: str = "1.0", created_at: str | None = None) -> HarvestManifest:
    from datetime import UTC, datetime

    materialized = list(items)
    qc = assess_harvest(materialized)
    sources = {item.source.strip().lower() for item in materialized if item.source.strip()}
    queries = {item.query_id for item in materialized if item.query_id}
    timestamp = created_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    return HarvestManifest(
        version=version,
        created_at=timestamp,
        item_count=len(materialized),
        source_count=len(sources),
        digest=_digest(materialized),
        qc=qc,
        query_ids=tuple(sorted(queries)),
    )
