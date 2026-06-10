"""Reaction service — CRUD for reaction plan templates."""

import db.database as db


def list_templates() -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM reaction_templates ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_template(template_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM reaction_templates WHERE id = ?", (template_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_template(
    name: str,
    stop_process: str = "",
    product_disposition: str = "",
    notify_who: str = "",
    recovery_condition: str = "",
    is_default: int = 0,
) -> int:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO reaction_templates
                  (name, stop_process, product_disposition,
                   notify_who, recovery_condition, is_default)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, stop_process, product_disposition,
             notify_who, recovery_condition, is_default),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_template(template_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    conn = db.get_connection()
    try:
        allowed = {
            "name", "stop_process", "product_disposition",
            "notify_who", "recovery_condition", "is_default",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [template_id]
        cur = conn.execute(
            f"UPDATE reaction_templates SET {set_clause} WHERE id = ?",
            values,
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_template(template_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM reaction_templates WHERE id = ?", (template_id,)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_default_templates() -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM reaction_templates WHERE is_default = 1 ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
