from cardiatlas.catalog import group_datasets
from cardiatlas.harmonize import harmonize_condition, harmonize_modality
from cardiatlas.identifiers import resolve, resolve_accession, resolve_gene
from cardiatlas.models import DatasetRecord, SampleRecord, StudyRecord
from cardiatlas.ontology import canonical_concept_id, descendants
from cardiatlas.sample_ingest import ingest_sample_rows, sample_from_metadata
from cardiatlas.studies import assess_study, study_from_datasets


def test_identifier_resolution():
    assert resolve_gene("cardiac troponin t").canonical_id == "TNNT2"
    assert resolve("GSE217494").identifier_type == "geo_series"
    assert resolve_accession("12345678").identifier_type == "pmid"


def test_harmonization():
    mi = harmonize_condition("Sham")
    assert mi.normalized == "reference"
    assert canonical_concept_id("MI") == "phenotype:myocardial_infarction"
    assert harmonize_modality("single-cell RNA").normalized == "scrna"


def test_sample_ingestion():
    sample = sample_from_metadata(
        {"accession": "GSM1", "group": "MI", "subject_id": "animal-1", "modality": "snRNA-seq"},
        dataset_id="dataset:gse1",
        study_id="study:gse1",
    )
    assert sample.condition == "myocardial_infarction"
    assert sample.modality == "snrna"


def test_study_qc_and_catalog():
    datasets = [
        DatasetRecord(id="dataset:1", name="study", accession="GSE1", study_id="study:1", study_title="Study", organism="human", tissue="heart", modalities=["scrna"], conditions=["reference", "MI"]),
        DatasetRecord(id="dataset:2", name="study2", accession="GSE1_SUPER", study_id="study:1", study_title="Study", organism="human", tissue="heart", modalities=["snrna"], conditions=["reference", "MI"]),
    ]
    study = study_from_datasets("study:1", datasets)
    samples = [
        SampleRecord(id="sample:1", name="GSM1", accession="GSM1", dataset_id="dataset:1", study_id="study:1", subject_id="s1", condition="reference"),
        SampleRecord(id="sample:2", name="GSM2", accession="GSM2", dataset_id="dataset:2", study_id="study:1", subject_id="s2", condition="myocardial_infarction"),
    ]
    qc = assess_study(study, samples)
    assert qc.sample_count == 2
    assert qc.subject_count == 2
    groups = group_datasets(datasets)
    assert len(groups) == 1


def test_ontology_descendants():
    assert any(item.id == "cell:t_cell" for item in descendants("cell:immune"))
