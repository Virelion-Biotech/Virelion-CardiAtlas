from cardiatlas import AtlasService, MarkerRecord, Query


def test_service_resolution_query_and_context():
    service = AtlasService.empty()
    service.add(MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2", tags=["cardiomyocyte"]))
    assert service.resolve("MI") == "phenotype:myocardial_infarction"
    hits = service.query(Query(text="TNNT2", record_type="marker"))
    assert hits and hits[0].record.id == "marker:tnnt2"
    context = service.atlas_context("ctx:1", ["marker:tnnt2"])
    assert context.marker_ids == ("marker:tnnt2",)


def test_atlas_context_does_not_claim_missing_records_as_provenance():
    service = AtlasService.empty()
    service.add(MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2"))
    context = service.atlas_context("ctx:missing", ["marker:tnnt2", "evidence:missing"])
    assert context.marker_ids == ("marker:tnnt2",)
    assert context.provenance == ("marker:tnnt2",)
    assert context.metadata == {"missing_record_ids": ["evidence:missing"]}
