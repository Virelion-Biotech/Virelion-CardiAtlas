# CardiAtlas release checklist

A CardiAtlas release should be reproducible and auditable before it is consumed by another Virelion component.

## Required checks

1. All records validate against the current schema version.
2. IDs are unique and stable.
3. Dataset accessions are not duplicated unintentionally.
4. Every provenance/source reference resolves to an indexed evidence record when a release claims a closed evidence graph.
5. Sample metadata contain enough biological grouping information for the intended benchmark or analysis use.
6. Controlled relationship predicates are used.
7. The release digest is generated from the canonical record payload.
8. The exact release version, schema version, and source inventory are recorded.
9. CI passes on the release commit.

## Release states

- **draft** — internally generated; may contain unresolved provenance or incomplete metadata.
- **candidate** — passes structural checks and is suitable for review.
- **verified** — CI and source/provenance checks pass on the exact release commit.
- **deprecated** — superseded by a newer release but retained for reproducibility.

## What is deliberately not automated

Automatic agreement with the literature is not treated as a release criterion. Biological interpretation, contradictory evidence, sample semantics, and benchmark eligibility may require explicit scientific review.
