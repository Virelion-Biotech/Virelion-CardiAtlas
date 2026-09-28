# Changelog

All notable changes to Virelion-CardiAtlas are documented here.

## 0.8.1

### Added

- `cardiatlas serve <db>`: stdlib-only HTTP deployment for HeartTwin's registered `atlas.search` and `atlas.context` capabilities.
- Request-local `records` overlays for HeartTwin workflows without mutating the persistent Atlas.
- Real-socket HTTP contract tests and a CI smoke test.

### Fixed

- Native/HTTP wire parity: `atlas.context` returns HeartTwin's typed wrapper rather than a raw `AtlasContext`, and `atlas.search` returns `{contract_version, query, records, count}`.
- Omitted HeartTwin search queries now return zero hits instead of dumping arbitrary persistent records.
- JSON bodies, field types, search limits, body size, and malformed `Content-Length` are validated; unknown routes return 404 and expected contract errors return 400.
- Request-local records are isolated from the server's base in-memory Atlas.
- Atlas context provenance now includes only records that actually resolve; missing requested IDs are reported under `context.metadata.missing_record_ids` instead of being represented as provenance.

## 0.7.0

This release turns CardiAtlas from a collection of correct-but-disconnected one-shot commands into an actual cumulative, queryable knowledge base end to end from the CLI, and fixes several more latent bugs of the same shape as 0.6.0's.

### Added

