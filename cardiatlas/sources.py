from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import Record


@dataclass(frozen=True, slots=True)
class SourceResult:
    source_name: str
    query: str
    records: tuple[Record, ...] = ()
    retrieved_at: str = ""
    source_version: str | None = None
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "query": self.query,
            "records": [record.to_dict() for record in self.records],
            "retrieved_at": self.retrieved_at,
            "source_version": self.source_version,
            "warnings": list(self.warnings),
            "metadata": self.metadata,
        }


class SourceAdapter(Protocol):
    name: str

    def search(self, query: str, limit: int = 20) -> SourceResult:
        """Return normalized records without mutating an Atlas store."""


def ingest_source(adapter: SourceAdapter, query: str, limit: int = 20) -> SourceResult:
    result = adapter.search(query, limit)
    if result.source_name != adapter.name:
        raise ValueError("source adapter returned an inconsistent source_name")
    return result
