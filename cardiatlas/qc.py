from __future__ import annotations

from dataclasses import dataclass

from .integrations import benchmark_readiness
from .models import DatasetRecord


@dataclass(frozen=True, slots=True)
class QualityReport:
    dataset_id: str
    ready: bool
    checks: dict[str, bool]
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "ready": self.ready,
            "checks": dict(self.checks),
            "warnings": list(self.warnings),
            "blockers": list(self.blockers),
        }


def assess_dataset(dataset: DatasetRecord) -> QualityReport:
    readiness = benchmark_readiness(dataset)
    warnings: list[str] = []
    blockers = list(readiness["missing"])
    if dataset.sample_count is None:
        warnings.append("sample_count is unavailable")
    if dataset.cell_or_nucleus == "unknown":
        warnings.append("cell_or_nucleus context is unknown")
    if "scrna" in dataset.modalities or "snrna" in dataset.modalities:
        if dataset.cell_count is None:
            warnings.append("single-cell/nucleus dataset has no cell_count")
    if len(dataset.conditions) < 2:
        warnings.append("fewer than two conditions are currently represented")
    return QualityReport(dataset.id, bool(readiness["ready"]), dict(readiness["checks"]), tuple(warnings), tuple(blockers))


def audit_datasets(datasets: list[DatasetRecord]) -> dict[str, object]:
    reports = [assess_dataset(dataset) for dataset in datasets]
    return {
        "dataset_count": len(reports),
        "ready_count": sum(report.ready for report in reports),
        "blocked_count": sum(not report.ready for report in reports),
        "reports": [report.to_dict() for report in reports],
    }
