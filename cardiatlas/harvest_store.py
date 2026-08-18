from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .harvest import HarvestItem, deduplicate_harvest
from .harvest_manifest import HarvestManifest, create_harvest_manifest


def write_harvest(
    items: Iterable[HarvestItem],
    directory: str | Path,
    *,
    version: str = "1.0",
    created_at: str | None = None,
) -> HarvestManifest:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    materialized = deduplicate_harvest(items)
    manifest = create_harvest_manifest(materialized, version=version, created_at=created_at)
    with (target / "items.jsonl").open("w", encoding="utf-8") as handle:
        for item in materialized:
            handle.write(json.dumps(item.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    (target / "manifest.json").write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_harvest(directory: str | Path) -> tuple[list[HarvestItem], dict[str, object]]:
    target = Path(directory)
    items: list[HarvestItem] = []
    with (target / "items.jsonl").open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            try:
                items.append(HarvestItem(**payload))
            except TypeError as exc:
                raise ValueError(f"invalid harvest item on line {line_number}: {exc}") from exc
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    return items, manifest
