from __future__ import annotations

from dataclasses import dataclass

from .models import DatasetRecord, EvidenceRecord, Record
from .release import digest_records
from .validation import validate_record


@dataclass(frozen=True, slots=True)
class ReleaseCheck:
    name: str
    passed: bool
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class ReleaseReadiness:
    passed: bool
    checks: tuple[ReleaseCheck, ...]
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "digest": self.digest,
            "checks": [
                {"name": c.name, "passed": c.passed, "severity": c.severity, "message": c.message}
                for c in self.checks
            ],
        }


def assess_release(records: list[Record]) -> ReleaseReadiness:
    checks: list[ReleaseCheck] = []
    validation_errors = [(r.id, validate_record(r)) for r in records]
    invalid = [(rid, errs) for rid, errs in validation_errors if errs]
    checks.append(ReleaseCheck("record_validation", not invalid, "error", f"{len(invalid)} invalid records"))

    ids = [record.id for record in records]
    duplicates = len(ids) - len(set(ids))
    checks.append(ReleaseCheck("unique_ids", duplicates == 0, "error", f"{duplicates} duplicate IDs"))

    evidence = [record for record in records if isinstance(record, EvidenceRecord)]
    missing_evidence_ids = [record.id for record in records if record.source_ids and not evidence]
    checks.append(ReleaseCheck("evidence_inventory", len(evidence) > 0 or not records, "warning", f"{len(evidence)} evidence records indexed"))

    datasets = [record for record in records if isinstance(record, DatasetRecord)]
    accession_dups = len([d.accession for d in datasets if d.accession]) - len({d.accession for d in datasets if d.accession})
    checks.append(ReleaseCheck("dataset_accessions", accession_dups == 0, "error", f"{accession_dups} duplicate dataset accessions"))

    orphan_sources = 0
    evidence_ids = {record.id for record in evidence}
    for record in records:
        for source_id in record.source_ids:
            if source_id not in evidence_ids:
                orphan_sources += 1
    checks.append(ReleaseCheck("provenance_links", orphan_sources == 0, "error", f"{orphan_sources} unresolved source references"))

    checks.append(ReleaseCheck("nonempty_release", bool(records), "error", "release contains no records" if not records else f"{len(records)} records"))
    passed = all(check.passed or check.severity != "error" for check in checks)
    return ReleaseReadiness(passed, tuple(checks), digest_records(records))
