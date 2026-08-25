from cardiatlas.geo_reconstruct import reconstruct_samples
from cardiatlas.models import DatasetRecord, StudyRecord
from cardiatlas.study_readiness import assess_study_benchmark_readiness


def test_accession_inferred_subject_does_not_pass_readiness():
    rows = [
        {"accession": "GSM1_mouse1", "group": "MI", "timepoint": "P35", "modality": "snRNA-seq"},
        {"accession": "GSM2_mouse2", "group": "sham", "timepoint": "P35", "modality": "snRNA-seq"},
    ]
    samples, _ = reconstruct_samples(rows, dataset_id="dataset:GSE1", study_id="study:GSE1")
    assert all(sample.metadata["subject_inferred"] for sample in samples)

    dataset = DatasetRecord(
        id="dataset:GSE1", name="GSE1", accession="GSE1", repository="GEO",
        organism="Mus musculus", tissue="heart", modalities=["snrna"],
        evidence_ids=["evidence:pubmed:1"],
    )
    study = StudyRecord(
        id="study:GSE1", name="GSE1", accession="GSE1", repository="GEO",
        title="GSE1", organism="Mus musculus", tissues=["heart"],
        modalities=["snrna"], dataset_ids=[dataset.id],
    )
    result = assess_study_benchmark_readiness(study, dataset, samples)
    assert not result.ready
    assert "subject_structure" in result.missing
