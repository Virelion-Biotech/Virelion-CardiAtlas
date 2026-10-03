from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .integrations import dataset_to_benchmark_candidate
from .models import DatasetRecord, Record
from .release import create_manifest


def write_records(records: Iterable[Record], path: str | Path) -> int:
    materialized = list(records)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in sorted(materialized, key=lambda item: (item.record_type, item.id)):
            handle.write(json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    return len(materialized)


def write_release(records: Iterable[Record], path: str | Path, version: str) -> dict[str, object]:
    materialized = list(records)
    manifest = create_manifest(materialized, version).to_dict()
    payload = {"manifest": manifest, "records": [record.to_dict() for record in sorted(materialized, key=lambda item: item.id)]}
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def write_cardiBench_candidates(datasets: Iterable[DatasetRecord], path: str | Path) -> int:
    materialized = list(datasets)
    payload = [dataset_to_benchmark_candidate(dataset).to_dict() for dataset in sorted(materialized, key=lambda item: item.id)]
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(payload)
