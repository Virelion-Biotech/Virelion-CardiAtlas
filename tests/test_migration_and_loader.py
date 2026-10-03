from pathlib import Path

from cardiatlas.loader import read_bundle, record_from_dict
from cardiatlas.migrate import migrate_payload


def test_migrate_legacy_dataset():
    migrated = migrate_payload({
        "id": "dataset:gse1",
        "record_type": "dataset",
        "name": "GSE1",
        "accession": "GSE1",
        "repository": "GEO",
        "study_title": "Example",
        "organism": "",
        "tissue": "heart",
        "modalities": [],
        "cell_or_nucleus": "unknown",
        "conditions": [],
        "schema_version": "0.2",
    })
    assert migrated["schema_version"] == "0.3"
    assert "study_id" in migrated
    assert record_from_dict(migrated).record_type == "dataset"


def test_load_checked_in_examples():
    root = Path(__file__).resolve().parents[1]
    records = read_bundle([
        root / "data/examples/atlas.jsonl",
        root / "data/examples/markers.jsonl",
        root / "data/examples/phenotypes.jsonl",
    ])
    assert len(records) >= 5
