from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .adapters import geo_summary_to_dataset
from .geo_reconstruct import ReconstructionReport, reconstruct_study
from .geo_soft import parse_geo_soft_bytes, samples_to_rows
from .models import DatasetRecord, SampleRecord, StudyRecord
from .ncbi import NcbiClient
from .study_readiness import StudyBenchmarkReadiness, assess_study_benchmark_readiness


@dataclass(frozen=True, slots=True)
class GeoReconstructionBundle:
    dataset: DatasetRecord
    study: StudyRecord
    samples: tuple[SampleRecord, ...]
    report: ReconstructionReport
    source_digest: str
    source_url: str
    retrieved_at_utc: str
    payload_bytes: int
    benchmark_readiness: StudyBenchmarkReadiness
    parser_version: str = "geo-soft-v1"

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset.to_dict(),
            "study": self.study.to_dict(),
            "sample_count": len(self.samples),
            "report": self.report.to_dict(),
            "source_digest": self.source_digest,
            "source_url": self.source_url,
            "retrieved_at_utc": self.retrieved_at_utc,
            "payload_bytes": self.payload_bytes,
            "parser_version": self.parser_version,
            "benchmark_readiness": self.benchmark_readiness.to_dict(),
        }


def reconstruct_geo_series(client: NcbiClient, dataset: DatasetRecord) -> GeoReconstructionBundle:
    accession = dataset.accession.strip().upper()
    payload = client.fetch_geo_family_soft(accession)
    source_digest = hashlib.sha256(payload).hexdigest()
    samples = parse_geo_soft_bytes(payload)
    study, sample_records, report = reconstruct_study(dataset, samples_to_rows(samples))
    readiness = assess_study_benchmark_readiness(study, dataset, sample_records)
    return GeoReconstructionBundle(
        dataset=dataset,
        study=study,
        samples=tuple(sample_records),
        report=report,
        source_digest=source_digest,
        source_url=client.geo_family_soft_url(accession),
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        payload_bytes=len(payload),
        benchmark_readiness=readiness,
    )


def write_geo_bundle(bundle: GeoReconstructionBundle, directory: str | Path) -> None:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / "dataset.json").write_text(json.dumps(bundle.dataset.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "study.json").write_text(json.dumps(bundle.study.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (target / "samples.jsonl").open("w", encoding="utf-8") as handle:
        for sample in bundle.samples:
            handle.write(json.dumps(sample.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    (target / "report.json").write_text(json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    acquisition = {
        "accession": bundle.dataset.accession,
        "repository": bundle.dataset.repository,
        "source_url": bundle.source_url,
        "retrieved_at_utc": bundle.retrieved_at_utc,
        "payload_bytes": bundle.payload_bytes,
        "sha256": bundle.source_digest,
        "parser_version": bundle.parser_version,
        "benchmark_ready": bundle.benchmark_readiness.ready,
        "benchmark_missing": list(bundle.benchmark_readiness.missing),
    }
    (target / "acquisition.json").write_text(json.dumps(acquisition, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reconstruct_geo_accession(client: NcbiClient, accession: str, summary: dict[str, object] | None = None) -> GeoReconstructionBundle:
    accession = accession.strip().upper()
    ids = client.esearch("gds", accession, retmax=1) if summary is None else []
    if summary is None:
        lookup = client.esummary("gds", ids)
        summary = next((value for key, value in lookup.items() if key != "uids" and isinstance(value, dict)), {})
    dataset = geo_summary_to_dataset(summary)
    dataset.accession = accession
    dataset.id = f"dataset:geo:{accession}"
    return reconstruct_geo_series(client, dataset)
