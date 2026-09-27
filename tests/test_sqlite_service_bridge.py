from pathlib import Path

from cardiatlas.graph import Relation
from cardiatlas.models import DatasetRecord, EvidenceRecord
from cardiatlas.sqlite import SQLiteAtlasStore


def test_load_service_on_empty_store_is_empty(tmp_path: Path):
    with SQLiteAtlasStore(tmp_path / "atlas.sqlite") as store:
        service = store.load_service()
        assert service.registry.all() == []
        assert service.graph.relations() == []


def test_save_and_reload_service_round_trips(tmp_path: Path):
    path = tmp_path / "atlas.sqlite"
    with SQLiteAtlasStore(path) as store:
        service = store.load_service()
        evidence = EvidenceRecord(id="evidence:e1", name="Paper", source_type="pubmed", source_identifier="1")
        dataset = DatasetRecord(id="dataset:geo:GSE1", name="GSE1", accession="GSE1", repository="GEO")
        service.add(evidence)
        service.add(dataset)
        service.relate(dataset.id, "derived_from", evidence.id, confidence=0.9, source="test")
        store.save_service(service)

    with SQLiteAtlasStore(path) as reopened:
        reloaded = reopened.load_service()
        assert {r.id for r in reloaded.registry.all()} == {"evidence:e1", "dataset:geo:GSE1"}
        assert len(reloaded.graph.relations()) == 1
        # search/explain/context should all work on the reloaded service --
        # this is the actual point of the bridge, not just data presence.
        assert reloaded.search("GSE1")
        assert reloaded.explain(dataset.id)["neighbors"] == [evidence.id]


def test_save_service_is_idempotent(tmp_path: Path):
    path = tmp_path / "atlas.sqlite"
    with SQLiteAtlasStore(path) as store:
        service = store.load_service()
        service.add(DatasetRecord(id="dataset:geo:GSE1", name="GSE1", accession="GSE1", repository="GEO"))
        store.save_service(service)
        store.save_service(service)
        assert store.count() == 1
