from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .models import AtlasRecord, DatasetRecord, SampleRecord, StudyRecord
from .schema import RECORD_TYPES, SCHEMA_VERSION


def validate_record(record: AtlasRecord) -> list[str]:
    """Return deterministic validation errors without mutating records."""
    errors: list[str] = []
    if not is_dataclass(record):
        return ["record must be a dataclass instance"]
    if not record.id.strip():
        errors.append("id must be non-empty")
    if not record.name.strip():
        errors.append("name must be non-empty")
    if record.record_type not in RECORD_TYPES:
        errors.append(f"unsupported record_type: {record.record_type}")
    if record.schema_version != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version: {record.schema_version}")
    for f in fields(record):
        value: Any = getattr(record, f.name)
        if f.name.endswith("_ids") and value is not None and not isinstance(value, list):
            errors.append(f"{f.name} must be a list")
    if hasattr(record, "confidence"):
        value = getattr(record, "confidence")
        if value is not None and not 0.0 <= float(value) <= 1.0:
            errors.append("confidence must be between 0 and 1")
    if isinstance(record, DatasetRecord):
        if not record.accession.strip():
            errors.append("dataset accession must be non-empty")
        if record.sample_count is not None and record.sample_count < 0:
            errors.append("sample_count must be non-negative")
        if record.cell_count is not None and record.cell_count < 0:
            errors.append("cell_count must be non-negative")
    if isinstance(record, StudyRecord) and not record.accession.strip():
        errors.append("study accession must be non-empty")
    if isinstance(record, SampleRecord):
        if not record.dataset_id.strip():
            errors.append("sample dataset_id must be non-empty")
        if not record.accession.strip():
            errors.append("sample accession must be non-empty")
    return errors


def require_valid(record: AtlasRecord) -> AtlasRecord:
    errors = validate_record(record)
    if errors:
        raise ValueError("Invalid CardiAtlas record: " + "; ".join(errors))
    return record
