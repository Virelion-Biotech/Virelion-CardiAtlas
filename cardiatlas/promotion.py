from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .harvest import HarvestItem
from .models import DatasetRecord, EvidenceRecord, Record
from .normalize import canonical_key
from .validation import validate_record


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    record_id: str
    status: str
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"record_id": self.record_id, "status": self.status, "reasons": list(self.reasons)}


def decide_promotion(record: Record, item: HarvestItem | None = None) -> PromotionDecision:
    reasons = list(validate_record(record))
    if not record.name.strip():
        reasons.append("missing_name")
    if isinstance(record, EvidenceRecord):
        if not record.source_identifier:
            reasons.append("missing_source_identifier")
        if not record.source_url:
            reasons.append("missing_source_url")
    if isinstance(record, DatasetRecord):
        if not record.accession:
            reasons.append("missing_accession")
        if not record.source_url:
            reasons.append("missing_source_url")
    if item is not None and not item.raw_digest:
        reasons.append("missing_raw_digest")
    status = "rejected" if reasons else "candidate"
    return PromotionDecision(record.id, status, tuple(dict.fromkeys(reasons)))


def promote_records(records: Iterable[Record], items: Iterable[HarvestItem] = ()) -> tuple[list[Record], list[PromotionDecision]]:
    by_source = {(item.source.lower(), item.external_id.strip()): item for item in items}
    accepted: list[Record] = []
    decisions: list[PromotionDecision] = []
    seen: set[str] = set()
    for record in records:
        if record.id in seen:
            continue
        seen.add(record.id)
        external_id = getattr(record, "source_identifier", "") or getattr(record, "accession", "")
        source = getattr(record, "source_type", "") or getattr(record, "repository", "")
        item = by_source.get((str(source).lower(), str(external_id).strip()))
        decision = decide_promotion(record, item)
        decisions.append(decision)
        if decision.status == "candidate":
            accepted.append(record)
    return accepted, decisions
