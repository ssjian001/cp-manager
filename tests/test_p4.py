"""Tests for P4 new features — step_service, change_service, approval workflow, presets (13 test cases)."""

import pytest

import db.database as db
import services.project_service as ps
import services.plan_service as pls
import services.approval_service as asrv
import services.step_service as ss
import services.change_service as cs
from core.presets import ensure_reaction_templates


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Use a temporary database so tests don't touch ~/.cp-manager/."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    db.init_db()
    yield test_db


@pytest.fixture
def project(db_path):
    """Create and return a basic project."""
    pid = ps.create_project(name="P4 Project", part_number="P4-001")
    return ps.get_project(pid)


@pytest.fixture
def plan(project):
    """Create and return a basic control plan."""
    pid = pls.create_plan(project["id"], cp_number="P4-CP-001", phase="prototype")
    return pls.get_plan(pid)


# ═══════════════════════════════════════════════════════════════════════════════
# step_service  (5)
# ═══════════════════════════════════════════════════════════════════════════════


class TestStepService:
    def test_create_step(self, plan):
        """创建步骤，验证 sort_order 自动递增"""
        s1_id = ss.create_step(plan["id"], "10", "Machining")
        s2_id = ss.create_step(plan["id"], "20", "Assembly")

        s1 = ss.get_step(s1_id)
        s2 = ss.get_step(s2_id)

        assert s1 is not None
        assert s2 is not None
        assert s1["step_number"] == "10"
        assert s1["step_name"] == "Machining"
        assert s1["sort_order"] == 0  # first step
        assert s2["sort_order"] == 1  # auto-incremented

    def test_list_steps(self, plan):
        """创建 3 个步骤，验证按 sort_order 排序"""
        ss.create_step(plan["id"], "30", "Inspection")   # sort_order=0
        ss.create_step(plan["id"], "10", "Machining")    # sort_order=1
        ss.create_step(plan["id"], "20", "Assembly")     # sort_order=2

        steps = ss.list_steps(plan["id"])
        assert len(steps) == 3
        # Verify sorted by sort_order ascending
        assert steps[0]["step_name"] == "Inspection"
        assert steps[1]["step_name"] == "Machining"
        assert steps[2]["step_name"] == "Assembly"
        # Verify sort_order values
        assert steps[0]["sort_order"] == 0
        assert steps[1]["sort_order"] == 1
        assert steps[2]["sort_order"] == 2

    def test_update_step(self, plan):
        """更新 step_name"""
        sid = ss.create_step(plan["id"], "10", "OldName")
        ok = ss.update_step(sid, step_name="NewName")
        assert ok is True

        step = ss.get_step(sid)
        assert step["step_name"] == "NewName"

    def test_delete_step(self, plan):
        """删除步骤"""
        sid = ss.create_step(plan["id"], "10", "ToDelete")
        assert len(ss.list_steps(plan["id"])) == 1

        ok = ss.delete_step(sid)
        assert ok is True
        assert ss.list_steps(plan["id"]) == []

    def test_reorder_steps(self, plan):
        """创建 3 步骤后反序重排"""
        id1 = ss.create_step(plan["id"], "10", "Alpha")
        id2 = ss.create_step(plan["id"], "20", "Beta")
        id3 = ss.create_step(plan["id"], "30", "Gamma")

        # Reverse order
        ss.reorder_steps([id3, id2, id1])

        steps = ss.list_steps(plan["id"])
        assert steps[0]["id"] == id3
        assert steps[0]["sort_order"] == 0
        assert steps[1]["id"] == id2
        assert steps[1]["sort_order"] == 1
        assert steps[2]["id"] == id1
        assert steps[2]["sort_order"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# change_service  (3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestChangeService:
    def test_record_change(self, plan):
        """记录变更"""
        cid = cs.record_change(plan["id"], "Updated specification", "Alice")
        record = cs.get_change(cid)
        assert record is not None
        assert record["plan_id"] == plan["id"]
        assert record["description"] == "Updated specification"
        assert record["changed_by"] == "Alice"
        assert record["changed_at"] is not None  # auto-set by DB

    def test_list_changes(self, plan):
        """创建 3 条变更记录，验证按时间倒序"""
        # Use direct SQL to set distinct timestamps (CURRENT_TIMESTAMP has second precision)
        conn = db.get_connection()
        try:
            conn.execute(
                "INSERT INTO change_records (plan_id, description, changed_by, changed_at) "
                "VALUES (?, ?, ?, '2026-06-10 08:00:00')",
                (plan["id"], "First change", "Alice"),
            )
            conn.execute(
                "INSERT INTO change_records (plan_id, description, changed_by, changed_at) "
                "VALUES (?, ?, ?, '2026-06-10 09:00:00')",
                (plan["id"], "Second change", "Bob"),
            )
            conn.execute(
                "INSERT INTO change_records (plan_id, description, changed_by, changed_at) "
                "VALUES (?, ?, ?, '2026-06-10 10:00:00')",
                (plan["id"], "Third change", "Charlie"),
            )
            conn.commit()
        finally:
            conn.close()

        # Fetch IDs sorted by time (oldest first)
        conn = db.get_connection()
        try:
            rows = conn.execute(
                "SELECT id FROM change_records WHERE plan_id = ? ORDER BY changed_at",
                (plan["id"],),
            ).fetchall()
        finally:
            conn.close()
        cid1, cid2, cid3 = (r["id"] for r in rows)

        changes = cs.list_changes(plan["id"])
        assert len(changes) == 3

        # Most recent first (changed_at DESC)
        assert changes[0]["id"] == cid3
        assert changes[1]["id"] == cid2
        assert changes[2]["id"] == cid1

    def test_change_fields(self, plan):
        """验证字段完整（plan_id, description, changed_by, changed_at）"""
        cid = cs.record_change(plan["id"], "Field check", "Tester")
        record = cs.get_change(cid)

        assert record["plan_id"] == plan["id"]
        assert record["description"] == "Field check"
        assert record["changed_by"] == "Tester"
        assert record["changed_at"] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# approval workflow  (4)
# ═══════════════════════════════════════════════════════════════════════════════


class TestApprovalWorkflow:
    def test_team_member_crud(self, plan):
        """添加/删除团队成员"""
        mid1 = asrv.add_team_member(plan["id"], "Alice", role="Engineer", department="QE")
        mid2 = asrv.add_team_member(plan["id"], "Bob", role="Manager", department="Prod")

        members = asrv.list_team_members(plan["id"])
        assert len(members) == 2
        names = {m["name"] for m in members}
        assert names == {"Alice", "Bob"}

        # Delete one
        ok = asrv.remove_team_member(mid1)
        assert ok is True

        remaining = asrv.list_team_members(plan["id"])
        assert len(remaining) == 1
        assert remaining[0]["name"] == "Bob"

    def test_approval_sign(self, plan):
        """创建签署记录并签署，验证 signed_at 非空"""
        aid = asrv.create_approval(plan["id"], "approved", "Jane Smith")
        ok = asrv.sign_approval(aid)
        assert ok is True

        approvals = asrv.list_approvals(plan["id"])
        assert len(approvals) == 1
        assert approvals[0]["signed_at"] is not None
        assert approvals[0]["approval_type"] == "approved"
        assert approvals[0]["name"] == "Jane Smith"

    def test_approval_types(self, plan):
        """创建三种类型的签署（prepared/reviewed/approved），验证区分正确"""
        aid1 = asrv.create_approval(plan["id"], "prepared", "Alice")
        aid2 = asrv.create_approval(plan["id"], "reviewed", "Bob")
        aid3 = asrv.create_approval(plan["id"], "approved", "Charlie")

        approvals = asrv.list_approvals(plan["id"])
        assert len(approvals) == 3

        # Map by type
        by_type = {a["approval_type"]: a["name"] for a in approvals}
        assert by_type["prepared"] == "Alice"
        assert by_type["reviewed"] == "Bob"
        assert by_type["approved"] == "Charlie"

    def test_status_workflow(self, plan):
        """draft → review → approved → obsolete 的状态转换"""
        # Initial status should be 'draft'
        assert plan["status"] == "draft"

        # draft → review
        ok = pls.update_plan(plan["id"], status="review")
        assert ok is True
        assert pls.get_plan(plan["id"])["status"] == "review"

        # review → approved
        ok = pls.update_plan(plan["id"], status="approved")
        assert ok is True
        assert pls.get_plan(plan["id"])["status"] == "approved"

        # approved → obsolete
        ok = pls.update_plan(plan["id"], status="obsolete")
        assert ok is True
        assert pls.get_plan(plan["id"])["status"] == "obsolete"


# ═══════════════════════════════════════════════════════════════════════════════
# presets  (1)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPresets:
    def test_presets_insert(self, db_path):
        """首次调用插入 6 个模板，再次调用返回 0"""
        # First call — should insert all 6 presets
        count1 = ensure_reaction_templates()
        assert count1 == 6

        import services.reaction_service as rs
        templates = rs.list_templates()
        assert len(templates) == 6
        names = {t["name"] for t in templates}
        assert "尺寸不合格" in names
        assert "SPC失控" in names
        assert "安全特性不合格" in names

        # Second call — templates already exist, should return 0
        count2 = ensure_reaction_templates()
        assert count2 == 0

        # Verify still 6 (no duplicates)
        templates2 = rs.list_templates()
        assert len(templates2) == 6
