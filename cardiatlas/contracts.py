from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AtlasContext:
    """Portable context payload for CardiAgent, CardiVex, and CardiEval."""

    context_id: str
    phenotype_ids: tuple[str, ...] = ()
    cell_state_ids: tuple[str, ...] = ()
    marker_ids: tuple[str, ...] = ()
    dataset_ids: tuple[str, ...] = ()
    study_ids: tuple[str, ...] = ()
    sample_ids: tuple[str, ...] = ()
    intervention_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    confidence: float | None = None
    provenance: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "phenotype_ids": list(self.phenotype_ids),
            "cell_state_ids": list(self.cell_state_ids),
            "marker_ids": list(self.marker_ids),
            "dataset_ids": list(self.dataset_ids),
            "study_ids": list(self.study_ids),
            "sample_ids": list(self.sample_ids),
            "intervention_ids": list(self.intervention_ids),
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "provenance": list(self.provenance),
            "metadata": self.metadata,
            "contract_version": "1.1",
        }


def context_from_dict(payload: dict[str, Any]) -> AtlasContext:
    version = payload.get("contract_version")
    if version not in (None, "1.0", "1.1"):
        raise ValueError(f"unsupported atlas context contract: {version}")
    return AtlasContext(
        context_id=str(payload["context_id"]),
        phenotype_ids=tuple(payload.get("phenotype_ids", ())),
        cell_state_ids=tuple(payload.get("cell_state_ids", ())),
        marker_ids=tuple(payload.get("marker_ids", ())),
        dataset_ids=tuple(payload.get("dataset_ids", ())),
        study_ids=tuple(payload.get("study_ids", ())),
        sample_ids=tuple(payload.get("sample_ids", ())),
        intervention_ids=tuple(payload.get("intervention_ids", ())),
        evidence_ids=tuple(payload.get("evidence_ids", ())),
        confidence=payload.get("confidence"),
        provenance=tuple(payload.get("provenance", ())),
        metadata=dict(payload.get("metadata", {})),
    )
