# GEO reconstruction and benchmark handoff

CardiAtlas treats a GEO Series accession as an auditable metadata reconstruction rather than a free-form scrape.

## Live path

```text
GSE accession
  -> NCBI GDS summary
  -> GEO family SOFT
  -> sample blocks
  -> normalized sample rows
  -> StudyRecord + SampleRecord[]
  -> study QC
  -> benchmark readiness
  -> portable bundle
```

The live CLI is:

```bash
cardiatlas reconstruct-geo GSE217494 --output ./GSE217494
```

The output directory contains:

- `dataset.json` — normalized GEO DatasetRecord
- `study.json` — reconstructed StudyRecord
- `samples.jsonl` — one normalized SampleRecord per GSM
- `report.json` — reconstruction decisions, warnings, source digest, and benchmark gate
- `acquisition.json` — source URL, UTC retrieval time, payload size, SHA-256, parser version, and benchmark gate summary

## Provenance contract

Every live reconstruction records:

- canonical NCBI GEO family-SOFT URL;
- UTC retrieval timestamp;
- uncompressed payload byte count;
- SHA-256 digest of the exact SOFT payload used for reconstruction;
- parser version;
- field-level reconstruction decisions containing raw value, normalized value, confidence, and source metadata field.

The raw SOFT payload is not committed by default. The digest is retained so an independently archived payload can be compared byte-for-byte with the source used to create the bundle.

## Benchmark gate

A reconstructed study is benchmark-ready only when all of the following are satisfied:

- dataset accession is present;
- organism is known;
- tissue context exists;
- at least one sample exists;
- at least two normalized conditions are represented;
- at least one recognized assay modality is represented;
- biological subject structure is present;
- sample accessions are unique;
- provenance is retained.

Warnings remain separate from blockers. In particular, missing subject IDs can limit leakage control and missing timepoints can limit downstream stratification without being silently repaired.

## Design rule

GEO annotations are observations about how a submitter described a sample. CardiAtlas records normalization decisions explicitly and does not convert ambiguous metadata into high-confidence biological facts.

## Downstream use

CardiBench can consume the bundle's normalized study/sample objects and readiness gate instead of implementing a second GEO reconstruction path. CardiLearn and CardiVex can consume the same objects while retaining sample-level provenance and subject/group structure.
