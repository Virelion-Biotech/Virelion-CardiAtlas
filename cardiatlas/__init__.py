"""Virelion CardiAtlas: structured cardiac biomedical knowledge."""

from .acquisition import AcquisitionTarget, acquisition_plan, plan_as_dict
from .api import AtlasAPI
from .build import ReferenceBuild, build_reference, populate_registry
from .catalog import CatalogGroup, attach_datasets, group_datasets
from .claims import Claim, ClaimAssessment, ClaimStore
from .contracts import AtlasContext, context_from_dict
from .corpus import CorpusReport, corpus_report
from .diff import SnapshotDiff, diff_records
from .evidence import EvidenceScore, score_evidence
from .export import write_cardiBench_candidates, write_records, write_release
from .graph import AtlasGraph, Relation
from .harmonize import HarmonizedValue, harmonize_condition, harmonize_label, harmonize_modality
from .harvest import HarvestItem, canonical_digest, deduplicate_harvest, harvest_report
from .harvester import HarvestBatch, harvest_plan, harvest_target
from .identifiers import IdentifierResolution, resolve as resolve_identifier
from .integrations import BenchmarkCandidate, benchmark_readiness, dataset_to_benchmark_candidate
from .loader import load_into_registry, read_bundle, record_from_dict
from .migrate import migrate_payload, migrate_records
from .models import AtlasRecord, CellStateRecord, DatasetRecord, EvidenceRecord, InterventionRecord, MarkerRecord, PhenotypeRecord, SampleRecord, StudyRecord
from .normalize import canonical_key, normalize_accession, normalize_gene_symbol, normalize_label, normalize_species
from .ontology import Concept, canonical_concept_id, concepts_by_category, descendants, resolve_concept
from .provenance import ProvenanceBundle, ProvenanceEvent
from .qc import QualityReport, assess_dataset, audit_datasets
from .query import Query, QueryHit, graph_context, query_registry
from .registry import AtlasRegistry
from .release import ReleaseManifest, create_manifest, digest_records, verify_digest
from .release_checks import ReleaseCheck, ReleaseReadiness, assess_release
from .retrieval import RetrievalResult, neighborhood_retrieve, retrieve
from .sample_ingest import ingest_sample_rows, sample_from_metadata
from .service import AtlasService
from .sources import SourceResult, ingest_source
from .sqlite import SQLiteAtlasStore
from .studies import StudyQC, assess_study, study_from_datasets

__all__ = [
    "AcquisitionTarget", "AtlasAPI", "AtlasContext", "AtlasGraph", "AtlasRecord", "AtlasRegistry", "AtlasService",
    "BenchmarkCandidate", "CatalogGroup", "CellStateRecord", "Claim", "ClaimAssessment", "ClaimStore", "Concept",
    "CorpusReport", "DatasetRecord", "EvidenceRecord", "EvidenceScore", "HarvestBatch", "HarvestItem", "HarmonizedValue", "IdentifierResolution",
    "InterventionRecord", "MarkerRecord", "PhenotypeRecord", "ProvenanceBundle", "ProvenanceEvent", "Query", "QueryHit",
    "QualityReport", "ReferenceBuild", "Relation", "ReleaseCheck", "ReleaseManifest", "ReleaseReadiness", "RetrievalResult",
    "SampleRecord", "SnapshotDiff", "SourceResult", "SQLiteAtlasStore", "StudyQC", "StudyRecord", "acquisition_plan",
    "assess_dataset", "assess_release", "assess_study", "attach_datasets", "audit_datasets", "benchmark_readiness", "build_reference",
    "canonical_concept_id", "canonical_digest", "canonical_key", "concepts_by_category", "context_from_dict", "corpus_report", "create_manifest",
    "dataset_to_benchmark_candidate", "deduplicate_harvest", "descendants", "diff_records", "digest_records", "graph_context", "group_datasets",
    "harvest_plan", "harvest_report", "harvest_target", "harmonize_condition", "harmonize_label", "harmonize_modality", "ingest_sample_rows",
    "ingest_source", "load_into_registry", "migrate_payload", "migrate_records", "neighborhood_retrieve", "normalize_accession", "normalize_gene_symbol",
    "normalize_label", "normalize_species", "plan_as_dict", "populate_registry", "query_registry", "read_bundle", "record_from_dict",
    "resolve_concept", "resolve_identifier", "retrieve", "sample_from_metadata", "score_evidence", "study_from_datasets", "verify_digest",
    "write_cardiBench_candidates", "write_records", "write_release",
]

__version__ = "0.5.0"
