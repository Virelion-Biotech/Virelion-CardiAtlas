from __future__ import annotations

from dataclasses import dataclass

from .normalize import canonical_key, normalize_label


@dataclass(frozen=True, slots=True)
class Concept:
    id: str
    label: str
    category: str
    synonyms: tuple[str, ...] = ()
    parent_id: str | None = None


CONCEPTS: tuple[Concept, ...] = (
    Concept("cell:cardiomyocyte", "cardiomyocyte", "cell_type", ("cardiomyocytes", "myocyte", "cardiac myocyte")),
    Concept("cell:fibroblast", "cardiac fibroblast", "cell_type", ("fibroblast", "cardiac fibroblasts")),
    Concept("cell:endothelial", "cardiac endothelial cell", "cell_type", ("endothelial", "endothelial cell")),
    Concept("cell:macrophage", "cardiac macrophage", "cell_type", ("macrophage", "macrophages")),
    Concept("cell:pericyte", "pericyte", "cell_type"),
    Concept("state:mature", "mature", "cell_state", ("maturation", "mature cardiac")),
    Concept("state:immature", "immature", "cell_state", ("immaturity", "fetal-like")),
    Concept("state:hypertrophic", "hypertrophic", "cell_state", ("hypertrophy",)),
    Concept("state:activated_fibroblast", "activated fibroblast", "cell_state", ("myofibroblast-like",)),
    Concept("state:inflammatory", "inflammatory", "cell_state", ("inflamed", "inflammation-associated")),
    Concept("phenotype:myocardial_infarction", "myocardial infarction", "phenotype", ("MI", "myocardial injury", "infarction")),
    Concept("phenotype:fibrosis", "cardiac fibrosis", "phenotype", ("fibrosis", "fibrotic remodeling")),
    Concept("phenotype:ischemia_reperfusion", "ischemia-reperfusion injury", "phenotype", ("I/R injury", "ischemia reperfusion")),
    Concept("phenotype:inflammation", "cardiac inflammation", "phenotype", ("inflammatory response",)),
    Concept("phenotype:regeneration", "cardiac regeneration", "phenotype", ("regenerative response",)),
    Concept("process:maturation", "cardiac maturation", "process", ("cardiomyocyte maturation",)),
    Concept("process:remodeling", "cardiac remodeling", "process", ("remodelling",)),
)

_INDEX: dict[str, Concept] = {
    canonical_key(value): concept
    for concept in CONCEPTS
    for value in (concept.id, concept.label, *concept.synonyms)
}


def resolve_concept(value: str) -> Concept | None:
    return _INDEX.get(canonical_key(value))


def canonical_concept_id(value: str) -> str | None:
    concept = resolve_concept(value)
    return concept.id if concept else None


def concept_terms(concept_id: str) -> tuple[str, ...]:
    concept = next((item for item in CONCEPTS if item.id == concept_id), None)
    if concept is None:
        return ()
    return (normalize_label(concept.label), *map(normalize_label, concept.synonyms))


def concepts_by_category(category: str) -> list[Concept]:
    return [item for item in CONCEPTS if item.category == category]
