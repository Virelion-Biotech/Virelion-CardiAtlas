# Virelion CardiAtlas

A structured knowledge layer for cardiac literature, public omics datasets, phenotypes, biomarkers, cell states, interventions, and evidence provenance.

## What CardiAtlas is

CardiAtlas is the evidence and biological-context layer of the Virelion cardiac-AI ecosystem. It turns heterogeneous cardiac knowledge into typed, traceable objects that downstream systems can query instead of repeatedly rediscovering the same biology.

The target model is:

```text
literature / GEO / SRA / ArrayExpress / phenotype data
                    |
                    v
        normalization + provenance
                    |
                    v
          CardiAtlas records
                    |
          +---------+---------+
          |                   |
          v                   v
    evidence graph        local search
          |                   |
          +---------+---------+
                    |
                    v
 CardiAgent / CardiVex / CardiEval / CardiLearn
```

## Current capabilities

### Typed biomedical records

CardiAtlas currently models:

- evidence and citations
- molecular markers
- cardiac phenotypes
- cell states
- public datasets

Records carry stable IDs, schema versions, source identifiers, organism/tissue context, modality information, tags, and provenance fields.

### Evidence scoring

`cardiatlas.evidence` provides a transparent, deterministic evidence score using evidence quality, record count, and source diversity. The score is intentionally an interpretability aid, not a replacement for statistical meta-analysis.

### Relationship graph

`AtlasGraph` stores typed relationships such as:

```text
marker -> expressed_in -> cell_state
marker -> associated_with -> phenotype
cell_state -> observed_in -> dataset
dataset -> supported_by -> evidence
phenotype -> supported_by -> evidence
```

Relationships retain optional evidence IDs, confidence, and source metadata. Duplicate edges merge evidence rather than silently creating parallel copies.

### Normalization

The normalization layer provides conservative utilities for labels, stable comparison keys, gene symbols, accessions, species names, and de-duplication. It does not perform silent species-specific alias rewriting; mappings that alter biological identity should carry explicit provenance.

### Public NCBI ingestion primitives

A dependency-free NCBI E-utilities client is included for:

- PubMed search and summaries
- PubMed XML retrieval
- GEO dataset search through NCBI GDS

Adapters convert returned metadata into native CardiAtlas records. Network ingestion remains opt-in and explicit; the repository does not silently download external data during import or tests.

### Unified service layer

`AtlasService` combines registry, graph, search, and evidence explanation into one downstream-facing interface. `explain(record_id)` returns the record, attached evidence, evidence metrics, graph neighbors, and one-hop relationships.

### CLI

After installation:

```bash
cardiatlas pubmed "myocardial infarction single cell" --limit 10
cardiatlas geo "heart myocardial infarction single cell" --limit 10
```

The commands emit normalized JSON suitable for subsequent persistence or ingestion into another Atlas instance.

## Repository layout

```text
cardiatlas/
  models.py        # Domain records
  schema.py        # Schema/version metadata
  validation.py    # Validation rules
  registry.py      # In-memory typed registry
  io.py            # JSONL import/export
  search.py        # Deterministic local search
  normalize.py     # Identifier/label normalization
  graph.py         # Typed relationship graph
  evidence.py      # Evidence scoring/provenance utilities
  ingest.py        # JSONL ingestion pipeline
  ncbi.py          # Dependency-free NCBI client
  adapters.py      # PubMed/GEO -> Atlas record adapters
  service.py       # Unified downstream service API
  cli.py           # Command-line interface

schemas/            # JSON schemas for interchange
data/examples/      # Small, transparent seed examples
tests/              # Unit and integration-style tests
.github/workflows/  # Continuous test workflow
```

## Interoperability contract

CardiAtlas should remain backend-agnostic. The core contract is stable typed records plus relationship edges and provenance. This makes it possible for a later persistent database, vector search service, graph database, or API gateway to sit underneath the same conceptual interface.

The intended ecosystem boundaries are:

- **CardiBench:** supplies curated benchmark datasets and evaluation splits.
- **CardiAgent:** uses Atlas context when constructing cardiac challenge scenarios.
- **CardiVex:** uses Atlas knowledge to map observations to interpretable biological states.
- **CardiEval:** can audit whether model claims agree with held-out evidence and known distributions.
- **CardiLearn:** can use Atlas-linked datasets and phenotype/marker metadata to build reproducible training corpora.

## Scientific scope

CardiAtlas is a biomedical information and evidence system. It stores and normalizes published/public observations and is not a source of operational instructions for harmful biological activity.

## Roadmap

1. Complete core schemas and validation across all record types.
2. Add robust literature ingestion with PMID/DOI normalization and deduplication.
3. Add GEO/SRA/ArrayExpress dataset registry and metadata harmonization.
4. Add ontology-backed normalization for genes, cell types, diseases, phenotypes, and modalities.
5. Add contradiction/conflict representation rather than forcing every source into one answer.
6. Add persistent storage and versioned Atlas snapshots.
7. Add retrieval APIs for CardiAgent, CardiVex, CardiEval, and CardiLearn.
8. Add reproducible release manifests with source timestamps and checksums.

## Status

**Phase 2 — usable foundation.** The repository now has typed records, validation, deterministic search, JSONL interchange, normalization, a relationship graph, evidence scoring, NCBI ingestion primitives, source adapters, a unified service interface, CLI commands, seed data, and expanded tests. Persistent storage, ontology services, full-scale ingestion, and production API deployment remain subsequent phases.

## License

MIT
