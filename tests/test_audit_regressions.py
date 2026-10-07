from dataclasses import replace
from pathlib import Path

import pytest

from cardiatlas.claims import Claim, ClaimStore
from cardiatlas.evidence import score_evidence
from cardiatlas.geo_reconstruct import reconstruct_samples
from cardiatlas.geo_soft import parse_geo_soft, samples_to_rows
from cardiatlas.graph import Relation
from cardiatlas.loader import read_bundle, record_from_dict
from cardiatlas.models import DatasetRecord, EvidenceRecord, SampleRecord, StudyRecord
from cardiatlas.release_checks import assess_release
from cardiatlas.release_lifecycle import create_draft, promote_to_candidate
from cardiatlas.study_readiness import assess_study_benchmark_readiness
from cardiatlas.validation import require_valid


def study_fixture():
    dataset = DatasetRecord(
        id="dataset:x", name="x", accession="GSE1", organism="mouse", tissue="heart", evidence_ids=["e:1"]
    )
    study = StudyRecord(id="study:x", name="x", accession="GSE1", dataset_ids=[dataset.id])
    samples = [
        SampleRecord(
            id=f"sample:{i}",
            name=str(i),
            accession=f"GSM{i}",
            dataset_id=dataset.id,
            study_id=study.id,
            subject_id=f"m{i}",
            condition=c,
            modality="scrna",
        )
        for i, c in enumerate(["MI", "reference"])
    ]
    return dataset, study, samples


@pytest.mark.parametrize("field,value", [("condition", ""), ("modality", "other")])
def test_every_sample_needs_condition_and_modality(field, value):
    d, s, rows = study_fixture()
    rows.append(replace(rows[0], id="sample:3", accession="GSM3", **{field: value}))
    assert not assess_study_benchmark_readiness(s, d, rows).ready


def test_foreign_samples_cannot_supply_condition_groups():
    d, s, rows = study_fixture()
    rows[1] = replace(rows[1], study_id="study:foreign")
    assert not assess_study_benchmark_readiness(s, d, rows).ready


def test_missing_tissue_is_not_replaced_by_nonzero_sample_count():
    d, s, rows = study_fixture()
    assert not assess_study_benchmark_readiness(s, replace(d, tissue=""), rows).ready


def test_missing_evidence_does_not_support_claim():
    store = ClaimStore()
    store.add(
        Claim(
            id="c", subject="a", predicate="marks", object="b", polarity="supports", evidence_ids=("missing",)
        )
    )
    assert store.assess("c", {}).status == "undetermined"


def test_repeated_paper_does_not_inflate_evidence_score():
    e = EvidenceRecord(
        id="e", name="paper", source_type="pubmed", source_identifier="123", evidence_level="primary"
    )
    assert score_evidence([e, e]) == score_evidence([e])


def test_relationship_drift_invalidates_release_transition():
    e = EvidenceRecord(id="e", name="paper")
    d = DatasetRecord(id="d", name="dataset", accession="GSE1")
    edge = Relation("d", "derived_from", "e", ("e",), 0.9)
    draft = create_draft([e, d], "x", [edge])
    with pytest.raises(ValueError, match="relationship"):
        promote_to_candidate(draft, [e, d], [replace(edge, confidence=0.1)])


def test_closed_graph_checks_evidence_ids_not_just_source_ids():
    d = DatasetRecord(id="d", name="dataset", accession="GSE1", evidence_ids=["missing"])
    assert not assess_release([d]).passed


@pytest.mark.parametrize(
    "change",
    [
        {"modality": "invented"},
        {"is_technical_replicate": "false"},
        {"tags": "string"},
        {"metadata": {"bad": float("nan")}},
        {"subject_id": 123},
    ],
)
def test_record_fields_follow_declared_types(change):
    _, _, rows = study_fixture()
    with pytest.raises(ValueError):
        require_valid(replace(rows[0], **change))


def test_unknown_record_fields_are_not_silently_discarded():
    with pytest.raises(ValueError, match="unknown"):
        record_from_dict({"id": "e", "name": "e", "record_type": "evidence", "typo_source_identifier": "123"})


def test_optical_records_are_loadable_by_public_loader():
    root = Path(__file__).resolve().parents[1]
    assert (
        len(
            read_bundle(
                [
                    root / "data/reference/optical_stimulation_evidence.jsonl",
                    root / "data/reference/optical_stimulation_interventions.jsonl",
                ]
            )
        )
        == 8
    )


def test_conflicting_subject_metadata_is_not_one_explicit_subject():
    text = "^SAMPLE = GSM1\n!Sample_characteristics_ch1 = subject: mouse1\n!Sample_characteristics_ch1 = subject: mouse2\n"
    records, report = reconstruct_samples(samples_to_rows(parse_geo_soft(text)), dataset_id="d", study_id="s")
    assert records[0].subject_id is None
    assert report.reconstructed_subjects == 0


def test_null_primary_subject_field_can_use_explicit_donor():
    records, _ = reconstruct_samples(
        [{"accession": "GSM1", "subject_id": "NA", "donor_id": "real-donor"}], dataset_id="d", study_id="s"
    )
    assert records[0].subject_id == "real-donor"
