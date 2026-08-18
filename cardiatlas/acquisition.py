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
    AcquisitionTarget("pubmed:mi-single-cell", "pubmed", '(myocardial infarction OR myocardial injury OR ischemia) AND (single-cell OR single-nucleus OR snRNA-seq OR scRNA-seq) AND (heart OR cardiac OR myocardium)', "myocardial_infarction", 100, ("evidence",), "Build injury-associated cardiac cell-state and marker evidence.", ("myocardial infarction", "myocardial injury", "cardiac", "single-cell")),
    AcquisitionTarget("pubmed:mi-sham-reference", "pubmed", '(myocardial infarction OR myocardial injury) AND (sham OR control OR reference) AND (cardiac OR heart) AND (transcriptomic OR single-cell OR single-nucleus)', "myocardial_infarction", 100, ("evidence",), "Prioritize studies with explicit injury/reference comparisons for downstream benchmark context.", ("myocardial infarction", "sham", "control")),
    AcquisitionTarget("pubmed:cardiac-maturation", "pubmed", '(cardiac OR cardiomyocyte) AND (maturation OR mature OR development) AND (single-cell OR transcriptomic)', "maturation", 95, ("evidence",), "Support developmental and maturation-state annotations.", ("cardiomyocyte", "maturation")),
    AcquisitionTarget("pubmed:cardiac-fibrosis", "pubmed", '(cardiac fibrosis OR myocardial fibrosis) AND (fibroblast OR extracellular matrix OR remodeling) AND (single-cell OR transcriptomic)', "fibrosis", 95, ("evidence",), "Capture fibroblast and extracellular-matrix evidence without forcing one signature.", ("fibrosis", "fibroblast")),
    AcquisitionTarget("pubmed:cardiac-regeneration", "pubmed", '(cardiac regeneration OR myocardial regeneration OR heart regeneration) AND (single-cell OR transcriptomic)', "regeneration", 90, ("evidence",), "Build evidence around reparative and regenerative states across models and timepoints.", ("regeneration", "heart")),
    AcquisitionTarget("pubmed:ischemia-reperfusion", "pubmed", '((ischemia-reperfusion OR ischemia reperfusion) AND (heart OR cardiac OR myocardium)) AND (single-cell OR single-nucleus OR transcriptomic)', "ischemia_reperfusion", 88, ("evidence",), "Separate reperfusion-associated biology from permanent infarction where possible.", ("ischemia-reperfusion", "cardiac")),
    AcquisitionTarget("pubmed:cardiac-electrophysiology", "pubmed", '(cardiac electrophysiology OR arrhythmia) AND (cardiomyocyte OR heart) AND (transcriptomic OR single-cell OR proteomic)', "electrophysiology", 82, ("evidence",), "Support electrical-state interpretation and marker context.", ("arrhythmia", "cardiac electrophysiology")),
    AcquisitionTarget("pubmed:heart-failure-remodeling", "pubmed", '(heart failure OR cardiac remodeling) AND (single-cell OR single-nucleus OR transcriptomic) AND (human OR mouse OR pig)', "heart_failure", 80, ("evidence",), "Capture chronic remodeling and failure-associated cellular states.", ("heart failure", "remodeling")),
    AcquisitionTarget("geo:mi-single-cell", "geo", "heart myocardial infarction single cell", "myocardial_infarction", 100, ("dataset",), "Discover public injury datasets for sample-level harmonization.", ("heart", "myocardial infarction", "single cell")),
    AcquisitionTarget("geo:mi-sham", "geo", "heart myocardial infarction sham", "myocardial_infarction", 100, ("dataset",), "Find datasets containing explicit injury/reference groups.", ("myocardial infarction", "sham")),
    AcquisitionTarget("geo:cardiac-maturation", "geo", "heart cardiomyocyte maturation single cell", "maturation", 90, ("dataset",), "Identify datasets for developmental-state calibration.", ("cardiomyocyte", "maturation")),
    AcquisitionTarget("geo:cardiac-fibrosis", "geo", "heart cardiac fibrosis fibroblast single cell", "fibrosis", 88, ("dataset",), "Identify fibroblast/remodeling datasets for Atlas context.", ("fibrosis", "fibroblast")),
)


def acquisition_plan(domain: str | None = None) -> list[AcquisitionTarget]:
    values = list(CARDIAC_ACQUISITION_PLAN)
    if domain is not None:
        values = [item for item in values if item.domain == domain]
    return sorted(values, key=lambda item: (-item.priority, item.target_id))


def plan_as_dict(domain: str | None = None) -> list[dict[str, object]]:
    return [item.to_dict() for item in acquisition_plan(domain)]
