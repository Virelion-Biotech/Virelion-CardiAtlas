from cardiatlas.acquisition import AcquisitionTarget
from cardiatlas.harvest import HarvestItem, deduplicate_harvest, harvest_report
from cardiatlas.harvester import HarvestBatch


def test_harvest_deduplication():
    items = [
        HarvestItem(source="pubmed", query_id="q1", external_id="1"),
        HarvestItem(source="pubmed", query_id="q1", external_id="1"),
        HarvestItem(source="geo", query_id="q2", external_id="GSE1"),
    ]
    unique = deduplicate_harvest(items)
    assert [(item.source, item.external_id) for item in unique] == [("pubmed", "1"), ("geo", "GSE1")]
    report = harvest_report(items)
    assert report["item_count"] == 2
    assert report["sources"] == {"geo": 1, "pubmed": 1}


def test_harvest_batch_is_portable():
    target = AcquisitionTarget(target_id="pubmed:test", source="pubmed", query="test", domain="test")
    batch = HarvestBatch(target.target_id, (), ())
    payload = batch.to_dict()
    assert payload["target_id"] == target.target_id
    assert payload["record_count"] == 0
