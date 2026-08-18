"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .claims import Claim, ClaimAssessment, ClaimStore
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
from .snapshot import SnapshotManifest, create_snapshot
from .sqlite import SQLiteAtlasStore

__all__ = [
    "AtlasGraph",
    "AtlasRecord",
    "AtlasRegistry",
    "AtlasService",
    "CellStateRecord",
    "Claim",
    "ClaimAssessment",
    "ClaimStore",
    "DatasetRecord",
    "EvidenceRecord",
    "EvidenceScore",
    "MarkerRecord",
    "PhenotypeRecord",
    "Relation",
    "SnapshotManifest",
    "SQLiteAtlasStore",
    "canonical_key",
    "create_snapshot",
    "normalize_accession",
    "normalize_gene_symbol",
    "normalize_label",
    "normalize_species",
    "score_evidence",
]

__version__ = "0.2.0"
