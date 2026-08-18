from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import DatasetRecord, StudyRecord
from .normalize import canonical_key


@dataclass(frozen=True, slots=True)
class CatalogGroup:
    key: str
    dataset_ids: tuple[str, ...]
    accessions: tuple[str, ...]
    organisms: tuple[str, ...]
    modalities: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "dataset_ids": list(self.dataset_ids),
            "accessions": list(self.accessions),
            "organisms": list(self.organisms),
            "modalities": list(self.modalities),
        }


def group_datasets(datasets: list[DatasetRecord]) -> list[CatalogGroup]:
    groups: dict[str, list[DatasetRecord]] = defaultdict(list)
    for dataset in datasets:
        key = canonical_key(dataset.study_id or dataset.study_title or dataset.accession)
        groups[key].append(dataset)
    result: list[CatalogGroup] = []
    for key, items in sorted(groups.items()):
        result.append(
            CatalogGroup(
                key=key,
                dataset_ids=tuple(sorted(item.id for item in items)),
                accessions=tuple(sorted({item.accession for item in items if item.accession})),
                organisms=tuple(sorted({item.organism for item in items if item.organism})),
                modalities=tuple(sorted({m for item in items for m in item.modalities})),
            )
        )
    return result


def attach_datasets(study: StudyRecord, datasets: list[DatasetRecord]) -> StudyRecord:
    attached = [dataset.id for dataset in datasets if dataset.study_id == study.id or dataset.accession == study.accession]
    if not attached:
        return study
    return StudyRecord(
        **{**study.to_dict(), "dataset_ids": sorted(set(study.dataset_ids) | set(attached)), "schema_version": study.schema_version}
    )
