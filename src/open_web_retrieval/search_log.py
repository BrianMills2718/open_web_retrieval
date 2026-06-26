"""Persistent SQLite log for search calls.

Records every provider search (query, provider, result count, latency, trace)
so search activity is queryable without llm_client or an external logger.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_calls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,
    query       TEXT    NOT NULL,
    provider    TEXT    NOT NULL,
    num_results INTEGER,
    latency_ms  INTEGER,
    trace_id    TEXT,
    task        TEXT,
    error       TEXT,
    top_sources TEXT
);
CREATE INDEX IF NOT EXISTS idx_search_calls_timestamp ON search_calls (timestamp);
CREATE INDEX IF NOT EXISTS idx_search_calls_provider  ON search_calls (provider);
CREATE INDEX IF NOT EXISTS idx_search_calls_trace_id  ON search_calls (trace_id);
"""


class SearchLog:
    """Append-only SQLite log for open_web_retrieval search calls.

    Thread-safe: uses check_same_thread=False with WAL mode.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def log_search(
        self,
        *,
        timestamp: str,
        query: str,
        provider: str,
        num_results: int | None = None,
        latency_ms: int | None = None,
        trace_id: str | None = None,
        task: str | None = None,
        error: str | None = None,
        top_sources: list[str] | None = None,
    ) -> None:
        """Append one search call record."""
        self._conn.execute(
            """
            INSERT INTO search_calls
                (timestamp, query, provider, num_results, latency_ms,
                 trace_id, task, error, top_sources)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                query,
                provider,
                num_results,
                latency_ms,
                trace_id,
                task,
                error,
                json.dumps(top_sources) if top_sources else None,
            ),
        )
        self._conn.commit()

    def query_recent(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return the most recent search calls as plain dicts."""
        cur = self._conn.execute(
            """
            SELECT id, timestamp, query, provider, num_results, latency_ms,
                   trace_id, task, error, top_sources
            FROM search_calls
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        rows = []
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            if d.get("top_sources"):
                d["top_sources"] = json.loads(d["top_sources"])
            rows.append(d)
        return rows

    def stats(self) -> dict[str, Any]:
        """Return aggregate counts: total calls, per-provider, per-task."""
        total = self._conn.execute("SELECT COUNT(*) FROM search_calls").fetchone()[0]
        per_provider = {
            row[0]: row[1]
            for row in self._conn.execute(
                "SELECT provider, COUNT(*) FROM search_calls GROUP BY provider ORDER BY COUNT(*) DESC"
            ).fetchall()
        }
        errors = self._conn.execute(
            "SELECT COUNT(*) FROM search_calls WHERE error IS NOT NULL"
        ).fetchone()[0]
        return {"total": total, "per_provider": per_provider, "errors": errors}

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SearchLog:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


__all__ = ["SearchLog"]
