from __future__ import annotations

from dataclasses import dataclass

from .normalize import canonical_key, normalize_accession, normalize_gene_symbol


@dataclass(frozen=True, slots=True)
class IdentifierResolution:
    query: str
    canonical_id: str | None
    identifier_type: str | None
    confidence: float
    matched_alias: str | None = None
    source: str = "curated"


# Deliberately small and auditable aliases. This is not intended to replace
# authoritative upstream identifier services.
GENE_ALIASES: dict[str, str] = {
    "tnnt2": "TNNT2",
    "cardiac troponin t": "TNNT2",
    "myh7": "MYH7",
    "beta myosin heavy chain": "MYH7",
    "actc1": "ACTC1",
    "actin alpha cardiac": "ACTC1",
    "nppa": "NPPA",
    "nppb": "NPPB",
    "col1a1": "COL1A1",
    "col3a1": "COL3A1",
    "vim": "VIM",
    "pecam1": "PECAM1",
    "kdr": "KDR",
    "ccl2": "CCL2",
    "tgfb1": "TGFB1",
}


def resolve_gene(value: str) -> IdentifierResolution:
    key = canonical_key(value)
    canonical = GENE_ALIASES.get(key)
    if canonical:
        return IdentifierResolution(value, canonical, "gene_symbol", 0.99, value, "curated")
    normalized = normalize_gene_symbol(value)
    if normalized and normalized == value.strip().upper():
        return IdentifierResolution(value, normalized, "gene_symbol", 0.80, value, "format")
    return IdentifierResolution(value, None, None, 0.0)


def resolve_accession(value: str) -> IdentifierResolution:
    accession = normalize_accession(value)
    if not accession:
        return IdentifierResolution(value, None, None, 0.0)
    upper = accession.upper()
    if upper.startswith("GSE"):
        typ = "geo_series"
    elif upper.startswith("GSM"):
        typ = "geo_sample"
    elif upper.startswith("SRP") or upper.startswith("SRA"):
        typ = "sra_project"
    elif upper.startswith("PRJNA") or upper.startswith("PRJEB") or upper.startswith("PRJDB"):
        typ = "bioproject"
    elif upper.isdigit():
        typ = "pmid"
    else:
        typ = "accession"
    return IdentifierResolution(value, upper, typ, 0.95, value, "format")


def resolve(value: str, identifier_type: str | None = None) -> IdentifierResolution:
    if identifier_type in {None, "gene_symbol"}:
        gene = resolve_gene(value)
        if gene.canonical_id:
            return gene
    if identifier_type in {None, "accession", "geo_series", "geo_sample", "bioproject", "sra_project", "pmid"}:
        accession = resolve_accession(value)
        if accession.canonical_id:
            return accession
    return IdentifierResolution(value, None, None, 0.0)
