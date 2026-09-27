import json
from pathlib import Path

import pytest

from cardiatlas.cli import main


def test_cli_reconstruct_study_end_to_end(tmp_path: Path, capsys):
    """End-to-end regression test for `cardiatlas reconstruct-study`.

    This exercises AtlasService.reconstruct_study through the actual CLI
    entry point rather than calling the underlying library function
    directly -- this is the path a real invocation of the CLI subcommand
    takes, and the one that surfaced the has_dataset/has_study predicate bug,
    which no other test in this suite covers.
    """
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps({
            "id": "dataset:GSETEST",
            "record_type": "dataset",
            "name": "GSETEST",
            "accession": "GSETEST",
            "repository": "GEO",
            "study_title": "CI cardiac study",
            "organism": "Sus scrofa",
            "tissue": "heart",
            "schema_version": "0.3",
        }),
        encoding="utf-8",
    )
    metadata_path = tmp_path / "samples.csv"
    metadata_path.write_text(
        "accession,group,subject_id,timepoint,modality,region\n"
        "GSMTEST1,MI,pig-1,P35,snRNA-seq,infarct\n"
        "GSMTEST2,sham,pig-2,P35,snRNA-seq,remote\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "reconstructed"

    exit_code = main(["reconstruct-study", str(dataset_path), str(metadata_path), "--output", str(output_dir)])

    assert exit_code == 0
    assert (output_dir / "study.json").exists()
    assert (output_dir / "samples.jsonl").exists()
    assert (output_dir / "report.json").exists()

    study = json.loads((output_dir / "study.json").read_text(encoding="utf-8"))
    assert study["id"] == "study:GSETEST"
    assert study["dataset_ids"] == ["dataset:GSETEST"]

    sample_lines = (output_dir / "samples.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(sample_lines) == 2
    samples = [json.loads(line) for line in sample_lines]
    assert {s["accession"] for s in samples} == {"GSMTEST1", "GSMTEST2"}
    assert all(s["study_id"] == "study:GSETEST" for s in samples)


def test_cli_identifier_disambiguates_gene_from_accession(capsys):
    """Regression test: resolve("GSE217494") must not be misclassified as a
    gene symbol by identifiers.resolve_gene's uncurated-format fallback."""
    exit_code = main(["identifier", "GSE217494"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["identifier_type"] == "geo_series"
    assert payload["canonical_id"] == "GSE217494"
