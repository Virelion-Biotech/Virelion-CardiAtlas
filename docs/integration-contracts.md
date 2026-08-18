# Downstream integration contracts

CardiAtlas is the shared biological context layer. Downstream repositories should depend on its **serialized contracts**, not private implementation details.

## CardiBench

CardiAtlas provides dataset and sample metadata, provenance, ontology mappings, and benchmark-candidate exports. CardiBench remains authoritative for locked benchmark splits, leakage policies, and benchmark manifests.

## CardiAgent

CardiAgent can request Atlas context using canonical phenotype, cell-state, marker, study, dataset, and evidence IDs. Agent generation should preserve Atlas provenance IDs so generated scenarios remain traceable to the underlying biological context.

## CardiVex

CardiVex can use Atlas relationships to translate observed phenotype/state signals into interpretable biological hypotheses. Atlas evidence should be surfaced alongside a hypothesis instead of being hidden behind a single score.

## CardiEval

CardiEval can attach Atlas provenance to evaluation reports, compare model claims against independent evidence, and identify when a benchmark case relies on incomplete or conflicting biological evidence.

## CardiLearn

CardiLearn can construct training corpora from Atlas-linked datasets while keeping dataset identity, study identity, biological subject grouping, modality, and provenance explicit.

## Contract rule

A downstream repository may cache Atlas records, but should retain:

- Atlas record ID;
- schema version;
- Atlas contract version when using an `AtlasContext`;
- source/evidence IDs;
- Atlas release digest when reproducibility matters.
