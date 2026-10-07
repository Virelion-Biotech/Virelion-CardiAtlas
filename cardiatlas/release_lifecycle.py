"""Release-state lifecycle described in docs/release-checklist.md.

A ReleaseManifest (release.py) and a ReleaseReadiness (release_checks.py) are
both pure, backend-agnostic descriptions of a record set. This module adds
the mutable lifecycle layered on top of them -- draft -> candidate ->
verified -> deprecated -- without changing what a release's digest attests
to: promoting or deprecating a release never touches canonical_payload() or
digest_records(), so the digest always means exactly one thing, the exact
record content, regardless of the release's current state. A separate
relationship_digest locks graph content during lifecycle transitions.

State meanings (docs/release-checklist.md):
  draft      internally generated; may contain unresolved provenance or
             incomplete metadata.
  candidate  passes structural checks and is suitable for review.
  verified   CI and source/provenance checks pass on the exact release
             commit.
  deprecated superseded by a newer release but retained for reproducibility.

CI status and commit identity (checklist item 9, "CI passes on the release
commit") are facts about the outside world that CardiAtlas cannot observe on
its own -- the caller (typically CI itself) must supply them to verify().
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .graph import Relation
from .models import Record
from .release import ReleaseManifest, create_manifest, digest_records, digest_relations
from .release_checks import ReleaseReadiness, ReleaseCheck, assess_release
from .schema import SCHEMA_VERSION

RELEASE_STATES = ("draft", "candidate", "verified", "deprecated")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class StateTransition:
    from_state: str
    to_state: str
    at: str
    note: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"from_state": self.from_state, "to_state": self.to_state, "at": self.at, "note": self.note}


def _transition_from_dict(payload: dict[str, object]) -> StateTransition:
    return StateTransition(
        from_state=str(payload.get("from_state", "")),
        to_state=str(payload.get("to_state", "")),
        at=str(payload.get("at", "")),
        note=str(payload.get("note", "")),
    )


@dataclass(frozen=True, slots=True)
class ReleaseRecord:
    """A release manifest plus its lifecycle state, readiness, and history."""

    manifest: ReleaseManifest
    state: str
    readiness: ReleaseReadiness
    history: tuple[StateTransition, ...]
    commit_sha: str | None = None
    ci_passed: bool | None = None
    superseded_by: str | None = None
    relationship_digest: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest.to_dict(),
            "state": self.state,
            "readiness": self.readiness.to_dict(),
            "history": [item.to_dict() for item in self.history],
            "commit_sha": self.commit_sha,
            "ci_passed": self.ci_passed,
            "superseded_by": self.superseded_by,
            "relationship_digest": self.relationship_digest,
        }


def release_record_from_dict(payload: dict[str, object]) -> ReleaseRecord:
    manifest_payload = dict(payload["manifest"])  # type: ignore[index]
    manifest = ReleaseManifest(
        version=str(manifest_payload["version"]),
        schema_version=str(manifest_payload["schema_version"]),
        created_at=str(manifest_payload["created_at"]),
        record_count=int(manifest_payload["record_count"]),
        record_types=dict(manifest_payload["record_types"]),
        digest=str(manifest_payload["digest"]),
        dataset_accessions=tuple(manifest_payload.get("dataset_accessions", ())),
        evidence_sources=tuple(manifest_payload.get("evidence_sources", ())),
    )
    readiness_payload = dict(payload["readiness"])  # type: ignore[index]
    readiness = ReleaseReadiness(
        passed=bool(readiness_payload["passed"]),
        digest=str(readiness_payload["digest"]),
        checks=tuple(
            ReleaseCheck(name=c["name"], passed=c["passed"], severity=c["severity"], message=c["message"])
            for c in readiness_payload["checks"]
        ),
    )
    history = tuple(_transition_from_dict(item) for item in payload.get("history", ()))
    return ReleaseRecord(
        manifest=manifest,
        state=str(payload["state"]),
        readiness=readiness,
        history=history,
        commit_sha=payload.get("commit_sha"),
        ci_passed=payload.get("ci_passed"),
        superseded_by=payload.get("superseded_by"),
        relationship_digest=payload.get("relationship_digest"),
    )


def _assert_unchanged(release: ReleaseRecord, records: list[Record], relations: list[Relation]) -> None:
    """Refuse to transition a release if the underlying record set has drifted.

    A release's digest is supposed to identify exactly one record set
    (release.py's design rule). If the store has changed since the release
    was staged, promoting/verifying the old digest against new content would
    silently misrepresent what was actually reviewed -- so this requires a
    fresh draft instead.
    """
    if release.relationship_digest is None:
        raise ValueError("legacy release lacks a relationship digest; stage a new draft")
    if digest_relations(relations) != release.relationship_digest:
        raise ValueError("relationship set has changed since this release was staged; stage a new draft")
    current_digest = digest_records(records)
    if current_digest != release.manifest.digest:
        raise ValueError(
            "record set has changed since this release was staged "
            f"(staged digest {release.manifest.digest[:12]}..., current digest {current_digest[:12]}...); "
            "stage a new draft release instead of transitioning a stale one"
        )


def create_draft(
    records: list[Record],
    version: str,
    relations: Iterable[Relation] = (),
    schema_version: str = SCHEMA_VERSION,
) -> ReleaseRecord:
    """Stage a new draft release: a manifest plus its as-of-now readiness.

    A draft may still have unresolved provenance or incomplete benchmark
    grouping (checklist items 4 and 5 are advisory, not blocking, in draft).
    """
    relations = list(relations)
    manifest = create_manifest(records, version, schema_version)
    readiness = assess_release(records, relations, closed_evidence_graph=False)
    return ReleaseRecord(
        manifest=manifest,
        state="draft",
        readiness=readiness,
        history=(StateTransition("", "draft", _now(), "release staged"),),
        relationship_digest=digest_relations(relations),
    )


def promote_to_candidate(
    release: ReleaseRecord,
    records: list[Record],
    relations: Iterable[Relation] = (),
) -> ReleaseRecord:
    """draft -> candidate: structural (error-severity) checks must all pass.

    Provenance may still be open at this point; a candidate is "suitable for
    review", not yet claiming a closed evidence graph.
    """
    if release.state != "draft":
        raise ValueError(f"cannot promote to candidate from state '{release.state}'; expected 'draft'")
    relations = list(relations)
    _assert_unchanged(release, records, relations)
    readiness = assess_release(records, relations, closed_evidence_graph=False)
    if not readiness.passed:
        failing = [c.name for c in readiness.checks if not c.passed and c.severity == "error"]
        raise ValueError(f"structural checks failing, cannot reach candidate: {', '.join(failing)}")
    history = release.history + (StateTransition("draft", "candidate", _now(), "structural checks passed"),)
    return ReleaseRecord(release.manifest, "candidate", readiness, history, release.commit_sha, release.ci_passed, release.superseded_by, release.relationship_digest)


def verify(
    release: ReleaseRecord,
    records: list[Record],
    relations: Iterable[Relation] = (),
    *,
    commit_sha: str,
    ci_passed: bool,
    require_benchmark_ready: bool = False,
) -> ReleaseRecord:
    """candidate -> verified: closed evidence graph, exact commit, passing CI.

    ``commit_sha`` and ``ci_passed`` must be supplied by the caller (normally
    the CI pipeline itself) -- CardiAtlas has no way to observe either fact on
    its own (checklist item 9).
    """
    if release.state != "candidate":
        raise ValueError(f"cannot verify from state '{release.state}'; expected 'candidate'")
    relations = list(relations)
    _assert_unchanged(release, records, relations)
    if not commit_sha.strip():
        raise ValueError("verify requires a non-empty commit_sha")
    if ci_passed is not True:
        raise ValueError("verify requires ci_passed=True; CI must pass on the release commit before verification")
    readiness = assess_release(records, relations, closed_evidence_graph=True, require_benchmark_ready=require_benchmark_ready)
    if not readiness.passed:
        failing = [c.name for c in readiness.checks if not c.passed and c.severity == "error"]
        raise ValueError(f"release does not satisfy verified-release checks: {', '.join(failing)}")
    history = release.history + (StateTransition("candidate", "verified", _now(), f"commit={commit_sha}"),)
    return ReleaseRecord(release.manifest, "verified", readiness, history, commit_sha, ci_passed, release.superseded_by, release.relationship_digest)


def deprecate(release: ReleaseRecord, *, superseded_by: str, note: str = "") -> ReleaseRecord:
    """Any non-deprecated state -> deprecated: retained for reproducibility, marked superseded."""
    if release.state == "deprecated":
        raise ValueError("release is already deprecated")
    if not superseded_by.strip():
        raise ValueError("deprecate requires the version that supersedes this release")
    history = release.history + (StateTransition(release.state, "deprecated", _now(), note or f"superseded by {superseded_by}"),)
    return ReleaseRecord(release.manifest, "deprecated", release.readiness, history, release.commit_sha, release.ci_passed, superseded_by, release.relationship_digest)
