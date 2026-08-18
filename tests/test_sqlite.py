from pathlib import Path

from cardiatlas.graph import Relation
from cardiatlas.models import MarkerRecord
from cardiatlas.sqlite import SQLiteAtlasStore


def test_sqlite_roundtrip(tmp_path: Path):
    path = tmp_path / "atlas.sqlite"
    record = MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2")
    with SQLiteAtlasStore(path) as store:
        assert store.upsert_many([record]) == 1
        store.put_relation(Relation("marker:tnnt2", "marks", "cell:cardiomyocyte", ("e1",), 0.9))
        store.put_relation(Relation("marker:tnnt2", "marks", "cell:cardiomyocyte", ("e2",), 0.95))
        assert store.count() == 1
        assert store.get_payload("marker:tnnt2")["entity_id"] == "TNNT2"
        relation = store.relations_for("marker:tnnt2")[0]
        assert relation["predicate"] == "marks"
        assert relation["object"] == "cell:cardiomyocyte"
        assert relation["evidence_ids"] == ["e1", "e2"]
        assert relation["confidence"] == 0.95
        assert store.graph().neighbors("marker:tnnt2") == ["cell:cardiomyocyte"]
        manifest = store.save_release([record], "0.4.0")
        assert manifest["schema_version"] == "0.3"
        assert store.release("0.4.0")["digest"] == manifest["digest"]

    assert path.exists()
