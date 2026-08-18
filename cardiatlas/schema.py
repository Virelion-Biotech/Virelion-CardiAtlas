SCHEMA_NAME = "virelion-cardi-atlas"
SCHEMA_VERSION = "0.1"

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
