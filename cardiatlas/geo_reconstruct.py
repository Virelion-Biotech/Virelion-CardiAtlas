from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping

from .harmonize import harmonize_condition, harmonize_modality
from .models import DatasetRecord, SampleRecord, StudyRecord
from .normalize import canonical_key, normalize_species


@dataclass(frozen=True, slots=True)
class ReconstructionDecision:
    field: str
    raw: str
    normalized: str
    confidence: float
    source_key: str

    def to_dict(self) -> dict[str, object]:
        return {
            "field": self.field,
            "raw": self.raw,
            "normalized": self.normalized,
            "confidence": self.confidence,
            "source_key": self.source_key,
        }


@dataclass(frozen=True, slots=True)
class ReconstructionReport:
    dataset_id: str
    study_id: str
    sample_count: int
    reconstructed_subjects: int
    condition_groups: tuple[str, ...]
    timepoints: tuple[str, ...]
    regions: tuple[str, ...]
    modalities: tuple[str, ...]
    warnings: tuple[str, ...]
    decisions: tuple[ReconstructionDecision, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "study_id": self.study_id,
            "sample_count": self.sample_count,
            "reconstructed_subjects": self.reconstructed_subjects,
            "condition_groups": list(self.condition_groups),
            "timepoints": list(self.timepoints),
            "regions": list(self.regions),
            "modalities": list(self.modalities),
            "warnings": list(self.warnings),
            "decisions": [item.to_dict() for item in self.decisions],
        }


def _first(row: Mapping[str, object], keys: tuple[str, ...]) -> tuple[str, str]:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip(), key
    return "", ""


def _subject_from_accession(accession: str) -> str | None:
    match = re.search(r"(?:animal|donor|subject|mouse|rat|pig|human)[_-]?[A-Za-z0-9]+", accession, re.I)
    return match.group(0) if match else None


def reconstruct_samples(
    rows: Iterable[Mapping[str, object]],
    *,
    dataset_id: str,
    study_id: str,
) -> tuple[list[SampleRecord], ReconstructionReport]:
    records: list[SampleRecord] = []
    decisions: list[ReconstructionDecision] = []
    warnings: list[str] = []

    for row in rows:
        accession, accession_key = _first(row, ("accession", "sample_accession", "geo_accession", "gsm"))
        if not accession:
            raise ValueError("GEO sample metadata requires an accession")

        raw_condition, condition_key = _first(row, ("condition", "group", "phenotype", "disease", "treatment"))
        condition = harmonize_condition(raw_condition) if raw_condition else None
        if condition and condition.normalized:
            decisions.append(ReconstructionDecision("condition", raw_condition, condition.normalized, condition.confidence, condition_key))

        raw_modality, modality_key = _first(row, ("modality", "library_strategy", "assay", "platform", "library_type"))
        modality = harmonize_modality(raw_modality) if raw_modality else harmonize_modality("other")
        decisions.append(ReconstructionDecision("modality", raw_modality or "other", modality.normalized, modality.confidence, modality_key or "default"))

        raw_subject, subject_key = _first(row, ("subject_id", "donor_id", "animal_id", "individual_id", "patient_id"))
        subject = raw_subject or _subject_from_accession(accession)
        if subject:
            decisions.append(ReconstructionDecision("subject_id", raw_subject or accession, subject, 0.99 if raw_subject else 0.55, subject_key or "accession_pattern"))

        region, region_key = _first(row, ("region", "heart_region", "tissue_region", "anatomical_region", "zone"))
        timepoint, timepoint_key = _first(row, ("timepoint", "time_point", "post_injury", "dpi", "day", "days_post_injury"))
        species, species_key = _first(row, ("species", "organism"))
        tissue, tissue_key = _first(row, ("tissue", "source_tissue", "sample_source"))
        cell_context, cell_key = _first(row, ("cell_context", "cell_type", "cell", "nucleus_type"))
        replicate, replicate_key = _first(row, ("replicate_group", "biological_replicate", "replicate", "animal"))

        normalized_condition = condition.normalized if condition else raw_condition
        record = SampleRecord(
            id=f"sample:{canonical_key(accession)}",
            name=str(row.get("name") or accession),
            accession=accession,
            dataset_id=dataset_id,
            study_id=study_id,
            subject_id=subject,
            replicate_group=replicate or None,
            species=normalize_species(species),
            tissue=tissue,
            region=region or None,
            cell_context=cell_context or None,
            condition=normalized_condition,
            timepoint=timepoint or None,
            modality=modality.normalized if modality.normalized in {"bulk_rna", "scrna", "snrna", "proteomics", "imaging", "ecg", "physiology", "clinical", "literature", "other"} else "other",
            is_technical_replicate=str(row.get("is_technical_replicate", "")).lower() in {"1", "true", "yes"},
            metadata_quality="reconstructed",
            metadata={
                "source_keys": {
                    "accession": accession_key,
                    "condition": condition_key,
                    "modality": modality_key,
                    "subject": subject_key or ("accession_pattern" if subject else ""),
                    "region": region_key,
                    "timepoint": timepoint_key,
                    "species": species_key,
                    "tissue": tissue_key,
                    "cell_context": cell_key,
                    "replicate": replicate_key,
                },
                "raw_metadata": dict(row),
            },
        )
        records.append(record)

    if not records:
        warnings.append("no samples reconstructed")
    if any(not item.condition for item in records):
        warnings.append("some samples lack condition metadata")
    if any(not item.timepoint for item in records):
        warnings.append("some samples lack timepoint metadata")
    if any(not item.subject_id for item in records):
        warnings.append("some samples lack subject identifiers; subject-aware leakage control may be limited")

    report = ReconstructionReport(
        dataset_id=dataset_id,
        study_id=study_id,
        sample_count=len(records),
        reconstructed_subjects=len({item.subject_id for item in records if item.subject_id}),
        condition_groups=tuple(sorted({item.condition for item in records if item.condition})),
        timepoints=tuple(sorted({item.timepoint for item in records if item.timepoint})),
        regions=tuple(sorted({item.region for item in records if item.region})),
        modalities=tuple(sorted({item.modality for item in records})),
        warnings=tuple(warnings),
        decisions=tuple(decisions),
    )
    return records, report


def reconstruct_study(
    dataset: DatasetRecord,
    sample_rows: Iterable[Mapping[str, object]],
) -> tuple[StudyRecord, list[SampleRecord], ReconstructionReport]:
    study_id = dataset.study_id or f"study:{canonical_key(dataset.accession)}"
    samples, report = reconstruct_samples(sample_rows, dataset_id=dataset.id, study_id=study_id)
    study = StudyRecord(
        id=study_id,
        name=dataset.study_title or dataset.name,
        accession=dataset.accession,
        repository=dataset.repository,
        title=dataset.study_title or dataset.name,
        organism=dataset.organism,
        tissues=sorted({s.tissue for s in samples if s.tissue} | ({dataset.tissue} if dataset.tissue else set())),
        modalities=sorted({s.modality for s in samples if s.modality != "other"} | set(dataset.modalities)),
        dataset_ids=[dataset.id],
        evidence_ids=list(dataset.evidence_ids),
        design=str(dataset.metadata.get("design", "")),
        publication_ids=[eid for eid in dataset.evidence_ids if eid.startswith("evidence:")],
    )
    return study, samples, report
