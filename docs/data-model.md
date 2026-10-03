# CardiAtlas data model

CardiAtlas separates **entities**, **evidence**, and **relationships**.

## Entity records

- `marker` — molecular or measurable features associated with cardiac biology.
- `cell_state` — normalized cell identity/state combinations and linked pathways/phenotypes.
- `phenotype` — observable cardiac states such as injury, remodeling, fibrosis, inflammation, regeneration, or electrical instability.
- `dataset` — public study-level dataset metadata.
- `study` — a logical study spanning one or more datasets.
- `sample` — sample-level metadata including biological subject, replicate grouping, region, condition, and timepoint.
- `intervention` — a published/publicly described intervention and its observed phenotype-level outcomes.
- `evidence` — provenance for publications, dataset records, and curated assertions.

## Why study and sample are separate

A GEO/SRA accession is not the same thing as an experimental unit. CardiAtlas therefore keeps study-level metadata separate from sample-level metadata so downstream systems can reason about:

- biological subjects/donors/animals;
- technical replicates;
- regions and cell contexts;
- temporal sampling;
- study-level versus sample-level leakage risk.

## Evidence is not truth

Evidence records carry a source, level, polarity, organism/tissue context, assay, and optional extracted claim. Multiple sources may support or refute the same claim. CardiAtlas does not collapse disagreement into a single unconditional fact.

## Stable IDs

Atlas IDs are intentionally independent of external accessions. External identifiers may change format, gain aliases, or become unavailable. The Atlas ID is the stable internal handle; upstream accessions remain attached as provenance.

## Relationship graph

Relationships are controlled predicates. Examples:

```text
marker -> marks -> cell_type
marker -> associated_with -> cell_state
phenotype -> involves -> process
dataset -> derived_from -> study
study -> has_dataset -> dataset
dataset -> has_sample -> sample
sample -> responds_to -> phenotype
intervention -> responds_to -> phenotype
record -> supports/refutes -> claim context
```

Every relationship can carry evidence IDs, confidence, and source information.
