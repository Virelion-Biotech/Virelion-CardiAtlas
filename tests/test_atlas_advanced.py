from cardiatlas import AtlasGraph, AtlasService, EvidenceRecord, MarkerRecord, Relation
from cardiatlas.adapters import geo_summary_to_dataset, pubmed_summary_to_evidence
from cardiatlas.evidence import score_evidence
from cardiatlas.normalize import canonical_key, normalize_accession, normalize_species


def test_normalization_is_stable():
    assert canonical_key("  Myocardial   Infarction ") == "myocardial_infarction"
    assert normalize_accession(" gse217494 ") == "GSE217494"
    assert normalize_species("mouse") == "Mus musculus"


def test_graph_merges_duplicate_evidence():
    graph = AtlasGraph()
    graph.add(Relation("a", "supports", "b", ("e1",)))
    graph.add(Relation("a", "supports", "b", ("e2",)))
    assert graph.relations()[0].evidence_ids == ("e1", "e2")
    assert graph.neighbors("a") == ["b"]


def test_evidence_score_rewards_diversity():
    values = [
        EvidenceRecord(id="e1", name="one", source_type="pubmed", source_identifier="1", evidence_level="primary"),
        EvidenceRecord(id="e2", name="two", source_type="doi", source_identifier="2", evidence_level="primary"),
    ]
    score = score_evidence(values)
    assert score.score > 0
    assert score.primary_count == 2
    assert score.independent_sources == 2


def test_adapters_create_typed_records():
    evidence = pubmed_summary_to_evidence({"uid": "123", "title": "A study", "pubdate": "2024", "fulljournalname": "Journal"})
    dataset = geo_summary_to_dataset({"uid": "99", "accession": "gse1", "title": "Heart", "organism": "mouse"})
    assert evidence.id == "evidence:pubmed:123"
    assert dataset.accession == "GSE1"
    assert dataset.organism == "Mus musculus"


def test_service_explain_returns_graph_and_evidence():
    service = AtlasService.empty()
    evidence = EvidenceRecord(
        id="e1", name="Study", source_type="pubmed", source_identifier="1", evidence_level="primary"
    )
    marker = MarkerRecord(id="m1", name="TNNT2", entity_id="TNNT2", evidence_ids=["e1"])
    service.add(evidence)
    service.add(marker)
    service.relate("m1", "associated_with", "cell_state:cm")
    result = service.explain("m1")
    assert result["evidence_score"] > 0
    assert result["neighbors"] == ["cell_state:cm"]
