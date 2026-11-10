import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("generate_json_schemas", ROOT / "scripts" / "generate_json_schemas.py")
generate_json_schemas = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate_json_schemas)  # type: ignore[union-attr]


def test_checked_in_schemas_match_current_models():
    """Regression test for schema/model drift: the checked-in schemas/*.json
    files were found describing schema_version "0.2" (missing every field
    the 0.2 -> 0.3 migration added, plus the AtlasRecord base fields) while
    cardiatlas.models had long since moved on. This fails loudly instead of
    letting that happen silently again -- run
    `python scripts/generate_json_schemas.py` to fix it.
    """
    stale = []
    for stem in sorted(generate_json_schemas._MODEL_FOR_STEM):
        if stem == "therapeutic_product_record":
            continue
        path = ROOT / "schemas" / f"{stem}.schema.json"
        expected = json.loads(json.dumps(generate_json_schemas.schema_for(stem)))
        actual = json.loads(path.read_text(encoding="utf-8"))
        if actual != expected:
            stale.append(stem)
    assert not stale, f"schemas out of sync with models, regenerate with scripts/generate_json_schemas.py: {stale}"


def test_therapeutic_product_schema_matches_nested_models():
    schema = json.loads((ROOT / "schemas" / "therapeutic_product.schema.json").read_text(encoding="utf-8"))
    assert generate_json_schemas.validate_therapeutic_product_schema(schema) == []


def test_generated_schema_covers_every_model_field():
    for stem, cls in generate_json_schemas._MODEL_FOR_STEM.items():
        schema = generate_json_schemas.schema_for(stem)
        model_field_names = {f.name for f in __import__("dataclasses").fields(cls)}
        assert set(schema["properties"]) == model_field_names, stem
        assert {"id", "record_type", "name"} <= set(schema["required"]), stem

def test_therapeutic_product_schema_detects_nested_literal_enum_drift():
    """Nested Literal checks must descend through JSON Schema properties and array items."""
    import copy

    original = json.loads((ROOT / "schemas" / "therapeutic_product.schema.json").read_text(encoding="utf-8"))
    cases = {
        "manufacturing.autologous_or_allogeneic": ["autologous", "unknown"],
        "potency_assays.items.status": ["not_reported", "expert_reviewed"],
        "regulatory_records.items.status": ["preclinical", "unknown"],
    }
    for path, wrong_values in cases.items():
        schema = copy.deepcopy(original)
        node = schema
        for part in path.split("."):
            if part == "items":
                node = node["items"]
            else:
                node = node["properties"][part]
        node["enum"] = wrong_values
        errors = generate_json_schemas.validate_therapeutic_product_schema(schema)
        assert f"{path}: enum differs from Python Literal values" in errors

