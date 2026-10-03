from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

from .models import EvidenceRecord


ClaimPolarity = Literal["supports", "refutes", "mixed", "unknown"]


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    subject: str
    predicate: str
    object: str
    polarity: ClaimPolarity = "unknown"
    evidence_ids: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ClaimAssessment:
    claim: Claim
    supporting_evidence: tuple[str, ...] = ()
    refuting_evidence: tuple[str, ...] = ()
    mixed_evidence: tuple[str, ...] = ()
    unknown_evidence: tuple[str, ...] = ()

    @property
    def status(self) -> str:
        if self.supporting_evidence and self.refuting_evidence:
            return "conflicted"
        if self.mixed_evidence:
            return "mixed"
        if self.supporting_evidence:
            return "supported"
        if self.refuting_evidence:
            return "refuted"
        return "undetermined"

    @property
    def evidence_count(self) -> int:
        return sum(
            len(items)
            for items in (
                self.supporting_evidence,
                self.refuting_evidence,
                self.mixed_evidence,
                self.unknown_evidence,
            )
        )


class ClaimStore:
    """Tracks competing evidence instead of collapsing disagreement into one fact."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    def add(self, claim: Claim) -> None:
        if claim.id in self._claims:
            raise ValueError(f"claim already exists: {claim.id}")
        self._claims[claim.id] = claim

    def get(self, claim_id: str) -> Claim:
        return self._claims[claim_id]

    def assess(self, claim_id: str, evidence: Mapping[str, EvidenceRecord] | None = None) -> ClaimAssessment:
        claim = self._claims[claim_id]
        supporting: list[str] = []
        refuting: list[str] = []
        mixed: list[str] = []
        unknown: list[str] = []
        for evidence_id in claim.evidence_ids:
            item = evidence.get(evidence_id) if evidence else None
            polarity = item.polarity if item else claim.polarity
            if polarity == "supports":
                supporting.append(evidence_id)
            elif polarity == "refutes":
                refuting.append(evidence_id)
            elif polarity == "mixed":
                mixed.append(evidence_id)
            else:
                unknown.append(evidence_id)
        return ClaimAssessment(claim, tuple(supporting), tuple(refuting), tuple(mixed), tuple(unknown))

    def conflicts(self, claim_id: str, evidence: Mapping[str, EvidenceRecord]) -> bool:
        assessment = self.assess(claim_id, evidence)
        return bool(assessment.supporting_evidence and assessment.refuting_evidence)

    def all(self) -> list[Claim]:
        return sorted(self._claims.values(), key=lambda item: item.id)
