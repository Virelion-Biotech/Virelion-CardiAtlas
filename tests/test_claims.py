from cardiatlas.claims import Claim, ClaimStore
from cardiatlas.models import EvidenceRecord


def test_conflicted_claim_is_not_collapsed():
    store = ClaimStore()
    store.add(Claim(
        id="claim:1",
        subject="marker:tgfb1",
        predicate="associated_with",
        object="phenotype:fibrosis",
        evidence_ids=("e:support", "e:refute"),
    ))
    evidence = {
        "e:support": EvidenceRecord(id="e:support", name="support", source_type="pubmed", polarity="supports"),
        "e:refute": EvidenceRecord(id="e:refute", name="refute", source_type="pubmed", polarity="refutes"),
    }
    assessment = store.assess("claim:1", evidence)
    assert assessment.status == "conflicted"
    assert assessment.evidence_count == 2
