import os
import sqlite3
import contextlib
from typing import Optional, List, Dict, Any

DB_PATH = os.getenv("DB_PATH", "jobs.db")


@contextlib.contextmanager
def get_connection(db_path: Optional[str] = None):
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS forwarded_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_text TEXT NOT NULL,
                source_group TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON forwarded_jobs(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_timestamp ON forwarded_jobs(timestamp)")


def save_job(
    message_text: str,
    source_group: str,
    timestamp: str,
    category: str,
    db_path: Optional[str] = None,
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO forwarded_jobs (message_text, source_group, timestamp, category)
            VALUES (?, ?, ?, ?)
            """,
            (message_text, source_group, timestamp, category),
        )
        return cursor.lastrowid


def get_jobs(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    clauses = []
    params: List[Any] = []

    if category and category.strip() and category.strip().lower() != "all":
        clauses.append("category = ?")
        params.append(category.strip())

    if start_date and start_date.strip():
        clauses.append("date(timestamp) >= date(?)")
        params.append(start_date.strip())

    if end_date and end_date.strip():
        clauses.append("date(timestamp) <= date(?)")
        params.append(end_date.strip())

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT id, message_text, source_group, timestamp, category, created_at
        FROM forwarded_jobs
        {where_sql}
        ORDER BY timestamp DESC, id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_categories(db_path: Optional[str] = None) -> List[str]:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT category
            FROM forwarded_jobs
            WHERE category IS NOT NULL AND TRIM(category) != ''
            ORDER BY category ASC
            """
        ).fetchall()
        return [row[0] for row in rows]


def get_stats(db_path: Optional[str] = None) -> Dict[str, Any]:
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) as total_jobs,
                COUNT(DISTINCT category) as total_categories,
                MAX(timestamp) as latest_job_time
            FROM forwarded_jobs
            """
        ).fetchone()
        return {
            "total_jobs": row["total_jobs"] if row else 0,
            "total_categories": row["total_categories"] if row else 0,
            "latest_job_time": row["latest_job_time"] if row else None,
        }
