# Virelion-HeartTwin integration

CardiAtlas supports native Python use and a stdlib-only HTTP fallback. The native adapter and HTTP server must keep their response contracts compatible as they evolve.

## Read capabilities

The native service capabilities are `atlas.search`, `atlas.context`, `atlas.retrieve`, `atlas.explain`, `atlas.claim`, `atlas.claims`, `atlas.dataset.readiness`, and `atlas.graph`.

| Capability | Input | Purpose |
|---|---|---|
| `atlas.search` | `query` or compatibility `text`, optional record type/tags/limit | Exact multi-field lexical query |
| `atlas.retrieve` | `query`, optional record type and bounded limit | Partial-term retrieval with separate lexical and heuristic evidence inventory scores |
| `atlas.context` | `record_ids`, optional `context_id` | Structured context for HeartTwin |
| `atlas.explain` | `record_id` | Record, indexed evidence, neighbors and graph edges |
| `atlas.claim` | `claim_id` | Current claim revision, evidence status and source-located citations |
| `atlas.claims` | empty object | Enumerate persisted current claim revisions |
| `atlas.dataset.readiness` | `study_id`, `dataset_id` | Explicit metadata and benchmark-readiness checks |
| `atlas.graph` | `record_id`, optional integer `hops` | Record, graph context and evidence explanation |

The HTTP server supports equivalent POST endpoints `/v1/atlas/search`, `/v1/atlas/context`, `/v1/atlas/retrieve`, `/v1/atlas/explain`, `/v1/atlas/claim`, `/v1/atlas/claims`, `/v1/atlas/dataset/readiness`, and `/v1/atlas/graph`; `GET /health` reports service status.

## Persistence

`CARDIATLAS_DB` points HeartTwin's native adapter to an existing SQLite database. Claim revisions are persisted separately from biomedical records; the current version is returned by APIs while earlier revisions remain available through SQLite's history API. This HTTP interface is read-only. Use authenticated curator tooling or local CLI operations to load new source-reviewed claim JSONL; never expose a write-enabled curation interface anonymously.

## Source and scientific limitations

A source-verified citation means the source location was checked, not that the biological interpretation was independently established. An expert-reviewed citation requires a reviewer identity. Claims without source locators or linked evidence cannot pass the strict claim-review release gate. A complete metadata checklist likewise does not prove statistical power, causal truth, or clinical validity.

`cardiatlas serve` loads SQLite into memory at startup. Restart after database changes. For public deployment, put the service behind HTTPS, authentication, rate limiting and resource limits; the stdlib server is not a standalone public-production boundary.
