from __future__ import annotations

from dataclasses import dataclass

from .evidence import EvidenceScore, score_evidence
from .graph import AtlasGraph
from .models import EvidenceRecord, Record
from .normalize import canonical_key
from .registry import AtlasRegistry
from .search import search_records


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
        }


def _terms(text: str) -> tuple[str, ...]:
    return tuple(term for term in canonical_key(text).split() if term)


def retrieve(
    registry: AtlasRegistry,
    query: str,
    *,
    record_type: str | None = None,
    limit: int = 20,
) -> list[RetrievalResult]:
    terms = _terms(query)
    candidates = search_records(registry.all(record_type), query) if query.strip() else registry.all(record_type)
    evidence_index = {
        record.id: record
        for record in registry.all("evidence")
        if isinstance(record, EvidenceRecord)
    }
    results: list[RetrievalResult] = []
    for index, record in enumerate(candidates):
        haystack = canonical_key(" ".join([record.id, record.name, record.description, " ".join(record.tags)]))
        matched = tuple(term for term in terms if term in haystack)
        lexical = len(matched) / max(len(terms), 1)
        evidence_score: EvidenceScore | None = None
        evidence_ids = getattr(record, "evidence_ids", []) or []
        evidence = [evidence_index[eid] for eid in evidence_ids if eid in evidence_index]
        if evidence:
            evidence_score = score_evidence(evidence)
        results.append(
            RetrievalResult(
                record=record,
                lexical_score=lexical + 1.0 / (index + 1),
                evidence_score=evidence_score.score if evidence_score else None,
                matched_terms=matched,
            )
        )
    return sorted(
        results,
        key=lambda item: (
            -(item.lexical_score + ((item.evidence_score or 0.0) * 0.25)),
            item.record.id,
        ),
    )[: max(limit, 0)]


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
        output.append(
            {
                "result": result.to_dict(),
                "context": {
                    "neighbors": graph.neighbors(result.record.id),
                    "relations": [relation.to_dict() for relation in graph.subgraph(result.record.id, hops=hops)],
                },
            }
        )
    return output
