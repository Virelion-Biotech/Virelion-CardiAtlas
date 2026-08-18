# Virelion CardiAtlas

**A structured, evidence-aware cardiac biomedical knowledge layer for the Virelion cardiac-AI ecosystem.**

CardiAtlas converts heterogeneous public biomedical information into **typed records, normalized concepts, evidence-linked relationships, contradiction-aware claims, study/sample metadata, reproducible releases, and portable context objects**.

## The role of CardiAtlas

CardiBench is the benchmark/data layer. CardiAtlas is the biological knowledge layer that explains what those datasets contain, how studies and samples are structured, and how observations relate to cardiac biology.

```text
                    PUBLIC KNOWLEDGE
        papers / PubMed / GEO / SRA / datasets
                         |
                         v
              ingestion + normalization
                         |
                         v
                 +----------------+
                 |   CardiAtlas    |
                 |-----------------|
                 | entities        |
                 | ontology        |
                 | evidence        |
                 | claims          |
                 | graph           |
                 | provenance      |
                 | releases        |
                 +-------+--------+
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
         CardiBench  CardiAgent   CardiVex
             |           |           |
             +-----------+-----------+
                         v
                    CardiEval
                         ^
                         |
                    CardiLearn
```

## What is implemented

### 1. Typed biomedical knowledge model

CardiAtlas natively represents:

- evidence records and citations
- molecular markers
- cardiac phenotypes
- cell states
- public datasets
- studies
- samples/biological experimental units
- interventions and observed phenotype-level outcomes

Study-level and sample-level metadata are deliberately separate so downstream systems can reason about subject/donor/animal grouping, technical replicates, cell context, region, condition, and timepoint.

### 2. Cardiac concept ontology

A lightweight controlled vocabulary normalizes recurring concepts across the ecosystem, including cardiac cell types, maturity/stress states, myocardial injury/remodeling phenotypes, electrophysiology, angiogenesis, extracellular-matrix processes, inflammation, regeneration, and vascular injury.

Resolution is conservative: known synonyms map to a canonical concept; unknown concepts remain unknown rather than being silently guessed.

The ontology supports parent/child traversal so a downstream system can ask for a broad concept such as `cell:immune` and retrieve its controlled descendants.

### 3. Evidence and contradiction handling

Evidence is not treated as a single truth value. Evidence records carry an explicit polarity:

```text
supports / refutes / mixed / unknown
```

Claims can therefore be assessed as supported, refuted, conflicted, mixed, or undetermined. Supporting and refuting sources remain queryable rather than being averaged away.

### 4. Relationship graph

`AtlasGraph` stores controlled predicates such as:

```text
marker  -> marks           -> cell type
marker  -> associated_with -> cell state/phenotype
phenotype -> involves      -> process
dataset -> derived_from    -> study
study   -> has_dataset     -> dataset
dataset -> has_sample      -> sample
```

Edges carry evidence IDs, confidence, and source metadata. Duplicate edges merge provenance. Unknown predicates are rejected so the published relationship vocabulary stays consistent across downstream projects.

### 5. Metadata harmonization and identifier resolution

The platform includes conservative utilities for:

- gene aliases such as common cardiac gene names;
- GEO/SRA/BioProject/PMID accession normalization;
- condition aliases such as sham/control/reference and MI/infarction;
- single-cell/single-nucleus modality normalization;
- ontology-backed label resolution.

The resolver reports confidence and provenance rather than presenting every fuzzy match as a fact.

### 6. Dataset/study/sample intelligence

CardiAtlas can construct a logical study from multiple dataset records, ingest sample metadata rows, normalize conditions/modalities, and assess study-level metadata completeness.

Study QC includes:

- sample counts;
- biological subject counts;
- technical replicate counts;
- missing subject IDs;
- missing conditions/timepoints;
- duplicate sample accessions;
- warnings about limited leakage-control metadata.

### 7. CardiBench integration

CardiAtlas exposes a **CardiBench integration contract** rather than hard-depending on CardiBench.

A dataset can become a portable benchmark candidate containing accession, study title, organism, tissue, modality, conditions, sample count, cell/nucleus context, and provenance. A conservative readiness gate blocks incomplete metadata instead of guessing missing biological labels.

The repository also carries a small metadata-only catalog of cardiac accessions already registered by CardiBench.

### 8. Persistent backend

`SQLiteAtlasStore` persists typed records and graph relations while keeping the storage backend separate from the public data contract.

### 9. Reproducible releases

Release/snapshot manifests contain:

- package/release version;
- schema version;
- creation timestamp;
- record counts by type;
- canonical SHA-256 digest.

Equivalent records hash identically regardless of insertion order. A snapshot diff utility identifies added, removed, and changed record IDs between Atlas states.

### 10. Release readiness

Before an Atlas release is considered structurally ready, the repository can check:

