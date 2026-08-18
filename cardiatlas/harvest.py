from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Iterable, Mapping


@dataclass(frozen=True, slots=True)
class HarvestItem:
    source: str
    query_id: str
    external_id: str
    title: str = ""
    source_url: str | None = None
    retrieved_at: str | None = None
    raw_digest: str | None = None
    status: str = "accepted"
    metadata: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def canonical_digest(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def deduplicate_harvest(items: Iterable[HarvestItem]) -> list[HarvestItem]:
    """Deduplicate by source/external identifier while preserving first-seen order."""
    seen: set[tuple[str, str]] = set()
    result: list[HarvestItem] = []
    for item in items:
        key = (item.source.lower(), item.external_id.strip())
        if not key[1] or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def harvest_report(items: Iterable[HarvestItem]) -> dict[str, object]:
    materialized = deduplicate_harvest(items)
    by_source: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for item in materialized:
        by_source[item.source] = by_source.get(item.source, 0) + 1
        by_status[item.status] = by_status.get(item.status, 0) + 1
    digest = hashlib.sha256(
        json.dumps([item.to_dict() for item in materialized], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        "item_count": len(materialized),
        "sources": dict(sorted(by_source.items())),
        "statuses": dict(sorted(by_status.items())),
        "digest": digest,
    }
