from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .graph import Relation, AtlasGraph
from .models import DatasetRecord, EvidenceRecord, Record, SampleRecord, StudyRecord
from .release import digest_records
from .schema import RELATION_TYPES
from .ontology import CONCEPTS
from .study_readiness import assess_study_benchmark_readiness
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


def _benchmark_readiness_summary(records: list[Record]) -> tuple[int, int, list[str]]:
    """Aggregate per-study benchmark readiness (release-checklist item 5).

    A release with no StudyRecords at all (e.g. an evidence/ontology-only
    release) has nothing to fail here, so it reports 0/0 rather than blocking.
    """
    studies = [r for r in records if isinstance(r, StudyRecord)]
    if not studies:
        return 0, 0, []
    datasets = {r.id: r for r in records if isinstance(r, DatasetRecord)}
    samples_by_study: dict[str, list[SampleRecord]] = {}
    for r in records:
        if isinstance(r, SampleRecord) and r.study_id:
            samples_by_study.setdefault(r.study_id, []).append(r)
    not_ready: list[str] = []
    for study in studies:
        dataset = next((datasets[did] for did in study.dataset_ids if did in datasets), None)
        if dataset is None:
            not_ready.append(study.id)
            continue
        readiness = assess_study_benchmark_readiness(study, dataset, samples_by_study.get(study.id, []))
        if not readiness.ready:
            not_ready.append(study.id)
    return len(studies), len(studies) - len(not_ready), not_ready


def assess_release(
    records: list[Record],
    relations: Iterable[Relation] = (),
    *,
    closed_evidence_graph: bool = True,
    require_benchmark_ready: bool = False,
) -> ReleaseReadiness:
    """Run release-checklist checks (docs/release-checklist.md) over a record set.

    ``closed_evidence_graph`` controls whether unresolved provenance is a hard
    error (checklist item 4: only required "when a release claims a closed
    evidence graph") or a warning -- a draft release may legitimately still
    have open provenance. ``require_benchmark_ready`` similarly controls
    whether every study in the release must pass its benchmark-readiness gate
    (item 5) or whether that's surfaced as advisory information.
    """
    checks: list[ReleaseCheck] = []
    validation_errors = [(r.id, validate_record(r)) for r in records]
    invalid = [(rid, errs) for rid, errs in validation_errors if errs]
    checks.append(ReleaseCheck("record_validation", not invalid, "error", f"{len(invalid)} invalid records"))

    ids = [record.id for record in records]
    duplicates = len(ids) - len(set(ids))
    checks.append(ReleaseCheck("unique_ids", duplicates == 0, "error", f"{duplicates} duplicate IDs"))

    evidence = [record for record in records if isinstance(record, EvidenceRecord)]
    checks.append(ReleaseCheck("evidence_inventory", len(evidence) > 0 or not records, "warning", f"{len(evidence)} evidence records indexed"))

    datasets = [record for record in records if isinstance(record, DatasetRecord)]
    accession_dups = len([d.accession for d in datasets if d.accession]) - len({d.accession for d in datasets if d.accession})
    checks.append(ReleaseCheck("dataset_accessions", accession_dups == 0, "error", f"{accession_dups} duplicate dataset accessions"))

    orphan_sources = 0
    evidence_ids = {record.id for record in evidence}
    for record in records:
        for source_id in set(record.source_ids + getattr(record, "evidence_ids", [])):
            if source_id not in evidence_ids:
                orphan_sources += 1
    # Item 4 is explicitly conditional: only a release that *claims* a closed
    # evidence graph must have zero unresolved provenance references.
    provenance_severity = "error" if closed_evidence_graph else "warning"
    checks.append(ReleaseCheck("provenance_links", orphan_sources == 0, provenance_severity, f"{orphan_sources} unresolved source references"))

    # Item 6: controlled relationship predicates. AtlasGraph.add() already
    # rejects an unrecognized predicate at insertion time, but a release may
    # assemble relations from a persisted store or an external bundle that
    # bypassed that guard, so this is checked again, independently, here.
    materialized_relations = list(relations)
    known_nodes = set(ids) | {concept.id for concept in CONCEPTS}
    unresolved_nodes = sorted({node for relation in materialized_relations for node in (relation.subject, relation.object) if node not in known_nodes})
    checks.append(ReleaseCheck("relationship_endpoints", not unresolved_nodes, "warning", f"{len(unresolved_nodes)} external or unresolved graph nodes: {unresolved_nodes}"))
    uncited = sum(not relation.evidence_ids for relation in materialized_relations)
    checks.append(ReleaseCheck("relationship_citations", uncited == 0, "warning", f"{uncited} relationships have no indexed evidence citations; curated source labels are not claim validation"))
    invalid_relations = 0
    for relation in materialized_relations:
        try:
            AtlasGraph([relation])
        except (TypeError, ValueError):
            invalid_relations += 1
    checks.append(ReleaseCheck("relationship_validation", invalid_relations == 0, "error", f"{invalid_relations} invalid relationships"))
    orphan_relation_evidence = sum(eid not in evidence_ids for relation in materialized_relations for eid in relation.evidence_ids)
    checks.append(ReleaseCheck("relationship_evidence", orphan_relation_evidence == 0, provenance_severity, f"{orphan_relation_evidence} unresolved relationship evidence references"))
    bad_predicates = sorted({r.predicate for r in materialized_relations if r.predicate not in RELATION_TYPES})
    checks.append(ReleaseCheck(
        "controlled_predicates",
        not bad_predicates,
        "error",
        "all relationship predicates are controlled" if not bad_predicates else f"unrecognized predicates: {', '.join(bad_predicates)}",
    ))

    # Item 5: sample metadata must carry enough biological grouping for the
    # intended benchmark/analysis use, assessed per study via the same gate
    # docs/geo-reconstruction.md describes ("Benchmark gate").
    total_studies, ready_studies, not_ready = _benchmark_readiness_summary(records)
    benchmark_severity = "error" if require_benchmark_ready else "warning"
    if total_studies:
        message = f"{ready_studies}/{total_studies} studies benchmark-ready"
        if not_ready:
            message += f" (not ready: {', '.join(not_ready[:5])}{', ...' if len(not_ready) > 5 else ''})"
    else:
        message = "no studies in release"
    checks.append(ReleaseCheck("benchmark_readiness", ready_studies == total_studies, benchmark_severity, message))

    checks.append(ReleaseCheck("nonempty_release", bool(records), "error", "release contains no records" if not records else f"{len(records)} records"))
    passed = all(check.passed or check.severity != "error" for check in checks)
    return ReleaseReadiness(passed, tuple(checks), digest_records(records))
