from pathlib import Path

import pytest

from cardiatlas.graph import Relation
from cardiatlas.models import DatasetRecord, EvidenceRecord
from cardiatlas.release_lifecycle import create_draft, deprecate, promote_to_candidate, release_record_from_dict, verify
from cardiatlas.sqlite import SQLiteAtlasStore


def _seed_records():
    evidence = EvidenceRecord(id="evidence:e1", name="Some paper", source_type="pubmed", source_identifier="12345678")
    dataset = DatasetRecord(
        id="dataset:geo:GSE1", name="GSE1", accession="GSE1", repository="GEO",
        evidence_ids=[evidence.id], source_ids=[evidence.id],
    )
    relation = Relation(subject=dataset.id, predicate="derived_from", object=evidence.id, evidence_ids=(evidence.id,), confidence=0.9, source="test")
    return [evidence, dataset], [relation]


def test_full_lifecycle_draft_to_deprecated():
    records, relations = _seed_records()

    draft = create_draft(records, "1.0.0", relations)
    assert draft.state == "draft"
    assert draft.readiness.passed

    candidate = promote_to_candidate(draft, records, relations)
    assert candidate.state == "candidate"
    assert [t.to_state for t in candidate.history] == ["draft", "candidate"]

    verified = verify(candidate, records, relations, commit_sha="abc123", ci_passed=True)
    assert verified.state == "verified"
    assert verified.commit_sha == "abc123"
    assert verified.ci_passed is True

    deprecated = deprecate(verified, superseded_by="1.0.1")
    assert deprecated.state == "deprecated"
    assert deprecated.superseded_by == "1.0.1"
    # deprecation must not touch the manifest digest -- it identifies the
    # exact same record content throughout the whole lifecycle.
    assert deprecated.manifest.digest == draft.manifest.digest


def test_verify_requires_candidate_state():
    records, relations = _seed_records()
    draft = create_draft(records, "1.0.0", relations)
    with pytest.raises(ValueError, match="expected 'candidate'"):
        verify(draft, records, relations, commit_sha="abc", ci_passed=True)


def test_verify_requires_ci_passed():
    records, relations = _seed_records()
    candidate = promote_to_candidate(create_draft(records, "1.0.0", relations), records, relations)
    with pytest.raises(ValueError, match="ci_passed"):
        verify(candidate, records, relations, commit_sha="abc", ci_passed=False)


def test_verify_requires_nonempty_commit():
    records, relations = _seed_records()
    candidate = promote_to_candidate(create_draft(records, "1.0.0", relations), records, relations)
    with pytest.raises(ValueError, match="commit_sha"):
        verify(candidate, records, relations, commit_sha="   ", ci_passed=True)


def test_promote_refuses_when_record_set_has_drifted():
    records, relations = _seed_records()
    draft = create_draft(records, "1.0.0", relations)
    drifted_records = records + [DatasetRecord(id="dataset:geo:GSE2", name="GSE2", accession="GSE2", repository="GEO")]
    with pytest.raises(ValueError, match="record set has changed"):
        promote_to_candidate(draft, drifted_records, relations)


def test_promote_refuses_unresolved_structural_errors():
    evidence, dataset = _seed_records()[0]
    duplicate_id_records = [dataset, DatasetRecord(id=dataset.id, name="dup", accession="GSE1", repository="GEO")]
    relations: list[Relation] = []
    draft = create_draft(duplicate_id_records, "1.0.0", relations)
    assert not draft.readiness.passed
    with pytest.raises(ValueError, match="structural checks failing"):
        promote_to_candidate(draft, duplicate_id_records, relations)


def test_release_record_round_trips_through_dict():
    records, relations = _seed_records()
    draft = create_draft(records, "1.0.0", relations)
    restored = release_record_from_dict(draft.to_dict())
    assert restored.manifest.digest == draft.manifest.digest
    assert restored.state == draft.state
    assert [t.to_state for t in restored.history] == [t.to_state for t in draft.history]


def test_sqlite_persists_lifecycle_across_reopen(tmp_path: Path):
    path = tmp_path / "atlas.sqlite"
    records, relations = _seed_records()
    with SQLiteAtlasStore(path) as store:
        store.upsert_many(records)
        for relation in relations:
            store.put_relation(relation)
        draft = create_draft(store.all_records(), "1.0.0", store.graph().relations())
        store.save_release_record(draft)

    with SQLiteAtlasStore(path) as reopened:
        reloaded = reopened.get_release_record("1.0.0")
        assert reloaded is not None
        assert reloaded.state == "draft"
        candidate = promote_to_candidate(reloaded, reopened.all_records(), reopened.graph().relations())
        reopened.save_release_record(candidate)
        assert [r["state"] for r in reopened.list_release_records()] == ["candidate"]
        assert reopened.list_release_records(state="candidate")
        assert reopened.list_release_records(state="verified") == []
