"""Actual installed-wheel persistence, lifecycle and CLI smoke outside checkout."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys

import cardiatlas
from cardiatlas.graph import Relation
from cardiatlas.models import DatasetRecord, EvidenceRecord
from cardiatlas.release_lifecycle import create_draft, promote_to_candidate, verify
from cardiatlas.sqlite import SQLiteAtlasStore

assert cardiatlas.__version__ == "0.9.0"
assert "site-packages" in str(Path(cardiatlas.__file__).resolve())
with TemporaryDirectory() as directory:
    path = str(Path(directory) / "atlas.sqlite")
    with SQLiteAtlasStore(path) as store:
        evidence = EvidenceRecord(
            id="e", name="cardiac evidence", source_type="pubmed", source_identifier="1"
        )
        dataset = DatasetRecord(id="d", name="cardiac dataset", accession="GSE1", evidence_ids=["e"])
        store.upsert_many([evidence, dataset])
        store.put_relation(Relation("d", "derived_from", "e", ("e",), 0.9))
        records, relations = store.all_records(), store.graph().relations()
        draft = create_draft(records, "wheel", relations)
        candidate = promote_to_candidate(draft, records, relations)
        verified = verify(candidate, records, relations, commit_sha="wheel-smoke", ci_passed=True)
        store.save_release_record(verified)
    with SQLiteAtlasStore(path) as store:
        assert store.get_release_record("wheel").state == "verified"
        assert store.get_release_record("wheel").relationship_digest == verified.relationship_digest
        assert store.count() == 2
    completed = subprocess.run(
        [sys.executable, "-m", "cardiatlas", "search", path, "cardiac"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)
    completed = subprocess.run(
        [sys.executable, "-m", "cardiatlas", "corpus", "--db", path],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout)["record_count"] == 2
print("Installed-wheel persistence, graph-locked lifecycle and real CLI passed")
