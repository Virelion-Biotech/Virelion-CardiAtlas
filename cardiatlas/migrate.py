from __future__ import annotations

from copy import deepcopy

from .schema import SCHEMA_VERSION


LEGACY_SCHEMA = "0.2"


def migrate_payload(payload: dict) -> dict:
    """Upgrade a legacy record payload without inventing biological metadata."""
    result = deepcopy(payload)
    version = result.get("schema_version")
    if version == SCHEMA_VERSION:
        return result
    if version != LEGACY_SCHEMA:
        raise ValueError(f"unsupported legacy schema: {version}")

    result["schema_version"] = SCHEMA_VERSION
    record_type = result.get("record_type")
    if record_type == "dataset":
        result.setdefault("study_id", None)
        result.setdefault("region", None)
        result.setdefault("timepoints", [])
        result.setdefault("quality_flags", [])
    elif record_type == "evidence":
        result.setdefault("polarity", "unknown")
        result.setdefault("source_url", None)
        result.setdefault("extracted_claim", "")
        result.setdefault("context", {})
    return result


def migrate_records(payloads: list[dict]) -> list[dict]:
    return [migrate_payload(payload) for payload in payloads]
