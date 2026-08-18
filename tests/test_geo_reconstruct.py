from cardiatlas.geo_reconstruct import reconstruct_samples, reconstruct_study
from cardiatlas.models import DatasetRecord


def test_reconstruct_samples_normalizes_condition_and_modality():
    rows = [
        {
            "accession": "GSM1001",
            "group": "MI",
            "subject_id": "pig-1",
            "region": "infarct zone",
            "timepoint": "P35",
            "modality": "snRNA-seq",
            "species": "Sus scrofa",
            "tissue": "heart",
        },
        {
            "accession": "GSM1002",
            "group": "sham",
            "subject_id": "pig-2",
            "region": "remote zone",
            "timepoint": "P35",
            "modality": "snRNA-seq",
            "species": "Sus scrofa",
            "tissue": "heart",
        },
    ]
    samples, report = reconstruct_samples(rows, dataset_id="dataset:GSE100", study_id="study:GSE100")
    assert [item.condition for item in samples] == ["myocardial_infarction", "reference"]
    assert all(item.modality == "snrna" for item in samples)
    assert report.reconstructed_subjects == 2
    assert report.regions == ("infarct zone", "remote zone")
    assert report.timepoints == ("P35",)


def test_reconstruct_study_links_dataset_and_evidence():
    dataset = DatasetRecord(
        id="dataset:GSE100",
        name="Example GEO",
        accession="GSE100",
        repository="GEO",
        study_title="Example cardiac study",
        organism="Sus scrofa",
        tissue="heart",
        modalities=["snrna"],
        conditions=["myocardial_infarction", "reference"],
        evidence_ids=["evidence:pubmed:123"],
    )
    study, samples, report = reconstruct_study(
        dataset,
        [{"accession": "GSM1", "group": "MI", "subject_id": "1", "timepoint": "day 3", "modality": "snRNA-seq"}],
    )
    assert study.accession == "GSE100"
    assert study.dataset_ids == ["dataset:GSE100"]
    assert study.evidence_ids == ["evidence:pubmed:123"]
    assert study.id == "study:GSE100"
    assert samples[0].study_id == "study:GSE100"
    assert report.condition_groups == ("myocardial_infarction",)
