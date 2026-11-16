from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TYPE_CHECKING, Union

EvidenceLevel = Literal["primary", "review", "database", "inferred", "curated"]
EvidencePolarity = Literal["supports", "refutes", "mixed", "unknown"]
Modality = Literal["bulk_rna", "scrna", "snrna", "proteomics", "imaging", "ecg", "physiology", "clinical", "literature", "other"]
Repository = Literal["GEO", "SRA", "ArrayExpress", "dbGaP", "other"]

@dataclass(slots=True)
class AtlasRecord:
    id: str
    record_type: str = field(init=False)
    name: str
    description: str = ""
    source_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.3"
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(slots=True)
class EvidenceRecord(AtlasRecord):
    record_type: str = field(default="evidence", init=False)
    source_type: Literal["pubmed", "doi", "geo", "sra", "arrayexpress", "clinical", "other"] = "other"
    source_identifier: str = ""
    citation: str = ""
    evidence_level: EvidenceLevel = "curated"
    polarity: EvidencePolarity = "unknown"
    organism: str | None = None
    tissue: str | None = None
    assay: str | None = None
    year: int | None = None
    source_url: str | None = None
    extracted_claim: str = ""
    context: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class MarkerRecord(AtlasRecord):
    record_type: str = field(default="marker", init=False)
    entity_id: str = ""
    entity_type: Literal["gene", "protein", "metabolite", "feature"] = "gene"
    role: str = ""
    cell_types: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    direction: Literal["up", "down", "context_dependent", "unknown"] = "unknown"
    modalities: list[Modality] = field(default_factory=list)
    species: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float | None = None

@dataclass(slots=True)
class PhenotypeRecord(AtlasRecord):
    record_type: str = field(default="phenotype", init=False)
    category: str = ""
    synonyms: list[str] = field(default_factory=list)
    manifestations: list[str] = field(default_factory=list)
    measurable_features: list[str] = field(default_factory=list)
    associated_states: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

@dataclass(slots=True)
class CellStateRecord(AtlasRecord):
    record_type: str = field(default="cell_state", init=False)
    cell_type: str = ""
    state: str = ""
    parent_states: list[str] = field(default_factory=list)
    marker_ids: list[str] = field(default_factory=list)
    pathways: list[str] = field(default_factory=list)
    phenotypes: list[str] = field(default_factory=list)
    species: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

@dataclass(slots=True)
class DatasetRecord(AtlasRecord):
    record_type: str = field(default="dataset", init=False)
    accession: str = ""
    repository: Repository = "other"
    study_title: str = ""
    organism: str = ""
    tissue: str = ""
    modalities: list[Modality] = field(default_factory=list)
    cell_or_nucleus: Literal["cell", "nucleus", "bulk", "mixed", "unknown"] = "unknown"
    conditions: list[str] = field(default_factory=list)
    sample_count: int | None = None
    cell_count: int | None = None
    release_date: str | None = None
    source_url: str | None = None
    evidence_ids: list[str] = field(default_factory=list)
    study_id: str | None = None
    region: str | None = None
    timepoints: list[str] = field(default_factory=list)
    quality_flags: list[str] = field(default_factory=list)

@dataclass(slots=True)
class StudyRecord(AtlasRecord):
    record_type: str = field(default="study", init=False)
    accession: str = ""
    repository: Repository = "other"
    title: str = ""
    organism: str = ""
    tissues: list[str] = field(default_factory=list)
    modalities: list[Modality] = field(default_factory=list)
    dataset_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    design: str = ""
    publication_ids: list[str] = field(default_factory=list)

@dataclass(slots=True)
class SampleRecord(AtlasRecord):
    record_type: str = field(default="sample", init=False)
    accession: str = ""
    dataset_id: str = ""
    study_id: str | None = None
    subject_id: str | None = None
    replicate_group: str | None = None
    species: str = ""
    tissue: str = ""
    region: str | None = None
    cell_context: str | None = None
    condition: str = ""
    timepoint: str | None = None
    modality: Modality = "other"
    is_technical_replicate: bool = False
    metadata_quality: str = "unknown"

@dataclass(slots=True)
class InterventionRecord(AtlasRecord):
    record_type: str = field(default="intervention", init=False)
    intervention_type: str = ""
    target: str = ""
    context: str = ""
    observed_outcomes: list[str] = field(default_factory=list)
    phenotype_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

@dataclass(slots=True)
class TherapeuticEvidenceRecord(AtlasRecord):
    """Study-level evidence about a cardiac therapeutic intervention.

    This record classifies the intended biological effect separately from the
    intervention's delivery modality. It stores observations and provenance;
    it does not assert efficacy or clinical readiness.
    """
    record_type: str = field(default="therapeutic_evidence", init=False)
    evidence_class: Literal[
        "myocardial_regeneration", "myocardial_repair", "myocardial_preservation",
        "genetic_disease_modification", "vascular_tissue_engineering",
        "immune_modulation", "other"
    ] = "other"
    modality: Literal[
        "circRNA", "modRNA", "siRNA", "ASO", "AAV", "gene_editing",
        "cell_therapy", "engineered_tissue", "hydrogel", "small_molecule",
        "biologic", "immune_intervention", "other"
    ] = "other"
    product_id: str | None = None
    target_or_genotype: str | None = None
    payload_or_construct: str | None = None
    delivery_method: str | None = None
    proposed_mechanism: str = ""
    model_system: str = ""
    species: str | None = None
    dose: str | None = None
    schedule: str | None = None
    comparator: str | None = None
    endpoints: list[dict[str, Any]] = field(default_factory=list)
    analysis_population: str | None = None
    denominator: str | None = None
    follow_up: str | None = None
    subgroup_analysis: str | None = None
    multiplicity_handling: str | None = None
    safety_findings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    source_locator: dict[str, Any] = field(default_factory=dict)
    curation_status: Literal["unreviewed", "source_checked", "expert_reviewed"] = "unreviewed"

    def __post_init__(self) -> None:
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("therapeutic evidence_ids must be unique")
        if any(not isinstance(item, dict) for item in self.endpoints):
            raise ValueError("endpoints must be structured objects")
        forbidden_phrases = ("proof of regeneration", "demonstrates regeneration", "regeneration demonstrated", "proves regeneration", "regenerative efficacy")
        for endpoint in self.endpoints:
            label = str(endpoint.get("endpoint", "")).strip().lower()
            interpretation = str(endpoint.get("interpretation", "")).strip().lower()
            negative_context = any(phrase in interpretation for phrase in ("not proof", "does not prove", "not evidence", "insufficient to establish", "cannot establish"))
            positive_claim = any(phrase in interpretation for phrase in forbidden_phrases)
            if label in {"lvef", "ejection fraction", "ki67", "scar size", "fibrosis"} and positive_claim and not negative_context:
                raise ValueError("surrogate endpoint cannot alone be labelled as proof of regeneration")

if TYPE_CHECKING:
    from .therapeutic_products import TherapeuticProductRecord

Record = Union[EvidenceRecord, MarkerRecord, PhenotypeRecord, CellStateRecord, DatasetRecord, StudyRecord, SampleRecord, InterventionRecord, TherapeuticEvidenceRecord, "TherapeuticProductRecord"]
