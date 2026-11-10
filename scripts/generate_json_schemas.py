"""Regenerate schemas/*_record.schema.json from the cardiatlas.models dataclasses.

These JSON Schema files are CardiAtlas's published, language-agnostic
contract for the 8 record types (docs/integration-contracts.md) -- other
Virelion-HeartTwin member repos, potentially written in other languages,
validate against them instead of importing cardiatlas.models directly.

They were found to have drifted: they described schema_version "0.2" and
were missing every field the 0.2 -> 0.3 migration added (cardiatlas/migrate.py),
plus the common AtlasRecord base fields (description, source_ids, tags,
metadata, schema_version). This script regenerates them from the actual
current dataclasses so the two can't silently drift apart again -- run it
whenever a record dataclass changes, and tests/test_schema_sync.py fails
loudly in CI if someone forgets to.

Usage: python scripts/generate_json_schemas.py [--check]
  --check: exit 1 if regenerating would change any file, without writing.
"""
from __future__ import annotations

import dataclasses
import json
import sys
import types
import typing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cardiatlas import models  # noqa: E402
from cardiatlas.therapeutic_products import (  # noqa: E402
    ManufacturingProfile, PotencyAssay, ProductRegulatoryRecord, TherapeuticProductRecord,
)

REPO = "https://virelion-biotech.github.io/Virelion-CardiAtlas/schemas"

_MODEL_FOR_STEM = {
    "evidence_record": models.EvidenceRecord,
    "marker_record": models.MarkerRecord,
    "phenotype_record": models.PhenotypeRecord,
    "cell_state_record": models.CellStateRecord,
    "dataset_record": models.DatasetRecord,
    "study_record": models.StudyRecord,
    "sample_record": models.SampleRecord,
    "intervention_record": models.InterventionRecord,
    "therapeutic_product_record": TherapeuticProductRecord,
}

_TITLE_FOR_STEM = {
    "evidence_record": "CardiAtlas Evidence Record",
    "marker_record": "CardiAtlas Marker Record",
    "phenotype_record": "CardiAtlas Phenotype Record",
    "cell_state_record": "CardiAtlas Cell State Record",
    "dataset_record": "CardiAtlas Dataset Record",
    "study_record": "CardiAtlas Study Record",
    "sample_record": "CardiAtlas Sample Record",
    "intervention_record": "CardiAtlas Intervention Record",
    "therapeutic_product_record": "CardiAtlas Therapeutic Product Evidence Record",
}


def _literal_values(tp: typing.Any) -> list[typing.Any] | None:
    if typing.get_origin(tp) is typing.Literal:
        return list(typing.get_args(tp))
    return None


def _type_schema(tp: typing.Any) -> dict[str, typing.Any]:
    origin = typing.get_origin(tp)

    if tp is type(None):
        return {"type": "null"}

    literal_values = _literal_values(tp)
    if literal_values is not None:
        return {"enum": list(literal_values)}

    if origin is typing.Union or origin is types.UnionType:
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        nullable = type(None) in typing.get_args(tp)
        if len(args) == 1:
            schema = _type_schema(args[0])
            if nullable:
                if "enum" in schema:
                    schema = {"enum": schema["enum"] + [None]}
                elif isinstance(schema.get("type"), str):
                    schema = {**schema, "type": [schema["type"], "null"]}
            return schema
        # Multiple non-None members: fall back to anyOf.
        variants = [_type_schema(a) for a in args]
        if nullable:
            variants.append({"type": "null"})
        return {"anyOf": variants}

    if origin in (list, typing.List):
        (item_type,) = typing.get_args(tp) or (str,)
        return {"type": "array", "items": _type_schema(item_type)}

    if origin in (dict, typing.Dict):
        return {"type": "object"}

    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is typing.Any:
        return {}
    return {}


def schema_for(stem: str) -> dict[str, typing.Any]:
    cls = _MODEL_FOR_STEM[stem]
    hints = typing.get_type_hints(cls, include_extras=False)
    properties: dict[str, typing.Any] = {}
    required: list[str] = []
    for f in dataclasses.fields(cls):
        tp = hints.get(f.name, typing.Any)
        if f.name == "record_type":
            properties[f.name] = {"const": f.default}
            required.append(f.name)
            continue
        properties[f.name] = _type_schema(tp)
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING and f.init:  # type: ignore[misc]
            required.append(f.name)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{REPO}/{stem}.schema.json",
        "title": _TITLE_FOR_STEM[stem],
        "type": "object",
        "required": required,
        "properties": dict(sorted(properties.items())),
    }



