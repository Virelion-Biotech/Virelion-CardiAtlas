from __future__ import annotations

from dataclasses import dataclass
from math import log1p
from typing import Iterable

from .models import EvidenceRecord, Record


_LEVEL_WEIGHT = {
    "primary": 1.0,
    "review": 0.75,
    "database": 0.7,
    "curated": 0.65,
    "inferred": 0.45,
}


@dataclass(frozen=True, slots=True)
class EvidenceScore:
    score: float
    evidence_count: int
    primary_count: int
    independent_sources: int


def score_evidence(records: Iterable[EvidenceRecord]) -> EvidenceScore:
    values = list(records)
    if not values:
        return EvidenceScore(0.0, 0, 0, 0)
    weighted = sum(_LEVEL_WEIGHT.get(item.evidence_level, 0.5) for item in values)
    diversity = len({(item.source_type, item.source_identifier) for item in values})
    primary = sum(item.evidence_level == "primary" for item in values)
    # Saturating transform: repeated evidence helps, but cannot overwhelm
    # quality/source diversity.
    count_factor = min(1.0, log1p(len(values)) / log1p(10))
    diversity_factor = min(1.0, diversity / 4)
    quality_factor = min(1.0, weighted / max(1.0, len(values)))
    score = round(100 * (0.45 * quality_factor + 0.30 * count_factor + 0.25 * diversity_factor), 3)
    return EvidenceScore(score, len(values), primary, diversity)


def evidence_for(record: Record, evidence_index: dict[str, EvidenceRecord]) -> list[EvidenceRecord]:
    ids = getattr(record, "evidence_ids", [])
    return [evidence_index[item] for item in ids if item in evidence_index]


def provenance_chain(record: Record, evidence_index: dict[str, EvidenceRecord]) -> list[dict]:
    return [
        {
            "record_id": record.id,
            "record_type": record.record_type,
            "evidence": evidence.to_dict(),
        }
        for evidence in evidence_for(record, evidence_index)
    ]
