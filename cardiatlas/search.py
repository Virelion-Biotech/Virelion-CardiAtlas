from __future__ import annotations

from .models import Record
from .registry import AtlasRegistry


def search(registry: AtlasRegistry, query: str, record_type: str | None = None) -> list[Record]:
    """Simple deterministic lexical search over normalized record fields."""
    terms = [term.lower() for term in query.split() if term.strip()]
    if not terms:
        return registry.all(record_type)

    hits: list[Record] = []
    for record in registry.all(record_type):
        haystack = " ".join(
            [record.id, record.name, record.description, " ".join(record.tags), str(record.metadata)]
        ).lower()
        if all(term in haystack for term in terms):
            hits.append(record)
    return sorted(hits, key=lambda item: (item.record_type, item.id))
