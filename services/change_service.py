"""Change service — CRUD for change_records."""

import db.database as db


def list_changes(plan_id: int) -> list[dict]:
    """Return all change records for a plan, newest first."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM change_records WHERE plan_id = ? ORDER BY changed_at DESC",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def record_change(plan_id: int, description: str, changed_by: str = "") -> int | None:
    """Insert a new change record and return its id."""
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO change_records (plan_id, description, changed_by) VALUES (?, ?, ?)",
            (plan_id, description, changed_by),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
