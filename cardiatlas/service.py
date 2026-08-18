from __future__ import annotations

from dataclasses import dataclass

from .evidence import evidence_for, score_evidence
from .graph import AtlasGraph, Relation
from .models import EvidenceRecord, Record
from .registry import AtlasRegistry
from .search import search_records


@dataclass(slots=True)
class AtlasService:
    registry: AtlasRegistry
    graph: AtlasGraph

    @classmethod
    def empty(cls) -> "AtlasService":
        return cls(AtlasRegistry(), AtlasGraph())

    def add(self, record: Record) -> None:
        self.registry.upsert(record)

    def relate(
        self,
        subject: str,
        predicate: str,
        object_id: str,
        evidence_ids: tuple[str, ...] = (),
        confidence: float | None = None,
        source: str | None = None,
    ) -> None:
        self.graph.add(Relation(subject, predicate, object_id, evidence_ids, confidence, source))

    def search(self, query: str, record_type: str | None = None) -> list[Record]:
        records = self.registry.all(record_type)
        return search_records(records, query)

    def explain(self, record_id: str) -> dict:
        record = self.registry.get(record_id)
        if record is None:
            raise KeyError(record_id)
        evidence_index = {
            item.id: item
            for item in self.registry.all("evidence")
            if isinstance(item, EvidenceRecord)
        }
        evidence = evidence_for(record, evidence_index)
        score = score_evidence(evidence)
        return {
            "record": record.to_dict(),
            "evidence": [item.to_dict() for item in evidence],
            "evidence_score": score.score,
            "evidence_metrics": {
                "count": score.evidence_count,
                "primary_count": score.primary_count,
                "independent_sources": score.independent_sources,
            },
            "neighbors": self.graph.neighbors(record_id),
            "relations": [r.to_dict() for r in self.graph.subgraph(record_id, hops=1)],
        }
