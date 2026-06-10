"""Step service — CRUD and reordering for process steps."""

import db.database as db


def list_steps(plan_id: int) -> list[dict]:
    """List all steps under a plan, ordered by sort_order."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM process_steps WHERE plan_id = ? ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_step(step_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM process_steps WHERE id = ?", (step_id,)
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
    """Create a process step with auto-incremented sort_order."""
    conn = db.get_connection()
    try:
        # Get current max sort_order for this plan
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) AS max_order FROM process_steps WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()
        next_order = row["max_order"] + 1

        cur = conn.execute(
            "INSERT INTO process_steps (plan_id, step_number, step_name, equipment, description, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, step_number, step_name, equipment, description, next_order),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_step(step_id: int, **kwargs) -> bool:
    """Update fields of a process step."""
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
        cur = conn.execute("DELETE FROM process_steps WHERE id = ?", (step_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_step_map_by_plan(plan_id: int) -> dict[int, dict]:
    """Return {step_id: {id, step_number, step_name}} for all steps in a plan."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, step_number, step_name FROM process_steps WHERE plan_id=?",
            (plan_id,),
        ).fetchall()
        return {r["id"]: dict(r) for r in rows}
    finally:
        conn.close()


def reorder_steps(step_ids: list[int]) -> bool:
    """Reorder steps by assigning sort_order based on position in the list.
    
    Args:
        step_ids: List of step IDs in the desired order.
    
    Returns:
        True if successful.
    """
    conn = db.get_connection()
    try:
        for i, step_id in enumerate(step_ids):
            conn.execute(
                "UPDATE process_steps SET sort_order = ? WHERE id = ?",
                (i, step_id),
            )
        conn.commit()
        return True
    finally:
        conn.close()
