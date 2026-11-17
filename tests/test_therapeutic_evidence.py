import pytest

from cardiatlas import TherapeuticEvidenceRecord
from cardiatlas.loader import record_from_dict
from cardiatlas.registry import AtlasRegistry
from cardiatlas.validation import require_valid


def example(**overrides):
    values = dict(
        id="therapeutic-evidence:1",
        name="Transient MYC-Cyclin T1 modRNA after myocardial infarction",
        evidence_class="myocardial_regeneration",
        modality="modRNA",
        target_or_genotype="MYC-Cyclin T1",
        payload_or_construct="transient MYC and Cyclin T1 modified mRNA",
        delivery_method="intramyocardial delivery",
        proposed_mechanism="Transient induction of cardiomyocyte cell-cycle activity",
        model_system="experimental myocardial infarction model",
        species="mouse",
        dose="not reported",
        comparator="vehicle",
        endpoints=[
            {"endpoint":"Ki67-positive cardiomyocytes","measurement":"immunostaining","interpretation":"cell-cycle entry; not proof of completed cytokinesis"},
            {"endpoint":"cardiomyocyte number","measurement":"lineage-aware stereology","interpretation":"not reported"},
        ],
        analysis_population="all randomized animals",
        denominator="not reported",
        follow_up="not reported",
        safety_findings=["duration-dependent expression toxicity requires assessment"],
        limitations=["Cell-cycle entry is not equivalent to new cardiomyocyte formation."],
        evidence_ids=["evidence:1"],
        source_locator={"source_id":"PMID:example","section":"Results"},
        curation_status="source_checked",
    )
    values.update(overrides)
    return TherapeuticEvidenceRecord(**values)


def test_therapeutic_evidence_round_trip_and_registry():
    record = example()
    require_valid(record)
    registry = AtlasRegistry()
    registry.add(record)
    restored = record_from_dict(record.to_dict())
    assert restored == record
    assert registry.get(record.id).record_type == "therapeutic_evidence"


def test_regeneration_class_is_separate_from_modality():
    record = example(evidence_class="myocardial_repair", modality="AAV")
    assert record.evidence_class == "myocardial_repair"
    assert record.modality == "AAV"


def test_surrogate_endpoint_cannot_be_mislabeled_as_regeneration():
    with pytest.raises(ValueError, match="surrogate endpoint"):
        example(endpoints=[{"endpoint":"LVEF","interpretation":"proof of regeneration"}])
    # Explicitly cautious language mentioning regeneration must remain admissible.
    cautious = example(endpoints=[{"endpoint":"LVEF","interpretation":"does not prove regeneration"}])
    assert cautious.endpoints[0]["interpretation"] == "does not prove regeneration"


def test_evidence_ids_must_be_unique():
    with pytest.raises(ValueError, match="unique"):
        example(evidence_ids=["e1","e1"])


def test_invalid_modality_rejected_by_atlas_validation():
    record = example(modality="viral vector")
    with pytest.raises(ValueError, match="modality"):
        require_valid(record)
