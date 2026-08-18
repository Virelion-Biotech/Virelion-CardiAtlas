from __future__ import annotations

from dataclasses import dataclass

from .claims import Claim, ClaimAssessment, ClaimStore
from .contracts import AtlasContext
from .evidence import evidence_for, score_evidence
from .graph import AtlasGraph, Relation
from .identifiers import IdentifierResolution, resolve as resolve_identifier
from .models import DatasetRecord, EvidenceRecord, Record, SampleRecord, StudyRecord
from .ontology import canonical_concept_id, resolve_concept
from .query import Query, QueryHit, graph_context, query_registry
from .qc import assess_dataset
from .registry import AtlasRegistry
from .release import ReleaseManifest, create_manifest
from .release_checks import ReleaseReadiness, assess_release
from .search import search_records
from .studies import StudyQC, assess_study


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

    def add_many(self, records: list[Record]) -> None:
        for record in records:
            self.add(record)

    def relate(self, subject: str, predicate: str, object_id: str, evidence_ids: tuple[str, ...] = (), confidence: float | None = None, source: str | None = None) -> None:
        self.graph.add(Relation(subject, predicate, object_id, evidence_ids, confidence, source))

    def add_claim(self, claim: Claim) -> None:
        self.claims.add(claim)

    def search(self, query: str, record_type: str | None = None) -> list[Record]:
        return search_records(self.registry.all(record_type), query)

    def query(self, query: Query) -> list[QueryHit]:
        return query_registry(self.registry, query)

    def resolve(self, value: str) -> str | None:
        return canonical_concept_id(value)

    def resolve_identifier(self, value: str, identifier_type: str | None = None) -> IdentifierResolution:
        return resolve_identifier(value, identifier_type)

    def concept(self, value: str):
        return resolve_concept(value)

    def context(self, record_id: str, hops: int = 2) -> dict[str, object]:
        return graph_context(self.graph, record_id, hops=hops)

    def explain(self, record_id: str) -> dict:
        record = self.registry.get(record_id)
        if record is None:
            raise KeyError(record_id)
        evidence_index = {item.id: item for item in self.registry.all("evidence") if isinstance(item, EvidenceRecord)}
        evidence = evidence_for(record, evidence_index)
        score = score_evidence(evidence)
        return {
            "record": record.to_dict(),
            "evidence": [item.to_dict() for item in evidence],
            "evidence_score": score.score,
            "evidence_metrics": {"count": score.evidence_count, "primary_count": score.primary_count, "independent_sources": score.independent_sources},
            "neighbors": self.graph.neighbors(record_id),
            "relations": [r.to_dict() for r in self.graph.subgraph(record_id, hops=1)],
        }

    def assess_dataset(self, dataset_id: str) -> dict[str, object]:
        record = self.registry.get(dataset_id)
        if record is None:
            raise KeyError(dataset_id)
        if not isinstance(record, DatasetRecord):
            raise TypeError(f"{dataset_id} is not a dataset")
        return assess_dataset(record).to_dict()

    def assess_study(self, study_id: str) -> StudyQC:
        record = self.registry.get(study_id)
        if record is None:
            raise KeyError(study_id)
        if not isinstance(record, StudyRecord):
            raise TypeError(f"{study_id} is not a study")
        samples = [item for item in self.registry.all("sample") if isinstance(item, SampleRecord)]
        return assess_study(record, samples)

    def assess_claim(self, claim_id: str) -> ClaimAssessment:
        evidence = {item.id: item for item in self.registry.all("evidence") if isinstance(item, EvidenceRecord)}
        return self.claims.assess(claim_id, evidence)

    def release_manifest(self, version: str, schema_version: str = "0.3") -> ReleaseManifest:
        return create_manifest(self.registry.all(), version, schema_version)

    def release_readiness(self) -> ReleaseReadiness:
        return assess_release(self.registry.all())

    def atlas_context(self, context_id: str, record_ids: list[str]) -> AtlasContext:
        grouped: dict[str, list[str]] = {}
        for record_id in record_ids:
            record = self.registry.get(record_id)
            if record is not None:
                grouped.setdefault(record.record_type, []).append(record_id)
        return AtlasContext(
            context_id=context_id,
            phenotype_ids=tuple(grouped.get("phenotype", ())),
            cell_state_ids=tuple(grouped.get("cell_state", ())),
            marker_ids=tuple(grouped.get("marker", ())),
            dataset_ids=tuple(grouped.get("dataset", ())),
            study_ids=tuple(grouped.get("study", ())),
            sample_ids=tuple(grouped.get("sample", ())),
            intervention_ids=tuple(grouped.get("intervention", ())),
            evidence_ids=tuple(grouped.get("evidence", ())),
            provenance=tuple(sorted(set(record_ids))),
        )
