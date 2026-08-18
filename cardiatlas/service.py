from __future__ import annotations

from dataclasses import dataclass

from .claims import Claim, ClaimAssessment, ClaimStore
from .contracts import AtlasContext
from .evidence import evidence_for, score_evidence
from .graph import AtlasGraph, Relation
from .models import EvidenceRecord, Record
from .ontology import canonical_concept_id, resolve_concept
from .query import Query, QueryHit, graph_context, query_registry
from .qc import assess_dataset
from .registry import AtlasRegistry
from .release import ReleaseManifest, create_manifest
from .search import search_records


@dataclass(slots=True)
class AtlasService:
    registry: AtlasRegistry
    graph: AtlasGraph
    claims: ClaimStore

    @classmethod
    def empty(cls) -> "AtlasService":
        return cls(AtlasRegistry(), AtlasGraph(), ClaimStore())

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

    def add_claim(self, claim: Claim) -> None:
        self.claims.add(claim)

    def search(self, query: str, record_type: str | None = None) -> list[Record]:
        records = self.registry.all(record_type)
        return search_records(records, query)

    def query(self, query: Query) -> list[QueryHit]:
        return query_registry(self.registry, query)

    def resolve(self, value: str) -> str | None:
        return canonical_concept_id(value)

    def concept(self, value: str):
        return resolve_concept(value)

    def context(self, record_id: str, hops: int = 2) -> dict[str, object]:
        return graph_context(self.graph, record_id, hops=hops)

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
        result = {
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
        return result

    def assess_dataset(self, dataset_id: str) -> dict[str, object]:
        record = self.registry.get(dataset_id)
        if record is None:
            raise KeyError(dataset_id)
        from .models import DatasetRecord
        if not isinstance(record, DatasetRecord):
            raise TypeError(f"{dataset_id} is not a dataset")
        return assess_dataset(record).to_dict()

    def assess_claim(self, claim_id: str) -> ClaimAssessment:
        evidence = {
            item.id: item
            for item in self.registry.all("evidence")
            if isinstance(item, EvidenceRecord)
        }
        return self.claims.assess(claim_id, evidence)

    def release_manifest(self, version: str, schema_version: str = "0.2") -> ReleaseManifest:
        return create_manifest(self.registry.all(), version, schema_version)

    def atlas_context(self, context_id: str, record_ids: list[str]) -> AtlasContext:
        phenotype_ids = tuple(record_id for record_id in record_ids if self.registry.get(record_id) and self.registry.get(record_id).record_type == "phenotype")
        cell_state_ids = tuple(record_id for record_id in record_ids if self.registry.get(record_id) and self.registry.get(record_id).record_type == "cell_state")
        marker_ids = tuple(record_id for record_id in record_ids if self.registry.get(record_id) and self.registry.get(record_id).record_type == "marker")
        dataset_ids = tuple(record_id for record_id in record_ids if self.registry.get(record_id) and self.registry.get(record_id).record_type == "dataset")
        evidence_ids = tuple(record_id for record_id in record_ids if self.registry.get(record_id) and self.registry.get(record_id).record_type == "evidence")
        return AtlasContext(context_id, phenotype_ids, cell_state_ids, marker_ids, dataset_ids, evidence_ids)
