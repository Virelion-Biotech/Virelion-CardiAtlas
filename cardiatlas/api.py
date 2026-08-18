from __future__ import annotations

from .contracts import AtlasContext
from .query import Query
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

    def snapshot(self, version: str = "0.0.0") -> dict[str, object]:
        return self.service.release_manifest(version).to_dict()
