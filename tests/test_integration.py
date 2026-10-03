from cardiatlas.integrations import benchmark_readiness, dataset_to_benchmark_candidate
from cardiatlas.models import DatasetRecord
from cardiatlas.qc import assess_dataset


def make_dataset(**kwargs):
    base = dict(
        id="dataset:gse-test",
        name="Test cardiac study",
        accession="GSETEST",
        repository="GEO",
        study_title="Test cardiac study",
        organism="Homo sapiens",
        tissue="heart",
        modalities=["scrna"],
        cell_or_nucleus="cell",
        conditions=["MI", "sham"],
        sample_count=6,
        cell_count=10000,
        evidence_ids=["evidence:1"],
    )
    base.update(kwargs)
    return DatasetRecord(**base)


def test_ready_dataset_maps_to_benchmark_candidate():
    dataset = make_dataset()
    candidate = dataset_to_benchmark_candidate(dataset)
    assert candidate.accession == "GSETEST"
    assert benchmark_readiness(dataset)["ready"] is True


def test_missing_provenance_blocks_readiness():
    dataset = make_dataset(evidence_ids=[])
    report = assess_dataset(dataset)
    assert report.ready is False
    assert "provenance" in report.blockers
