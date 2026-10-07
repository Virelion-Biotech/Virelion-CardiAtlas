"""Strict JSON for biomedical metadata and reproducible digests."""

from __future__ import annotations

import json
import math


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_json(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, list):
        for item in value:
            validate_json(item)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for item in value.values():
            validate_json(item)
        return
    raise ValueError("metadata must contain only finite JSON values and string object keys")


def strict_loads(value):
    result = json.loads(
        value,
        object_pairs_hook=_pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"nonfinite JSON constant: {x}")),
    )
    validate_json(result)
    return result
