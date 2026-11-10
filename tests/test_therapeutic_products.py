import pytest

from cardiatlas.therapeutic_products import (
    ManufacturingProfile, PotencyAssay, ProductRegulatoryRecord, TherapeuticProductRecord,
)


def test_product_record_serializes_structured_evidence():
    record = TherapeuticProductRecord(
        id="product-1",
        name="Example cardiac cell product",
        modality="autologous_cell",
        intended_indication="ischemic heart failure",
        manufacturing=ManufacturingProfile(autologous_or_allogeneic="autologous"),
        potency_assays=(PotencyAssay(
            assay_name="contractile response",
            biological_function="stimulus-linked contraction",
            method="paced force measurement",
            evidence_ids=["ev-1"],
            status="reported",
        ),),
        regulatory_records=(ProductRegulatoryRecord(
            jurisdiction="JP", status="scientific_advice", authority="PMDA",
            evidence_ids=["ev-2"],
        ),),
        evidence_ids=["ev-1", "ev-2"],
        limitations=("Company-reported milestone; not marketing authorization.",),
    )
    payload = record.to_dict()
    assert payload["potency_assays"][0]["biological_function"] == "stimulus-linked contraction"
    assert payload["regulatory_records"][0]["status"] == "scientific_advice"
    assert payload["product_schema_version"] == "1.0"


def test_product_rejects_duplicate_evidence_ids():
    with pytest.raises(ValueError, match="evidence_ids must be unique"):
        TherapeuticProductRecord(
            id="p", name="Product", modality="gene_therapy",
            intended_indication="CPVT", evidence_ids=("e1", "e1"),
        )


def test_potency_assay_requires_functional_definition():
    with pytest.raises(ValueError, match="biological function"):
        PotencyAssay(assay_name="assay", biological_function=" ", method="method")


def test_product_rejects_nonpositive_version():
    with pytest.raises(ValueError, match="positive"):
        TherapeuticProductRecord(
            id="p", name="Product", modality="gene_therapy",
            intended_indication="CPVT", version=0,
        )


def test_product_is_first_class_registry_record():
    from cardiatlas.registry import AtlasRegistry
    from cardiatlas.validation import require_valid

    record = TherapeuticProductRecord(
        id="product-registry", name="Example product", modality="gene_therapy",
        intended_indication="CPVT",
    )
    require_valid(record)
    registry = AtlasRegistry()
    registry.add(record)
    assert registry.get("product-registry").record_type == "therapeutic_product"
