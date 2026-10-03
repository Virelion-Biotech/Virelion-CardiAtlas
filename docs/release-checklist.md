# CardiAtlas release checklist

A CardiAtlas release should be reproducible and auditable before it is consumed by another Virelion component.

## Required checks

1. All records validate against the current schema version. — `release_checks.assess_release` → `record_validation`.
2. IDs are unique and stable. — `release_checks.assess_release` → `unique_ids`.
3. Dataset accessions are not duplicated unintentionally. — `release_checks.assess_release` → `dataset_accessions`.
4. Every provenance/source reference resolves to an indexed evidence record when a release claims a closed evidence graph. — `release_checks.assess_release` → `provenance_links`; hard error only when `closed_evidence_graph=True` (the default for `build-reference`/`release-check`, and always true once a release reaches `verified`), otherwise advisory.
5. Sample metadata contain enough biological grouping information for the intended benchmark or analysis use. — `release_checks.assess_release` → `benchmark_readiness`, aggregating `study_readiness.assess_study_benchmark_readiness` across every study in the release; advisory unless `require_benchmark_ready=True` is requested (e.g. `cardiatlas release verify --require-benchmark-ready`).
6. Controlled relationship predicates are used. — enforced at insertion time by `AtlasGraph.add()`, and re-checked independently at release time by `release_checks.assess_release` → `controlled_predicates`, since a release may assemble relations from a persisted store that bypassed that guard.
7. The release digest is generated from the canonical record payload. — `release.digest_records` / `release.canonical_payload`; this never changes as a release moves through lifecycle states.
8. The exact release version, schema version, and source inventory are recorded. — `release.ReleaseManifest` (`version`, `schema_version`, `dataset_accessions`, `evidence_sources`).
9. CI passes on the release commit. — supplied by the caller (normally CI itself) to `cardiatlas release verify --commit <sha> --ci-passed`; CardiAtlas has no way to observe this on its own.

## Release states

- **draft** — internally generated; may contain unresolved provenance or incomplete metadata.
- **candidate** — passes structural checks and is suitable for review.
- **verified** — CI and source/provenance checks pass on the exact release commit.
- **deprecated** — superseded by a newer release but retained for reproducibility.

Implemented in `cardiatlas/release_lifecycle.py` as an explicit, one-way state machine (`draft -> candidate -> verified -> deprecated`; see `RELEASE_STATES`). Every transition re-derives the release's manifest digest from whatever is currently in the store and refuses to proceed if it no longer matches the digest captured when the release was staged, so a `verified` release always reflects an exact, unchanged record set.

### CLI

```bash
# Snapshot everything currently in a CardiAtlas SQLite store as a new draft release.
cardiatlas release stage atlas.sqlite --version 1.2.0

# draft -> candidate: structural (error-severity) checks must all pass.
cardiatlas release promote atlas.sqlite 1.2.0

# candidate -> verified: requires the exact commit and a passing CI run.
cardiatlas release verify atlas.sqlite 1.2.0 --commit "$GITHUB_SHA" --ci-passed

# Any non-deprecated state -> deprecated, once superseded.
cardiatlas release deprecate atlas.sqlite 1.2.0 --superseded-by 1.3.0

# Inspect.
cardiatlas release show atlas.sqlite 1.2.0
cardiatlas release list atlas.sqlite --state verified
```

The same operations are available as plain functions in `cardiatlas.release_lifecycle` (`create_draft`, `promote_to_candidate`, `verify`, `deprecate`) for callers that want to drive the lifecycle without going through the CLI, and `SQLiteAtlasStore.save_release_record` / `get_release_record` / `list_release_records` persist it.

## What is deliberately not automated

Automatic agreement with the literature is not treated as a release criterion. Biological interpretation, contradictory evidence, sample semantics, and benchmark eligibility may require explicit scientific review.
