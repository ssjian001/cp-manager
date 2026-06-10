"""Approval service — CRUD for approvals and team members."""

import db.database as db


# ── Approvals ──────────────────────────────────────────────────────────────────


def list_approvals(plan_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE plan_id = ? ORDER BY id",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def create_approval(plan_id: int, approval_type: str, name: str) -> int:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO approvals (plan_id, approval_type, name) VALUES (?, ?, ?)",
            (plan_id, approval_type, name),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def sign_approval(approval_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "UPDATE approvals SET signed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (approval_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_approval(approval_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM approvals WHERE id = ?", (approval_id,)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ── Team Members ───────────────────────────────────────────────────────────────


def list_team_members(plan_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM team_members WHERE plan_id = ? ORDER BY id",
            (plan_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_team_member(
    plan_id: int,
    name: str,
    role: str = "",
    department: str = "",
) -> int:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO team_members (plan_id, name, role, department) VALUES (?, ?, ?, ?)",
            (plan_id, name, role, department),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def remove_team_member(member_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "DELETE FROM team_members WHERE id = ?", (member_id,)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
