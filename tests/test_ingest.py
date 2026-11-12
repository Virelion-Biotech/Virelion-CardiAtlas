"""Tests for JSONL ingestion helpers in cardiatlas.ingest."""
from __future__ import annotations

import json

import pytest

from cardiatlas import AtlasRegistry, MarkerRecord, PhenotypeRecord, record_from_dict
from cardiatlas.ingest import IngestionError, dump_jsonl, iter_jsonl, load_jsonl


def _records():
    return [
        MarkerRecord(id="marker:tnnt2", name="TNNT2", entity_id="TNNT2", entity_type="gene"),
        PhenotypeRecord(id="phenotype:mi", name="Myocardial infarction", category="injury"),
    ]


def test_dump_and_reload_round_trip(tmp_path):
    path = tmp_path / "nested" / "records.jsonl"
    assert dump_jsonl(_records(), path) == 2
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["marker:tnnt2", "phenotype:mi"]
    assert lines[0] == json.dumps(_records()[0].to_dict(), sort_keys=True, ensure_ascii=False)

    registry = AtlasRegistry()
    assert load_jsonl(registry, path, record_from_dict) == 2
    assert len(registry) == 2
    assert registry.get("marker:tnnt2").entity_id == "TNNT2"
    # upsert semantics: loading the same file twice does not duplicate records
    assert load_jsonl(registry, path, record_from_dict) == 2
    assert len(registry) == 2


def test_iter_jsonl_skips_blank_lines(tmp_path):
    path = tmp_path / "x.jsonl"
    path.write_text('{"a": 1}\n\n   \n{"b": 2}\n', encoding="utf-8")
    assert list(iter_jsonl(path)) == [{"a": 1}, {"b": 2}]


@pytest.mark.parametrize(
    "content, message",
    [('{"a": 1}\n{not json}\n', "invalid JSON on line 2"), ('[1, 2]\n', "line 1 must contain a JSON object")],
)
def test_iter_jsonl_reports_bad_lines(tmp_path, content, message):
    path = tmp_path / "bad.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(IngestionError, match=message):
        list(iter_jsonl(path))
    assert issubclass(IngestionError, ValueError)


def test_load_jsonl_rejects_invalid_records(tmp_path):
    path = tmp_path / "invalid.jsonl"
    payload = _records()[0].to_dict()
    payload["name"] = ""
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    registry = AtlasRegistry()
    with pytest.raises(ValueError, match="name must be non-empty"):
        load_jsonl(registry, path, record_from_dict)
    assert len(registry) == 0
