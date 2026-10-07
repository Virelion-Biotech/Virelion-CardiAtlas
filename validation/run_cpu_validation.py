"""Reproducible metadata validation; optionally repeat against live NCBI sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jsonschema

from cardiatlas import __version__
from cardiatlas.build import build_reference
from cardiatlas.geo_reconstruct import reconstruct_study
from cardiatlas.geo_soft import parse_geo_soft_bytes, samples_to_rows
from cardiatlas.loader import read_bundle
from cardiatlas.models import DatasetRecord
from cardiatlas.ncbi import NcbiClient
from cardiatlas.normalize import canonical_key
from cardiatlas.study_readiness import assess_study_benchmark_readiness

ROOT = Path(__file__).resolve().parents[1]


def run(live=False):
    build = build_reference(ROOT, "validation")
    assert build.readiness.passed
    for record in build.records:
        schema = json.loads((ROOT / "schemas" / f"{record.record_type}_record.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(record.to_dict())
    assert len(build.records) == 21
    payload = (ROOT / "validation/fixtures/GSE153480-selected.soft").read_bytes()
    bibliography = json.loads((ROOT / "validation/fixtures/pubmed-selected.json").read_text())
    source = json.loads((ROOT / "validation/fixtures/provenance.json").read_text())
    assert hashlib.sha256(payload).hexdigest() == source["geo_selected_fixture_sha256"]
    if live:
        client = NcbiClient(timeout=30)
        payload = client.fetch_geo_family_soft("GSE153480")
        bibliography = client.esummary("pubmed", list(bibliography))
    dataset = DatasetRecord(
        id="dataset:geo:GSE153480",
        name="GSE153480",
        accession="GSE153480",
        organism="Mus musculus",
        tissue="ventricle",
        modalities=["scrna"],
        source_ids=["evidence:geo:GSE153480"],
    )
    study, samples, report = reconstruct_study(dataset, samples_to_rows(parse_geo_soft_bytes(payload)))
    assert [item.accession for item in samples] == [f"GSM{i}" for i in range(4644949, 4644957)]
    assert {item.modality for item in samples} == {"scrna"}
    assert {item.condition for item in samples} == {"myocardial_infarction", "reference"}
    assert {item.timepoint for item in samples} == {"day1", "day3"}
    assert all(item.species == "Mus musculus" for item in samples)
    assert all(item.subject_id is None for item in samples)
    assert report.reconstructed_subjects == 0
    readiness = assess_study_benchmark_readiness(study, dataset, samples)
    assert not readiness.ready and "subject_structure" in readiness.missing
    catalog = json.loads((ROOT / "validation/fixtures/geo-catalog-selected.json").read_text())
    catalog_checks = []
    for record in read_bundle([ROOT / "data/reference/cardiac_datasets.jsonl"]):
        row = next(item for item in catalog if item["accession"] == record.accession)
        if live:
            ids = client.esearch("gds", record.accession, retmax=20)
            lookup = client.esummary("gds", ids)
            matches = [item for item in lookup.values() if isinstance(item, dict) and item.get("accession") == record.accession]
            assert len(matches) == 1
            row = matches[0]
        assert record.study_title == row["title"]
        assert record.organism == row["taxon"]
        assert record.sample_count == row["n_samples"]
        catalog_checks.append({"accession": record.accession, "title_taxon_sample_inventory_match": True,
                               "sample_records": record.sample_count, "taxon": record.organism})
    source_checks = []
    for item in read_bundle([ROOT / "data/reference/optical_stimulation_evidence.jsonl"]):
        summary = bibliography[item.source_identifier]
        assert canonical_key(item.name) == canonical_key(summary["title"])
        dois = {row["value"].lower() for row in summary["articleids"] if row["idtype"] == "doi"}
        assert item.context["doi"].lower() in dois
        assert str(item.year) in summary["pubdate"]
        assert (item.evidence_level == "review") == any("review" in t.lower() for t in summary["pubtype"])
        source_checks.append({"pmid": item.source_identifier, "title_doi_year_review_type_match": True})
    return {
        "passed": True,
        "package_version": __version__,
        "python": platform.python_version(),
        "source_mode": "live_ncbi" if live else "selected_source_fixtures",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Metadata/schema/bibliographic validation; not independent biological validation or claim-content review",
        "reference_records_validated": len(build.records),
        "reference_relationships": len(build.relations),
        "reference_warnings": [check.message for check in build.readiness.checks if not check.passed and check.severity == "warning"],
        "gse153480": {
            "samples": len(samples),
            "modality": "scrna",
            "conditions": list(report.condition_groups),
            "timepoints": list(report.timepoints),
            "explicit_subjects": 0,
            "benchmark_ready": readiness.ready,
            "blockers": list(readiness.missing),
            "input_sha256": hashlib.sha256(payload).hexdigest(),
        },
        "optical_bibliographic_checks": source_checks,
        "catalog_checks": catalog_checks,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default="validation/results.json")
    args = parser.parse_args()
    result = run(args.live)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        f"Validated {result['reference_records_validated']} reference records, 8 GEO samples and 6 bibliographic sources ({result['source_mode']})"
    )
