# Virelion CardiAtlas

A structured knowledge layer for cardiac literature, public omics datasets, phenotypes, biomarkers, cell states, interventions, and evidence provenance.

## Purpose

CardiAtlas is the evidence and knowledge layer of the Virelion cardiac-AI ecosystem. It makes heterogeneous cardiac biomedical knowledge computable, traceable, and reusable by CardiAgent, CardiVex, CardiEval, CardiLearn, and future components.

## Core design principles

- **Evidence first:** every biological assertion carries provenance and evidence metadata.
- **Machine-readable:** concepts use stable identifiers and normalized schemas.
- **Multi-modal:** support literature, transcriptomics, single-cell/single-nucleus data, imaging, ECG, physiology, and clinical phenotypes.
- **Human-auditable:** records retain source, organism, tissue, cell type, condition, assay, directionality, and confidence.
- **Versioned:** atlas releases are immutable snapshots with explicit schema and source versions.
- **Interoperable:** outputs connect with CardiBench, CardiAgent, CardiVex, CardiEval, and CardiLearn.

## Initial knowledge domains

1. Cardiac cell types and states
2. Disease and injury phenotypes
3. Molecular markers and pathways
4. Cardiac developmental and maturation states
5. Myocardial infarction and remodeling
6. Fibrosis, inflammation, vascular injury, and regeneration
7. Public cardiac omics datasets and study metadata
8. Interventions and observed responses
9. Evidence and provenance

## Repository layout

```text
cardiatlas/
  models.py        # Typed domain models
  schema.py        # Schema/version metadata
  validation.py    # Record validation and normalization
  registry.py      # In-memory knowledge registry
  io.py            # JSONL import/export
  search.py        # Deterministic local search

schemas/
  evidence_record.schema.json
  dataset_record.schema.json
  phenotype_record.schema.json
  marker_record.schema.json
  cell_state_record.schema.json

data/examples/
  markers.jsonl
  phenotypes.jsonl
  datasets.jsonl
  evidence.jsonl

tests/
  test_models.py
  test_registry.py
  test_io.py
```

## Status

**Phase 1 — foundation.** The repository starts with typed records, validation, deterministic local indexing/search, example records, and JSONL interchange. External ingestion connectors and a persistent backend are separate next phases.

## Scientific scope

CardiAtlas is a biomedical information and evidence system. It stores and normalizes published/public observations and is not a source of operational instructions for harmful biological activity.

## License

MIT
