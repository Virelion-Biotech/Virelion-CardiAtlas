from pathlib import Path

from cardiatlas.harvest import HarvestItem
from cardiatlas.harvest_manifest import create_harvest_manifest
from cardiatlas.harvest_qc import assess_harvest
from cardiatlas.harvest_store import read_harvest, write_harvest


def _item(external_id: str, *, digest: str = "abc") -> HarvestItem:
    return HarvestItem(
        source="pubmed",
        query_id="pubmed:mi-single-cell",
        external_id=external_id,
        title=f"Study {external_id}",
        raw_digest=digest,
        source_url=f"https://pubmed.ncbi.nlm.nih.gov/{external_id}/",
    )


def test_harvest_qc_accepts_complete_items():
    qc = assess_harvest([_item("1"), _item("2")])
    assert qc.passed
    assert qc.item_count == 2
    assert qc.missing_digests == 0


def test_harvest_qc_rejects_missing_digest():
    qc = assess_harvest([_item("1", digest="")])
    assert not qc.passed
    assert qc.missing_digests == 1


def test_manifest_is_deterministic_for_order():
    a = create_harvest_manifest([_item("1"), _item("2")], created_at="2026-01-01T00:00:00+00:00")
    b = create_harvest_manifest([_item("2"), _item("1")], created_at="2026-01-01T00:00:00+00:00")
    assert a.digest == b.digest
    assert a.item_count == 2


def test_harvest_storage_roundtrip(tmp_path: Path):
    out = tmp_path / "harvest"
    manifest = write_harvest([_item("1"), _item("1"), _item("2")], out, created_at="2026-01-01T00:00:00+00:00")
    items, saved = read_harvest(out)
    assert len(items) == 2
    assert saved["digest"] == manifest.digest
