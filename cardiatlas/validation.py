from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .models import AtlasRecord

SUPPORTED_SCHEMA_VERSIONS = {"0.1", "0.2"}


def validate_record(record: AtlasRecord) -> list[str]:
    """Return validation errors without mutating the record."""
    errors: list[str] = []
    if not is_dataclass(record):
        return ["record must be a dataclass instance"]
    if not record.id.strip():
        errors.append("id must be non-empty")
    if not record.name.strip():
        errors.append("name must be non-empty")
    if record.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"unsupported schema_version: {record.schema_version}")
    for f in fields(record):
        value: Any = getattr(record, f.name)
        if f.name.endswith("_ids") and value is not None and not isinstance(value, list):
            errors.append(f"{f.name} must be a list")
    for attr in ("confidence",):
        if hasattr(record, attr):
            value = getattr(record, attr)
            if value is not None and not 0.0 <= float(value) <= 1.0:
                errors.append(f"{attr} must be between 0 and 1")
    if hasattr(record, "sample_count"):
        value = getattr(record, "sample_count")
        if value is not None and int(value) < 0:
            errors.append("sample_count must be non-negative")
    if hasattr(record, "cell_count"):
        value = getattr(record, "cell_count")
        if value is not None and int(value) < 0:
            errors.append("cell_count must be non-negative")
    return errors


def require_valid(record: AtlasRecord) -> AtlasRecord:
    errors = validate_record(record)
    if errors:
        raise ValueError("Invalid CardiAtlas record: " + "; ".join(errors))
    return record
