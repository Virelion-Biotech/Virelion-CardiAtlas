from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .acquisition import AcquisitionTarget, acquisition_plan
from .harvest import HarvestItem, harvest_report
from .models import DatasetRecord, EvidenceRecord, Record, SampleRecord, StudyRecord
from .release import digest_records


@dataclass(frozen=True, slots=True)
class CorpusReport:
    record_count: int
    evidence_count: int
    dataset_count: int
    study_count: int
    sample_count: int
    unique_sources: int
    record_digest: str
    harvest_digest: str
    domains: tuple[str, ...]
    acquisition_targets: int

    def to_dict(self) -> dict[str, object]:
        return {
            "record_count": self.record_count,
            "evidence_count": self.evidence_count,
            "dataset_count": self.dataset_count,
            "study_count": self.study_count,
            "sample_count": self.sample_count,
            "unique_sources": self.unique_sources,
            "record_digest": self.record_digest,
            "harvest_digest": self.harvest_digest,
            "domains": list(self.domains),
            "acquisition_targets": self.acquisition_targets,
        }


def corpus_report(
    records: Iterable[Record],
    targets: list[AcquisitionTarget] | None = None,
    harvest_items: Iterable[HarvestItem] = (),
) -> CorpusReport:
    values = list(records)
    evidence = [record for record in values if isinstance(record, EvidenceRecord)]
    datasets = [record for record in values if isinstance(record, DatasetRecord)]
    studies = [record for record in values if isinstance(record, StudyRecord)]
    samples = [record for record in values if isinstance(record, SampleRecord)]
    sources = {record.source_identifier for record in evidence if record.source_identifier}
    sources.update(record.repository for record in datasets if record.repository)
    domains = {
        tag
        for record in values
        for tag in record.tags
        if tag and not tag.startswith("seed")
    }
    selected = targets if targets is not None else acquisition_plan()
    harvest = harvest_report(harvest_items)
    return CorpusReport(
        record_count=len(values),
        evidence_count=len(evidence),
        dataset_count=len(datasets),
        study_count=len(studies),
        sample_count=len(samples),
        unique_sources=len(sources),
        record_digest=digest_records(values),
        harvest_digest=str(harvest["digest"]),
        domains=tuple(sorted(domains)),
        acquisition_targets=len(selected),
    )
