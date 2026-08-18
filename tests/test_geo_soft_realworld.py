from cardiatlas.geo_reconstruct import reconstruct_samples
from cardiatlas.geo_soft import parse_geo_soft, samples_to_rows


SOFT = '''
^SERIES = GSE999999
!Series_title = Cardiac metadata fixture
^SAMPLE = GSM1000001
!Sample_title = MI animal 1
!Sample_geo_accession = GSM1000001
!Sample_organism_ch1 = Mus musculus
!Sample_source_name_ch1 = left ventricle
!Sample_characteristics_ch1 = condition: MI
!Sample_characteristics_ch1 = animal_id: mouse01
!Sample_characteristics_ch1 = timepoint: 7 dpi
!Sample_characteristics_ch1 = region: infarct zone
!Sample_library_strategy = RNA-Seq
^SAMPLE = GSM1000002
!Sample_title = Sham animal 2
!Sample_geo_accession = GSM1000002
!Sample_organism_ch1 = Mus musculus
!Sample_source_name_ch1 = left ventricle
!Sample_characteristics_ch1 = condition: sham
!Sample_characteristics_ch1 = animal_id: mouse02
!Sample_characteristics_ch1 = timepoint: 7 dpi
!Sample_characteristics_ch1 = region: remote zone
!Sample_library_strategy = RNA-Seq
'''


def test_parse_soft_characteristics_and_rows():
    samples = parse_geo_soft(SOFT)
    assert [sample.accession for sample in samples] == ["GSM1000001", "GSM1000002"]
    rows = samples_to_rows(samples)
    assert rows[0]["condition"] == "MI"
    assert rows[0]["animal_id"] == "mouse01"
    assert rows[0]["region"] == "infarct zone"


def test_reconstruction_preserves_source_decisions():
    rows = samples_to_rows(parse_geo_soft(SOFT))
    records, report = reconstruct_samples(rows, dataset_id="dataset:geo:GSE999999", study_id="study:GSE999999")
    assert len(records) == 2
    assert {record.condition for record in records} == {"myocardial_infarction", "reference"}
    assert {record.subject_id for record in records} == {"mouse01", "mouse02"}
    assert report.reconstructed_subjects == 2
    assert any(decision.source_key == "condition" for decision in report.decisions)
