import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EVIDENCE_PATH = ROOT / "data" / "reference" / "optical_stimulation_evidence.jsonl"
INTERVENTION_PATH = ROOT / "data" / "reference" / "optical_stimulation_interventions.jsonl"
CONTRACT = "virelion.optical-stimulation/1.0.0"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_optical_evidence_records_are_unique_and_traceable():
    records = _read_jsonl(EVIDENCE_PATH)
    assert len(records) == 6
    ids = [record["id"] for record in records]
    assert len(ids) == len(set(ids))
    for record in records:
        assert record["record_type"] == "evidence"
        assert record["source_type"] == "pubmed"
        assert record["source_identifier"].isdigit()
        assert record["source_url"] == f"https://pubmed.ncbi.nlm.nih.gov/{record['source_identifier']}/"
        assert record["year"] == 2026


def test_optical_interventions_join_to_evidence_and_shared_contract():
    evidence_ids = {record["id"] for record in _read_jsonl(EVIDENCE_PATH)}
    interventions = _read_jsonl(INTERVENTION_PATH)
    assert {record["id"] for record in interventions} == {
        "intervention:cardiac-optogenetic-stimulation",
        "intervention:cardiac-optoelectronic-stimulation",
    }
    for record in interventions:
        assert record["record_type"] == "intervention"
        assert record["intervention_type"] == "optical_stimulation"
        assert record["metadata"]["shared_contract"] == CONTRACT
        assert record["metadata"]["scope"] == "research_compatibility_only"
        assert record["metadata"]["therapeutic_claim"] is False
        assert record["source_ids"]
        assert set(record["source_ids"]).issubset(evidence_ids)
