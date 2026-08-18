from cardiatlas import AtlasAPI, AtlasService, EvidenceRecord, PhenotypeRecord
from cardiatlas.diff import diff_records


def build_service() -> AtlasService:
    service = AtlasService.empty()
    evidence = EvidenceRecord(
        id="evidence:pmid1",
        name="Example paper",
        source_type="pubmed",
        source_identifier="12345678",
        citation="Example citation",
        evidence_level="primary",
    )
    phenotype = PhenotypeRecord(
        id="phenotype:mi",
        name="Myocardial infarction",
        category="injury",
        source_ids=[evidence.id],
        synonyms=["MI"],
    )
    service.add_many([evidence, phenotype])
    return service


def test_api_health_search_and_context():
    service = build_service()
    api = AtlasAPI(service)
    assert api.health()["record_count"] == 2
    assert api.search("myocardial infarction")["results"]
    context = api.context(["phenotype:mi", "evidence:pmid1"])
    assert context.context_id == "atlas-context"
    assert "phenotype:mi" in context.phenotype_ids


def test_release_readiness_and_diff():
    service = build_service()
    readiness = service.release_readiness()
    assert readiness.passed
    before = service.registry.all()
    service.add(PhenotypeRecord(id="phenotype:fibrosis", name="Fibrosis", category="remodeling"))
    delta = diff_records(before, service.registry.all())
    assert delta.added == ("phenotype:fibrosis",)
    assert not delta.removed


def test_api_snapshot():
    api = AtlasAPI(build_service())
    snapshot = api.snapshot("0.4.0")
    assert snapshot["version"] == "0.4.0"
    assert len(snapshot["digest"]) == 64
