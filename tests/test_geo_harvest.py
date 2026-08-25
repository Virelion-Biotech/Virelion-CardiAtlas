from pathlib import Path

from cardiatlas.adapters import geo_summary_to_dataset
from cardiatlas.geo_harvest import reconstruct_geo_series, write_geo_bundle


class FakeNcbiClient:
    def __init__(self, payload: bytes):
        self.payload = payload

    @staticmethod
    def geo_family_soft_url(accession: str) -> str:
        return f"https://ftp.ncbi.nlm.nih.gov/geo/series/GSE000nnn/{accession}/{accession}_family.soft.gz"

    def fetch_geo_family_soft(self, accession: str) -> bytes:
        return self.payload


def test_geo_bundle_records_source_digest_and_readiness(tmp_path: Path):
    soft = b'''^SAMPLE = GSM1\n!Sample_title = MI pig\n!Sample_organism_ch1 = Sus scrofa\n!Sample_source_name_ch1 = heart\n!Sample_library_strategy = RNA-Seq\n!Sample_characteristics_ch1 = disease state: myocardial infarction\n!Sample_characteristics_ch1 = animal: pig-1\n\n^SAMPLE = GSM2\n!Sample_title = sham pig\n!Sample_organism_ch1 = Sus scrofa\n!Sample_source_name_ch1 = heart\n!Sample_library_strategy = RNA-Seq\n!Sample_characteristics_ch1 = disease state: sham\n!Sample_characteristics_ch1 = animal: pig-2\n'''
    dataset = geo_summary_to_dataset({"accession": "GSE123456", "title": "Example", "organism": "Sus scrofa", "tissue": "heart"})
    dataset.conditions = ["myocardial_infarction", "reference"]
    bundle = reconstruct_geo_series(FakeNcbiClient(soft), dataset)

    assert bundle.source_digest
    assert bundle.source_url.endswith("GSE123456_family.soft.gz")
    assert bundle.payload_bytes == len(soft)
    assert bundle.benchmark_readiness.checks["sample_count"]
    assert bundle.benchmark_readiness.checks["multiple_conditions"]

    write_geo_bundle(bundle, tmp_path)
    acquisition = (tmp_path / "acquisition.json").read_text(encoding="utf-8")
    assert bundle.source_digest in acquisition
    assert "parser_version" in acquisition
    assert (tmp_path / "dataset.json").exists()
    assert (tmp_path / "study.json").exists()
    assert (tmp_path / "samples.jsonl").exists()
    assert (tmp_path / "report.json").exists()
