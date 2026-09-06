# Virelion-CardiAtlas

CardiAtlas is a Python library and data layer for representing and retrieving cardiac biomedical metadata, evidence, phenotypes, datasets, studies, samples, and provenance.

## Scope

CardiAtlas provides:

- typed records for studies, datasets, samples, markers, phenotypes, interventions, evidence, and claims;
- controlled cardiac terminology and conservative identifier/label normalization;
- evidence-linked relationships and contradiction-aware claims;
- study/sample metadata ingestion and quality checks;
- SQLite persistence and JSONL interchange;
- deterministic release manifests, hashes, and snapshot diffs;
- NCBI PubMed/GEO metadata retrieval;
- service/API interfaces for downstream Virelion repositories;
- a CardiBench integration contract.

CardiAtlas stores metadata and derived records. It does not redistribute third-party source datasets unless their licensing permits it.

## Data model

```text
source
  ↓
study → dataset → sample
  ↓        ↓
 evidence  phenotype / marker / intervention
  ↓
claim → relationship graph
  ↓
provenance → release manifest
```

Study-level and sample-level metadata are kept separate so downstream analyses can distinguish biological subjects, technical replicates, conditions, regions, modalities, and timepoints.

Unknown metadata remain unknown. Normalization functions expose confidence and provenance rather than silently converting uncertain matches into facts.

## Installation

```bash
pip install -e '.[test]'
```

## CLI

```bash
cardiatlas pubmed "myocardial infarction single cell" --limit 10
cardiatlas geo "heart myocardial infarction single cell" --limit 10
cardiatlas resolve "MI"
cardiatlas identifier GSE217494
cardiatlas ontology --category phenotype
cardiatlas release-check
```

Network access is explicit; importing the package and running tests does not silently contact external services.

## Python API

```python
from cardiatlas import AtlasService

service = AtlasService()
print(service.resolve("MI"))
```

See `docs/` and the examples directory for the current API surface.

## Repository layout

```text
cardiatlas/        package source
schemas/           machine-readable contracts
data/examples/    example records
data/reference/   reference metadata
docs/              architecture and integration documentation
tests/             regression and integration tests
```

## Integrations

- **CardiBench:** benchmark context and normalized dataset/study metadata.
- **CardiLearn:** training-corpus metadata and biological grouping/provenance.
- **CardiEval:** evaluation context and evidence links.
- **CardiAgent/CardiVex:** phenotype, evidence, dataset, and graph context.
- **CardiBridge:** cross-repository contract exchange.
- **HeartTwin:** upstream context and metadata service.

CardiAtlas does not own benchmark split policy or model evaluation; those remain in the respective repositories.

## Validation and scientific limitations

Automated validation checks schema integrity, IDs, duplicate accessions, provenance, release state, and metadata completeness. Passing these checks does not establish biological correctness. Ontology mappings, study interpretation, and scientific conclusions require review.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See `LICENSE`.

## Citation

If you use CardiAtlas in research, cite the repository release and the original datasets/publications from which records were derived.
