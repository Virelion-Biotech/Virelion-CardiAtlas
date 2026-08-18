from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .models import DatasetRecord, EvidenceRecord
from .normalize import normalize_accession, normalize_species


def pubmed_summary_to_evidence(summary: dict[str, Any]) -> EvidenceRecord:
    pmid = str(summary.get("uid", ""))
    title = str(summary.get("title", "")).rstrip(".")
    pubdate = str(summary.get("pubdate", ""))
    year_match = re.search(r"(19|20)\d{2}", pubdate)
    year = int(year_match.group(0)) if year_match else None
    journal = str(summary.get("fulljournalname", ""))
    authors = summary.get("authors") or []
    author_names = [str(item.get("name", "")) for item in authors if isinstance(item, dict)]
    citation = ", ".join(author_names[:6])
    if len(author_names) > 6:
        citation += ", et al."
    if journal:
        citation = f"{citation}. {journal}" if citation else journal
    return EvidenceRecord(
        id=f"evidence:pubmed:{pmid}",
        name=title or f"PubMed {pmid}",
        description=title,
        source_type="pubmed",
        source_identifier=pmid,
        citation=citation,
        evidence_level="primary",
        year=year,
        metadata={"url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"},
    )


def geo_summary_to_dataset(summary: dict[str, Any]) -> DatasetRecord:
    uid = str(summary.get("uid", ""))
    accession = normalize_accession(str(summary.get("accession", "") or summary.get("accessionversion", "")))
    title = str(summary.get("title", ""))
    organism = normalize_species(str(summary.get("organism", "")))
    tissue = str(summary.get("tissue", ""))
    n_samples = summary.get("n_samples")
    try:
        sample_count = int(n_samples) if n_samples is not None else None
    except (TypeError, ValueError):
        sample_count = None
    identifier = accession or uid
    return DatasetRecord(
        id=f"dataset:geo:{identifier}",
        name=title or identifier,
        description=title,
        accession=identifier,
        repository="GEO",
        study_title=title,
        organism=organism,
        tissue=tissue,
        sample_count=sample_count,
        metadata={
            "ncbi_uid": uid,
            "url": f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={identifier}",
        },
    )
