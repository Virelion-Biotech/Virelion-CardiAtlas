# Virelion CardiAtlas

**A structured, evidence-aware cardiac biomedical knowledge layer for the Virelion cardiac-AI ecosystem.**

CardiAtlas converts heterogeneous public biomedical information into **typed records, normalized concepts, evidence-linked relationships, contradiction-aware claims, reproducible releases, and portable context objects**.

## The role of CardiAtlas

CardiBench is the benchmark/data layer. CardiAtlas is the biological knowledge layer that explains what those datasets contain and how observations relate to cardiac biology.

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
                 | records         |
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

Records carry stable IDs, source metadata, schema versions, organism/tissue context, modalities, tags, and provenance.

### 2. Cardiac concept ontology

A lightweight controlled vocabulary now normalizes recurring concepts across the ecosystem, including:

- cardiomyocyte, fibroblast, endothelial, macrophage, pericyte and immune cell types
- mature, immature, hypertrophic, inflammatory, proliferative and stressed states
- myocardial infarction, fibrosis, ischemia-reperfusion, inflammation, regeneration, arrhythmia and heart failure phenotypes
- maturation, remodeling, electrophysiology, angiogenesis and extracellular-matrix remodeling processes

Resolution is conservative: known synonyms map to a canonical concept; unknown concepts remain unknown rather than being silently guessed.

### 3. Evidence and contradiction handling

Evidence is not treated as a single truth value. Evidence records carry an explicit polarity:

```text
supports / refutes / mixed / unknown
```

Claims can therefore be assessed as:

```text
supported / refuted / conflicted / mixed / undetermined
```

The system preserves both supporting and refuting evidence instead of averaging disagreement away.

### 4. Relationship graph

`AtlasGraph` supports typed edges such as:

```text
marker       -> marks            -> cell type
marker       -> associated_with  -> phenotype
cell state   -> observed_in      -> dataset
dataset      -> supported_by     -> evidence
phenotype    -> supported_by     -> evidence
```

Edges can carry evidence IDs, confidence, and source metadata. Duplicate edges merge provenance rather than creating silent duplicates.

### 5. Dataset quality and CardiBench integration

The repository now exposes a **CardiBench integration contract** rather than making CardiBench a hard dependency.

A dataset can be converted into a portable benchmark candidate containing:

- accession
- study title
- organism
- tissue
- modalities
- conditions
- sample count
- cell/nucleus context
- provenance

A conservative readiness gate checks whether the metadata required for benchmark promotion are actually present. Missing provenance, conditions, modality, organism, tissue, or accession block readiness rather than being inferred.

The Atlas repository also carries a small cross-project accession catalog for the cardiac datasets already registered by CardiBench. The entries are intentionally metadata-only; they do not duplicate source datasets.

### 6. Persistent backend

`SQLiteAtlasStore` now persists:

- typed records
- graph relations
- release manifests
- indexed record types and graph endpoints

The storage layer remains an implementation detail. The public record and relation contracts do not depend on SQLite.

### 7. Deterministic release snapshots

Release manifests contain:

- Atlas version
- schema version
- creation timestamp
- record count
- record-type counts
- canonical SHA-256 digest

Canonical serialization makes equivalent record collections hash identically regardless of insertion order.

### 8. Provenance

`ProvenanceEvent` and `ProvenanceBundle` provide an audit trail for ingestion, transformation, curation, and publication events without forcing a particular storage engine.

### 9. Unified query/service API

`AtlasService` combines:

- registry operations
- graph operations
- deterministic search
- structured queries
- concept resolution
- dataset readiness assessment
- evidence explanation
- claim assessment
- release manifests
- portable `AtlasContext` creation

The `AtlasContext` contract is versioned independently so CardiAgent, CardiVex, and CardiEval can exchange biological context without importing each other's internals.

### 10. NCBI ingestion primitives

A dependency-free NCBI E-utilities client supports explicit retrieval of public metadata for:

- PubMed searches and summaries
- PubMed XML
- GEO/GDS searches

Adapters convert these results into CardiAtlas-native records.

Network access is explicit; tests and package imports do not silently contact external services.

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
cardiatlas ontology --category phenotype
```

The ingestion commands emit normalized JSON suitable for further persistence or processing.

## Repository layout

```text
cardiatlas/
  models.py          # typed domain records
  ontology.py        # cardiac concept resolution
  normalize.py       # identifiers and labels
  validation.py      # schema and integrity checks
  registry.py        # in-memory registry
  sqlite.py          # persistent SQLite backend
  graph.py           # typed relationship graph
  evidence.py        # evidence scoring
  claims.py          # contradiction-aware claims
  provenance.py      # lineage/audit events
  query.py           # structured local retrieval
  service.py         # unified orchestration layer
  integrations.py    # CardiBench integration contract
  qc.py              # dataset quality/readiness gates
  release.py         # deterministic snapshot manifests
  export.py          # portable release/benchmark exports
  contracts.py       # cross-repository context contract
  ingest.py          # JSONL ingestion pipeline
  ncbi.py            # public NCBI client
  adapters.py        # source -> Atlas adapters
  io.py              # JSONL interchange
  cli.py             # command-line interface

schemas/
  *.schema.json      # machine-readable interchange contracts

data/
  examples/          # transparent small examples
  reference/         # cross-project cardiac metadata/reference seeds

tests/
  *                  # unit/integration-style tests

.github/workflows/
  test.yml            # multi-version CI
```

## Interoperability

CardiAtlas is deliberately **backend-agnostic and downstream-friendly**.

### CardiBench

CardiAtlas provides biological context and dataset metadata; CardiBench remains authoritative for locked benchmark definitions, leakage-aware splits, and benchmark release policy.

### CardiAgent

Agent generation can retrieve normalized phenotypes, cell states, markers, datasets, and supporting evidence to keep generated scenarios tied to explicit biological context.

### CardiVex

Vex can use Atlas graph neighborhoods and evidence explanations to convert observed phenotype signatures into interpretable candidate states without hard-coding every biological relationship into the detector.

### CardiEval

Eval can attach model results to an Atlas context, identify which evidence or dataset definitions supported the interpretation, and distinguish supported conclusions from conflicted biological claims.

### CardiLearn

Learn can use Atlas-linked datasets and normalized metadata to build reproducible training corpora while keeping source provenance separate from model artifacts.

## Data principles

1. **Evidence first.** Biological assertions should remain traceable to their source.
2. **No silent inference.** Unknown metadata are not converted into confident facts.
3. **Conflict is data.** Contradictory evidence remains queryable.
4. **Provenance survives transformation.** Normalization and export should not erase source lineage.
5. **Reproducibility over convenience.** Release manifests are hashable and deterministic.
6. **Metadata before raw data.** Public accession metadata can be indexed without redistributing source datasets.

## Current status

**Phase 3 — platform foundation.** CardiAtlas now has a typed knowledge model, cardiac ontology, evidence/claim layer, graph, deterministic retrieval, persistent storage, reproducible releases, dataset quality gates, CardiBench integration contracts, portable inter-repository context contracts, NCBI ingestion, CLI support, reference data, and expanded automated tests.

The major work remaining is **large-scale evidence acquisition and normalization**: systematic literature/dataset ingestion, stronger ontology mappings, sample-level dataset harmonization, and a production API/retrieval layer. Those are data-scale and verification problems rather than missing core architecture.

## Scientific scope

CardiAtlas is a biomedical information and evidence system. It stores and normalizes published/public observations and does not provide operational instructions for harmful biological activity.

## License

MIT
