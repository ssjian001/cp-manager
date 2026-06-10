"""Step service — CRUD for process_steps."""

import db.database as db


def list_steps(plan_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, plan_id, step_number, step_name, equipment, description, sort_order "
            "FROM process_steps WHERE plan_id = ? ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_step(step_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT id, plan_id, step_number, step_name, equipment, description, sort_order "
            "FROM process_steps WHERE id = ?",
            (step_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_step(
    plan_id: int,
    step_number: str,
    step_name: str,
    equipment: str = "",
    description: str = "",
) -> int:
    conn = db.get_connection()
    try:
        # Get current max sort_order
        row = conn.execute(
            "SELECT MAX(sort_order) FROM process_steps WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()
        sort = (row[0] or 0) + 1
        cur = conn.execute(
            "INSERT INTO process_steps (plan_id, step_number, step_name, equipment, description, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, step_number, step_name, equipment, description, sort),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_step(step_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    conn = db.get_connection()
    try:
        allowed = {"step_number", "step_name", "equipment", "description", "sort_order"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [step_id]
        cur = conn.execute(
            f"UPDATE process_steps SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_step(step_id: int) -> bool:
    conn = db.get_connection()
    try:
        # CASCADE will automatically delete related cp_items
        cur = conn.execute("DELETE FROM process_steps WHERE id = ?", (step_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def reorder_steps(step_ids: list[int]) -> None:
    """Update sort_order sequentially based on the order of step_ids."""
    conn = db.get_connection()
    try:
        for idx, step_id in enumerate(step_ids):
            conn.execute(
                "UPDATE process_steps SET sort_order = ? WHERE id = ?",
                (idx, step_id),
            )
        conn.commit()
    finally:
        conn.close()
