from __future__ import annotations

import json
from dataclasses import replace
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import pytest
from hypothesis import given, settings, strategies as st

from cardiatlas.adapters import pubmed_summary_to_evidence
from cardiatlas.cli import main
from cardiatlas.geo_reconstruct import reconstruct_samples
from cardiatlas.graph import AtlasGraph, Relation
from cardiatlas.integrations import benchmark_readiness
from cardiatlas.jsonutil import strict_loads
from cardiatlas.models import DatasetRecord, EvidenceRecord
from cardiatlas.ncbi import NcbiClient
from cardiatlas.registry import AtlasRegistry
from cardiatlas.release import digest_records, digest_relations
from cardiatlas.release_lifecycle import create_draft, promote_to_candidate, release_record_from_dict
from cardiatlas.retrieval import retrieve
from cardiatlas.sqlite import SQLiteAtlasStore


@pytest.mark.parametrize("payload", ['{"id":1,"id":2}', '{"x":NaN}', '{"x":1e999}'])
def test_json_rejects_ambiguous_or_nonfinite_input(payload):
    with pytest.raises(ValueError):
        strict_loads(payload)


def test_ambiguous_rna_strategy_is_not_bulk():
    records, _ = reconstruct_samples(
        [{"accession": "GSM1", "library_strategy": "RNA-Seq"}], dataset_id="d", study_id="s"
    )
    assert records[0].modality == "other"


@pytest.mark.parametrize(
    "title,expected",
    [("scRNA-seq_P1_1MI", "scrna"), ("snRNA-seq donor 1", "snrna"), ("bulk RNA-seq", "bulk_rna")],
)
def test_explicit_assay_in_title_has_provenance(title, expected):
    records, _ = reconstruct_samples(
        [{"accession": "GSM1", "library_strategy": "RNA-Seq", "name": title}], dataset_id="d", study_id="s"
    )
    assert records[0].modality == expected
    assert records[0].metadata["source_keys"]["modality"] == "name"


def test_sqlite_validates_entire_batch_before_writing(tmp_path):
    valid = EvidenceRecord(id="e", name="paper")
    with SQLiteAtlasStore(tmp_path / "a.sqlite") as store:
        with pytest.raises(ValueError):
            store.upsert_many([valid, replace(valid, id="e2", year="invalid")])
        assert store.count() == 0
        with pytest.raises(ValueError):
            store.put_relation(Relation("a", "invented", "b"))
        assert store.all_relations() == []


@pytest.mark.parametrize("confidence", [float("nan"), float("inf"), True])
def test_graph_rejects_invalid_confidence(confidence):
    with pytest.raises(ValueError):
        AtlasGraph([Relation("a", "supports", "b", confidence=confidence)])


def test_legacy_release_requires_new_graph_locked_draft():
    records = [EvidenceRecord(id="e", name="paper")]
    data = create_draft(records, "v").to_dict()
    data.pop("relationship_digest")
    with pytest.raises(ValueError, match="legacy"):
        promote_to_candidate(release_record_from_dict(data), records)


def test_graph_digest_is_order_independent_and_includes_evidence():
    a = Relation("a", "supports", "b", ("e2", "e1"), 0.5)
    b = Relation("b", "supports", "a", ("e1",), 0.6)
    assert digest_relations([a, b]) == digest_relations([b, replace(a, evidence_ids=("e1", "e2"))])
    assert digest_relations([a, b]) != digest_relations([replace(a, evidence_ids=("e1",)), b])
    release = create_draft([EvidenceRecord(id="e", name="paper")], "v", iter([a, b]))
    assert release.relationship_digest == digest_relations([a, b])


def test_dataset_readiness_requires_distinct_conditions():
    d = DatasetRecord(
        id="d",
        name="d",
        accession="GSE1",
        organism="mouse",
        tissue="heart",
        modalities=["scrna"],
        conditions=["MI", "MI"],
        source_ids=["e"],
    )
    assert not benchmark_readiness(d)["ready"]


