import datetime
import json
import sqlite3
from pathlib import Path
from typing import Optional, Any

DB_PATH = Path(__file__).resolve().parent.parent / "research_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_runs (
            run_id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            depth TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence TEXT NOT NULL,
            created_at TEXT NOT NULL,
            report_json TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            metrics_json TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenge_history (
            challenge_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            finding_id TEXT NOT NULL,
            claim_text TEXT NOT NULL,
            outcome TEXT NOT NULL,
            created_at TEXT NOT NULL,
            challenge_json TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES research_runs (run_id)
        )
    """)
    conn.commit()
    conn.close()

def save_research_run(run_id: str, question: str, depth: str, result: dict) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    report = result.get("report", {})
    plan = result.get("plan", {})
    metrics = result.get("metrics", {})
    
    status = report.get("status", "COMPLETED")
    confidence = report.get("confidence", "medium")
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO research_runs (
            run_id, question, depth, status, confidence, created_at, report_json, plan_json, metrics_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        question,
        depth,
        status,
        confidence,
        now_iso,
        json.dumps(report, ensure_ascii=False),
        json.dumps(plan, ensure_ascii=False),
        json.dumps(metrics, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def list_recent_runs(limit: int = 25) -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT run_id, question, depth, status, confidence, created_at
        FROM research_runs
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    runs = [dict(row) for row in rows]
    conn.close()
    return runs

def get_research_run(run_id: str) -> Optional[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT run_id, question, depth, status, confidence, created_at, report_json, plan_json, metrics_json
        FROM research_runs
        WHERE run_id = ?
    """, (run_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None

    return {
        "run_id": row["run_id"],
        "question": row["question"],
        "depth": row["depth"],
        "status": row["status"],
        "confidence": row["confidence"],
        "created_at": row["created_at"],
        "report": json.loads(row["report_json"]),
        "plan": json.loads(row["plan_json"]),
        "metrics": json.loads(row["metrics_json"]),
    }

def save_challenge_record(run_id: str, finding_id: str, claim_text: str, challenge_result: dict) -> None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cid = f"CHAL-{run_id}-{finding_id}-{abs(hash(claim_text)) % 10000}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    cursor.execute("""
        INSERT OR REPLACE INTO challenge_history (
            challenge_id, run_id, finding_id, claim_text, outcome, created_at, challenge_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        cid,
        run_id,
        finding_id,
        claim_text,
        challenge_result.get("outcome", "Claim remains supported"),
        now_iso,
        json.dumps(challenge_result, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_challenges_for_run(run_id: str) -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT challenge_id, finding_id, claim_text, outcome, created_at, challenge_json
        FROM challenge_history
        WHERE run_id = ?
        ORDER BY created_at DESC
    """, (run_id,))
    rows = cursor.fetchall()
    res = [json.loads(row["challenge_json"]) for row in rows]
    conn.close()
    return res

