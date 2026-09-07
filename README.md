# Virelion-CardiAtlas

CardiAtlas is a Python library for representing and retrieving cardiac biomedical metadata, evidence, phenotypes, datasets, studies, samples, and provenance.

## What it contains

- Typed records for studies, datasets, samples, markers, phenotypes, interventions, evidence, and claims.
- Controlled cardiac terminology and identifier/label normalization.
- Evidence-linked relationships and contradiction-aware claims.
- Study/sample metadata ingestion and quality checks.
- SQLite persistence and JSONL interchange.
- Deterministic release manifests, hashes, and snapshot diffs.
- PubMed and GEO metadata retrieval.
- CLI and Python APIs.

CardiAtlas stores metadata and derived records. It does not redistribute third-party source datasets unless their licenses permit it.

## Installation

```bash
pip install -e '.[test]'
```

## Usage

CLI examples:

```bash
cardiatlas pubmed "myocardial infarction single cell" --limit 10
cardiatlas geo "heart myocardial infarction single cell" --limit 10
cardiatlas resolve "MI"
cardiatlas identifier GSE217494
cardiatlas ontology --category phenotype
cardiatlas release-check
```

Python:

```python
from cardiatlas import AtlasService

service = AtlasService()
print(service.resolve("MI"))
```

Network access is explicit; importing the package and running tests do not silently contact external services.

## Inputs and outputs

**Inputs:** study/dataset/sample metadata, identifiers, phenotype and ontology terms, evidence records, JSONL records, and optional PubMed/GEO queries.

**Outputs:** typed metadata/evidence records, normalized identifiers and labels, SQLite/JSONL records, release manifests, hashes, snapshot diffs, and query results.

Unknown metadata remain unknown; normalization retains confidence and provenance rather than silently converting uncertain matches into facts.

## Validation

Automated checks cover schema integrity, identifiers, duplicate accessions, provenance, release state, and metadata completeness. Tests cover the public API and regression behavior. Passing validation does not establish biological correctness; ontology mappings and scientific interpretation require review.

## Limitations

Metadata quality is limited by the source records. Identifier and ontology normalization can remain ambiguous. Public-accession availability does not guarantee complete sample-level metadata or correct biological interpretation. CardiAtlas does not replace scientific review of study design or evidence.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See `LICENSE`.
