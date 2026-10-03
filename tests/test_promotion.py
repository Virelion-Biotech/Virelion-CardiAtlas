from cardiatlas.harvest import HarvestItem
from cardiatlas.models import EvidenceRecord
from cardiatlas.promotion import decide_promotion, promote_records


def test_promotion_accepts_provenanced_evidence():
    record = EvidenceRecord(
        id="evidence:pubmed:1",
        name="Example cardiac study",
        source_identifier="1",
        source_url="https://pubmed.ncbi.nlm.nih.gov/1/",
    )
    item = HarvestItem(source="pubmed", query_id="q", external_id="1", raw_digest="abc")
    decision = decide_promotion(record, item)
    assert decision.status == "candidate"


def test_promotion_rejects_missing_provenance():
    record = EvidenceRecord(id="evidence:pubmed:1", name="Example", source_identifier="1")
    decision = decide_promotion(record)
    assert decision.status == "rejected"
    assert "missing_source_url" in decision.reasons


def test_promote_deduplicates_records():
    record = EvidenceRecord(
        id="evidence:pubmed:1", name="Example", source_identifier="1", source_url="https://example.test/1"
    )
    promoted, decisions = promote_records([record, record])
    assert len(promoted) == 1
    assert len(decisions) == 1
