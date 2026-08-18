from cardiatlas.claims import Claim, ClaimStore
from cardiatlas.models import MarkerRecord
from cardiatlas.sqlite import SQLiteAtlasStore


def test_sqlite_persists_records(tmp_path):
    path = tmp_path / "atlas.db"
    record = MarkerRecord(id="m1", name="TNNT2", entity_id="TNNT2")
    with SQLiteAtlasStore(path) as store:
        store.upsert(record)
        assert store.count() == 1
        assert store.get_payload("m1")["entity_id"] == "TNNT2"
    with SQLiteAtlasStore(path) as reopened:
        assert reopened.count("marker") == 1


def test_claim_store_detects_explicit_refutation():
    claims = ClaimStore()
    claims.add(Claim(id="c1", subject="m1", predicate="associated_with", object="p1", polarity="refutes", evidence_ids=("e1",)))
    assessment = claims.assess("c1")
    assert assessment.status == "refuted"
    assert assessment.refuting_evidence == ("e1",)
