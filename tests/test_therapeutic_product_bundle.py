from pathlib import Path

from cardiatlas.loader import read_bundle
from cardiatlas.therapeutic_products import TherapeuticProductRecord


def test_curated_therapeutic_product_bundle_is_loadable_and_provenanced():
    path = Path(__file__).resolve().parents[1] / "data" / "therapeutic_products" / "curated_evidence.v1.jsonl"
    records = read_bundle([path])
    evidence = {record.id: record for record in records if record.record_type == "evidence"}
    products = [record for record in records if isinstance(record, TherapeuticProductRecord)]

    assert {record.id for record in products} == {
        "product-cardiamp",
        "product-protheracytes",
        "product-sgt501",
    }
    assert len(evidence) == 7
    for product in products:
        assert product.evidence_ids
        assert set(product.evidence_ids) <= set(evidence)
        assert product.source_ids
