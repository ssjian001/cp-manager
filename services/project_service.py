"""Project service — CRUD for the projects table."""

import db.database as db


def list_projects() -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            """SELECT id, name, part_number, part_name, supplier,
                      supplier_code, contact_person, contact_phone,
                      created_at, updated_at
               FROM projects
               ORDER BY updated_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_project(project_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            """SELECT id, name, part_number, part_name, supplier,
                      supplier_code, contact_person, contact_phone,
                      created_at, updated_at
               FROM projects
               WHERE id = ?""",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_project(
    name: str,
    part_number: str = "",
    part_name: str = "",
    supplier: str = "",
    supplier_code: str = "",
    contact_person: str = "",
    contact_phone: str = "",
) -> int:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO projects
                  (name, part_number, part_name, supplier,
                   supplier_code, contact_person, contact_phone)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, part_number, part_name, supplier, supplier_code, contact_person, contact_phone),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_project(project_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    conn = db.get_connection()
    try:
        allowed = {
            "name", "part_number", "part_name", "supplier",
            "supplier_code", "contact_person", "contact_phone",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [project_id]
        cur = conn.execute(
            f"UPDATE projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_project(project_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_project_stats(project_id: int) -> dict:
    """Return statistics for a project: control plan count, item count, phase breakdown."""
    conn = db.get_connection()
    try:
        plan_count = conn.execute(
            "SELECT COUNT(*) AS cnt FROM control_plans WHERE project_id = ?",
            (project_id,),
        ).fetchone()["cnt"]

        item_count = conn.execute(
            """SELECT COUNT(*) AS cnt
               FROM cp_items i
               JOIN control_plans p ON i.plan_id = p.id
               WHERE p.project_id = ?""",
            (project_id,),
        ).fetchone()["cnt"]

        phase_counts = conn.execute(
            """SELECT phase, COUNT(*) AS cnt
               FROM control_plans
               WHERE project_id = ?
               GROUP BY phase""",
            (project_id,),
        ).fetchall()

        phases = {r["phase"]: r["cnt"] for r in phase_counts}
        return {
            "plan_count": plan_count,
            "item_count": item_count,
            "phases": phases,
        }
    finally:
        conn.close()
