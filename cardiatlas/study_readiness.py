from __future__ import annotations

from dataclasses import dataclass

from .models import DatasetRecord, SampleRecord, StudyRecord
from .studies import assess_study


@dataclass(frozen=True, slots=True)
class StudyBenchmarkReadiness:
    study_id: str
    ready: bool
    checks: dict[str, bool]
    missing: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "ready": self.ready,
            "checks": dict(self.checks),
            "missing": list(self.missing),
            "warnings": list(self.warnings),
        }


def assess_study_benchmark_readiness(
    study: StudyRecord,
    dataset: DatasetRecord,
    samples: list[SampleRecord],
) -> StudyBenchmarkReadiness:
    qc = assess_study(study, samples)
    conditions = {sample.condition for sample in samples if sample.condition}
    modalities = {sample.modality for sample in samples if sample.modality and sample.modality != "other"}
    subjects = {sample.subject_id for sample in samples if sample.subject_id and not sample.metadata.get("subject_inferred", False)}
    checks = {
        "accession": bool(dataset.accession),
        "organism": bool(dataset.organism),
        "tissue": bool(dataset.tissue or qc.sample_count),
        "sample_count": qc.sample_count > 0,
        "multiple_conditions": len(conditions) >= 2,
        "recognized_modality": bool(modalities),
        "subject_structure": bool(subjects) and qc.missing_subject_ids == 0,
        "no_duplicate_sample_accessions": qc.duplicate_accessions == 0,
        "provenance": bool(dataset.evidence_ids or dataset.source_ids),
    }
    warnings = list(qc.warnings)
    if qc.sample_count > 0 and qc.missing_subject_ids:
        warnings.append("subject metadata is incomplete or heuristic and therefore cannot support leakage-control readiness")
    missing = tuple(key for key, passed in checks.items() if not passed)
    return StudyBenchmarkReadiness(
        study_id=study.id,
        ready=not missing,
        checks=checks,
        missing=missing,
        warnings=tuple(dict.fromkeys(warnings)),
    )
