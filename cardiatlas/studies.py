from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import DatasetRecord, SampleRecord, StudyRecord


@dataclass(frozen=True, slots=True)
class StudyQC:
    study_id: str
    sample_count: int
    dataset_count: int
    subject_count: int
    technical_replicates: int
    missing_subject_ids: int
    missing_conditions: int
    missing_timepoints: int
    duplicate_accessions: int
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "study_id": self.study_id,
            "sample_count": self.sample_count,
            "dataset_count": self.dataset_count,
            "subject_count": self.subject_count,
            "technical_replicates": self.technical_replicates,
            "missing_subject_ids": self.missing_subject_ids,
            "missing_conditions": self.missing_conditions,
            "missing_timepoints": self.missing_timepoints,
            "duplicate_accessions": self.duplicate_accessions,
            "warnings": list(self.warnings),
        }


def study_from_datasets(study_id: str, datasets: list[DatasetRecord], name: str = "") -> StudyRecord:
    if not datasets:
        raise ValueError("at least one dataset is required")
    first = datasets[0]
    dataset_ids = [item.id for item in datasets]
    evidence_ids = sorted({eid for item in datasets for eid in item.evidence_ids})
    tissues = sorted({item.tissue for item in datasets if item.tissue})
    modalities = sorted({m for item in datasets for m in item.modalities})
    return StudyRecord(
        id=study_id,
        name=name or first.study_title or first.accession,
        accession=first.accession,
        repository=first.repository,
        title=first.study_title or first.name,
        organism=first.organism,
        tissues=tissues,
        modalities=modalities,
        dataset_ids=dataset_ids,
        evidence_ids=evidence_ids,
        design=str(first.metadata.get("design", "")),
    )


def assess_study(study: StudyRecord, samples: list[SampleRecord]) -> StudyQC:
    scoped = [sample for sample in samples if sample.study_id == study.id]
    accessions = [sample.accession for sample in scoped if sample.accession]
    subjects = {sample.subject_id for sample in scoped if sample.subject_id}
    duplicate_accessions = sum(count - 1 for count in Counter(accessions).values() if count > 1)
    technical = sum(1 for sample in scoped if sample.is_technical_replicate)
    missing_subject = sum(1 for sample in scoped if not sample.subject_id)
    missing_condition = sum(1 for sample in scoped if not sample.condition)
    missing_timepoint = sum(1 for sample in scoped if not sample.timepoint)
    warnings: list[str] = []
    if missing_subject:
        warnings.append("some samples lack biological subject identifiers; leakage control may be limited")
    if duplicate_accessions:
        warnings.append("duplicate sample accessions detected")
    if missing_condition:
        warnings.append("some samples lack harmonizable condition labels")
    if missing_timepoint:
        warnings.append("some samples lack timepoint metadata")
    return StudyQC(
        study_id=study.id,
        sample_count=len(scoped),
        dataset_count=len(study.dataset_ids),
        subject_count=len(subjects),
        technical_replicates=technical,
        missing_subject_ids=missing_subject,
        missing_conditions=missing_condition,
        missing_timepoints=missing_timepoint,
        duplicate_accessions=duplicate_accessions,
        warnings=tuple(warnings),
    )
