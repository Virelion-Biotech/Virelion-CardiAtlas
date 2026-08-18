"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .evidence import EvidenceScore, score_evidence
from .graph import AtlasGraph, Relation
from .models import (
    AtlasRecord,
    CellStateRecord,
    DatasetRecord,
    EvidenceRecord,
    MarkerRecord,
    PhenotypeRecord,
)
from .normalize import canonical_key, normalize_accession, normalize_gene_symbol, normalize_label, normalize_species
from .registry import AtlasRegistry
from .service import AtlasService

__all__ = [
    "AtlasRecord",
    "AtlasGraph",
    "AtlasRegistry",
    "AtlasService",
    "CellStateRecord",
    "DatasetRecord",
    "EvidenceRecord",
    "EvidenceScore",
    "MarkerRecord",
    "PhenotypeRecord",
    "Relation",
    "canonical_key",
    "normalize_accession",
    "normalize_gene_symbol",
    "normalize_label",
    "normalize_species",
    "score_evidence",
]

__version__ = "0.2.0"
