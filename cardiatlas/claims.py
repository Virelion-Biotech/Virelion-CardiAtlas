from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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

    @property
    def status(self) -> str:
        if self.supporting_evidence and self.refuting_evidence:
            return "conflicted"
        if self.supporting_evidence:
            return "supported"
        if self.refuting_evidence:
            return "refuted"
        return "undetermined"


class ClaimStore:
    """Tracks competing evidence instead of collapsing disagreement into one fact."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    def add(self, claim: Claim) -> None:
        if claim.id in self._claims:
            raise ValueError(f"claim already exists: {claim.id}")
        self._claims[claim.id] = claim

    def assess(self, claim_id: str) -> ClaimAssessment:
        claim = self._claims[claim_id]
        supporting: list[str] = []
        refuting: list[str] = []
        mixed: list[str] = []
        for evidence_id in claim.evidence_ids:
            # Evidence polarity can be encoded as evidence IDs in higher-level
            # records; this base store preserves explicit claim polarity while
            # allowing future source-level polarity annotations.
            if claim.polarity == "supports":
                supporting.append(evidence_id)
            elif claim.polarity == "refutes":
                refuting.append(evidence_id)
            elif claim.polarity == "mixed":
                mixed.append(evidence_id)
        return ClaimAssessment(claim, tuple(supporting), tuple(refuting), tuple(mixed))

    def all(self) -> list[Claim]:
        return list(self._claims.values())