def _dataclass_required_fields(cls: type) -> set[str]:
    return {
        item.name for item in dataclasses.fields(cls)
        if item.init and item.default is dataclasses.MISSING
        and item.default_factory is dataclasses.MISSING
    }


def validate_therapeutic_product_schema(schema: dict[str, typing.Any]) -> list[str]:
    """Check the detailed public product schema against every Python dataclass field.

    The product schema retains hand-authored descriptions and stricter constraints;
    this check prevents top-level or nested dataclass fields and Literal enums drifting.
    """
    errors: list[str] = []
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("wrong JSON Schema dialect")
    if schema.get("$id") != f"{REPO}/therapeutic_product.schema.json":
        errors.append("wrong $id")
    expected = {
        "therapeutic_product_record": TherapeuticProductRecord,
    }
    for stem, cls in expected.items():
        props = schema.get("properties", {})
        model_names = {f.name for f in dataclasses.fields(cls)}
        if set(props) != model_names:
            errors.append(f"{stem}: top-level properties differ from model fields")
        if set(schema.get("required", [])) != _dataclass_required_fields(cls):
            errors.append(f"{stem}: required fields differ from model defaults")
    nested = {
        "manufacturing": ManufacturingProfile,
        "potency_assays.items": PotencyAssay,
        "regulatory_records.items": ProductRegulatoryRecord,
    }
    for path, cls in nested.items():
        node: typing.Any = schema.get("properties", {})
        for part in path.split("."):
            node = node.get(part, {}) if isinstance(node, dict) else {}
            if part == "items" and isinstance(node, dict):
                continue
        props = node.get("properties", {}) if isinstance(node, dict) else {}
        model_names = {f.name for f in dataclasses.fields(cls)}
        if set(props) != model_names:
            errors.append(f"{path}: properties differ from {cls.__name__} fields")
        if set(node.get("required", [])) != _dataclass_required_fields(cls):
            errors.append(f"{path}: required fields differ from model defaults")
    literal_fields = {
        "modality": typing.get_type_hints(TherapeuticProductRecord)["modality"],
        "manufacturing.autologous_or_allogeneic": typing.get_type_hints(ManufacturingProfile)["autologous_or_allogeneic"],
        "potency_assays.items.status": typing.get_type_hints(PotencyAssay)["status"],
        "regulatory_records.items.status": typing.get_type_hints(ProductRegulatoryRecord)["status"],
    }
    for path, annotation in literal_fields.items():
        node: typing.Any = schema.get("properties", {})
        for part in path.split("."):
            node = node.get(part, {}) if isinstance(node, dict) else {}
            if part == "items" and isinstance(node, dict):
                continue
        expected_values = list(typing.get_args(annotation))
        if not isinstance(node, dict) or node.get("enum") != expected_values:
            errors.append(f"{path}: enum differs from Python Literal values")
    return errors


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    root = Path(__file__).resolve().parents[1] / "schemas"
    changed: list[str] = []
    for stem in sorted(_MODEL_FOR_STEM):
        if stem == "therapeutic_product_record":
            continue  # Rich hand-authored schema is structurally checked below.
        target = root / f"{stem}.schema.json"
        rendered = json.dumps(schema_for(stem), indent=2, sort_keys=False) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") == rendered:
            continue
        changed.append(str(target))
        if not check_only:
            target.write_text(rendered, encoding="utf-8")
    product_schema_path = root / "therapeutic_product.schema.json"
    if product_schema_path.exists():
        product_schema = json.loads(product_schema_path.read_text(encoding="utf-8"))
        errors = validate_therapeutic_product_schema(product_schema)
        if errors:
            changed.extend(f"{product_schema_path}: {error}" for error in errors)
    else:
        changed.append(str(product_schema_path))
    if check_only and changed:
        print("out of sync with cardiatlas.models:")
        for path in changed:
            print(f"  {path}")
        return 1
    if not check_only:
        for path in changed:
            print(f"wrote {path}")
        if not changed:
            print("all record schemas already in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
