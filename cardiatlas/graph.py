from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class Relation:
    subject: str
    predicate: str
    object: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = None
    source: str | None = None

    def to_dict(self) -> dict:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        return value


class AtlasGraph:
    """Deterministic in-memory graph over Atlas record identifiers.

    The graph is deliberately storage-agnostic so it can later back onto a
    database or graph engine without changing CardiAtlas's relationship API.
    """

    def __init__(self, relations: Iterable[Relation] = ()) -> None:
        self._relations: list[Relation] = []
        self._index: dict[tuple[str, str, str], Relation] = {}
        for relation in relations:
            self.add(relation)

    def add(self, relation: Relation) -> None:
        if not relation.subject or not relation.predicate or not relation.object:
            raise ValueError("subject, predicate, and object are required")
        if relation.confidence is not None and not 0 <= relation.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        key = (relation.subject, relation.predicate, relation.object)
        existing = self._index.get(key)
        if existing is not None:
            if relation.evidence_ids:
                evidence = tuple(dict.fromkeys(existing.evidence_ids + relation.evidence_ids))
                relation = Relation(existing.subject, existing.predicate, existing.object, evidence,
                                    relation.confidence if relation.confidence is not None else existing.confidence,
                                    relation.source or existing.source)
            else:
                relation = existing
            self._index[key] = relation
            self._relations[self._relations.index(existing)] = relation
            return
        self._index[key] = relation
        self._relations.append(relation)

    def relations(self, predicate: str | None = None) -> list[Relation]:
        values = self._relations
        if predicate is not None:
            values = [r for r in values if r.predicate == predicate]
        return list(values)

    def neighbors(self, node_id: str, predicate: str | None = None) -> list[str]:
        values: set[str] = set()
        for relation in self._relations:
            if predicate is not None and relation.predicate != predicate:
                continue
            if relation.subject == node_id:
                values.add(relation.object)
            if relation.object == node_id:
                values.add(relation.subject)
        return sorted(values)

    def subgraph(self, node_id: str, hops: int = 1) -> list[Relation]:
        if hops < 0:
            raise ValueError("hops must be non-negative")
        frontier = {node_id}
        seen = {node_id}
        selected: list[Relation] = []
        for _ in range(hops):
            next_frontier: set[str] = set()
            for relation in self._relations:
                if relation.subject in frontier or relation.object in frontier:
                    selected.append(relation)
                    for node in (relation.subject, relation.object):
                        if node not in seen:
                            seen.add(node)
                            next_frontier.add(node)
            frontier = next_frontier
            if not frontier:
                break
        return selected

    def to_dict(self) -> dict:
        return {"relations": [relation.to_dict() for relation in self._relations]}
