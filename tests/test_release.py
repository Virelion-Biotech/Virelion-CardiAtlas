from cardiatlas.models import MarkerRecord
from cardiatlas.release import create_manifest, digest_records, verify_digest


def test_digest_is_order_independent():
    first = MarkerRecord(id="m:b", name="B", entity_id="GENEB")
    second = MarkerRecord(id="m:a", name="A", entity_id="GENEA")
    assert digest_records([first, second]) == digest_records([second, first])


def test_manifest_and_verification():
    record = MarkerRecord(id="m:a", name="A", entity_id="GENEA")
    manifest = create_manifest([record], "0.3.0")
    assert manifest.record_count == 1
    assert manifest.record_types == {"marker": 1}
    assert verify_digest([record], manifest.digest)
