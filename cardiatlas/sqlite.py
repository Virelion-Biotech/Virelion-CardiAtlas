from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .graph import AtlasGraph, Relation
from .models import Record
from .release import create_manifest
from .schema import SCHEMA_VERSION


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
            """
        )
        self._connection.commit()

    def upsert(self, record: Record) -> None:
        payload = json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False)
        self._connection.execute(
            "INSERT INTO records(id, record_type, name, payload) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET record_type=excluded.record_type, name=excluded.name, payload=excluded.payload",
            (record.id, record.record_type, record.name, payload),
        )
        self._connection.commit()

    def upsert_many(self, records: Iterable[Record]) -> int:
        rows = [(record.id, record.record_type, record.name, json.dumps(record.to_dict(), sort_keys=True, ensure_ascii=False)) for record in records]
        self._connection.executemany(
            "INSERT INTO records(id, record_type, name, payload) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET record_type=excluded.record_type, name=excluded.name, payload=excluded.payload",
            rows,
        )
        self._connection.commit()
        return len(rows)

    def put_relation(self, relation: Relation) -> None:
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

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteAtlasStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
