from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any

from .models import AtlasRecord


def validate_record(record: AtlasRecord) -> list[str]:
    """Return validation errors without mutating the record."""
    errors: list[str] = []
    if not is_dataclass(record):
        return ["record must be a dataclass instance"]
    if not record.id.strip():
        errors.append("id must be non-empty")
    if not record.name.strip():
        errors.append("name must be non-empty")
    if record.schema_version != "0.1":
        errors.append(f"unsupported schema_version: {record.schema_version}")
    for f in fields(record):
        value: Any = getattr(record, f.name)
        if f.name.endswith("_ids") and value is not None and not isinstance(value, list):
            errors.append(f"{f.name} must be a list")
    return errors


def require_valid(record: AtlasRecord) -> AtlasRecord:
    errors = validate_record(record)
    if errors:
        raise ValueError("Invalid CardiAtlas record: " + "; ".join(errors))
    return record
