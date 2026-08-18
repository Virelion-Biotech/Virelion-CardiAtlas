from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AcquisitionTarget:
    """A bounded, auditable target for public cardiac evidence acquisition."""

    target_id: str
    source: str
    query: str
    domain: str
    priority: int = 50
    expected_record_types: tuple[str, ...] = ()
    rationale: str = ""
    inclusion_terms: tuple[str, ...] = ()
    exclusion_terms: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "source": self.source,
            "query": self.query,
            "domain": self.domain,
            "priority": self.priority,
            "expected_record_types": list(self.expected_record_types),
            "rationale": self.rationale,
            "inclusion_terms": list(self.inclusion_terms),
            "exclusion_terms": list(self.exclusion_terms),
            "metadata": dict(self.metadata),
        }


CARDIAC_ACQUISITION_PLAN: tuple[AcquisitionTarget, ...] = (
    AcquisitionTarget(
        target_id="pubmed:mi-single-cell",
        source="pubmed",
        query='(myocardial infarction OR myocardial injury OR ischemia) AND (single-cell OR single-nucleus OR snRNA-seq OR scRNA-seq) AND (heart OR cardiac OR myocardium)',
        domain="myocardial_infarction",
        priority=100,
        expected_record_types=("evidence",),
        rationale="Build a broad evidence base for injury-associated cardiac cell states and markers.",
        inclusion_terms=("myocardial infarction", "myocardial injury", "cardiac", "single-cell"),
    ),
    AcquisitionTarget(
        target_id="pubmed:cardiac-maturation",
        source="pubmed",
        query='(cardiac OR cardiomyocyte) AND (maturation OR mature OR development) AND (single-cell OR transcriptomic)',
        domain="maturation",
        priority=95,
        expected_record_types=("evidence",),
        rationale="Support developmental and maturation-state annotations used by CardiLearn and CardiVex.",
    ),
    AcquisitionTarget(
        target_id="pubmed:cardiac-fibrosis",
        source="pubmed",
        query='(cardiac fibrosis OR myocardial fibrosis) AND (fibroblast OR extracellular matrix OR remodeling) AND (single-cell OR transcriptomic)',
        domain="fibrosis",
        priority=95,
        expected_record_types=("evidence",),
        rationale="Capture fibroblast-state and extracellular-matrix evidence without forcing a single molecular signature.",
    ),
    AcquisitionTarget(
        target_id="pubmed:cardiac-regeneration",
        source="pubmed",
        query='(cardiac regeneration OR myocardial regeneration OR heart regeneration) AND (single-cell OR transcriptomic)',
        domain="regeneration",
        priority=90,
        expected_record_types=("evidence",),
        rationale="Build evidence around reparative and regenerative states across models and timepoints.",
    ),
    AcquisitionTarget(
        target_id="geo:mi-single-cell",
        source="geo",
        query="heart myocardial infarction single cell",
        domain="myocardial_infarction",
        priority=100,
        expected_record_types=("dataset",),
        rationale="Discover public cardiac datasets suitable for sample-level harmonization and benchmark candidacy.",
    ),
    AcquisitionTarget(
        target_id="geo:cardiac-maturation",
        source="geo",
        query="heart cardiomyocyte maturation single cell",
        domain="maturation",
        priority=90,
        expected_record_types=("dataset",),
        rationale="Identify datasets for developmental-state calibration.",
    ),
)


def acquisition_plan(domain: str | None = None) -> list[AcquisitionTarget]:
    values = list(CARDIAC_ACQUISITION_PLAN)
    if domain is not None:
        values = [item for item in values if item.domain == domain]
    return sorted(values, key=lambda item: (-item.priority, item.target_id))


def plan_as_dict(domain: str | None = None) -> list[dict[str, object]]:
    return [item.to_dict() for item in acquisition_plan(domain)]
