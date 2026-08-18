from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import (
    CellStateRecord,
    DatasetRecord,
    EvidenceRecord,
    InterventionRecord,
    MarkerRecord,
    PhenotypeRecord,
    SampleRecord,
    StudyRecord,
    Record,
)
from .registry import AtlasRegistry
from .validation import require_valid

_RECORD_CLASSES = {
    "evidence": EvidenceRecord,
    "marker": MarkerRecord,
    "phenotype": PhenotypeRecord,
    "cell_state": CellStateRecord,
    "dataset": DatasetRecord,
    "study": StudyRecord,
    "sample": SampleRecord,
    "intervention": InterventionRecord,
}


def record_from_dict(payload: dict) -> Record:
    record_type = payload.get("record_type")
    cls = _RECORD_CLASSES.get(record_type)
    if cls is None:
        raise ValueError(f"unsupported record_type: {record_type}")
    field_names = {field.name for field in cls.__dataclass_fields__.values()}
    filtered = {key: value for key, value in payload.items() if key in field_names}
    return require_valid(cls(**filtered))


def read_bundle(paths: Iterable[str | Path]) -> list[Record]:
    records: list[Record] = []
    for path in paths:
        source = Path(path)
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    records.append(record_from_dict(payload))
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    raise ValueError(f"invalid Atlas record in {source}:{line_number}: {exc}") from exc
    return records


def load_into_registry(paths: Iterable[str | Path], registry: AtlasRegistry | None = None) -> AtlasRegistry:
    target = registry or AtlasRegistry()
    for record in read_bundle(paths):
        target.upsert(record)
    return target
