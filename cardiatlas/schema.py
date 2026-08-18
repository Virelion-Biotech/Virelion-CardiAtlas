SCHEMA_NAME = "virelion-cardi-atlas"
SCHEMA_VERSION = "0.3"
CONTRACT_VERSION = "1.0"

RECORD_TYPES = (
    "evidence",
    "marker",
    "phenotype",
    "cell_state",
    "dataset",
    "study",
    "sample",
    "intervention",
)

ID_NAMESPACES = {
    "evidence": "evidence",
    "marker": "marker",
    "phenotype": "phenotype",
    "cell_state": "cell-state",
    "dataset": "dataset",
    "study": "study",
    "sample": "sample",
    "intervention": "intervention",
}

RELATION_TYPES = (
    "supports",
    "refutes",
    "mixed_evidence_for",
    "expressed_in",
    "marks",
    "associated_with",
    "observed_in",
    "involves",
    "derived_from",
    "part_of",
    "has_sample",
    "has_dataset",
    "uses_modality",
    "occurs_in",
    "precedes",
    "responds_to",
    "measures",
)
