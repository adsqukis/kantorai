import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from .models import Analysis, RawData, ReporterResult, RunSummary, Summary

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_date TEXT UNIQUE NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  summary_json TEXT
);
CREATE TABLE IF NOT EXISTS raw(run_id INTEGER NOT NULL, source_id TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reporters(
  run_id INTEGER NOT NULL, source_id TEXT NOT NULL, status TEXT NOT NULL,
  report_json TEXT, error TEXT, attempts INTEGER NOT NULL, mismatches_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analyses(run_id INTEGER NOT NULL, json TEXT);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(path: str) -> sqlite3.Connection:
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def start_run(conn: sqlite3.Connection, run_date: date) -> int:
    with conn:
        old = conn.execute("SELECT id FROM runs WHERE run_date=?", (run_date.isoformat(),)).fetchone()
        if old:
            for t in ("raw", "reporters", "analyses"):
                conn.execute(f"DELETE FROM {t} WHERE run_id=?", (old["id"],))
            conn.execute("DELETE FROM runs WHERE id=?", (old["id"],))
        cur = conn.execute(
            "INSERT INTO runs(run_date, started_at, status) VALUES(?,?,?)",
            (run_date.isoformat(), _now(), "BERJALAN"),
        )
        return cur.lastrowid


def save_raw(conn: sqlite3.Connection, run_id: int, raw: RawData) -> None:
    with conn:
        conn.execute("DELETE FROM raw WHERE run_id=? AND source_id=?", (run_id, raw.source_id))
        conn.execute("INSERT INTO raw VALUES(?,?,?)", (run_id, raw.source_id, raw.model_dump_json()))


def save_reporter(conn: sqlite3.Connection, run_id: int, r: ReporterResult) -> None:
    with conn:
        conn.execute("DELETE FROM reporters WHERE run_id=? AND source_id=?", (run_id, r.source_id))
        conn.execute(
            "INSERT INTO reporters VALUES(?,?,?,?,?,?,?)",
            (
                run_id, r.source_id, r.status,
                r.report.model_dump_json() if r.report else None,
                r.error, r.attempts, json.dumps(r.mismatches),
            ),
        )


def save_analysis(conn: sqlite3.Connection, run_id: int, a: Analysis | None) -> None:
    with conn:
        conn.execute("DELETE FROM analyses WHERE run_id=?", (run_id,))
        conn.execute("INSERT INTO analyses VALUES(?,?)", (run_id, a.model_dump_json() if a else None))


def finish_run(conn: sqlite3.Connection, run_id: int, summary: Summary | None, status: str) -> None:
    with conn:
        conn.execute(
            "UPDATE runs SET finished_at=?, status=?, summary_json=? WHERE id=?",
            (_now(), status, summary.model_dump_json() if summary else None, run_id),
        )


def load_raw(conn: sqlite3.Connection, run_date: date) -> list[RawData]:
    rows = conn.execute(
        "SELECT raw.json FROM raw JOIN runs ON runs.id=raw.run_id WHERE runs.run_date=?",
        (run_date.isoformat(),),
    ).fetchall()
    return [RawData.model_validate_json(r["json"]) for r in rows]


def load_run(conn: sqlite3.Connection, run_date: date) -> RunSummary | None:
    run = conn.execute("SELECT * FROM runs WHERE run_date=?", (run_date.isoformat(),)).fetchone()
    if not run:
        return None
    reps = []
    for r in conn.execute("SELECT * FROM reporters WHERE run_id=? ORDER BY rowid", (run["id"],)):
        reps.append(ReporterResult(
            source_id=r["source_id"], status=r["status"],
            report=json.loads(r["report_json"]) if r["report_json"] else None,
            error=r["error"], attempts=r["attempts"], mismatches=json.loads(r["mismatches_json"]),
        ))
    an = conn.execute("SELECT json FROM analyses WHERE run_id=?", (run["id"],)).fetchone()
    return RunSummary(
        run_date=date.fromisoformat(run["run_date"]),
        started_at=datetime.fromisoformat(run["started_at"]),
        finished_at=datetime.fromisoformat(run["finished_at"]) if run["finished_at"] else None,
        status=run["status"],
        reporters=reps,
        analysis=Analysis.model_validate_json(an["json"]) if an and an["json"] else None,
        summary=Summary.model_validate_json(run["summary_json"]) if run["summary_json"] else None,
    )


def list_run_dates(conn: sqlite3.Connection, limit: int = 60) -> list[date]:
    rows = conn.execute("SELECT run_date FROM runs ORDER BY run_date DESC LIMIT ?", (limit,)).fetchall()
    return [date.fromisoformat(r["run_date"]) for r in rows]
