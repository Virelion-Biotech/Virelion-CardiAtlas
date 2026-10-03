from __future__ import annotations

from .models import Record
from .normalize import canonical_key, normalize_label
from .registry import AtlasRegistry


def _score(record: Record, terms: list[str]) -> tuple[int, int, str, str]:
    exact = 0
    matched = 0
    searchable = [
        record.id,
        record.name,
        record.description,
        *record.tags,
        *getattr(record, "cell_types", []),
        *getattr(record, "states", []),
        *getattr(record, "conditions", []),
        *getattr(record, "pathways", []),
        *getattr(record, "synonyms", []),
        str(record.metadata),
    ]
    normalized_fields = [normalize_label(value) for value in searchable]
    key_blob = canonical_key(" ".join(searchable))
    for term in terms:
        normalized = normalize_label(term)
        if any(normalized == field for field in normalized_fields):
            exact += 1
        if normalized in " ".join(normalized_fields):
            matched += 1
    return (matched, exact, record.record_type, record.id)


def search_records(records: list[Record], query: str) -> list[Record]:
    """Rank records deterministically by lexical field matches."""
    terms = [normalize_label(term) for term in query.split() if term.strip()]
    if not terms:
        return sorted(records, key=lambda item: (item.record_type, item.id))
    hits = []
    for record in records:
        score = _score(record, terms)
        if score[0] == len(terms):
            hits.append((score, record))
    hits.sort(key=lambda pair: (-pair[0][0], -pair[0][1], pair[0][2], pair[0][3]))
    return [record for _, record in hits]


def search(registry: AtlasRegistry, query: str, record_type: str | None = None) -> list[Record]:
    """Deterministic lexical search over normalized record fields."""
    return search_records(registry.all(record_type), query)
