"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .api import AtlasAPI
from .claims import Claim, ClaimAssessment, ClaimStore
from .contracts import AtlasContext, context_from_dict
from .diff import SnapshotDiff, diff_records
from .evidence import EvidenceScore, score_evidence
from .export import write_cardiBench_candidates, write_records, write_release
from .graph import AtlasGraph, Relation
from .harmonize import HarmonizedValue, harmonize_condition, harmonize_label, harmonize_modality
from .identifiers import IdentifierResolution, resolve as resolve_identifier
from .integrations import BenchmarkCandidate, benchmark_readiness, dataset_to_benchmark_candidate
from .models import (
    AtlasRecord,
    CellStateRecord,
    DatasetRecord,
    EvidenceRecord,
    InterventionRecord,
    MarkerRecord,
    PhenotypeRecord,
    SampleRecord,
    StudyRecord,
)
from .normalize import canonical_key, normalize_accession, normalize_gene_symbol, normalize_label, normalize_species
from .ontology import Concept, canonical_concept_id, concepts_by_category, resolve_concept
from .provenance import ProvenanceBundle, ProvenanceEvent
from .qc import QualityReport, assess_dataset, audit_datasets
from .query import Query, QueryHit, graph_context, query_registry
from .registry import AtlasRegistry
from .release import ReleaseManifest, create_manifest, digest_records, verify_digest
from .release_checks import ReleaseCheck, ReleaseReadiness, assess_release
from .service import AtlasService
from .sqlite import SQLiteAtlasStore
from .studies import StudyQC, assess_study, study_from_datasets

__all__ = [
    "AtlasAPI",
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
    "HarmonizedValue",
    "IdentifierResolution",
    "InterventionRecord",
    "MarkerRecord",
    "PhenotypeRecord",
    "ProvenanceBundle",
    "ProvenanceEvent",
    "Query",
    "QueryHit",
    "QualityReport",
    "Relation",
    "ReleaseCheck",
    "ReleaseManifest",
    "ReleaseReadiness",
    "SampleRecord",
    "SnapshotDiff",
    "SQLiteAtlasStore",
    "StudyQC",
    "StudyRecord",
    "SnapshotDiff",
    "assess_dataset",
    "assess_release",
    "assess_study",
    "audit_datasets",
    "benchmark_readiness",
    "canonical_concept_id",
    "canonical_key",
    "concepts_by_category",
    "context_from_dict",
    "create_manifest",
    "dataset_to_benchmark_candidate",
    "diff_records",
    "digest_records",
    "harmonize_condition",
    "harmonize_label",
    "harmonize_modality",
    "normalize_accession",
    "normalize_gene_symbol",
    "normalize_label",
    "normalize_species",
    "query_registry",
    "resolve_concept",
    "resolve_identifier",
    "score_evidence",
    "study_from_datasets",
    "verify_digest",
    "write_cardiBench_candidates",
    "write_records",
    "write_release",
]

__version__ = "0.4.0"
