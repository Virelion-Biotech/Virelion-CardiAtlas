import json
from pathlib import Path

from cardiatlas.catalog import attach_datasets, group_datasets
from cardiatlas.io import read_jsonl, write_jsonl
from cardiatlas.models import DatasetRecord, StudyRecord


def test_attach_datasets_does_not_crash_on_record_type():
    """Regression test: attach_datasets used to rebuild StudyRecord via
    StudyRecord(**study.to_dict()), which includes the init=False
    'record_type' field and always raised TypeError.
    """
    study = StudyRecord(id="study:1", name="Test study", accession="GSE1")
    dataset = DatasetRecord(id="dataset:1", name="D1", accession="GSE1", repository="GEO", study_id="study:1")

    updated = attach_datasets(study, [dataset])

    assert updated.record_type == "study"
    assert updated.dataset_ids == ["dataset:1"]
    # Attaching nothing new is a no-op and must not error either.
    assert attach_datasets(updated, [dataset]).dataset_ids == ["dataset:1"]


def test_group_datasets_by_study():
    a = DatasetRecord(id="dataset:a", name="A", accession="GSE1", repository="GEO", study_id="study:1", organism="Sus scrofa", modalities=["snrna"])
    b = DatasetRecord(id="dataset:b", name="B", accession="GSE2", repository="GEO", study_id="study:1", organism="Sus scrofa", modalities=["scrna"])
    groups = group_datasets([a, b])
    assert len(groups) == 1
    assert set(groups[0].dataset_ids) == {"dataset:a", "dataset:b"}


def test_read_jsonl_round_trips_and_ignores_init_false_fields(tmp_path: Path):
    """Regression test: read_jsonl used to pass every field name from
    dataclasses.fields() straight into the constructor, including
    init=False fields like 'record_type', which always raised TypeError.
    """
    path = tmp_path / "datasets.jsonl"
    original = [DatasetRecord(id="dataset:1", name="D1", accession="GSE1", repository="GEO")]
    write_jsonl(original, path)

    loaded = read_jsonl(path, DatasetRecord)

    assert len(loaded) == 1
    assert loaded[0].id == "dataset:1"
    assert loaded[0].record_type == "dataset"
