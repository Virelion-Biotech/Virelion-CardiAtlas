from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class GeoSoftSample:
    accession: str
    fields: dict[str, str]
    characteristics: dict[str, str]
    raw: dict[str, str]

    def to_row(self) -> dict[str, object]:
        row: dict[str, object] = {
            "accession": self.accession,
            "name": self.fields.get("Sample_title", self.accession),
            "species": self.fields.get("Sample_organism_ch1", ""),
            "tissue": self.fields.get("Sample_source_name_ch1", ""),
            "platform": self.fields.get("Sample_platform_id", ""),
            "library_strategy": self.fields.get("Sample_library_strategy", ""),
            "molecule": self.fields.get("Sample_molecule_ch1", ""),
            "cell_type": self.fields.get("Sample_characteristics_ch1", ""),
        }
        row.update(self.characteristics)
        row["geo_accession"] = self.accession
        row["raw_fields"] = dict(self.raw)
        return row


def _parse_assignment(line: str) -> tuple[str, str] | None:
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    return key.strip(), value.strip()


def _characteristic_value(key: str, value: str) -> tuple[str, str] | None:
    if not key.startswith("Sample_characteristics_ch1"):
        return None
    if ":" in value:
        field, content = value.split(":", 1)
    else:
        field, content = "characteristic", value
    field = re.sub(r"[^A-Za-z0-9]+", "_", field.strip().lower()).strip("_")
    content = content.strip()
    if not field or not content:
        return None
    aliases = {
        "condition": "condition",
        "group": "condition",
        "disease": "condition",
        "phenotype": "condition",
        "treatment": "treatment",
        "timepoint": "timepoint",
        "time_point": "timepoint",
        "post_injury": "timepoint",
        "dpi": "timepoint",
        "day": "timepoint",
        "days_post_injury": "timepoint",
        "region": "region",
        "heart_region": "region",
        "zone": "region",
        "tissue": "tissue",
        "subject": "subject_id",
        "subject_id": "subject_id",
        "animal": "animal_id",
        "animal_id": "animal_id",
        "donor": "donor_id",
        "donor_id": "donor_id",
        "replicate": "replicate_group",
    }
    return aliases.get(field, field), content


def parse_geo_soft(text: str) -> list[GeoSoftSample]:
    """Parse the sample metadata portion of a GEO family SOFT file.

    Expression matrices and platform tables are intentionally ignored. The
    parser only retains sample-level metadata required for reconstruction.
    """
    samples: list[GeoSoftSample] = []
    current_accession: str | None = None
    fields: dict[str, str] = {}
    characteristics: dict[str, str] = {}
    raw: dict[str, str] = {}

    def flush() -> None:
        nonlocal current_accession, fields, characteristics, raw
        if current_accession:
            samples.append(GeoSoftSample(current_accession, dict(fields), dict(characteristics), dict(raw)))
        current_accession = None
        fields = {}
        characteristics = {}
        raw = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("^PLATFORM") or line.startswith("^SERIES"):
            continue
        if line.startswith("^SAMPLE"):
            flush()
            accession = line.split("=", 1)[-1].strip()
            current_accession = accession
            continue
        if not current_accession:
            continue
        parsed = _parse_assignment(line)
        if not parsed:
            continue
        key, value = parsed
        if key.startswith("!Sample_characteristics_ch1"):
            parsed_characteristic = _characteristic_value(key, value)
            if parsed_characteristic:
                char_key, char_value = parsed_characteristic
                characteristics.setdefault(char_key, char_value)
        elif key.startswith("!Sample_"):
            clean_key = key[len("!Sample_"):]
            fields.setdefault(f"Sample_{clean_key}", value)
        raw[key] = value
    flush()
    return samples


def parse_geo_soft_bytes(payload: bytes, *, gzip_compressed: bool = False) -> list[GeoSoftSample]:
    data = gzip.decompress(payload) if gzip_compressed else payload
    return parse_geo_soft(data.decode("utf-8", errors="replace"))


def samples_to_rows(samples: Iterable[GeoSoftSample]) -> list[dict[str, object]]:
    return [sample.to_row() for sample in samples]
