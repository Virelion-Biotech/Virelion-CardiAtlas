from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


_whitespace = re.compile(r"\s+")
_non_alnum = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class NormalizedTerm:
    raw: str
    normalized: str
    key: str


def normalize_label(value: str) -> str:
    """Normalize a human-facing biomedical label without destroying meaning."""
    text = _whitespace.sub(" ", value.strip().lower())
    return text


def canonical_key(value: str) -> str:
    """Create a stable comparison key suitable for search/indexing."""
    return _non_alnum.sub("_", normalize_label(value)).strip("_")


def normalize_gene_symbol(value: str) -> str:
    """Conservative gene/protein symbol normalization.

    This intentionally does not attempt species-specific symbol conversion;
    alias resolution belongs in an explicit mapping layer with provenance.
    """
    return value.strip().upper()


def normalize_accession(value: str) -> str:
    """Normalize common GEO/SRA/ENA/ArrayExpress accession formatting."""
    value = value.strip().upper()
    return re.sub(r"\s+", "", value)


def deduplicate(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = canonical_key(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value.strip())
    return result


def normalize_species(value: str) -> str:
    aliases = {
        "human": "Homo sapiens",
        "h. sapiens": "Homo sapiens",
        "mouse": "Mus musculus",
        "m. musculus": "Mus musculus",
        "rat": "Rattus norvegicus",
        "r. norvegicus": "Rattus norvegicus",
        "pig": "Sus scrofa",
        "sus scrofa domesticus": "Sus scrofa",
        "zebrafish": "Danio rerio",
    }
    cleaned = normalize_label(value)
    return aliases.get(cleaned, value.strip())
