from __future__ import annotations

from dataclasses import dataclass

from .evidence import EvidenceScore, score_evidence
from .graph import AtlasGraph
from .models import EvidenceRecord, Record
from .normalize import canonical_key
from .registry import AtlasRegistry


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    record: Record
    lexical_score: float
    evidence_score: float | None = None
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "record": self.record.to_dict(),
            "lexical_score": self.lexical_score,
            "evidence_score": self.evidence_score,
            "matched_terms": list(self.matched_terms),
            "score_semantics": "lexical relevance only; evidence_score is a separate heuristic source inventory",
        }


def _terms(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(term for term in canonical_key(text).split("_") if term))


def _searchable_values(record: Record) -> list[str]:
    def as_values(value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value]

    values = [
        record.id, record.name, record.description, *as_values(record.tags),
        *as_values(getattr(record, "cell_types", [])), *as_values(getattr(record, "states", [])),
        *as_values(getattr(record, "conditions", [])), *as_values(getattr(record, "pathways", [])),
        *as_values(getattr(record, "synonyms", [])), *as_values(getattr(record, "species", [])),
        *as_values(getattr(record, "modalities", [])), *as_values(getattr(record, "tissues", [])),
        *as_values(getattr(record, "evidence_ids", [])), str(record.metadata),
    ]
    for field_name in ("organism", "tissue", "region", "timepoint", "condition", "assay", "accession", "study_title", "modality"):
        value = getattr(record, field_name, None)
        if value:
            values.append(str(value))
    return [canonical_key(value) for value in values if value]


def retrieve(
    registry: AtlasRegistry,
    query: str,
    *,
    record_type: str | None = None,
    limit: int = 20,
) -> list[RetrievalResult]:
    """Rank partial lexical matches with transparent, order-independent scores.

    Scores are based on query-term coverage plus exact phrase/name matches.
    Evidence inventory is reported separately and never blended into relevance.
    """
    if limit < 0:
        raise ValueError("limit must be non-negative")
    terms = _terms(query)
    candidates = registry.all(record_type)
    evidence_index = {
        item.id: item for item in registry.all("evidence")
        if isinstance(item, EvidenceRecord)
    }
    results: list[RetrievalResult] = []
    for record in candidates:
        fields = _searchable_values(record)
        haystack = " ".join(fields)
        matched = tuple(term for term in terms if any(term in field.split("_") for field in fields))
        if terms and not matched:
            continue
        coverage = len(matched) / len(terms) if terms else 0.0
        phrase = canonical_key(query) in haystack if query.strip() else False
        name_or_id = canonical_key(query) in {canonical_key(record.name), canonical_key(record.id)} if query.strip() else False
        lexical = round(min(1.0, 0.75 * coverage + 0.15 * float(phrase) + 0.10 * float(name_or_id)), 6) if terms else 0.0
        evidence_ids = getattr(record, "evidence_ids", []) or []
        evidence_records = [evidence_index[eid] for eid in evidence_ids if eid in evidence_index]
        evidence_score: EvidenceScore | None = score_evidence(evidence_records) if evidence_records else None
        results.append(RetrievalResult(record, lexical, evidence_score.score if evidence_score else None, matched))
    return sorted(
        results,
        key=lambda item: (-item.lexical_score, item.record.record_type, item.record.id),
    )[:limit]


def neighborhood_retrieve(
    registry: AtlasRegistry,
    graph: AtlasGraph,
    query: str,
    *,
    hops: int = 1,
    limit: int = 20,
) -> list[dict[str, object]]:
    results = retrieve(registry, query, limit=limit)
    output: list[dict[str, object]] = []
    for result in results:
        output.append({
            "result": result.to_dict(),
            "context": {
                "neighbors": graph.neighbors(result.record.id),
                "relations": [relation.to_dict() for relation in graph.subgraph(result.record.id, hops=hops)],
            },
        })
    return output
