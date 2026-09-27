# Virelion-CardiAtlas

CardiAtlas is a Python library for representing and retrieving cardiac biomedical metadata, evidence, phenotypes, datasets, studies, samples, and provenance.

## What it contains

- Typed records for studies, datasets, samples, markers, phenotypes, interventions, evidence, and claims.
- Controlled cardiac terminology and identifier/label normalization.
- Evidence-linked relationships and contradiction-aware claims.
- Study/sample metadata ingestion and quality checks.
- Real PubMed/GEO metadata retrieval and live GEO Series (SOFT) reconstruction, using only the standard library.
- SQLite persistence, JSONL interchange, and a `cardiatlas.models` <-> `schemas/*.json` contract kept in sync by `scripts/generate_json_schemas.py`.
- A draft -> candidate -> verified -> deprecated release lifecycle (`cardiatlas.release_lifecycle`), with deterministic manifests, hashes, and readiness checks.
- CLI and Python APIs, including a small framework-agnostic facade (`AtlasAPI`) for other Virelion-HeartTwin repos to call into.

CardiAtlas stores metadata and derived records. It does not redistribute third-party source datasets unless their licenses permit it.

## Installation

```bash
pip install -e '.[test]'
```

## Quickstart: an in-memory session

```python
from cardiatlas import AtlasService

service = AtlasService.empty()
print(service.resolve("MI"))  # "phenotype:myocardial_infarction"
```

Or, framed as a small API facade for another repo to call into:

```python
from cardiatlas import AtlasAPI, AtlasService

api = AtlasAPI(AtlasService.empty())
print(api.health())
```

## Quickstart: a persistent, cumulative knowledge base (CLI)

Most CLI commands are ephemeral by default (nothing persists once the process exits) -- pass `--db path/to/atlas.sqlite` (or, for `load`/`search`/`context`/`export`/`release`, a required `db` argument) to accumulate a real, queryable knowledge base across separate invocations instead:

```bash
# Ingest one or more JSONL record bundles (and optionally a relations JSONL) into a store.
cardiatlas load atlas.sqlite data/examples/*.jsonl data/reference/cardiBench_evidence.jsonl data/reference/cardiac_datasets.jsonl --relations data/reference/core_relationships.jsonl

# Everything below now sees, and can add to, whatever's in atlas.sqlite.
cardiatlas corpus --db atlas.sqlite
cardiatlas search atlas.sqlite "cardiac fibrosis" --limit 10
cardiatlas context atlas.sqlite marker:postn --hops 1
cardiatlas explain marker:postn --db atlas.sqlite
cardiatlas release-check --db atlas.sqlite

# Fetch and persist in the same step.
cardiatlas pubmed "myocardial infarction single cell" --limit 10 --db atlas.sqlite
cardiatlas geo "heart myocardial infarction single cell" --limit 10 --db atlas.sqlite
cardiatlas reconstruct-geo GSE217494 --output ./bundles/gse217494 --db atlas.sqlite
cardiatlas reconstruct-study dataset.json samples.csv --output ./bundles/study --db atlas.sqlite

# Get everything back out again.
cardiatlas export atlas.sqlite everything.jsonl
cardiatlas export atlas.sqlite release.json --release-version 1.2.0
cardiatlas export atlas.sqlite candidates.json --benchmark-candidates
```

## Release lifecycle

A release moves through an explicit, one-way state machine -- draft -> candidate -> verified -> deprecated (docs/release-checklist.md) -- backed by the same SQLite store:

```bash
cardiatlas release stage atlas.sqlite --version 1.2.0
cardiatlas release promote atlas.sqlite 1.2.0
cardiatlas release verify atlas.sqlite 1.2.0 --commit "$GITHUB_SHA" --ci-passed
cardiatlas release show atlas.sqlite 1.2.0
cardiatlas release list atlas.sqlite --state verified
cardiatlas release deprecate atlas.sqlite 1.2.0 --superseded-by 1.3.0
```

Every transition re-derives the release's digest from what's currently in the store and refuses to proceed if it no longer matches what was staged -- so a `verified` release always reflects an exact, unchanged record set. `verify` also requires an explicit commit SHA and confirmed CI status from the caller, since CardiAtlas has no way to observe either fact on its own.

## Other CLI commands

```bash
cardiatlas resolve "MI"                        # -> canonical ontology concept
cardiatlas identifier GSE217494                 # -> gene symbol / accession / PMID resolution
cardiatlas ontology --category phenotype        # -> controlled cardiac concepts
cardiatlas harvest --domain myocardial_infarction --plan-only   # -> the bounded public acquisition plan
cardiatlas harvest --domain myocardial_infarction --output ./harvest   # -> live PubMed/GEO harvest, QC'd and deduplicated
cardiatlas promote-harvest ./harvest --output ./promoted        # -> promote a harvested artifact into candidate records
cardiatlas build-reference --version 1.0.0                      # -> build the checked-in reference Atlas
```

Network access is explicit; importing the package and running tests do not silently contact external services. `pubmed`/`geo`/`harvest`/`reconstruct-geo` are the only commands that do, all via `cardiatlas.ncbi.NcbiClient`, a small stdlib-only NCBI E-utilities/GEO client with built-in rate limiting.

## Inputs and outputs

**Inputs:** study/dataset/sample metadata, identifiers, phenotype and ontology terms, evidence records, JSONL records, relation bundles, and PubMed/GEO queries.

**Outputs:** typed metadata/evidence records, normalized identifiers and labels, SQLite/JSONL records, release manifests, hashes, snapshot diffs, and query results.

Unknown metadata remain unknown; normalization retains confidence and provenance rather than silently converting uncertain matches into facts.

## Validation

Automated checks cover schema integrity, identifiers, duplicate accessions, provenance, controlled relationship predicates, benchmark-readiness, release state, and metadata completeness (docs/release-checklist.md). Tests cover the public API and regression behavior, and CI checks that `schemas/*.json` hasn't drifted from `cardiatlas.models` (`scripts/generate_json_schemas.py --check`). Passing validation does not establish biological correctness; ontology mappings and scientific interpretation require review.

## Limitations

Metadata quality is limited by the source records. Identifier and ontology normalization can remain ambiguous. Public-accession availability does not guarantee complete sample-level metadata or correct biological interpretation. CardiAtlas does not replace scientific review of study design or evidence.

A few internal modules (`snapshot.py`, `ingest.py`, `io.py`) predate, and functionally overlap with, `release.py`, `corpus_promote.py`/`promotion.py`, and `loader.py` respectively. They aren't part of the public `__init__.py` API surface and aren't used elsewhere in the codebase; they're left in place rather than restructured, since nothing currently depends on them and merging them isn't a functional fix so much as a cleanup with its own risk of regressions.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See `LICENSE`.
