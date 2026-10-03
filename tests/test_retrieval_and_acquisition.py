from cardiatlas.acquisition import acquisition_plan
from cardiatlas.models import EvidenceRecord, PhenotypeRecord
from cardiatlas.registry import AtlasRegistry
from cardiatlas.retrieval import retrieve


def test_acquisition_plan_is_prioritized_and_filterable():
    plan = acquisition_plan()
    assert plan
    assert plan[0].priority >= plan[-1].priority
    assert all(item.domain == "fibrosis" for item in acquisition_plan("fibrosis"))


def test_retrieval_prefers_matching_evidence_context():
    registry = AtlasRegistry()
    registry.add(
        EvidenceRecord(
            id="evidence:1",
            name="MI single-cell study",
            source_type="pubmed",
            source_identifier="1",
            evidence_level="primary",
            year=2025,
        )
    )
    registry.add(
        PhenotypeRecord(
            id="phenotype:mi",
            name="Myocardial infarction",
            tags=["injury", "MI"],
            evidence_ids=["evidence:1"],
        )
    )
    results = retrieve(registry, "MI", limit=5)
    assert results
    assert results[0].record.id == "phenotype:mi"
    assert results[0].evidence_score is not None
    assert "mi" in results[0].matched_terms
