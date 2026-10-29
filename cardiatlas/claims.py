from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Mapping

from .models import EvidenceRecord

ClaimPolarity = Literal["supports", "refutes", "mixed", "unknown"]
ReviewStatus = Literal["unreviewed", "source_verified", "expert_reviewed", "rejected"]


@dataclass(frozen=True, slots=True)
class ClaimEvidence:
    """Claim-level citation with a stable source locator and review state."""

    evidence_id: str
    source_locator: str
    locator_type: str = "section"
    locator_label: str = ""
    quote: str = ""
    review_status: ReviewStatus = "unreviewed"
    reviewer_id: str | None = None
    reviewed_at: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("claim evidence requires evidence_id")
        if self.review_status not in {"unreviewed", "source_verified", "expert_reviewed", "rejected"}:
            raise ValueError("unsupported claim evidence review_status")
        if self.review_status in {"source_verified", "expert_reviewed"} and not self.source_locator.strip():
            raise ValueError("verified claim evidence requires a source_locator")
        if self.review_status == "expert_reviewed" and not self.reviewer_id:
            raise ValueError("expert-reviewed evidence requires reviewer_id")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Claim:
    id: str
    subject: str
    predicate: str
    object: str
    polarity: ClaimPolarity = "unknown"
    evidence_ids: tuple[str, ...] = ()
    notes: str = ""
    schema_version: str = "1.0"
    version: int = 1
    supersedes: str | None = None
    citations: tuple[ClaimEvidence, ...] = ()

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.id, self.subject, self.predicate, self.object)):
            raise ValueError("claim id, subject, predicate, and object must be non-empty")
        if self.polarity not in {"supports", "refutes", "mixed", "unknown"}:
            raise ValueError("unsupported claim polarity")
        if self.schema_version != "1.0":
            raise ValueError("unsupported claim schema_version")
        if type(self.version) is not int or self.version < 1:
            raise ValueError("claim version must be a positive integer")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("claim evidence_ids must be unique")
        if len({item.evidence_id + "|" + item.source_locator for item in self.citations}) != len(self.citations):
            raise ValueError("duplicate claim evidence locator")

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        value["citations"] = [item.to_dict() for item in self.citations]
        return value

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "Claim":
        raw = dict(payload)
        raw["evidence_ids"] = tuple(raw.get("evidence_ids", ()))
        raw["citations"] = tuple(
            item if isinstance(item, ClaimEvidence) else ClaimEvidence(**item)
            for item in raw.get("citations", ())
        )
        return cls(**raw)


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
        return sum(len(items) for items in (
            self.supporting_evidence, self.refuting_evidence,
            self.mixed_evidence, self.unknown_evidence,
        ))


class ClaimStore:
    """Versioned claims with transparent, source-located evidence relationships."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}

    def add(self, claim: Claim) -> None:
        if not isinstance(claim, Claim):
            raise TypeError("claim must be a Claim instance")
        if claim.id in self._claims:
            raise ValueError(f"claim already exists: {claim.id}")
        self._claims[claim.id] = claim

    def upsert(self, claim: Claim) -> None:
        """Insert a claim or accept only a strictly newer revision."""
        current = self._claims.get(claim.id)
        if current is not None and claim.version <= current.version:
            raise ValueError(f"claim revision must increase beyond {current.version}: {claim.id}")
        self._claims[claim.id] = claim

    def get(self, claim_id: str) -> Claim:
        return self._claims[claim_id]

    def assess(self, claim_id: str, evidence: Mapping[str, EvidenceRecord] | None = None) -> ClaimAssessment:
        claim = self._claims[claim_id]
        supporting: list[str] = []
        refuting: list[str] = []
        mixed: list[str] = []
        unknown: list[str] = []
        for evidence_id in dict.fromkeys(claim.evidence_ids):
            item = evidence.get(evidence_id) if evidence is not None else None
            polarity = item.polarity if item is not None else (claim.polarity if evidence is None else "unknown")
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
        return sorted(self._claims.values(), key=lambda item: (item.id, item.version))

    def to_dict(self) -> dict[str, object]:
        return {"schema_version": "1.0", "claims": [item.to_dict() for item in self.all()]}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ClaimStore":
        if payload.get("schema_version", "1.0") != "1.0":
            raise ValueError("unsupported ClaimStore schema_version")
        result = cls()
        for raw in payload.get("claims", ()):
            result.add(Claim.from_dict(raw))
        return result


def digest_claims(claims) -> str:
    """Canonical SHA-256 over sorted versioned claim payloads."""
    import hashlib
    import json
    payload = [item.to_dict() for item in sorted(claims, key=lambda item: (item.id, item.version))]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
