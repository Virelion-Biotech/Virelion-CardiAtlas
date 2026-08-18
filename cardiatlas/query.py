from __future__ import annotations

from dataclasses import dataclass, field

from .graph import AtlasGraph
from .models import Record
from .normalize import canonical_key
from .registry import AtlasRegistry
from .search import search_records


@dataclass(frozen=True, slots=True)
class Query:
    text: str = ""
    record_type: str | None = None
    tags: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    limit: int = 50


@dataclass(frozen=True, slots=True)
class QueryHit:
    record: Record
    score: float


def _matches_filters(record: Record, query: Query) -> bool:
    if query.tags:
        tags = {canonical_key(tag) for tag in record.tags}
        if not all(canonical_key(tag) in tags for tag in query.tags):
            return False
    for key, value in query.metadata.items():
        if str(record.metadata.get(key, "")).lower() != value.lower():
            return False
    return True


def query_registry(registry: AtlasRegistry, query: Query) -> list[QueryHit]:
    candidates = registry.all(query.record_type)
    if query.text:
        candidates = search_records(candidates, query.text)
    candidates = [record for record in candidates if _matches_filters(record, query)]
    hits = []
    for index, record in enumerate(candidates):
        score = 1.0 / (index + 1)
        if query.text and canonical_key(query.text) == canonical_key(record.name):
            score += 1.0
        hits.append(QueryHit(record, score))
    return sorted(hits, key=lambda hit: (-hit.score, hit.record.id))[: max(query.limit, 0)]


def graph_context(graph: AtlasGraph, record_id: str, hops: int = 2) -> dict[str, object]:
    relations = graph.subgraph(record_id, hops=hops)
    return {
        "record_id": record_id,
        "hops": hops,
        "neighbors": graph.neighbors(record_id),
        "relations": [relation.to_dict() for relation in relations],
    }
