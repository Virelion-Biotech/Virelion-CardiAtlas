from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .harvest import HarvestItem, harvest_report


@dataclass(frozen=True, slots=True)
class HarvestQC:
    item_count: int
    accepted_count: int
    duplicate_count: int
    missing_external_ids: int
    missing_digests: int
    source_count: int
    passed: bool
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "item_count": self.item_count,
            "accepted_count": self.accepted_count,
            "duplicate_count": self.duplicate_count,
            "missing_external_ids": self.missing_external_ids,
            "missing_digests": self.missing_digests,
            "source_count": self.source_count,
            "passed": self.passed,
            "issues": list(self.issues),
        }


def assess_harvest(items: Iterable[HarvestItem]) -> HarvestQC:
    values = list(items)
    seen: set[tuple[str, str]] = set()
    duplicates = 0
    missing_ids = 0
    missing_digests = 0
    accepted = 0
    issues: list[str] = []
    for item in values:
        key = (item.source.strip().lower(), item.external_id.strip())
        if not key[1]:
            missing_ids += 1
            continue
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
        if not item.raw_digest:
            missing_digests += 1
        if item.status == "accepted":
            accepted += 1
    if missing_ids:
        issues.append("one or more harvest items lack an external identifier")
    if missing_digests:
        issues.append("one or more accepted harvest items lack a raw-response digest")
    if not values:
        issues.append("harvest contains no items")
    report = harvest_report(values)
    passed = not issues and report["item_count"] > 0
    return HarvestQC(
        item_count=len(values),
        accepted_count=accepted,
        duplicate_count=duplicates,
        missing_external_ids=missing_ids,
        missing_digests=missing_digests,
        source_count=len(report["sources"]),
        passed=passed,
        issues=tuple(issues),
    )
