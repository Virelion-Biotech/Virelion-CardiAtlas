"""Structured evidence records for regenerative and genetic therapeutic products.

These records describe product identity, manufacturing, potency, quality, stability,
regulatory state and linked evidence. They are research metadata, not a release
decision, regulatory determination, or proof of clinical efficacy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ProductModality = Literal[
    "autologous_cell", "allogeneic_cell", "engineered_tissue", "gene_therapy",
    "gene_editing", "cell_gene_combination", "secretome", "other",
]
EvidenceStatus = Literal["not_reported", "reported", "source_verified", "expert_reviewed"]
RegulatoryStatus = Literal[
    "preclinical", "clinical_trial", "scientific_advice", "classification",
    "application_submitted", "authorized", "withdrawn", "unknown",
]


@dataclass(frozen=True, slots=True)
class PotencyAssay:
    """A functional assay with explicit assay context and evidence provenance."""
    assay_name: str
    biological_function: str
    method: str
    result: str | None = None
    units: str | None = None
    acceptance_criterion: str | None = None
    evidence_ids: tuple[str, ...] = ()
    status: EvidenceStatus = "not_reported"

    def __post_init__(self) -> None:
        if not all(x.strip() for x in (self.assay_name, self.biological_function, self.method)):
            raise ValueError("potency assay requires name, biological function and method")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("potency assay evidence_ids must be unique")


@dataclass(frozen=True, slots=True)
class ManufacturingProfile:
    source_material: str | None = None
    autologous_or_allogeneic: Literal["autologous", "allogeneic", "not_applicable", "unknown"] = "unknown"
    expansion_or_processing: str | None = None
    purification: str | None = None
    delivery_route: str | None = None
    manufacturing_standard: str | None = None
    batch_count_reported: int | None = None
    batch_variability: str | None = None
    process_parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.batch_count_reported is not None and self.batch_count_reported < 0:
            raise ValueError("batch_count_reported cannot be negative")


@dataclass(frozen=True, slots=True)
class ProductRegulatoryRecord:
    jurisdiction: str
    status: RegulatoryStatus
    authority: str | None = None
    procedure_or_trial_id: str | None = None
    as_of_date: str | None = None
    scope_note: str = ""
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.jurisdiction.strip():
            raise ValueError("regulatory record requires a jurisdiction")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("regulatory evidence_ids must be unique")


@dataclass(frozen=True, slots=True)
class TherapeuticProductRecord:
    """Versionable product-centred record; all efficacy claims remain evidence-linked."""
    id: str
    name: str
    modality: ProductModality
    intended_indication: str
    product_identity: dict[str, Any] = field(default_factory=dict)
    genetic_target: str | None = None
    delivery_vector_or_construct: str | None = None
    cell_source_and_phenotype: str | None = None
    manufacturing: ManufacturingProfile = field(default_factory=ManufacturingProfile)
    quality_attributes: dict[str, Any] = field(default_factory=dict)
    potency_assays: tuple[PotencyAssay, ...] = ()
    release_criteria: dict[str, Any] = field(default_factory=dict)
    stability: dict[str, Any] = field(default_factory=dict)
    regulatory_records: tuple[ProductRegulatoryRecord, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    version: int = 1
    supersedes: str | None = None
    limitations: tuple[str, ...] = ()
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip() or not self.intended_indication.strip():
            raise ValueError("product id, name and intended_indication are required")
        if self.version < 1:
            raise ValueError("product version must be positive")
        if self.schema_version != "1.0":
            raise ValueError("unsupported therapeutic product schema version")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("product evidence_ids must be unique")
        if len({(r.jurisdiction, r.authority, r.procedure_or_trial_id) for r in self.regulatory_records}) != len(self.regulatory_records):
            raise ValueError("duplicate regulatory record for the same procedure")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence_ids"] = list(self.evidence_ids)
        payload["potency_assays"] = [asdict(x) for x in self.potency_assays]
        payload["regulatory_records"] = [asdict(x) for x in self.regulatory_records]
        payload["limitations"] = list(self.limitations)
        return payload
