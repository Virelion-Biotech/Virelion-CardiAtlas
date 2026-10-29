# Claim curation and the GSE132880 reference dataset

## Claim record contract

Claims are versioned independently from bibliographic and dataset records. A claim has a stable identifier, subject/predicate/object proposition, polarity, evidence IDs, schema version, revision, optional superseded identifier, and one or more ClaimEvidence citations. Each citation records the stable evidence record ID, source URL/locator, locator type/label, a short supporting quotation, review status, optional reviewer identity/time, and curator notes.

source_verified means the cited source location and the description attributed to it were checked against the source record. It does not mean the underlying scientific interpretation has been independently peer reviewed. expert_reviewed requires a reviewer identity. Unreviewed citations, source-less claims, and unresolved evidence IDs are surfaced by release checks; candidate/verified releases reject claims that lack reviewed source locations. Superseded revisions remain in SQLite history.

## Loading the reference bundle

From the repository root:

```bash
python -m pip install -e '.[test]'
cardiatlas load atlas.sqlite data/reference/cardiatlas_gse132880.jsonl --relations data/reference/cardiatlas_gse132880_relationships.jsonl
cardiatlas claims-load atlas.sqlite data/reference/cardiatlas_gse132880_claims.jsonl
python scripts/evaluate_retrieval.py
```

The sample records and graph edges link to the public NCBI GEO Series and sample pages. The benchmark bundle contains eight sample records from GSE132880, a source-level design claim, and graph relationships carrying the GEO evidence ID. It is appropriate for validating metadata reconstruction, provenance and retrieval plumbing; it is not a clinical benchmark or a gold standard for biological discovery.

## Important limits

The source design identifies four healthy and four seven-day post-MI adult mouse hearts and describes single-cell RNA-seq of FACS-sorted cardiac endothelial cell populations. Source-title numeric labels are preserved as source-derived subject labels, with mapping basis recorded in metadata. Before using these labels for a formal held-out-subject model benchmark, a domain reviewer should verify that these title suffixes uniquely identify animals rather than libraries or sample aliases.

No human/clinical performance or therapeutic efficacy claim follows from this bundle. The raw expression matrix is not copied into CardiAtlas; the bundle stores public metadata and provenance only.

## HTTP read API

The standard-library server exposes POST /v1/atlas/search, /v1/atlas/retrieve, /v1/atlas/context, /v1/atlas/explain, /v1/atlas/claim, /v1/atlas/claims, /v1/atlas/dataset/readiness, and /v1/atlas/graph. These are read endpoints; curation writes should be performed through authenticated workflow tooling, not an unauthenticated public server.
