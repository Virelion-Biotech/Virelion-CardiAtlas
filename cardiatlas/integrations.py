from __future__ import annotations

from dataclasses import dataclass

from .models import DatasetRecord


@dataclass(frozen=True, slots=True)
class BenchmarkCandidate:
    accession: str
    dataset_id: str
    study_title: str
    organism: str
    tissue: str
    modalities: tuple[str, ...]
    conditions: tuple[str, ...]
    sample_count: int | None
    cell_or_nucleus: str
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "accession": self.accession,
            "dataset_id": self.dataset_id,
            "study_title": self.study_title,
            "organism": self.organism,
            "tissue": self.tissue,
            "modalities": list(self.modalities),
            "conditions": list(self.conditions),
            "sample_count": self.sample_count,
            "cell_or_nucleus": self.cell_or_nucleus,
            "provenance": list(self.provenance),
        }


def dataset_to_benchmark_candidate(dataset: DatasetRecord) -> BenchmarkCandidate:
    if not dataset.accession:
        raise ValueError(f"dataset {dataset.id} has no accession")
    return BenchmarkCandidate(
        accession=dataset.accession,
        dataset_id=dataset.id,
        study_title=dataset.study_title or dataset.name,
        organism=dataset.organism,
        tissue=dataset.tissue,
        modalities=tuple(dataset.modalities),
        conditions=tuple(dataset.conditions),
        sample_count=dataset.sample_count,
        cell_or_nucleus=dataset.cell_or_nucleus,
        provenance=tuple(dataset.evidence_ids or dataset.source_ids),
    )


def benchmark_readiness(dataset: DatasetRecord) -> dict[str, object]:
    checks = {
        "accession": bool(dataset.accession),
        "organism": bool(dataset.organism),
        "tissue": bool(dataset.tissue),
        "modality": bool(dataset.modalities),
        "conditions": len(dataset.conditions) >= 2,
        "provenance": bool(dataset.evidence_ids or dataset.source_ids),
    }
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "missing": [key for key, passed in checks.items() if not passed],
    }
