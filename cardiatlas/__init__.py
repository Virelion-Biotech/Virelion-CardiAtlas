"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .claims import Claim, ClaimAssessment, ClaimStore
from .contracts import AtlasContext, context_from_dict
from .evidence import EvidenceScore, score_evidence
from .export import write_cardiBench_candidates, write_records, write_release
from .graph import AtlasGraph, Relation
from .integrations import BenchmarkCandidate, benchmark_readiness, dataset_to_benchmark_candidate
from .models import (
    AtlasRecord,
    CellStateRecord,
    DatasetRecord,
    EvidenceRecord,
    MarkerRecord,
    PhenotypeRecord,
)
from .normalize import canonical_key, normalize_accession, normalize_gene_symbol, normalize_label, normalize_species
from .ontology import Concept, canonical_concept_id, concepts_by_category, resolve_concept
from .provenance import ProvenanceBundle, ProvenanceEvent
from .qc import QualityReport, assess_dataset, audit_datasets
from .query import Query, QueryHit, graph_context, query_registry
from .registry import AtlasRegistry
from .release import ReleaseManifest, create_manifest, digest_records, verify_digest
from .service import AtlasService
from .sqlite import SQLiteAtlasStore

__all__ = [
    "AtlasContext",
    "AtlasGraph",
    "AtlasRecord",
    "AtlasRegistry",
    "AtlasService",
    "BenchmarkCandidate",
    "CellStateRecord",
    "Claim",
    "ClaimAssessment",
    "ClaimStore",
    "Concept",
    "DatasetRecord",
    "EvidenceRecord",
    "EvidenceScore",
    "MarkerRecord",
    "PhenotypeRecord",
    "ProvenanceBundle",
    "ProvenanceEvent",
    "Query",
    "QueryHit",
    "QualityReport",
    "Relation",
    "ReleaseManifest",
    "SQLiteAtlasStore",
    "assess_dataset",
    "audit_datasets",
    "benchmark_readiness",
    "canonical_concept_id",
    "canonical_key",
    "concepts_by_category",
    "context_from_dict",
    "create_manifest",
    "dataset_to_benchmark_candidate",
    "digest_records",
    "graph_context",
    "normalize_accession",
    "normalize_gene_symbol",
    "normalize_label",
    "normalize_species",
    "query_registry",
    "resolve_concept",
    "score_evidence",
    "verify_digest",
    "write_cardiBench_candidates",
    "write_records",
    "write_release",
]

__version__ = "0.3.0"
