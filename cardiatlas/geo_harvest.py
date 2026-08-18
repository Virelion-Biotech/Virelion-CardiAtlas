from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .adapters import geo_summary_to_dataset
from .geo_reconstruct import ReconstructionReport, reconstruct_study
from .geo_soft import parse_geo_soft_bytes, samples_to_rows
from .models import DatasetRecord, SampleRecord, StudyRecord
from .ncbi import NcbiClient


@dataclass(frozen=True, slots=True)
class GeoReconstructionBundle:
    dataset: DatasetRecord
    study: StudyRecord
    samples: tuple[SampleRecord, ...]
    report: ReconstructionReport
    source_digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset.to_dict(),
            "study": self.study.to_dict(),
            "sample_count": len(self.samples),
            "report": self.report.to_dict(),
            "source_digest": self.source_digest,
        }


def reconstruct_geo_series(client: NcbiClient, dataset: DatasetRecord) -> GeoReconstructionBundle:
    payload = client.fetch_geo_family_soft(dataset.accession)
    source_digest = hashlib.sha256(payload).hexdigest()
    samples = parse_geo_soft_bytes(payload)
    study, sample_records, report = reconstruct_study(dataset, samples_to_rows(samples))
    return GeoReconstructionBundle(dataset, study, tuple(sample_records), report, source_digest)


def write_geo_bundle(bundle: GeoReconstructionBundle, directory: str | Path) -> None:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    (target / "dataset.json").write_text(json.dumps(bundle.dataset.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "study.json").write_text(json.dumps(bundle.study.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (target / "samples.jsonl").open("w", encoding="utf-8") as handle:
        for sample in bundle.samples:
            handle.write(json.dumps(sample.to_dict(), sort_keys=True, ensure_ascii=False) + "\n")
    (target / "report.json").write_text(json.dumps(bundle.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def reconstruct_geo_accession(client: NcbiClient, accession: str, summary: dict[str, object] | None = None) -> GeoReconstructionBundle:
    accession = accession.strip().upper()
    if summary is None:
        ids = client.esearch("gds", accession, retmax=1)
        lookup = client.esummary("gds", ids)
        summary = next((value for key, value in lookup.items() if key != "uids" and isinstance(value, dict)), {})
    dataset = geo_summary_to_dataset(summary)
    dataset.accession = accession
    dataset.id = f"dataset:geo:{accession}"
    return reconstruct_geo_series(client, dataset)
