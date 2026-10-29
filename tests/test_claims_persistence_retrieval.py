from __future__ import annotations

import pytest

from cardiatlas.claims import Claim, ClaimEvidence
from cardiatlas.evidence import score_evidence
from cardiatlas.models import DatasetRecord, EvidenceRecord, MarkerRecord, SampleRecord, StudyRecord
from cardiatlas.retrieval import retrieve
from cardiatlas.service import AtlasService
from cardiatlas.sqlite import SQLiteAtlasStore
from cardiatlas.loader import read_bundle
from cardiatlas.release_checks import assess_release
from cardiatlas.release_lifecycle import create_draft, promote_to_candidate


def _evidence(eid: str, source_id: str, level: str) -> EvidenceRecord:
    return EvidenceRecord(
        id=eid, name=eid, source_type="pubmed", source_identifier=source_id,
        evidence_level=level, polarity="supports",
    )


def _claim(version: int = 1, status: str = "source_verified") -> Claim:
    citation = ClaimEvidence(
        evidence_id="evidence:paper", source_locator="https://example.org/paper#results",
        locator_label="Results", quote="A source-checked result.", review_status=status,
        reviewer_id="reviewer:demo" if status == "expert_reviewed" else None,
        reviewed_at="2026-10-29" if status != "unreviewed" else None,
    )
    return Claim(
        id="claim:example", subject="marker:postn", predicate="associated_with",
        object="state:activated_fibroblast", polarity="supports",
        evidence_ids=("evidence:paper",), notes=f"revision {version}",
        version=version, supersedes="claim:example@1" if version > 1 else None,
        citations=(citation,),
    )


def test_evidence_deduplication_is_order_independent_and_keeps_strongest_level():
    weak = _evidence("evidence:weak", "  PMID-1 ", "inferred")
    strong = _evidence("evidence:strong", "pmid-1", "primary")
    other = _evidence("evidence:other", "PMID-2", "review")
    forward = score_evidence([weak, strong, other])
    reverse = score_evidence([other, strong, weak])
    assert forward == reverse
    assert forward.evidence_count == 2
    assert forward.primary_count == 1
    assert forward.independent_sources == 2


def test_claim_revision_persists_across_reopen_and_history_is_retained(tmp_path):
    db = tmp_path / "atlas.sqlite"
    first = _claim()
    with SQLiteAtlasStore(db) as store:
        service = store.load_service()
        service.add(_evidence("evidence:paper", "PMID-1", "primary"))
        service.add_claim(first)
        store.save_service(service)
        service.claims.upsert(_claim(version=2))
        store.save_service(service)
    with SQLiteAtlasStore(db) as reopened:
        service = reopened.load_service()
        assert service.claims.get("claim:example").version == 2
        assert [item.version for item in reopened.claim_history("claim:example")] == [1, 2]
        assert service.assess_claim("claim:example").status == "supported"
        assert service.assess_claim("claim:example").evidence_count == 1


def test_claim_evidence_verified_status_requires_source_locator():
    with pytest.raises(ValueError, match="source_locator"):
        ClaimEvidence(evidence_id="evidence:1", source_locator="", review_status="source_verified")


def test_retrieval_partial_matches_have_stable_scores_and_explain_terms():
    service = AtlasService.empty()
    target = MarkerRecord(
        id="marker:postn", name="POSTN", description="activated cardiac fibroblast marker",
        entity_id="POSTN", cell_types=["fibroblast"], states=["activated_fibroblast"],
    )
    unrelated = MarkerRecord(id="marker:tnnt2", name="TNNT2", description="cardiomyocyte marker", entity_id="TNNT2")
    service.add(target)
    service.add(unrelated)
    first = retrieve(service.registry, "activated cardiac fibroblast")
    second = retrieve(service.registry, "activated cardiac fibroblast")
    assert [hit.record.id for hit in first] == [hit.record.id for hit in second]
    assert first[0].record.id == target.id
    assert set(first[0].matched_terms) == {"activated", "cardiac", "fibroblast"}
    assert 0 < first[0].lexical_score <= 1
    assert first[0].to_dict()["score_semantics"].startswith("lexical relevance only")


def test_gse132880_reference_fixture_is_benchmark_ready():
    records = read_bundle(["data/reference/cardiatlas_gse132880.jsonl"])
    service = AtlasService.empty()
    service.add_many(records)
    dataset = service.registry.get("dataset:gse132880")
    study = service.registry.get("study:gse132880")
    assert isinstance(dataset, DatasetRecord)
    assert isinstance(study, StudyRecord)
    result = service.assess_study_benchmark_readiness(study.id, dataset.id)
    assert result.ready, result.to_dict()
    assert result.checks["subject_structure"]
    assert result.checks["subject_mapping_provenance"]
    assert len([r for r in records if isinstance(r, SampleRecord)]) == 8


def test_release_gate_rejects_unreviewed_claim_citations():
    source = _evidence("evidence:paper", "PMID-1", "primary")
    dataset = DatasetRecord(id="dataset:test", name="Test", accession="GSE1", repository="GEO", source_ids=[source.id])
    readiness = assess_release([source, dataset], claims=[_claim(status="unreviewed")], require_claim_review=True)
    check = next(item for item in readiness.checks if item.name == "claim_provenance")
    assert not check.passed and check.severity == "error"


def test_release_candidate_locks_claim_digest_and_requires_reviewed_citations():
    source = _evidence("evidence:paper", "PMID-1", "primary")
    dataset = DatasetRecord(id="dataset:test", name="Test", accession="GSE1", repository="GEO", source_ids=[source.id])
    records = [source, dataset]
    staged = create_draft(records, "1.0.0", claims=[_claim()])
    candidate = promote_to_candidate(staged, records, claims=[_claim()])
    assert candidate.state == "candidate"
    with pytest.raises(ValueError, match="claim set has changed"):
        promote_to_candidate(staged, records, claims=[_claim(version=2)])