- record/schema validity;
- unique IDs;
- duplicate dataset accessions;
- provenance resolution;
- non-empty release state;
- evidence inventory.

This does not claim that automated checks replace scientific review. Biological disagreement and interpretation remain explicit data problems.

### 11. Unified service/API layer

`AtlasService` combines registry, graph, search, structured queries, ontology resolution, identifier resolution, dataset/study QC, claim assessment, release manifests, and portable context generation.

`AtlasAPI` provides a framework-agnostic facade for downstream services with health, search, resolution, explanation, context, and snapshot operations.

### 12. NCBI ingestion primitives

A dependency-free NCBI E-utilities client supports explicit retrieval of public metadata for PubMed and GEO/GDS. Adapters convert returned source metadata into CardiAtlas records.

Network access is explicit; imports and tests do not silently contact external services.

## CLI

Install locally:

```bash
pip install -e '.[test]'
```

Examples:

```bash
cardiatlas pubmed "myocardial infarction single cell" --limit 10
cardiatlas geo "heart myocardial infarction single cell" --limit 10
cardiatlas resolve "MI"
cardiatlas identifier TNNT2
cardiatlas identifier GSE217494
cardiatlas ontology --category phenotype
cardiatlas release-check
```

## Repository layout

```text
cardiatlas/
  models.py          # typed domain records
  ontology.py        # cardiac concept resolution
  normalize.py       # identifiers and labels
  harmonize.py       # condition/modality harmonization
  identifiers.py     # conservative identifier resolution
  validation.py      # schema and integrity checks
  registry.py        # in-memory registry
  sqlite.py          # persistent backend
  graph.py           # controlled relationship graph
  evidence.py        # evidence scoring
  claims.py          # contradiction-aware claims
  provenance.py      # lineage/audit events
  query.py           # structured retrieval
  studies.py         # study/sample QC
  sample_ingest.py   # sample metadata ingestion
  catalog.py         # dataset grouping/catalog helpers
  service.py         # orchestration layer
  api.py             # downstream API facade
  integrations.py    # CardiBench contract
  qc.py              # dataset readiness gates
  release.py         # deterministic manifests
  release_checks.py  # structural release readiness
  diff.py            # snapshot diffing
  export.py          # portable exports
  contracts.py       # cross-repository context contract
  ingest.py          # JSONL ingestion
  ncbi.py            # NCBI client
  adapters.py        # source adapters
  io.py              # JSONL interchange
  cli.py             # CLI

schemas/              # machine-readable contracts
data/examples/       # transparent examples
data/reference/       # cardiac/reference metadata seeds
docs/                 # architecture, data model, release, integration policy
tests/                # unit/integration regression tests
.github/workflows/    # multi-version CI
```

## Interoperability

### CardiBench

CardiAtlas supplies biological context and normalized study/dataset metadata. CardiBench remains authoritative for locked benchmark definitions, leakage-aware splits, and benchmark release policy.

### CardiAgent

Agent generation can retrieve normalized phenotypes, cell states, markers, datasets, study context, and supporting evidence while retaining Atlas provenance.

### CardiVex

Vex can use Atlas graph neighborhoods, ontology resolution, and evidence explanations to map observed cardiac signals to interpretable candidate states.

### CardiEval

Eval can attach model results to an Atlas context and distinguish biological conclusions supported by independent evidence from conflicted or weakly evidenced conclusions.

### CardiLearn

Learn can build reproducible training corpora from Atlas-linked datasets while preserving study, subject, modality, and provenance metadata.

## Data principles

1. **Evidence first.** Assertions remain traceable to sources.
2. **No silent inference.** Unknown metadata are not promoted to confident facts.
3. **Conflict is data.** Contradictory evidence remains queryable.
4. **Provenance survives transformation.** Normalization must not erase lineage.
5. **Reproducibility over convenience.** Releases are hashable and diffable.
6. **Metadata before raw data.** Public accession metadata can be indexed without redistributing source datasets.

## Current status

**Phase 4 — platform foundation.** CardiAtlas now has an expanded domain model, controlled cardiac ontology, evidence/claim layer, controlled graph, identifier and metadata harmonization, study/sample intelligence, SQLite persistence, deterministic releases and diffs, release readiness checks, CardiBench integration, portable downstream contracts, NCBI ingestion, CLI/API surfaces, reference metadata, and broader automated regression coverage.

The major remaining work is now **scale and scientific verification**: systematic literature/dataset acquisition, authoritative ontology mappings, sample-level harmonization across many public studies, richer retrieval/ranking, and deployment of the API as a service. The core architecture is no longer the limiting factor.

## Scientific scope

CardiAtlas is a biomedical information and evidence system. It stores and normalizes published/public observations and does not provide operational instructions for harmful biological activity.

## License

MIT
