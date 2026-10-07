from __future__ import annotations

import json
from .jsonutil import strict_loads
from pathlib import Path
from typing import Iterable

from .migrate import migrate_payload
from .models import CellStateRecord, DatasetRecord, EvidenceRecord, InterventionRecord, MarkerRecord, PhenotypeRecord, SampleRecord, StudyRecord, Record
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
    if not isinstance(payload, dict):
        raise ValueError("record payload must be a JSON object")
    payload = migrate_payload(payload) if payload.get("schema_version") == "0.2" else payload
    record_type = payload.get("record_type")
    cls = _RECORD_CLASSES.get(record_type)
    if cls is None:
        raise ValueError(f"unsupported record_type: {record_type}")
    field_names = {field.name for field in cls.__dataclass_fields__.values() if field.init}
    unknown = set(payload) - field_names - {"record_type"}
    if unknown:
        raise ValueError(f"unknown record fields: {sorted(unknown)}")
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
                    payload = strict_loads(line)
                    records.append(record_from_dict(payload))
                except (json.JSONDecodeError, TypeError, ValueError) as exc:
                    raise ValueError(f"invalid Atlas record in {source}:{line_number}: {exc}") from exc
    return records


def load_into_registry(paths: Iterable[str | Path], registry: AtlasRegistry | None = None) -> AtlasRegistry:
    target = registry or AtlasRegistry()
    for record in read_bundle(paths):
        target.upsert(record)
    return target
