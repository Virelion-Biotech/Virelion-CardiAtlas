from __future__ import annotations

import json
from pathlib import Path

from .harvest_store import read_harvest
from .loader import read_bundle
from .promotion import promote_records


def promote_harvest(directory: str | Path, output: str | Path) -> dict[str, object]:
    source = Path(directory)
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    items, _manifest = read_harvest(source)
    records_path = source / "records.jsonl"
    if not records_path.exists():
        raise FileNotFoundError(f"harvest records not found: {records_path}")
    records = read_bundle([records_path])
    promoted, decisions = promote_records(records, items)
    with (target / "records.jsonl").open("w", encoding="utf-8") as handle:
        for record in promoted:
            handle.write(json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    report = {
        "input": str(source),
        "output": str(target),
        "input_record_count": len(records),
        "promoted_record_count": len(promoted),
        "rejected_record_count": sum(item.status == "rejected" for item in decisions),
        "decisions": [item.to_dict() for item in decisions],
    }
    (target / "promotion.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report
