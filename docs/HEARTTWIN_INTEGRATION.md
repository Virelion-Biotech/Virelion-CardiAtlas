# Virelion-HeartTwin integration

CardiAtlas supports the two capabilities HeartTwin currently registers for it:
`atlas.search` and `atlas.context`. HeartTwin can invoke them either through its
native adapter when the `cardiatlas` package is installed, or through the HTTP
fallback configured by `CARDIATLAS_URL`.

The important contract is **wire parity**: both modes return the same
HeartTwin-facing JSON shape. The raw `AtlasContext` inside the wrapper retains
CardiAtlas's own contract version (`1.1`), while the outer HeartTwin adapter
payload is version `1.0`.

## HTTP deployment

```bash
cardiatlas serve atlas.sqlite --host 0.0.0.0 --port 8420
# export CARDIATLAS_URL=http://<host>:8420 for HeartTwin
```

Routes:

| Route | Method | Request | HeartTwin-facing response |
|---|---|---|---|
| `/health` | GET | none | `AtlasAPI.health()` |
| `/v1/atlas/search` | POST | `{query?, text?, record_type?, tags?, limit?, records?}` | `{contract_version, query, records, count}` |
| `/v1/atlas/context` | POST | `{record_ids?, context_id?, entity_id?, records?}` | `{contract_version, context_id, record_ids, context, provenance}` |

`query` is the HeartTwin-native name; `text` is accepted as a compatibility
alias. If both are supplied they must agree.

`records` is optional. When present, those records are overlaid on the loaded
SQLite Atlas **for that request only**. They do not mutate the server's
in-memory base Atlas or the SQLite database. This makes the HTTP fallback
semantically compatible with HeartTwin workflows that pass transient Atlas
records while still allowing a deployed server to answer from a persistent
knowledge base.

Invalid JSON, invalid field types, or oversized bodies fail with HTTP 400.
Unknown routes return 404. An omitted `record_ids` list yields an explicit
empty context, which matches HeartTwin's generic invocation path without
inventing biological context. An omitted search query yields zero hits rather
than dumping arbitrary records from the persistent Atlas.

### Example

```bash
curl -sS -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:8420/v1/atlas/search \
  -d '{"query":"cardiac fibrosis","limit":10}'

curl -sS -H 'Content-Type: application/json' \
  -X POST http://127.0.0.1:8420/v1/atlas/context \
  -d '{"entity_id":"sample-001","record_ids":["marker:postn"]}'
```

## Native use inside HeartTwin

CardiAtlas itself exposes the framework-agnostic `AtlasAPI`:

```python
from cardiatlas import AtlasAPI
from cardiatlas.sqlite import SQLiteAtlasStore

with SQLiteAtlasStore("atlas.sqlite") as store:
    api = AtlasAPI(store.load_service())
    api.search(text="cardiac fibrosis", limit=10)
    api.context(record_ids=["marker:postn"], context_id="sample-001-context")
```

HeartTwin's native adapter is responsible for wrapping those calls into the
same outer JSON contract used by the HTTP routes. HeartTwin may also load a
persistent store through its own `CARDIATLAS_DB` configuration when supported
by the installed HeartTwin revision.

## Store lifecycle

`cardiatlas serve` loads the SQLite store into memory once at startup. Restart
the process after changing the persistent store. The HTTP API is intentionally
read-only; request-local overlays are discarded after each request.
