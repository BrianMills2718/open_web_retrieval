"""open_web_retrieval workbench backend.

Read-only FastAPI server over ~/projects/data/owr_search_log.db.
Configure DB path with OWR_SEARCH_LOG_DB env var.

Start:
    cd workbench/backend
    uvicorn server:app --host 0.0.0.0 --port 5205 --reload
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DEFAULT_DB = Path.home() / "projects/data/owr_search_log.db"
DB_PATH = Path(os.environ.get("OWR_SEARCH_LOG_DB", str(DEFAULT_DB)))

app = FastAPI(title="open_web_retrieval Search Activity")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _con() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Search log not found: {DB_PATH}")
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)


# ── Response models ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    db_path: str
    db_exists: bool
    total_calls: int = 0


class ProviderStat(BaseModel):
    provider: str = Field(description="Provider name: brave|exa|tavily|searxng")
    calls: int
    avg_latency_ms: Optional[float] = Field(description="Average latency in milliseconds")
    errors: int


class SearchCallRow(BaseModel):
    id: int
    timestamp: str
    query: str
    provider: str
    num_results: Optional[int] = None
    latency_ms: Optional[int] = None
    trace_id: Optional[str] = None
    task: Optional[str] = None
    error: Optional[str] = None
    top_sources: Optional[list[str]] = None


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health() -> HealthResponse:
    """Liveness + DB status."""
    exists = DB_PATH.exists()
    total = 0
    if exists:
        try:
            con = _con()
            total = con.execute("SELECT COUNT(*) FROM search_calls").fetchone()[0]
            con.close()
        except Exception:
            pass
    return HealthResponse(
        status="ok",
        db_path=str(DB_PATH),
        db_exists=exists,
        total_calls=total,
    )


@app.get("/api/stats")
def stats() -> list[ProviderStat]:
    """Per-provider call counts, average latency, and error counts."""
    con = _con()
    try:
        rows = con.execute(
            """
            SELECT provider,
                   COUNT(*) AS calls,
                   ROUND(AVG(latency_ms), 1) AS avg_latency_ms,
                   SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) AS errors
            FROM search_calls
            GROUP BY provider
            ORDER BY calls DESC
            """
        ).fetchall()
        return [
            ProviderStat(
                provider=r[0],
                calls=r[1],
                avg_latency_ms=r[2],
                errors=r[3],
            )
            for r in rows
        ]
    finally:
        con.close()


@app.get("/api/calls/recent")
def calls_recent(
    limit: int = Query(default=200, ge=1, le=1000),
    provider: Optional[str] = Query(default=None),
    trace_id: Optional[str] = Query(default=None),
    has_error: bool = Query(default=False),
) -> list[SearchCallRow]:
    """Recent search calls with optional filters."""
    import json as _json

    con = _con()
    try:
        clauses: list[str] = []
        params: list = []

        if provider:
            clauses.append("provider = ?")
            params.append(provider)
        if trace_id:
            clauses.append("trace_id = ?")
            params.append(trace_id)
        if has_error:
            clauses.append("error IS NOT NULL")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        rows = con.execute(
            f"""
            SELECT id, timestamp, query, provider, num_results, latency_ms,
                   trace_id, task, error, top_sources
            FROM search_calls
            {where}
            ORDER BY id DESC
            LIMIT ?
            """,
            params,
        ).fetchall()

        result = []
        for r in rows:
            top = None
            if r[9]:
                try:
                    top = _json.loads(r[9])
                except Exception:
                    pass
            result.append(
                SearchCallRow(
                    id=r[0],
                    timestamp=r[1],
                    query=r[2],
                    provider=r[3],
                    num_results=r[4],
                    latency_ms=r[5],
                    trace_id=r[6],
                    task=r[7],
                    error=r[8],
                    top_sources=top,
                )
            )
        return result
    finally:
        con.close()


@app.get("/api/calls/{call_id}")
def get_call(call_id: int) -> SearchCallRow:
    """Single search call by ID."""
    import json as _json
    from fastapi import HTTPException

    con = _con()
    try:
        r = con.execute(
            "SELECT id, timestamp, query, provider, num_results, latency_ms, trace_id, task, error, top_sources FROM search_calls WHERE id = ?",
            (call_id,),
        ).fetchone()
        if not r:
            raise HTTPException(404, f"No call with id {call_id}")
        top = None
        if r[9]:
            try:
                top = _json.loads(r[9])
            except Exception:
                pass
        return SearchCallRow(
            id=r[0], timestamp=r[1], query=r[2], provider=r[3],
            num_results=r[4], latency_ms=r[5], trace_id=r[6],
            task=r[7], error=r[8], top_sources=top,
        )
    finally:
        con.close()
