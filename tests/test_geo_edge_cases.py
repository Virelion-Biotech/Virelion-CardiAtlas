from cardiatlas.geo_reconstruct import reconstruct_samples
from cardiatlas.geo_soft import parse_geo_soft


SOFT = """^SAMPLE = GSM1001
!Sample_title = pig MI snRNA
!Sample_organism_ch1 = Sus scrofa
!Sample_source_name_ch1 = left ventricle
!Sample_platform_id = GPL24676
!Sample_library_strategy = snRNA-Seq
!Sample_library_source = transcriptomic
!Sample_library_selection = cDNA
!Sample_characteristics_ch1 = condition: MI
!Sample_characteristics_ch1.1 = region: infarct zone
!Sample_characteristics_ch1.2 = region: left ventricle
!Sample_characteristics_ch1.3 = animal: pig-01
!Sample_characteristics_ch1.4 = dpi: 28
^SAMPLE = GSM1002
!Sample_title = pig sham snRNA
!Sample_organism_ch1 = Sus scrofa
!Sample_source_name_ch1 = left ventricle
!Sample_platform_id = GPL24676
!Sample_library_strategy = RNA-Seq
!Sample_characteristics_ch1 = condition: n/a
!Sample_characteristics_ch1.1 = zone: remote
!Sample_characteristics_ch1.2 = animal: pig-02
!Sample_characteristics_ch1.3 = timepoint: P35
"""


def test_soft_preserves_repeated_characteristics_and_library_strategy():
    samples = parse_geo_soft(SOFT)
    assert len(samples) == 2
    assert samples[0].characteristics["region"] == "infarct zone | left ventricle"
    assert samples[0].characteristics["animal_id"] == "pig-01"
    assert samples[0].fields["Sample_library_strategy"] == "snRNA-Seq"


def test_reconstruction_uses_library_strategy_and_null_condition_rules():
    samples = parse_geo_soft(SOFT)
    rows = [sample.to_row() for sample in samples]
    records, report = reconstruct_samples(rows, dataset_id="dataset:geo:GSETEST", study_id="study:GSETEST")
    assert records[0].modality == "snrna"
    assert records[0].condition == "myocardial_infarction"
    assert records[1].modality == "bulk_rna"
    assert records[1].condition == ""
    assert "myocardial_infarction" in report.condition_groups
    assert "some samples lack condition metadata" in report.warnings
