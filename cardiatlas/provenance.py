from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ProvenanceEvent:
    action: str
    actor: str = "system"
    source: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "actor": self.actor,
            "source": self.source,
            "timestamp": self.timestamp,
            "details": dict(sorted(self.details.items())),
        }


@dataclass(slots=True)
class ProvenanceBundle:
    record_id: str
    events: list[ProvenanceEvent] = field(default_factory=list)

    def add(self, event: ProvenanceEvent) -> None:
        self.events.append(event)

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "events": [event.to_dict() for event in self.events],
        }

    def latest_source(self) -> str | None:
        for event in reversed(self.events):
            if event.source:
                return event.source
        return None
