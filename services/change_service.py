"""Change record service — tracking plan changes."""

import db.database as db


def record_change(
    plan_id: int,
    description: str,
    changed_by: str = "",
) -> int:
    """Record a change to a control plan.
    
    Returns the new change record id.
    """
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


def list_changes(plan_id: int) -> list[dict]:
    """List change records for a plan, ordered by changed_at DESC (most recent first)."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM change_records WHERE plan_id = ? ORDER BY changed_at DESC",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_change(change_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM change_records WHERE id = ?", (change_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_change(change_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute("DELETE FROM change_records WHERE id = ?", (change_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
