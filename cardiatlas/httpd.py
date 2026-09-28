"""Minimal stdlib-only HTTP surface for Virelion-HeartTwin.

The wire contract mirrors HeartTwin's native CardiAtlas adapter so switching
between an installed package and ``CARDIATLAS_URL`` does not change response
shape. The persistent SQLite store is loaded once at startup. Optional records
supplied in a request are overlaid in a request-local service and never mutate
the server's base Atlas.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .api import AtlasAPI
from .loader import record_from_dict
from .service import AtlasService
from .sqlite import SQLiteAtlasStore

DEFAULT_PORT = 8420
MAX_BODY_BYTES = 1_048_576
MAX_SEARCH_LIMIT = 1_000


def _as_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("JSON body must be an object")
    return value


def _request_api(base_api: AtlasAPI, payload: dict[str, Any]) -> AtlasAPI:
    """Return the base API or a request-local overlay containing payload records."""
    raw_records = payload.get("records", [])
    if raw_records is None:
        raw_records = []
    if not isinstance(raw_records, list):
        raise ValueError("records must be an array of record objects")
    if not raw_records:
        return base_api

    service = AtlasService.empty()
    service.add_many(base_api.service.registry.all())
    for index, raw in enumerate(raw_records):
        if not isinstance(raw, dict):
            raise ValueError(f"records[{index}] must be an object")
        service.add(record_from_dict(raw))
    return AtlasAPI(service)


def _search_response(base_api: AtlasAPI, payload: dict[str, Any]) -> dict[str, Any]:
    has_query = "query" in payload
    has_text = "text" in payload
    if has_query and has_text and payload["query"] != payload["text"]:
        raise ValueError("query and text disagree")
    if not has_query and not has_text:
        return {"contract_version": "1.0", "query": "", "records": [], "count": 0}
    text = payload.get("query", payload.get("text", ""))
    if not isinstance(text, str):
        raise ValueError("query/text must be a string")

    record_type = payload.get("record_type")
    if record_type is not None and not isinstance(record_type, str):
        raise ValueError("record_type must be a string or null")

    raw_tags = payload.get("tags", [])
    if not isinstance(raw_tags, (list, tuple)) or isinstance(raw_tags, (str, bytes)):
        raise ValueError("tags must be an array of strings")
    if not all(isinstance(tag, str) for tag in raw_tags):
        raise ValueError("tags must contain only strings")

    raw_limit = payload.get("limit", 20)
    if isinstance(raw_limit, bool) or not isinstance(raw_limit, int):
        raise ValueError("limit must be an integer")
    if not 0 <= raw_limit <= MAX_SEARCH_LIMIT:
        raise ValueError(f"limit must be between 0 and {MAX_SEARCH_LIMIT}")

    api = _request_api(base_api, payload)
    result = api.search(text=text, record_type=record_type, tags=tuple(raw_tags), limit=raw_limit)
    records = [item["record"] for item in result["results"]]
    return {
        "contract_version": "1.0",
        "query": text,
        "records": records,
        "count": len(records),
    }


def _context_response(base_api: AtlasAPI, payload: dict[str, Any]) -> dict[str, Any]:
    record_ids = payload.get("record_ids", [])
    if not isinstance(record_ids, list) or not all(isinstance(item, str) for item in record_ids):
        raise ValueError("record_ids must be an array of strings")

    context_id = payload.get("context_id")
    if context_id is None:
        context_id = f"ctx-{payload.get('entity_id', 'unknown')}"
    if not isinstance(context_id, str) or not context_id:
        raise ValueError("context_id must be a non-empty string")

    api = _request_api(base_api, payload)
    raw = api.context(record_ids=record_ids, context_id=context_id).to_dict()
    return {
        "contract_version": "1.0",
        "context_id": context_id,
        "record_ids": list(record_ids),
        "context": raw,
        "provenance": list(raw.get("provenance", [])),
    }


def _make_handler(api: AtlasAPI) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "CardiAtlas/1.0"
        protocol_version = "HTTP/1.1"

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            raw_length = self.headers.get("Content-Length")
            if raw_length is None:
                raise ValueError("Content-Length is required")
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length < 0:
                raise ValueError("Content-Length must not be negative")
            if length > MAX_BODY_BYTES:
                raise ValueError(f"request body exceeds {MAX_BODY_BYTES} bytes")
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                decoded = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid JSON body: {exc}") from exc
            return _as_object(decoded)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send_json(200, api.health())
            else:
                self._send_json(404, {"error": f"not found: {self.path}"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path not in {"/v1/atlas/search", "/v1/atlas/context"}:
                self._send_json(404, {"error": f"not found: {self.path}"})
                return
            try:
                payload = self._read_json()
                if self.path == "/v1/atlas/search":
                    result = _search_response(api, payload)
                else:
                    result = _context_response(api, payload)
            except (KeyError, TypeError, ValueError) as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, result)

        def log_message(self, format: str, *args: object) -> None:
            pass

    return Handler


def build_server(db_path: str, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> tuple[ThreadingHTTPServer, AtlasAPI]:
    """Build (but do not start) the HTTP server and AtlasAPI it serves."""
    store = SQLiteAtlasStore(db_path)
    try:
        api = AtlasAPI(store.load_service())
    finally:
        store.close()
    handler = _make_handler(api)
    httpd = ThreadingHTTPServer((host, port), handler)
    return httpd, api


def serve(db_path: str, host: str = "127.0.0.1", port: int = DEFAULT_PORT) -> None:
    """Run the CardiAtlas HTTP surface against a persistent store until interrupted."""
    httpd, api = build_server(db_path, host, port)
    health = api.health()
    print(f"CardiAtlas serving {health['record_count']} records on http://{host}:{port}")
    print("  GET  /health")
    print("  POST /v1/atlas/search    {query|text, record_type?, tags?, limit?, records?}")
    print("  POST /v1/atlas/context   {record_ids?, context_id?, entity_id?, records?}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
