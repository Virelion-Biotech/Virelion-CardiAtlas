from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from .acquisition import AcquisitionTarget, acquisition_plan
from .adapters import geo_summary_to_dataset, pubmed_summary_to_evidence
from .harvest import HarvestItem, canonical_digest, deduplicate_harvest
from .models import Record
from .ncbi import NcbiClient


@dataclass(frozen=True, slots=True)
class HarvestBatch:
    target_id: str
    records: tuple[Record, ...]
    items: tuple[HarvestItem, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "record_count": len(self.records),
            "item_count": len(self.items),
            "records": [record.to_dict() for record in self.records],
            "items": [item.to_dict() for item in self.items],
        }


def _target_item(target: AcquisitionTarget, external_id: str, title: str, source_url: str | None, payload: dict) -> HarvestItem:
    return HarvestItem(
        source=target.source,
        query_id=target.target_id,
        external_id=external_id,
        title=title,
        source_url=source_url,
        retrieved_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        raw_digest=canonical_digest(payload),
        metadata={"domain": target.domain, "priority": target.priority},
    )


def _deduplicate_records(records: Iterable[Record]) -> list[Record]:
    seen: set[str] = set()
    result: list[Record] = []
    for record in records:
        if record.id in seen:
            continue
        seen.add(record.id)
        result.append(record)
    return result


def harvest_target(client: NcbiClient, target: AcquisitionTarget, limit: int = 20) -> HarvestBatch:
    records: list[Record] = []
    items: list[HarvestItem] = []
    if target.source == "pubmed":
        result = client.search_pubmed(target.query, limit)
        for uid, summary in result["summaries"].items():
            if uid == "uids":
                continue
            record = pubmed_summary_to_evidence(summary)
            record.tags = list(dict.fromkeys([*record.tags, target.domain]))
            records.append(record)
            items.append(_target_item(target, str(uid), record.name, record.source_url, summary))
    elif target.source == "geo":
        result = client.search_geo(target.query, limit)
        for uid, summary in result["summaries"].items():
            if uid == "uids":
                continue
            record = geo_summary_to_dataset(summary)
            record.tags = list(dict.fromkeys([*record.tags, target.domain]))
            records.append(record)
            items.append(_target_item(target, str(uid), record.name, record.source_url, summary))
    else:
        raise ValueError(f"unsupported acquisition source: {target.source}")
    return HarvestBatch(target.target_id, tuple(_deduplicate_records(records)), tuple(deduplicate_harvest(items)))


def harvest_plan(
    client: NcbiClient,
    targets: Iterable[AcquisitionTarget] | None = None,
    limit: int = 20,
) -> list[HarvestBatch]:
    selected = list(targets) if targets is not None else acquisition_plan()
    selected.sort(key=lambda target: (-target.priority, target.target_id))
    return [harvest_target(client, target, limit=limit) for target in selected]
