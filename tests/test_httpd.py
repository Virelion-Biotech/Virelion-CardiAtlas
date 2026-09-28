import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from cardiatlas.httpd import build_server
from cardiatlas.models import EvidenceRecord, MarkerRecord
from cardiatlas.sqlite import SQLiteAtlasStore


@pytest.fixture()
def running_server(tmp_path: Path):
    db_path = tmp_path / "atlas.sqlite"
    with SQLiteAtlasStore(db_path) as store:
        store.upsert_many([
            MarkerRecord(id="marker:postn", name="POSTN", entity_id="POSTN"),
            EvidenceRecord(id="evidence:e1", name="Cardiac fibrosis paper", source_type="pubmed", source_identifier="1"),
        ])
    httpd, _ = build_server(str(db_path), "127.0.0.1", 0)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=2)
        httpd.server_close()


def _get(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _post(url: str, payload: object) -> tuple[int, dict]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def test_health(running_server):
    status, body = _get(f"{running_server}/health")
    assert status == 200
    assert body["status"] == "ok"
    assert body["record_count"] == 2
    assert body["contract_version"] == "1.0"


def test_atlas_search_matches_hearttwin_native_shape(running_server):
    status, body = _post(f"{running_server}/v1/atlas/search", {"query": "POSTN", "limit": 5})
    assert status == 200
    assert body["contract_version"] == "1.0"
    assert body["query"] == "POSTN"
    assert body["count"] == 1
    assert body["records"][0]["id"] == "marker:postn"


def test_atlas_context_matches_hearttwin_typed_payload(running_server):
    status, body = _post(
        f"{running_server}/v1/atlas/context",
        {"entity_id": "sample-1", "context_id": "sample-1-context", "record_ids": ["marker:postn"]},
    )
    assert status == 200
    assert body["contract_version"] == "1.0"
    assert body["context_id"] == "sample-1-context"
    assert body["record_ids"] == ["marker:postn"]
    assert body["context"]["marker_ids"] == ["marker:postn"]
    assert body["context"]["contract_version"] == "1.1"
    assert body["provenance"] == ["marker:postn"]


def test_request_local_records_overlay_without_mutating_server(running_server):
    transient = {
        "id": "marker:tnnt2",
        "record_type": "marker",
        "name": "TNNT2",
        "entity_id": "TNNT2",
        "schema_version": "0.3",
    }
    status, body = _post(
        f"{running_server}/v1/atlas/context",
        {"record_ids": ["marker:tnnt2"], "records": [transient]},
    )
    assert status == 200
    assert body["context"]["marker_ids"] == ["marker:tnnt2"]

    status, body = _post(f"{running_server}/v1/atlas/search", {"query": "TNNT2"})
    assert status == 200
    assert body["count"] == 0


def test_missing_record_ids_yields_explicit_empty_context(running_server):
    status, body = _post(f"{running_server}/v1/atlas/context", {"entity_id": "sample-1"})
    assert status == 200
    assert body["record_ids"] == []
    assert body["context"]["provenance"] == []


def test_missing_search_query_does_not_dump_persistent_corpus(running_server):
    status, body = _post(f"{running_server}/v1/atlas/search", {"entity_id": "sample-1"})
    assert status == 200
    assert body == {"contract_version": "1.0", "query": "", "records": [], "count": 0}


def test_bad_types_fail_closed(running_server):
    cases = [
        ("/v1/atlas/search", {"query": 123}),
        ("/v1/atlas/search", {"query": "POSTN", "tags": "fibrosis"}),
        ("/v1/atlas/search", {"query": "POSTN", "limit": True}),
        ("/v1/atlas/context", {"record_ids": "marker:postn"}),
        ("/v1/atlas/context", {"record_ids": [1]}),
    ]
    for route, payload in cases:
        status, body = _post(f"{running_server}{route}", payload)
        assert status == 400
        assert "error" in body


def test_non_object_json_is_400(running_server):
    status, body = _post(f"{running_server}/v1/atlas/search", ["not", "an", "object"])
    assert status == 400
    assert "object" in body["error"]


def test_unknown_route_is_404(running_server):
    status, body = _get(f"{running_server}/v1/atlas/nonexistent")
    assert status == 404
    assert "error" in body
    status, body = _post(f"{running_server}/v1/atlas/nonexistent", {})
    assert status == 404
    assert "error" in body


def test_bad_json_is_400(running_server):
    req = urllib.request.Request(
        f"{running_server}/v1/atlas/search",
        data=b"not json",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as excinfo:
        urllib.request.urlopen(req)
    assert excinfo.value.code == 400
