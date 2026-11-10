import json
from pathlib import Path

from cardiatlas.loader import read_bundle
from cardiatlas.therapeutic_products import TherapeuticProductRecord


def test_clinical_trial_contexts_are_linked_to_product_evidence():
    bundle = Path(__file__).resolve().parents[1] / "data" / "therapeutic_products" / "curated_evidence.v1.jsonl"
    records = read_bundle([bundle])
    products = {r.id: r for r in records if isinstance(r, TherapeuticProductRecord)}
    evidence = {r.id: r for r in records if r.record_type == "evidence"}
    trial_records = {
        record_id: record for record_id, record in evidence.items()
        if record.context.get("clinical_trial_evidence")
    }
    assert set(trial_records) == {
        "ev-cardiamp-outcome-company-2025",
        "ev-protheracytes-hrqol-pmid-41774093",
        "ev-sgt501-registry-nct07148089",
    }
    for evidence_id, record in trial_records.items():
        trial = record.context["clinical_trial_evidence"]
        product = products[trial["product_id"]]
        assert evidence_id in product.evidence_ids
        assert trial["trial_id"]
        assert trial["endpoints"]
        assert trial["source_type"] in {
            "registry", "peer_reviewed_publication", "regulatory_document", "company_report", "other"
        }


def test_trial_context_preserves_unknown_subgroup_details():
    bundle = Path(__file__).resolve().parents[1] / "data" / "therapeutic_products" / "curated_evidence.v1.jsonl"
    records = read_bundle([bundle])
    outcome = next(r for r in records if r.id == "ev-cardiamp-outcome-company-2025")
    subgroup = outcome.context["clinical_trial_evidence"]["endpoints"][1]
    assert subgroup["prespecified"] is None
    assert subgroup["multiplicity_adjusted"] is None
    assert subgroup["treatment_by_subgroup_interaction_p_value"] is None
