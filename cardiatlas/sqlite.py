from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import AtlasRecord, Record


class SQLiteAtlasStore:
    """Simple persistent backend for Atlas records and graph edges."""

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
            CREATE TABLE IF NOT EXISTS relations (
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY(subject, predicate, object_id)
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

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteAtlasStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
