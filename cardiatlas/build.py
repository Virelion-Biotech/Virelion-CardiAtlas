from __future__ import annotations

from pathlib import Path

from .graph import Relation
from .jsonutil import strict_loads
from .loader import read_bundle
from .models import Record
from .release import ReleaseManifest, create_manifest
from .release_checks import ReleaseReadiness, assess_release
from .registry import AtlasRegistry


class ReferenceBuild:
    """Result of building the checked-in reference Atlas bundle."""

    def __init__(self, records: list[Record], relations: list[Relation], manifest: ReleaseManifest, readiness: ReleaseReadiness) -> None:
        self.records = records
        self.relations = relations
        self.manifest = manifest
        self.readiness = readiness

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest.to_dict(),
            "readiness": self.readiness.to_dict(),
            "record_count": len(self.records),
            "relation_count": len(self.relations),
        }


def _load_relations(path: Path) -> list[Relation]:
    if not path.exists():
        return []
    relations: list[Relation] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            payload = strict_loads(line)
            try:
                relations.append(Relation(
                    subject=str(payload["subject"]),
                    predicate=str(payload["predicate"]),
                    object=str(payload["object"]),
                    evidence_ids=tuple(payload.get("evidence_ids", ())),
                    confidence=payload.get("confidence"),
                    source=payload.get("source"),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid relationship at {path}:{line_number}: {exc}") from exc
    return relations


def build_reference(root: str | Path, version: str = "0.4.0") -> ReferenceBuild:
    base = Path(root)
    paths = [
        base / "data/examples/atlas.jsonl",
        base / "data/examples/markers.jsonl",
        base / "data/examples/phenotypes.jsonl",
        base / "data/reference/cardiBench_evidence.jsonl",
        base / "data/reference/cardiac_datasets.jsonl",
        base / "data/reference/optical_stimulation_evidence.jsonl",
        base / "data/reference/optical_stimulation_interventions.jsonl",
    ]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"reference build requires all declared bundles; missing: {missing}")
    records = read_bundle(paths)
    relations = _load_relations(base / "data/reference/core_relationships.jsonl")
    manifest = create_manifest(records, version)
    readiness = assess_release(records, relations)
    return ReferenceBuild(records, relations, manifest, readiness)


def populate_registry(build: ReferenceBuild, registry: AtlasRegistry | None = None) -> AtlasRegistry:
    target = registry or AtlasRegistry()
    for record in build.records:
        target.upsert(record)
    return target
