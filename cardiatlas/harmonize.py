from __future__ import annotations

from dataclasses import dataclass

from .normalize import canonical_key
from .ontology import canonical_concept_id


@dataclass(frozen=True, slots=True)
class HarmonizedValue:
    raw: str
    normalized: str
    concept_id: str | None = None
    confidence: float = 1.0
    note: str = ""


CONDITION_ALIASES = {
    "sham": "reference",
    "control": "reference",
    "healthy": "reference",
    "normal": "reference",
    "mi": "myocardial_infarction",
    "myocardial infarction": "myocardial_infarction",
    "infarct": "myocardial_infarction",
    "ischemia reperfusion": "ischemia_reperfusion",
    "ischemia-reperfusion": "ischemia_reperfusion",
    "fibrosis": "fibrosis",
    "cardiac fibrosis": "fibrosis",
    "inflammation": "inflammation",
    "inflammatory": "inflammation",
}

MODALITY_ALIASES = {
    "single cell rna": "scrna",
    "single-cell rna": "scrna",
    "scrna-seq": "scrna",
    "single nucleus rna": "snrna",
    "single-nucleus rna": "snrna",
    "snrna-seq": "snrna",
    "bulk rna-seq": "bulk_rna",
    "rna-seq": "bulk_rna",
}


def harmonize_condition(raw: str) -> HarmonizedValue:
    key = canonical_key(raw)
    normalized = CONDITION_ALIASES.get(key, key.replace(" ", "_"))
    concept = canonical_concept_id(normalized)
    confidence = 0.98 if key in CONDITION_ALIASES else 0.70
    note = "curated alias" if key in CONDITION_ALIASES else "normalized only; not ontology-mapped"
    return HarmonizedValue(raw, normalized, concept, confidence, note)


def harmonize_modality(raw: str) -> HarmonizedValue:
    key = canonical_key(raw)
    normalized = MODALITY_ALIASES.get(key, key.replace(" ", "_"))
    confidence = 0.98 if key in MODALITY_ALIASES else 0.70
    return HarmonizedValue(raw, normalized, None, confidence, "curated alias" if key in MODALITY_ALIASES else "normalized only")


def harmonize_label(raw: str) -> HarmonizedValue:
    concept = canonical_concept_id(raw)
    return HarmonizedValue(
        raw=raw,
        normalized=canonical_key(raw),
        concept_id=concept,
        confidence=0.99 if concept else 0.70,
        note="ontology match" if concept else "lexical normalization only",
    )
