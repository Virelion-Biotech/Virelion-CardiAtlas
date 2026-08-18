from cardiatlas import AtlasService, MarkerRecord, Query


def test_service_resolution_query_and_context():
    service = AtlasService.empty()
    service.add(MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2", tags=["cardiomyocyte"]))
    assert service.resolve("MI") == "phenotype:myocardial_infarction"
    hits = service.query(Query(text="TNNT2", record_type="marker"))
    assert hits and hits[0].record.id == "marker:tnnt2"
    context = service.atlas_context("ctx:1", ["marker:tnnt2"])
    assert context.marker_ids == ("marker:tnnt2",)
