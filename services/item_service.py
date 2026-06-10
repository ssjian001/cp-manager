"""Item service — CRUD for cp_items and batch operations."""

import db.database as db


def list_items(plan_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM cp_items WHERE plan_id = ? ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_items_by_step(step_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM cp_items WHERE step_id = ? ORDER BY sort_order",
            (step_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_item(item_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM cp_items WHERE id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_item(step_id: int, plan_id: int, **kwargs) -> int:
    conn = db.get_connection()
    try:
        allowed = {
            "char_number", "char_type", "char_description",
            "special_classification", "specification", "tolerance",
            "measurement_method", "gauge_id", "sample_size",
            "sample_frequency", "control_method_type",
            "ep_verification_freq", "ep_verification_method",
            "responsible", "reaction_plan", "notes", "sort_order",
        }
        fields = {}
        for k, v in kwargs.items():
            if k in allowed:
                fields[k] = v

        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        values = list(fields.values())
        cur = conn.execute(
            f"INSERT INTO cp_items (step_id, plan_id, {columns}) "
            f"VALUES (?, ?, {placeholders})",
            [step_id, plan_id] + values,
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_item(item_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    conn = db.get_connection()
    try:
        allowed = {
            "char_number", "char_type", "char_description",
            "special_classification", "specification", "tolerance",
            "measurement_method", "gauge_id", "sample_size",
            "sample_frequency", "control_method_type",
            "ep_verification_freq", "ep_verification_method",
            "responsible", "reaction_plan", "notes", "sort_order",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [item_id]
        cur = conn.execute(
            f"UPDATE cp_items SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_item(item_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute("DELETE FROM cp_items WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def batch_update_order(item_ids: list[int]) -> None:
    """Update sort_order sequentially based on the order of item_ids."""
    conn = db.get_connection()
    try:
        for idx, item_id in enumerate(item_ids):
            conn.execute(
                "UPDATE cp_items SET sort_order = ? WHERE id = ?",
                (idx, item_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_items_count(plan_id: int) -> int:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM cp_items WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_special_char_items(plan_id: int) -> list[dict]:
    """Return items where special_classification is not 'none'."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM cp_items WHERE plan_id = ? AND special_classification != 'none' ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
