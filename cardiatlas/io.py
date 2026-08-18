from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Any, TypeVar

from .models import Record

T = TypeVar("T", bound=Record)


def write_jsonl(records: list[Record], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: str | Path, record_cls: type[T]) -> list[T]:
    target = Path(path)
    result: list[T] = []
    allowed = {f.name for f in fields(record_cls)}
    with target.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload: dict[str, Any] = json.loads(line)
            filtered = {k: v for k, v in payload.items() if k in allowed}
            try:
                result.append(record_cls(**filtered))
            except TypeError as exc:
                raise ValueError(f"invalid record on line {line_number}: {exc}") from exc
    return result
