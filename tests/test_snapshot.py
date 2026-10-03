from cardiatlas.models import MarkerRecord
from cardiatlas.snapshot import create_snapshot


def test_snapshot_digest_is_order_independent():
    a = MarkerRecord(id="a", name="TNNT2", entity_id="TNNT2")
    b = MarkerRecord(id="b", name="MYH7", entity_id="MYH7")
    left = create_snapshot([a, b])
    right = create_snapshot([b, a])
    assert left.digest == right.digest
    assert left.record_count == 2
    assert left.record_types == {"marker": 2}
