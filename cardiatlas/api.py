from __future__ import annotations

from collections.abc import Iterable, Mapping

from .contracts import AtlasContext
from .corpus import corpus_report
from .query import Query
from .retrieval import neighborhood_retrieve, retrieve
from .service import AtlasService


class AtlasAPI:
    """Small framework-agnostic API facade for downstream repositories."""

    def __init__(self, service: AtlasService) -> None:
        self.service = service

    def health(self) -> dict[str, object]:
        records = self.service.registry.all()
        return {
            "status": "ok",
            "record_count": len(records),
            "record_types": sorted({record.record_type for record in records}),
            "contract_version": "1.0",
        }

    def search(self, text: str = "", record_type: str | None = None, tags: tuple[str, ...] = (), limit: int = 20) -> dict[str, object]:
        hits = self.service.query(Query(text=text, record_type=record_type, tags=tags, limit=limit))
        return {
            "query": {"text": text, "record_type": record_type, "tags": list(tags), "limit": limit},
            "results": [{"score": hit.score, "record": hit.record.to_dict()} for hit in hits],
        }

    def retrieve(self, text: str, record_type: str | None = None, limit: int = 20) -> dict[str, object]:
        hits = retrieve(self.service.registry, text, record_type=record_type, limit=limit)
        return {
            "query": {"text": text, "record_type": record_type, "limit": limit},
            "results": [hit.to_dict() for hit in hits],
        }

    def context_retrieve(self, text: str, hops: int = 1, limit: int = 20) -> dict[str, object]:
        return {
            "query": {"text": text, "hops": hops, "limit": limit},
            "results": neighborhood_retrieve(self.service.registry, self.service.graph, text, hops=hops, limit=limit),
        }

    def reconstruct_study(self, dataset_id: str, rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
        study, samples, report = self.service.reconstruct_study(dataset_id, rows)
        return {
            "study": study.to_dict(),
            "samples": [sample.to_dict() for sample in samples],
            "report": report.to_dict(),
        }

    def study_benchmark_readiness(self, study_id: str, dataset_id: str) -> dict[str, object]:
        return self.service.assess_study_benchmark_readiness(study_id, dataset_id).to_dict()

    def resolve(self, value: str) -> dict[str, object]:
        concept = self.service.concept(value)
        if concept is None:
            return {"query": value, "resolved": False}
        return {
            "query": value,
            "resolved": True,
            "concept": {
                "id": concept.id,
                "label": concept.label,
                "category": concept.category,
                "synonyms": list(concept.synonyms),
                "parent_id": concept.parent_id,
            },
        }

    def explain(self, record_id: str) -> dict[str, object]:
        return self.service.explain(record_id)

    def context(self, record_ids: list[str], context_id: str = "atlas-context") -> AtlasContext:
        return self.service.atlas_context(context_id, record_ids)

    def corpus(self) -> dict[str, object]:
        return corpus_report(self.service.registry.all()).to_dict()

    def claim(self, claim_id: str) -> dict[str, object]:
        """Return claim status, source-located support, and linked evidence records."""
        claim = self.service.claims.get(claim_id)
        evidence_index = {
            item.id: item for item in self.service.registry.all("evidence")
            if hasattr(item, "source_identifier")
        }
        assessment = self.service.assess_claim(claim_id)
        citations = []
        for citation in claim.citations:
            linked = evidence_index.get(citation.evidence_id)
            citations.append({
                **citation.to_dict(),
                "evidence_record": linked.to_dict() if linked else None,
            })
        return {
            "claim": claim.to_dict(),
            "assessment": {
                "status": assessment.status,
                "evidence_count": assessment.evidence_count,
                "supporting_evidence": list(assessment.supporting_evidence),
                "refuting_evidence": list(assessment.refuting_evidence),
                "mixed_evidence": list(assessment.mixed_evidence),
                "unknown_evidence": list(assessment.unknown_evidence),
            },
            "citations": citations,
            "missing_evidence_ids": sorted(set(claim.evidence_ids) - set(evidence_index)),
        }

    def claims(self) -> dict[str, object]:
        return {"count": len(self.service.claims.all()), "claims": [item.to_dict() for item in self.service.claims.all()]}

    def dataset_readiness(self, study_id: str, dataset_id: str) -> dict[str, object]:
        return self.service.assess_study_benchmark_readiness(study_id, dataset_id).to_dict()

    def graph(self, record_id: str, hops: int = 1) -> dict[str, object]:
        record = self.service.registry.get(record_id)
        if record is None:
            raise KeyError(record_id)
        return {
            "record": record.to_dict(),
            "context": self.service.context(record_id, hops=hops),
            "explanation": self.service.explain(record_id),
        }

    def snapshot(self, version: str = "0.0.0") -> dict[str, object]:
        return self.service.release_manifest(version).to_dict()
