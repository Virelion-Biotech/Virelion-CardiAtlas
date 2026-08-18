from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .models import Record
from .registry import AtlasRegistry
from .validation import require_valid


class IngestionError(ValueError):
    pass


def iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise IngestionError(f"invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise IngestionError(f"line {line_number} must contain a JSON object")
            yield value


def load_jsonl(registry: AtlasRegistry, path: str | Path, factory) -> int:
    count = 0
    for payload in iter_jsonl(path):
        record = factory(payload)
        require_valid(record)
        registry.upsert(record)
        count += 1
    return count


def dump_jsonl(records: Iterable[Record], path: str | Path) -> int:
    count = 0
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count
