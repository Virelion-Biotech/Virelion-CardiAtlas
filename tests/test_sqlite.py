from pathlib import Path

from cardiatlas.graph import Relation
from cardiatlas.models import MarkerRecord
from cardiatlas.sqlite import SQLiteAtlasStore


def test_sqlite_roundtrip(tmp_path: Path):
    path = tmp_path / "atlas.sqlite"
    record = MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2")
    with SQLiteAtlasStore(path) as store:
        assert store.upsert_many([record]) == 1
        store.put_relation(Relation("marker:tnnt2", "marks", "cell:cardiomyocyte"))
        assert store.count() == 1
        assert store.get_payload("marker:tnnt2")["entity_id"] == "TNNT2"
        assert store.relations_for("marker:tnnt2")[0]["predicate"] == "marks"
        manifest = store.save_release([record], "0.3.0")
        assert store.release("0.3.0")["digest"] == manifest["digest"]

    assert path.exists()
