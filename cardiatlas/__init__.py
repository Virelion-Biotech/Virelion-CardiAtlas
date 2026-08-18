"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .models import (
    AtlasRecord,
    CellStateRecord,
    DatasetRecord,
    EvidenceRecord,
    MarkerRecord,
    PhenotypeRecord,
)
from .registry import AtlasRegistry

__all__ = [
    "AtlasRecord",
    "CellStateRecord",
    "DatasetRecord",
    "EvidenceRecord",
    "MarkerRecord",
    "PhenotypeRecord",
    "AtlasRegistry",
]

__version__ = "0.1.0"
