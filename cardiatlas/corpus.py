from __future__ import annotations

from dataclasses import dataclass

from .acquisition import AcquisitionTarget, acquisition_plan
from .models import DatasetRecord, EvidenceRecord, Record
from .release import digest_records


@dataclass(frozen=True, slots=True)
class CorpusReport:
    record_count: int
    evidence_count: int
    dataset_count: int
    unique_sources: int
    record_digest: str
    domains: tuple[str, ...]
    acquisition_targets: int

    def to_dict(self) -> dict[str, object]:
        return {
            "record_count": self.record_count,
            "evidence_count": self.evidence_count,
            "dataset_count": self.dataset_count,
            "unique_sources": self.unique_sources,
            "record_digest": self.record_digest,
            "domains": list(self.domains),
            "acquisition_targets": self.acquisition_targets,
        }


def corpus_report(records: list[Record], targets: list[AcquisitionTarget] | None = None) -> CorpusReport:
    evidence = [record for record in records if isinstance(record, EvidenceRecord)]
    datasets = [record for record in records if isinstance(record, DatasetRecord)]
    sources = {
        record.source_identifier
        for record in evidence
        if record.source_identifier
    }
    domains = {
        tag
        for record in records
        for tag in record.tags
        if tag and not tag.startswith("seed")
    }
    selected = targets if targets is not None else acquisition_plan()
    return CorpusReport(
        record_count=len(records),
        evidence_count=len(evidence),
        dataset_count=len(datasets),
        unique_sources=len(sources),
        record_digest=digest_records(records),
        domains=tuple(sorted(domains)),
        acquisition_targets=len(selected),
    )