- **Persistent-store CLI.** `corpus`, `explain`, `release-check`, `pubmed`, `geo`, `harvest`, `promote-harvest`, `reconstruct-study`, and `reconstruct-geo` all gained an optional `--db PATH` that runs them against a `SQLiteAtlasStore` instead of a throwaway empty `AtlasService`, so records and relations accumulate across separate CLI invocations instead of vanishing when the process exits. Previously, nothing in the CLI ever loaded anything into `service` before these commands ran, so `corpus`/`explain`/`release-check` could never report anything but empty/404, and `pubmed`/`geo`/`harvest`'s fetched records were never added to the service at all -- fixed as part of this change.
- **New CLI commands**: `load` (ingest JSONL record bundles, and optionally a relations JSONL, into a store -- rejects and reports any relation using a predicate outside `schema.RELATION_TYPES` rather than silently accepting it), `search` (lexical + evidence-aware retrieval, with `--context` for graph neighborhoods), `context` (a record's graph neighborhood), and `export` (dump a store back out as JSONL, a full release bundle, or CardiBench benchmark candidates).
- **`SQLiteAtlasStore.load_service()` / `.save_service()`**: the bridge that makes the above possible -- turns the store's contents into a fully-featured, in-memory `AtlasService` (search/retrieve/context/reconstruct/release-readiness/etc.) and flushes one back, idempotently.
- `reconstruct-geo` now actually adds the fetched dataset/study/samples to the service (with the same `has_dataset`/`has_sample` relations `reconstruct-study` records), so a live GEO reconstruction is queryable in-process, not just written to files.
- `python -m cardiatlas` now works (`cardiatlas/__main__.py`), alongside the installed console script.
- `scripts/generate_json_schemas.py`: regenerates `schemas/*_record.schema.json` from the actual `cardiatlas.models` dataclasses, and a new CI step (`--check`) fails the build if they drift again.
- `release_lifecycle`'s public API (`create_draft`, `promote_to_candidate`, `verify` as `verify_release`, `deprecate`, `ReleaseRecord`, `RELEASE_STATES`, ...) and `search.search`/`search_records` are now re-exported from the top-level `cardiatlas` package, matching every other module.
- Regression tests for all of the above: `test_sqlite_service_bridge.py`, `test_cli_persistence.py`, `test_catalog_and_io.py`, `test_schema_sync.py`, `test_public_api.py`.

### Fixed

- `schemas/*_record.schema.json` (all 8) described schema_version "0.2": every field the 0.2 -> 0.3 migration added (`cardiatlas/migrate.py`) was missing, along with the common `AtlasRecord` base fields (`description`, `source_ids`, `tags`, `metadata`, `schema_version`) that every record type has. These are CardiAtlas's published, language-agnostic contract for other Virelion-HeartTwin repos (docs/integration-contracts.md); a consumer validating against them would have been checking against a schema roughly one migration behind the real data. Regenerated from the current models; kept in sync going forward by `scripts/generate_json_schemas.py` and its CI check.
- `catalog.attach_datasets` rebuilt a `StudyRecord` via `StudyRecord(**study.to_dict())`, which includes the `init=False` `record_type` field and always raised `TypeError`. Same bug class as 0.6.0's `loader.record_from_dict` fix; this instance was untouched because nothing called it. Fixed with `dataclasses.replace()`, which handles `init=False` fields correctly by construction instead of needing a manual field filter.
- `io.read_jsonl` built its allowed-field set from `dataclasses.fields()` without excluding `init=False` fields (the same bug, again) -- any call with a `cardiatlas.models` record class always raised `TypeError`. Filtered by `.init`, matching the loader.py fix.
- README.md's quickstart called `AtlasService()` with no arguments; `AtlasService` is a plain dataclass with three required fields and has no default constructor. `AtlasService.empty()` is correct and is what the rest of the codebase actually uses.

### Changed

- README.md rewritten to document the persistent-store workflow, the release lifecycle CLI, `AtlasAPI`, and every CLI command -- every runnable example in it is now verified to execute exactly as written.
- `.github/workflows/test.yml` gained a schema-sync check step and a persistent-store CLI smoke-test step (`load` -> `corpus`/`search`/`context`/`release-check`/`export`).
- Noted, deliberately not restructured: `snapshot.py`, `ingest.py`, and `io.py` predate and functionally overlap with `release.py`, `corpus_promote.py`/`promotion.py`, and `loader.py` respectively. They are not part of the public `__init__.py` API and nothing else in the codebase calls them (confirmed by search), so merging them would be a cleanup with real regression risk rather than a functional fix; `io.read_jsonl`'s bug was still fixed since it's reachable, public library code.

## 0.6.0

### Fixed

- `loader.record_from_dict` crashed on every JSONL/JSON load (`build-reference`, checked-in examples, `migrate`) because its field filter passed the `init=False` `record_type` field back into the record's constructor.
- `harmonize.CONDITION_ALIASES` / `harmonize.MODALITY_ALIASES` / `identifiers.GENE_ALIASES` used human-readable keys with spaces and hyphens, but lookups are run through `normalize.canonical_key()`, which collapses those to underscores. Every multi-word alias (e.g. `"cardiac troponin t"`, `"single-cell RNA"`, `"snRNA-seq"`) silently missed its lookup and fell back to weak normalization. The lookup tables are now built by canonicalizing the raw keys at import time.
- `geo_reconstruct.reconstruct_study` built a synthesized study ID by lowercasing the dataset accession (`study:gse100`), inconsistent with dataset IDs elsewhere, which preserve accession case (`dataset:geo:GSE100`).
- `sqlite.SQLiteAtlasStore.put_relation` overwrote a relation's whole payload on conflict instead of merging evidence IDs the way the in-memory `AtlasGraph.add()` does, silently dropping evidence when the same relation was persisted twice.
- `identifiers.resolve_gene`'s uncurated "format" fallback was a tautology (`normalize_gene_symbol(value) == value.strip().upper()` is always true), so any uppercase token — including GEO/SRA accessions like `GSE217494` — was misclassified as a gene symbol before accession resolution ever ran.
- `AtlasService.reconstruct_study` recorded the dataset\<->study relation backwards and with an unrecognized predicate (`dataset --has_study--> study`, not in `schema.RELATION_TYPES`), instead of the documented `study --has_dataset--> dataset` (docs/data-model.md). This broke the `reconstruct-study` CLI command outright; no test previously covered that path.
- `pyproject.toml`'s `[project].version` (0.5.5) and `cardiatlas.__version__` (0.5.4) had drifted apart.

### Added

- **Release-state lifecycle** (`cardiatlas/release_lifecycle.py`): an explicit `draft -> candidate -> verified -> deprecated` state machine matching docs/release-checklist.md, with a digest-drift guard (a transition refuses to proceed if the underlying record set changed since the release was staged) and a fail-closed `verify()` that requires an explicit commit SHA and `ci_passed=True` from the caller.
  - New CLI: `cardiatlas release stage|promote|verify|deprecate|show|list`, operating against a `SQLiteAtlasStore`.
  - New persistence: `SQLiteAtlasStore.save_release_record` / `get_release_record` / `list_release_records`, backed by a new `release_lifecycle` table (kept separate from the existing `releases` table/`save_release`/`release` methods, which are unchanged).
- `release_checks.assess_release` gained two checks: `controlled_predicates` (validates relation predicates against `schema.RELATION_TYPES`) and `benchmark_readiness` (aggregates `study_readiness.assess_study_benchmark_readiness` across every study in the release). `provenance_links` severity is now conditional on a new `closed_evidence_graph` parameter, matching the "when a release claims a closed evidence graph" qualifier in the checklist.
- `release.ReleaseManifest` records a source inventory (`dataset_accessions`, `evidence_sources`), closing release-checklist item 8.
- CI now exercises the release-lifecycle CLI end to end (`.github/workflows/test.yml`).
- Regression tests: `test_service_reconstruct.py`, `test_cli_reconstruct_study.py` (covers the CLI path that shipped bug #6 undetected), `test_release_lifecycle.py`, `test_version_consistency.py`, plus new cases in `test_release.py`.

### Changed

- `build.build_reference` and `AtlasService.release_readiness` now pass their relations into `assess_release`, so `controlled_predicates` is actually exercised rather than silently checking zero relations.
- docs/release-checklist.md and docs/architecture.md updated to describe the implemented checks and the release lifecycle.
