from __future__ import annotations

from collections.abc import Iterable, Mapping

from .harmonize import harmonize_condition, harmonize_modality
from .models import SampleRecord
from .normalize import canonical_key


def sample_from_metadata(
    row: Mapping[str, object],
    *,
    dataset_id: str,
    study_id: str | None = None,
) -> SampleRecord:
    accession = str(row.get("accession") or row.get("sample_accession") or "").strip()
    if not accession:
        raise ValueError("sample metadata requires accession")
    raw_condition = str(row.get("condition") or row.get("group") or row.get("phenotype") or "").strip()
    raw_modality = str(row.get("modality") or "other").strip()
    condition = harmonize_condition(raw_condition) if raw_condition else None
    modality = harmonize_modality(raw_modality)
    subject = row.get("subject_id") or row.get("donor_id") or row.get("animal_id")
    replicate = row.get("replicate_group") or row.get("biological_replicate")
    name = str(row.get("name") or accession)
    normalized = dict(row)
    normalized["condition_normalized"] = condition.normalized if condition else ""
    if condition:
        normalized["condition_concept_id"] = condition.concept_id
        normalized["condition_confidence"] = condition.confidence
    normalized["modality_normalized"] = modality.normalized
    normalized["modality_confidence"] = modality.confidence
    return SampleRecord(
        id=f"sample:{canonical_key(accession)}",
        name=name,
        accession=accession,
        dataset_id=dataset_id,
        study_id=study_id,
        subject_id=str(subject) if subject else None,
        replicate_group=str(replicate) if replicate else None,
        species=str(row.get("species") or ""),
        tissue=str(row.get("tissue") or ""),
        region=str(row.get("region")) if row.get("region") else None,
        cell_context=str(row.get("cell_context") or row.get("cell_type")) if (row.get("cell_context") or row.get("cell_type")) else None,
        condition=condition.normalized if condition else raw_condition,
        timepoint=str(row.get("timepoint")) if row.get("timepoint") else None,
        modality=modality.normalized if modality.normalized in {"bulk_rna", "scrna", "snrna", "proteomics", "imaging", "ecg", "physiology", "clinical", "literature", "other"} else "other",
        is_technical_replicate=bool(row.get("is_technical_replicate", False)),
        metadata_quality=str(row.get("metadata_quality") or "normalized"),
        metadata=normalized,
    )


def ingest_sample_rows(rows: Iterable[Mapping[str, object]], *, dataset_id: str, study_id: str | None = None) -> list[SampleRecord]:
    records: list[SampleRecord] = []
    seen: set[str] = set()
    for row in rows:
        record = sample_from_metadata(row, dataset_id=dataset_id, study_id=study_id)
        if record.id in seen:
            raise ValueError(f"duplicate sample accession: {record.accession}")
        seen.add(record.id)
        records.append(record)
    return records
