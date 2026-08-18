SCHEMA_NAME = "virelion-cardi-atlas"
SCHEMA_VERSION = "0.2"

RECORD_TYPES = (
    "evidence",
    "marker",
    "phenotype",
    "cell_state",
    "dataset",
)

# Reserved namespaces for stable IDs. IDs are intentionally separate from
# external accessions so records remain stable when upstream sources change.
ID_NAMESPACES = {
    "evidence": "evidence",
    "marker": "marker",
    "phenotype": "phenotype",
    "cell_state": "cell-state",
    "dataset": "dataset",
}

CONTRACTS = {
    "atlas_context": "1.0",
    "release_manifest": "1.0",
    "benchmark_candidate": "1.0",
}
