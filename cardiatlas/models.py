from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EvidenceLevel = Literal["primary", "review", "database", "inferred", "curated"]
EvidencePolarity = Literal["supports", "refutes", "mixed", "unknown"]
Modality = Literal["bulk_rna", "scrna", "snrna", "proteomics", "imaging", "ecg", "physiology", "clinical", "literature", "other"]


@dataclass(slots=True)
class AtlasRecord:
    id: str
    record_type: str
    name: str
    description: str = ""
    source_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "0.2"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceRecord(AtlasRecord):
    record_type: str = "evidence"
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
    record_type: str = "marker"
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
    record_type: str = "phenotype"
    category: str = ""
    synonyms: list[str] = field(default_factory=list)
    manifestations: list[str] = field(default_factory=list)
    measurable_features: list[str] = field(default_factory=list)
    associated_states: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CellStateRecord(AtlasRecord):
    record_type: str = "cell_state"
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
    record_type: str = "dataset"
    accession: str = ""
    repository: Literal["GEO", "SRA", "ArrayExpress", "dbGaP", "other"] = "other"
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


Record = EvidenceRecord | MarkerRecord | PhenotypeRecord | CellStateRecord | DatasetRecord
