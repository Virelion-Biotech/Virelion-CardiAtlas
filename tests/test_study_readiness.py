from cardiatlas.models import DatasetRecord, SampleRecord, StudyRecord
from cardiatlas.study_readiness import assess_study_benchmark_readiness


def test_study_benchmark_readiness_requires_real_structure():
    dataset = DatasetRecord(
        id="dataset:gse1",
        name="cardiac MI",
        accession="GSE1",
        repository="GEO",
        organism="Sus scrofa",
        tissue="heart",
        modalities=["snrna"],
        evidence_ids=["evidence:pubmed:1"],
    )
    study = StudyRecord(
        id="study:gse1",
        name="cardiac MI",
        accession="GSE1",
        repository="GEO",
        title="cardiac MI",
        organism="Sus scrofa",
        tissues=["heart"],
        modalities=["snrna"],
        dataset_ids=[dataset.id],
    )
    samples = [
        SampleRecord(id="sample:1", name="GSM1", accession="GSM1", dataset_id=dataset.id, study_id=study.id, subject_id="pig1", condition="myocardial_infarction", timepoint="P35", modality="snrna"),
        SampleRecord(id="sample:2", name="GSM2", accession="GSM2", dataset_id=dataset.id, study_id=study.id, subject_id="pig2", condition="reference", timepoint="P35", modality="snrna"),
    ]
    ready = assess_study_benchmark_readiness(study, dataset, samples)
    assert ready.ready
    assert not ready.missing


def test_study_readiness_blocks_single_condition_data():
    dataset = DatasetRecord(
        id="dataset:gse2", name="single group", accession="GSE2", repository="GEO",
        organism="human", tissue="heart", modalities=["scrna"], evidence_ids=["evidence:pubmed:2"]
    )
    study = StudyRecord(id="study:gse2", name="single group", accession="GSE2", repository="GEO", title="single group", organism="human", tissues=["heart"], modalities=["scrna"], dataset_ids=[dataset.id])
    samples = [SampleRecord(id="sample:3", name="GSM3", accession="GSM3", dataset_id=dataset.id, study_id=study.id, subject_id="p1", condition="reference", modality="scrna")]
    result = assess_study_benchmark_readiness(study, dataset, samples)
    assert not result.ready
    assert "multiple_conditions" in result.missing