def test_pubmed_bibliography_does_not_automatically_claim_primary_evidence():
    assert (
        pubmed_summary_to_evidence({"uid": "1", "title": "Review", "pubtype": ["Review"]}).evidence_level
        == "review"
    )
    assert (
        pubmed_summary_to_evidence(
            {"uid": "2", "title": "Article", "pubtype": ["Journal Article"]}
        ).evidence_level
        == "curated"
    )


def test_multiword_retrieval_reports_individual_matched_terms():
    registry = AtlasRegistry()
    registry.add(EvidenceRecord(id="e", name="cardiac fibrosis"))
    assert retrieve(registry, "cardiac fibrosis")[0].matched_terms == ("cardiac", "fibrosis")


def test_cli_bad_metadata_returns_error_and_does_not_commit_partial_changes(tmp_path, capsys):
    records = tmp_path / "r.jsonl"
    records.write_text(json.dumps(EvidenceRecord(id="e", name="paper").to_dict()) + "\n")
    relations = tmp_path / "bad.jsonl"
    relations.write_text('{"subject":"a","subject":"b"}\n')
    db = tmp_path / "a.sqlite"
    assert main(["load", str(db), str(records), "--relations", str(relations)]) == 2
    assert "duplicate" in capsys.readouterr().err
    with SQLiteAtlasStore(db) as store:
        assert store.count() == 0


def test_ncbi_retries_rate_limit_and_limits_permanent_failures():
    client = NcbiClient(min_interval=0, max_retries=2)
    response = BytesIO(b'{"esearchresult":{"idlist":["1"]}}')
    error = HTTPError("http://example", 429, "rate limited", {"Retry-After": "0"}, None)
    with (
        patch("cardiatlas.ncbi.urllib.request.urlopen", side_effect=[error, response]) as request,
        patch("cardiatlas.ncbi.time.sleep"),
    ):
        assert client.esearch("pubmed", "heart") == ["1"]
        assert request.call_count == 2
    permanent = HTTPError("http://example", 404, "missing", {}, None)
    with patch("cardiatlas.ncbi.urllib.request.urlopen", side_effect=permanent) as request:
        with pytest.raises(HTTPError):
            client.esearch("pubmed", "heart")
        assert request.call_count == 1


@pytest.mark.parametrize("retmax", [-1, True, 1.5, "1"])
def test_ncbi_rejects_invalid_limits_without_network(retmax):
    with pytest.raises(ValueError):
        NcbiClient().esearch("pubmed", "heart", retmax)


@given(
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8),
        min_size=1,
        max_size=15,
        unique=True,
    )
)
@settings(max_examples=30, deadline=None)
def test_record_digest_stable_under_order_and_mutation(ids):
    records = [EvidenceRecord(id=key, name=key) for key in ids]
    assert digest_records(records) == digest_records(reversed(records))
    assert digest_records(records) != digest_records(
        [replace(records[0], name=records[0].name + " changed"), *records[1:]]
    )


def test_geo_lookup_selects_matching_series_not_first_summary():
    from cardiatlas.geo_harvest import reconstruct_geo_accession
    from unittest.mock import Mock

    client = Mock()
    client.esearch.return_value = ["wrong", "right"]
    client.esummary.return_value = {
        "uids": ["wrong", "right"],
        "wrong": {"accession": "GSE2", "title": "wrong"},
        "right": {"accession": "GSE1", "title": "right", "taxon": "Mus musculus"},
    }
    client.fetch_geo_family_soft.return_value = b"^SAMPLE = GSM1\n!Sample_title = scRNA-seq\n"
    client.geo_family_soft_url.return_value = "https://example/GSE1"
    bundle = reconstruct_geo_accession(client, "GSE1")
    assert bundle.dataset.name == "right"
    assert bundle.dataset.organism == "Mus musculus"
    with pytest.raises(ValueError, match="does not match"):
        reconstruct_geo_accession(client, "GSE1", {"accession": "GSE2"})
    client.esummary.return_value = {"wrong": {"accession": "GSE2"}}
    with pytest.raises(ValueError, match="matching Series"):
        reconstruct_geo_accession(client, "GSE1")
