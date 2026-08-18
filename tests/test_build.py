from pathlib import Path

from cardiatlas.build import build_reference


def test_reference_build_from_repository_data():
    root = Path(__file__).resolve().parents[1]
    result = build_reference(root, "test")
    assert result.records
    assert result.relations
    assert result.manifest.record_count == len(result.records)
    assert len(result.manifest.digest) == 64
    assert result.readiness.passed
