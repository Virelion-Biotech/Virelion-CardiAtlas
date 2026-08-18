from cardiatlas import AtlasRegistry, MarkerRecord, PhenotypeRecord
from cardiatlas.search import search


def test_registry_add_and_get() -> None:
    registry = AtlasRegistry()
    marker = MarkerRecord(
        id="marker:tnnt2",
        name="TNNT2",
        entity_id="TNNT2",
        entity_type="gene",
        tags=["cardiomyocyte", "contractile"],
    )
    registry.add(marker)
    assert registry.get("marker:tnnt2") is marker
    assert len(registry) == 1


def test_search_is_deterministic() -> None:
    registry = AtlasRegistry()
    registry.add(PhenotypeRecord(id="phenotype:mi", name="Myocardial infarction", category="injury"))
    registry.add(PhenotypeRecord(id="phenotype:fibrosis", name="Cardiac fibrosis", category="remodeling"))
    hits = search(registry, "cardiac")
    assert [item.id for item in hits] == ["phenotype:fibrosis"]


def test_duplicate_ids_rejected() -> None:
    registry = AtlasRegistry()
    record = PhenotypeRecord(id="phenotype:test", name="Test", category="other")
    registry.add(record)
    try:
        registry.add(record)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate record was accepted")
