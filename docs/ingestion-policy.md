# Evidence ingestion policy

CardiAtlas treats ingestion as a reproducibility operation, not a scrape-and-store operation.

## Source hierarchy

Every external item should preserve:

- source type
- source identifier
- source URL when available
- retrieval timestamp or release date when available
- source-specific accession
- organism/tissue/assay context when known
- transformation history

## Normalization rules

1. Normalize labels only when the mapping is deterministic.
2. Normalize gene symbols conservatively and preserve the original token.
3. Normalize accessions to a canonical comparison form while retaining the source accession.
4. Do not guess condition, species, cell type, region, or replicate identity from ambiguous text.
5. When ambiguity remains, record the uncertainty in metadata and allow the record to fail a downstream readiness gate.

## Evidence rules

Published evidence may support, refute, or mix a claim. Multiple sources are not automatically independent; duplicated references and derivative databases must not be counted as independent biological replication.

Evidence scores are triage aids. They are not substitutes for statistical analysis, systematic-review methodology, or expert adjudication.

## Dataset promotion

A dataset accession is not automatically benchmark-ready.

Before a dataset can become a CardiBench candidate, CardiAtlas should have sufficient metadata for:

- accession
- organism
- tissue/context
- modality
- conditions
- provenance

Sample-level biological replicate information should be recovered separately before creating a locked benchmark split.

## Release discipline

A release should be produced from an explicit record set and accompanied by a deterministic manifest. Raw public datasets are not redistributed by this repository.
