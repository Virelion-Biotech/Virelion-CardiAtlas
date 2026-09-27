import json
from pathlib import Path

from cardiatlas.cli import main


def _write_records(path: Path) -> None:
    records = [
        {"id": "evidence:e1", "record_type": "evidence", "name": "Cardiac remodeling paper", "schema_version": "0.3", "source_type": "pubmed", "source_identifier": "1"},
        {"id": "dataset:geo:GSE1", "record_type": "dataset", "name": "GSE1", "schema_version": "0.3", "accession": "GSE1", "repository": "GEO", "source_ids": ["evidence:e1"]},
    ]
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _write_relations(path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"subject": "dataset:geo:GSE1", "predicate": "derived_from", "object": "evidence:e1", "confidence": 0.9, "source": "test"}) + "\n")


def test_load_then_corpus_and_search_and_context_and_explain(tmp_path: Path, capsys):
    db = tmp_path / "atlas.sqlite"
    records_path = tmp_path / "records.jsonl"
    relations_path = tmp_path / "relations.jsonl"
    _write_records(records_path)
    _write_relations(relations_path)

    exit_code = main(["load", str(db), str(records_path), "--relations", str(relations_path)])
    assert exit_code == 0
    load_report = json.loads(capsys.readouterr().out)
    assert load_report["records_loaded"] == 2
    assert load_report["relations_loaded"] == 1
    assert load_report["relations_rejected"] == []

    # Persistence must survive a completely separate process-level main() call.
    assert main(["corpus", "--db", str(db)]) == 0
    corpus = json.loads(capsys.readouterr().out)
    assert corpus["record_count"] == 2
    assert corpus["evidence_count"] == 1
    assert corpus["dataset_count"] == 1

    assert main(["search", str(db), "cardiac remodeling", "--limit", "5"]) == 0
    hits = json.loads(capsys.readouterr().out)
    assert hits
    assert hits[0]["record"]["id"] == "evidence:e1"

    assert main(["context", str(db), "dataset:geo:GSE1", "--hops", "1"]) == 0
    context = json.loads(capsys.readouterr().out)
    assert context["neighbors"] == ["evidence:e1"]

    assert main(["explain", "dataset:geo:GSE1", "--db", str(db)]) == 0
    explanation = json.loads(capsys.readouterr().out)
    assert explanation["neighbors"] == ["evidence:e1"]

    assert main(["release-check", "--db", str(db)]) == 0
    readiness = json.loads(capsys.readouterr().out)
    assert readiness["passed"]
    check_names = {c["name"] for c in readiness["checks"]}
    assert {"controlled_predicates", "benchmark_readiness"} <= check_names


def test_load_rejects_uncontrolled_predicate(tmp_path: Path, capsys):
    db = tmp_path / "atlas.sqlite"
    records_path = tmp_path / "records.jsonl"
    _write_records(records_path)
    relations_path = tmp_path / "relations.jsonl"
    with relations_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({"subject": "dataset:geo:GSE1", "predicate": "has_study", "object": "evidence:e1"}) + "\n")

    exit_code = main(["load", str(db), str(records_path), "--relations", str(relations_path)])
    assert exit_code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["relations_loaded"] == 0
    assert "has_study" in report["relations_rejected"][0]

    # The valid records must still have been committed even though the
    # relation load failed -- a bad relations file shouldn't roll back
    # otherwise-good records.
    assert main(["corpus", "--db", str(db)]) == 0
    corpus = json.loads(capsys.readouterr().out)
    assert corpus["record_count"] == 2


def test_export_plain_release_and_benchmark_candidates(tmp_path: Path, capsys):
    db = tmp_path / "atlas.sqlite"
    records_path = tmp_path / "records.jsonl"
    _write_records(records_path)
    main(["load", str(db), str(records_path)])
    capsys.readouterr()

    plain_out = tmp_path / "export.jsonl"
    assert main(["export", str(db), str(plain_out)]) == 0
    capsys.readouterr()
    assert len(plain_out.read_text(encoding="utf-8").strip().splitlines()) == 2

    release_out = tmp_path / "release.json"
    assert main(["export", str(db), str(release_out), "--release-version", "1.0.0"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["manifest"]["version"] == "1.0.0"
    assert payload["manifest"]["dataset_accessions"] == ["GSE1"]

    candidates_out = tmp_path / "candidates.json"
    assert main(["export", str(db), str(candidates_out), "--benchmark-candidates"]) == 0
    candidates = json.loads(candidates_out.read_text(encoding="utf-8"))
    assert candidates[0]["accession"] == "GSE1"


def test_reconstruct_study_with_db_persists_across_separate_main_calls(tmp_path: Path, capsys):
    db = tmp_path / "atlas.sqlite"
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(json.dumps({
        "id": "dataset:GSETEST", "record_type": "dataset", "name": "GSETEST", "accession": "GSETEST",
        "repository": "GEO", "schema_version": "0.3",
    }), encoding="utf-8")
    metadata_path = tmp_path / "samples.csv"
    metadata_path.write_text("accession,group,subject_id,timepoint,modality\nGSMTEST1,MI,pig-1,P35,snRNA-seq\n", encoding="utf-8")
    output_dir = tmp_path / "reconstructed"

    exit_code = main(["reconstruct-study", str(dataset_path), str(metadata_path), "--output", str(output_dir), "--db", str(db)])
    assert exit_code == 0
    capsys.readouterr()

    # A brand new main() invocation, sharing nothing but the db file, must see it.
    assert main(["corpus", "--db", str(db)]) == 0
    corpus = json.loads(capsys.readouterr().out)
    assert corpus["study_count"] == 1
    assert corpus["sample_count"] == 1

    assert main(["context", str(db), "study:GSETEST", "--hops", "1"]) == 0
    context = json.loads(capsys.readouterr().out)
    assert "dataset:GSETEST" in context["neighbors"]
    assert "sample:gsmtest1" in context["neighbors"]
