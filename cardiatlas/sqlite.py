from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .claims import ClaimStore
from .graph import AtlasGraph, Relation
from .loader import record_from_dict
from .models import Record
from .registry import AtlasRegistry
from .release import create_manifest
from .release_lifecycle import ReleaseRecord, release_record_from_dict
from .schema import SCHEMA_VERSION
from .validation import require_valid
from .service import AtlasService


class SQLiteAtlasStore:
    """Persistent backend for records, graph edges, and release metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                record_type TEXT NOT NULL,
                name TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_records_type ON records(record_type);
            CREATE INDEX IF NOT EXISTS idx_records_name ON records(name);
            CREATE TABLE IF NOT EXISTS relations (
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY(subject, predicate, object_id)
            );
            CREATE INDEX IF NOT EXISTS idx_relations_subject ON relations(subject);
            CREATE INDEX IF NOT EXISTS idx_relations_object ON relations(object_id);
            CREATE TABLE IF NOT EXISTS releases (
                version TEXT PRIMARY KEY,
                manifest TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS release_lifecycle (
                version TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_release_lifecycle_state ON release_lifecycle(state);
            """
        )
        self._connection.commit()

    def upsert(self, record: Record) -> None:
        require_valid(record)
        payload = json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False)
        self._connection.execute(
            "INSERT INTO records(id, record_type, name, payload) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET record_type=excluded.record_type, name=excluded.name, payload=excluded.payload",
            (record.id, record.record_type, record.name, payload),
        )
        self._connection.commit()

    def upsert_many(self, records: Iterable[Record]) -> int:
        records = [require_valid(record) for record in records]
        rows = [(record.id, record.record_type, record.name, json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False)) for record in records]
        self._connection.executemany(
            "INSERT INTO records(id, record_type, name, payload) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET record_type=excluded.record_type, name=excluded.name, payload=excluded.payload",
            rows,
        )
        self._connection.commit()
        return len(rows)

    def put_relation(self, relation: Relation) -> None:
        AtlasGraph([relation])  # validate before any persistent mutation
        # Mirror AtlasGraph.add()'s merge semantics: a relation persisted twice
        # for the same (subject, predicate, object) should accumulate evidence
        # rather than have the later write silently discard the earlier one.
        existing_row = self._connection.execute(
            "SELECT payload FROM relations WHERE subject=? AND predicate=? AND object_id=?",
            (relation.subject, relation.predicate, relation.object),
        ).fetchone()
        if existing_row is not None:
            existing = json.loads(existing_row["payload"])
            merged_evidence = tuple(dict.fromkeys(tuple(existing.get("evidence_ids", ())) + relation.evidence_ids))
            relation = Relation(
                relation.subject,
                relation.predicate,
                relation.object,
                merged_evidence,
                relation.confidence if relation.confidence is not None else existing.get("confidence"),
                relation.source or existing.get("source"),
            )
        payload = json.dumps(relation.to_dict(), sort_keys=True, ensure_ascii=False)
        self._connection.execute(
            "INSERT INTO relations(subject,predicate,object_id,payload) VALUES(?,?,?,?) "
            "ON CONFLICT(subject,predicate,object_id) DO UPDATE SET payload=excluded.payload",
            (relation.subject, relation.predicate, relation.object, payload),
        )
        self._connection.commit()

    def relations_for(self, node_id: str) -> list[dict]:
        rows = self._connection.execute(
            "SELECT payload FROM relations WHERE subject=? OR object_id=? ORDER BY subject,predicate,object_id",
            (node_id, node_id),
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def all_relations(self) -> list[dict]:
        rows = self._connection.execute("SELECT payload FROM relations ORDER BY subject,predicate,object_id").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def graph(self) -> AtlasGraph:
        relations = []
        for payload in self.all_relations():
            relations.append(Relation(
                subject=payload["subject"],
                predicate=payload["predicate"],
                object=payload["object"],
                evidence_ids=tuple(payload.get("evidence_ids", ())),
                confidence=payload.get("confidence"),
                source=payload.get("source"),
            ))
        return AtlasGraph(relations)

    def get_payload(self, record_id: str) -> dict | None:
        row = self._connection.execute("SELECT payload FROM records WHERE id=?", (record_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def all_payloads(self, record_type: str | None = None) -> list[dict]:
        if record_type is None:
            rows = self._connection.execute("SELECT payload FROM records ORDER BY id").fetchall()
        else:
            rows = self._connection.execute("SELECT payload FROM records WHERE record_type=? ORDER BY id", (record_type,)).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def all_records(self, record_type: str | None = None) -> list[Record]:
        """Reconstruct typed Record objects for every stored payload.

        Use this (rather than all_payloads()) whenever code needs to reason
        about record types -- e.g. staging or transitioning a release, which
        needs isinstance checks against DatasetRecord/StudyRecord/etc.
        """
        return [record_from_dict(payload) for payload in self.all_payloads(record_type)]

    def delete(self, record_id: str) -> bool:
        cursor = self._connection.execute("DELETE FROM records WHERE id=?", (record_id,))
        self._connection.commit()
        return cursor.rowcount > 0

    def count(self, record_type: str | None = None) -> int:
        if record_type is None:
            row = self._connection.execute("SELECT COUNT(*) AS n FROM records").fetchone()
        else:
            row = self._connection.execute("SELECT COUNT(*) AS n FROM records WHERE record_type=?", (record_type,)).fetchone()
        return int(row["n"])

    def save_release(self, records: Iterable[Record], version: str, schema_version: str = SCHEMA_VERSION) -> dict:
        manifest = create_manifest(records, version, schema_version).to_dict()
        self._connection.execute(
            "INSERT OR REPLACE INTO releases(version, manifest) VALUES(?, ?)",
            (version, json.dumps(manifest, sort_keys=True)),
        )
        self._connection.commit()
        return manifest

    def release(self, version: str) -> dict | None:
        row = self._connection.execute("SELECT manifest FROM releases WHERE version=?", (version,)).fetchone()
        return json.loads(row["manifest"]) if row else None

    def save_release_record(self, release: ReleaseRecord) -> None:
        """Persist a full release-lifecycle record (release_lifecycle.ReleaseRecord).

        Distinct from save_release()/release() above, which store a bare
        manifest snapshot: this stores the manifest plus its lifecycle state,
        readiness, and transition history, keyed by the same version string.
        """
        payload = json.dumps(release.to_dict(), sort_keys=True, ensure_ascii=False)
        self._connection.execute(
            "INSERT INTO release_lifecycle(version, state, payload) VALUES(?,?,?) "
            "ON CONFLICT(version) DO UPDATE SET state=excluded.state, payload=excluded.payload",
            (release.manifest.version, release.state, payload),
        )
        self._connection.commit()

    def get_release_record(self, version: str) -> ReleaseRecord | None:
        row = self._connection.execute("SELECT payload FROM release_lifecycle WHERE version=?", (version,)).fetchone()
        return release_record_from_dict(json.loads(row["payload"])) if row else None

    def list_release_records(self, state: str | None = None) -> list[dict]:
        if state is None:
            rows = self._connection.execute("SELECT payload FROM release_lifecycle ORDER BY version").fetchall()
        else:
            rows = self._connection.execute("SELECT payload FROM release_lifecycle WHERE state=? ORDER BY version", (state,)).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def close(self) -> None:
        self._connection.close()

    def load_service(self, claims: ClaimStore | None = None) -> AtlasService:
        """Build a fully-featured, in-memory AtlasService from everything persisted here.

        Bridges the two halves of the library that otherwise don't know
        about each other: AtlasService (search/retrieve/context/reconstruct/
        release-readiness/etc., all pure and in-memory) and SQLiteAtlasStore
        (durable storage). This is what lets the CLI accumulate a real,
        queryable knowledge base across separate invocations instead of
        starting from nothing every time.
        """
        registry = AtlasRegistry()
        for record in self.all_records():
            registry.upsert(record)
        return AtlasService(registry, self.graph(), claims or ClaimStore())

    def save_service(self, service: AtlasService) -> int:
        """Persist everything currently in an AtlasService's registry and graph.

        Returns the number of records written. Existing records/relations
        with the same identity are updated in place (see upsert_many() and
        put_relation()'s merge semantics), so calling this repeatedly against
        the same service is safe and idempotent.
        """
        count = self.upsert_many(service.registry.all())
        for relation in service.graph.relations():
            self.put_relation(relation)
        return count

    def __enter__(self) -> "SQLiteAtlasStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
