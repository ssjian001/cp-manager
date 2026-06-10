"""Plan service — CRUD for control_plans, safe-launch, and derivation."""

import db.database as db


def list_plans(project_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM control_plans WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_plan(plan_id: int) -> dict | None:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM control_plans WHERE id = ?", (plan_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_plan(
    project_id: int,
    cp_number: str = "",
    phase: str = "prototype",
    **kwargs,
) -> int:
    conn = db.get_connection()
    try:
        allowed = {
            "cp_number", "phase", "is_safe_launch",
            "safe_launch_start", "safe_launch_end",
            "safe_launch_duration_days", "safe_launch_fail_count",
            "safe_launch_exit_criteria", "foundation_source_id",
            "status", "core_team",
        }
        fields = {"cp_number": cp_number, "phase": phase}
        for k, v in kwargs.items():
            if k in allowed:
                fields[k] = v

        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        values = list(fields.values())
        cur = conn.execute(
            f"INSERT INTO control_plans (project_id, {columns}) "
            f"VALUES (?, {placeholders})",
            [project_id] + values,
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_plan(plan_id: int, **kwargs) -> bool:
    if not kwargs:
        return False
    conn = db.get_connection()
    try:
        allowed = {
            "cp_number", "phase", "is_safe_launch",
            "safe_launch_start", "safe_launch_end",
            "safe_launch_duration_days", "safe_launch_fail_count",
            "safe_launch_exit_criteria", "foundation_source_id",
            "status", "core_team",
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [plan_id]
        cur = conn.execute(
            f"UPDATE control_plans SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_plan(plan_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute("DELETE FROM control_plans WHERE id = ?", (plan_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_plans_by_phase(project_id: int, phase: str) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM control_plans WHERE project_id = ? AND phase = ? ORDER BY created_at DESC",
            (project_id, phase),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_safe_launch_plans(project_id: int) -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM control_plans WHERE project_id = ? AND is_safe_launch = 1 ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def start_safe_launch(
    plan_id: int,
    duration_days: int = 90,
    exit_criteria: str = "",
) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            """UPDATE control_plans
               SET is_safe_launch = 1,
                   safe_launch_start = CURRENT_TIMESTAMP,
                   safe_launch_duration_days = ?,
                   safe_launch_exit_criteria = ?,
                   safe_launch_fail_count = 0,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (duration_days, exit_criteria, plan_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def complete_safe_launch(plan_id: int) -> bool:
    conn = db.get_connection()
    try:
        cur = conn.execute(
            """UPDATE control_plans
               SET safe_launch_end = CURRENT_TIMESTAMP,
                   is_safe_launch = 0,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (plan_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def reset_safe_launch(plan_id: int) -> bool:
    """Increment fail count and restart the safe-launch timer."""
    conn = db.get_connection()
    try:
        cur = conn.execute(
            """UPDATE control_plans
               SET safe_launch_fail_count = safe_launch_fail_count + 1,
                   safe_launch_start = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (plan_id,),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def count_safe_launch_plans(project_id: int) -> int:
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM control_plans "
            "WHERE project_id = ? AND is_safe_launch = 1",
            (project_id,),
        ).fetchone()
        return row["cnt"]
    finally:
        conn.close()


def list_all_plans_with_project() -> list[dict]:
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT cp.id, cp.cp_number, p.name AS project_name, cp.phase "
            "FROM control_plans cp "
            "LEFT JOIN projects p ON p.id = cp.project_id "
            "ORDER BY cp.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_safe_launch_by_project(project_id: int) -> int:
    """Return count of active Safe Launch plans for a project."""
    conn = db.get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM control_plans "
            "WHERE project_id = ? AND is_safe_launch = 1",
            (project_id,),
        ).fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_plan_list_all() -> list[dict]:
    """Return all plans with project name (for audit view combo box)."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT cp.id, cp.cp_number, p.name AS project_name, cp.phase "
            "FROM control_plans cp "
            "LEFT JOIN projects p ON p.id = cp.project_id "
            "ORDER BY cp.id DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_plans_for_foundation(project_id: int) -> list[dict]:
    """Return plans for a project (for foundation source selector)."""
    conn = db.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, cp_number, phase FROM control_plans "
            "WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def derive_from_foundation(
    foundation_plan_id: int,
    new_project_id: int,
    new_cp_number: str = "",
) -> int:
    """Copy an entire control plan (process_steps + cp_items) from a foundation plan
    into a new plan under the target project.

    Returns the new plan id.
    """
    conn = db.get_connection()
    try:
        # 1. Get foundation plan
        foundation = conn.execute(
            "SELECT * FROM control_plans WHERE id = ?",
            (foundation_plan_id,),
        ).fetchone()
        if not foundation:
            raise ValueError(f"Foundation plan {foundation_plan_id} not found")

        foundation = dict(foundation)

        # 2. Create new plan (copy most fields, reset safe-launch & status)
        new_plan_id = conn.execute(
            """INSERT INTO control_plans
                  (project_id, cp_number, phase, is_safe_launch, status,
                   foundation_source_id)
               VALUES (?, ?, ?, 0, 'draft', ?)""",
            (new_project_id, new_cp_number or foundation["cp_number"],
             foundation["phase"], foundation_plan_id),
        ).lastrowid

        # 3. Copy process_steps (map old step_id -> new step_id)
        old_steps = conn.execute(
            "SELECT * FROM process_steps WHERE plan_id = ? ORDER BY sort_order",
            (foundation_plan_id,),
        ).fetchall()

        step_id_map: dict[int, int] = {}
        for step in old_steps:
            s = dict(step)
            cur = conn.execute(
                """INSERT INTO process_steps
                      (plan_id, step_number, step_name, equipment, description, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (new_plan_id, s["step_number"], s["step_name"],
                 s["equipment"], s["description"], s["sort_order"]),
            )
            step_id_map[s["id"]] = cur.lastrowid

        # 4. Copy cp_items
        old_items = conn.execute(
            "SELECT * FROM cp_items WHERE plan_id = ? ORDER BY sort_order",
            (foundation_plan_id,),
        ).fetchall()

        for item in old_items:
            i = dict(item)
            new_step_id = step_id_map.get(i["step_id"])
            if new_step_id is None:
                continue  # skip orphaned items (should not happen)
            conn.execute(
                """INSERT INTO cp_items
                      (step_id, plan_id, char_number, char_type, char_description,
                       special_classification, specification, tolerance,
                       measurement_method, gauge_id, sample_size, sample_frequency,
                       control_method_type, ep_verification_freq, ep_verification_method,
                       responsible, reaction_plan, notes, sort_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (new_step_id, new_plan_id, i["char_number"], i["char_type"],
                 i["char_description"], i["special_classification"],
                 i["specification"], i["tolerance"], i["measurement_method"],
                 i["gauge_id"], i["sample_size"], i["sample_frequency"],
                 i["control_method_type"], i["ep_verification_freq"],
                 i["ep_verification_method"], i["responsible"],
                 i["reaction_plan"], i["notes"], i["sort_order"]),
            )

        conn.commit()
        return new_plan_id
    finally:
        conn.close()
