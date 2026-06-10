"""Tests for all service modules (23 test cases)."""

import pytest

import db.database as db
import services.project_service as ps
import services.plan_service as pls
import services.item_service as its
import services.reaction_service as rs
import services.approval_service as asrv


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
    pid = ps.create_project(
        name="Test Project",
        part_number="PN-001",
        part_name="Widget",
        supplier="Acme Corp",
    )
    return ps.get_project(pid)


@pytest.fixture
def plan(project):
    """Create and return a basic control plan under the fixture project."""
    pid = pls.create_plan(project["id"], cp_number="CP-001", phase="prototype")
    return pls.get_plan(pid)


@pytest.fixture
def step(plan):
    """Create a process step under the fixture plan and return it."""
    import sqlite3

    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
            "VALUES (?, ?, ?, ?)",
            (plan["id"], "10", "Machining", 0),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM process_steps WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# project_service  (5)
# ═══════════════════════════════════════════════════════════════════════════════


class TestProjectService:
    def test_create_and_list_projects(self, db_path):
        """创建 2 个项目，列表返回 2"""
        ps.create_project(name="Alpha")
        ps.create_project(name="Beta")
        projects = ps.list_projects()
        assert len(projects) == 2
        names = {p["name"] for p in projects}
        assert names == {"Alpha", "Beta"}

    def test_get_project(self, db_path):
        """创建后读取，验证字段"""
        pid = ps.create_project(
            name="My Project",
            part_number="PN-999",
            part_name="Gadget",
            supplier="SupplierX",
        )
        p = ps.get_project(pid)
        assert p is not None
        assert p["name"] == "My Project"
        assert p["part_number"] == "PN-999"
        assert p["part_name"] == "Gadget"
        assert p["supplier"] == "SupplierX"
        assert p["id"] == pid

    def test_update_project(self, db_path):
        """更新 name 和 part_number"""
        pid = ps.create_project(name="Old", part_number="OLD")
        ok = ps.update_project(pid, name="Updated", part_number="NEW")
        assert ok is True
        p = ps.get_project(pid)
        assert p["name"] == "Updated"
        assert p["part_number"] == "NEW"

    def test_delete_project(self, db_path):
        """删除后列表为空"""
        pid = ps.create_project(name="ToDelete")
        assert len(ps.list_projects()) == 1
        ok = ps.delete_project(pid)
        assert ok is True
        assert ps.list_projects() == []

    def test_project_stats(self, db_path):
        """创建项目+2个计划+3个控制项，验证统计数"""
        # project
        pid = ps.create_project(name="StatsProject", part_number="STATS-1")
        # 2 plans
        p1_id = pls.create_plan(pid, cp_number="CP-A", phase="prototype")
        p2_id = pls.create_plan(pid, cp_number="CP-B", phase="production")

        # add a step for each plan, then 2 items for p1, 1 for p2
        def _make_step(plan_id, label):
            conn = db.get_connection()
            try:
                cur = conn.execute(
                    "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
                    "VALUES (?, ?, ?, ?)",
                    (plan_id, "10", label, 0),
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

        def _make_item(step_id, plan_id):
            conn = db.get_connection()
            try:
                cur = conn.execute(
                    "INSERT INTO cp_items (step_id, plan_id, char_number, char_type) "
                    "VALUES (?, ?, ?, 'product')",
                    (step_id, plan_id, f"CHAR-{step_id}"),
                )
                conn.commit()
                return cur.lastrowid
            finally:
                conn.close()

        s1 = _make_step(p1_id, "Step A")
        s2 = _make_step(p1_id, "Step B")
        s3 = _make_step(p2_id, "Step C")

        _make_item(s1, p1_id)
        _make_item(s1, p1_id)
        _make_item(s3, p2_id)  # item via plan 2 step

        stats = ps.get_project_stats(pid)
        assert stats["plan_count"] == 2
        assert stats["item_count"] == 3
        assert "prototype" in stats["phases"]
        assert "production" in stats["phases"]
        assert stats["phases"]["prototype"] == 1
        assert stats["phases"]["production"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# plan_service  (7)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlanService:
    def test_create_plan(self, db_path):
        """创建控制计划，验证默认 phase=prototype"""
        pid = ps.create_project(name="P")
        plan_id = pls.create_plan(pid, cp_number="CP-001")
        plan = pls.get_plan(plan_id)
        assert plan is not None
        assert plan["phase"] == "prototype"
        assert plan["cp_number"] == "CP-001"

    def test_update_plan_phase(self, db_path):
        """从 prototype 改为 production"""
        pid = ps.create_project(name="P")
        plan_id = pls.create_plan(pid, cp_number="CP-X", phase="prototype")
        ok = pls.update_plan(plan_id, phase="production")
        assert ok is True
        plan = pls.get_plan(plan_id)
        assert plan["phase"] == "production"

    def test_get_plans_by_phase(self, db_path):
        """创建 3 个不同阶段计划，按 phase 过滤"""
        pid = ps.create_project(name="P")
        pls.create_plan(pid, cp_number="CP-A", phase="prototype")
        pls.create_plan(pid, cp_number="CP-B", phase="pre_launch")
        pls.create_plan(pid, cp_number="CP-C", phase="production")

        prototypes = pls.get_plans_by_phase(pid, "prototype")
        assert len(prototypes) == 1
        assert prototypes[0]["cp_number"] == "CP-A"

        pre_launch = pls.get_plans_by_phase(pid, "pre_launch")
        assert len(pre_launch) == 1
        assert pre_launch[0]["cp_number"] == "CP-B"

        prod = pls.get_plans_by_phase(pid, "production")
        assert len(prod) == 1
        assert prod[0]["cp_number"] == "CP-C"

    def test_start_safe_launch(self, db_path):
        """启动 SL，验证 is_safe_launch=1 和 start 日期"""
        pid = ps.create_project(name="P")
        plan_id = pls.create_plan(pid, cp_number="CP-SL")
        ok = pls.start_safe_launch(plan_id, duration_days=60, exit_criteria="Zero defects")
        assert ok is True

        plan = pls.get_plan(plan_id)
        assert plan["is_safe_launch"] == 1
        assert plan["safe_launch_start"] is not None
        assert plan["safe_launch_duration_days"] == 60
        assert plan["safe_launch_exit_criteria"] == "Zero defects"
        assert plan["safe_launch_fail_count"] == 0

    def test_complete_safe_launch(self, db_path):
        """启动后完成，验证 end 日期"""
        pid = ps.create_project(name="P")
        plan_id = pls.create_plan(pid, cp_number="CP-SL2")
        pls.start_safe_launch(plan_id)
        ok = pls.complete_safe_launch(plan_id)
        assert ok is True

        plan = pls.get_plan(plan_id)
        assert plan["safe_launch_end"] is not None
        assert plan["is_safe_launch"] == 0  # completed → no longer active

    def test_reset_safe_launch(self, db_path):
        """启动后归零，验证 fail_count+1 和 start 重置"""
        pid = ps.create_project(name="P")
        plan_id = pls.create_plan(pid, cp_number="CP-SL3")
        pls.start_safe_launch(plan_id)

        old_start = pls.get_plan(plan_id)["safe_launch_start"]

        ok = pls.reset_safe_launch(plan_id)
        assert ok is True

        plan = pls.get_plan(plan_id)
        assert plan["safe_launch_fail_count"] == 1
        # start should be refreshed (newer or equal timestamp)
        assert plan["safe_launch_start"] >= old_start

    def test_derive_from_foundation(self, db_path):
        """创建 foundation plan + step + item，派生到新 plan，验证复制"""
        # foundation project & plan
        pid1 = ps.create_project(name="Foundation Project")
        plan1_id = pls.create_plan(pid1, cp_number="FOUNDATION-01", phase="production")

        # add step
        conn = db.get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
                "VALUES (?, ?, ?, ?)",
                (plan1_id, "20", "Assembly", 0),
            )
            step_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        # add item
        conn = db.get_connection()
        try:
            conn.execute(
                "INSERT INTO cp_items (step_id, plan_id, char_number, char_type, "
                "special_classification, specification, control_method_type) "
                "VALUES (?, ?, ?, 'product', 'CC', '10±0.5', 'SPC')",
                (step_id, plan1_id, "CHAR-001"),
            )
            conn.commit()
        finally:
            conn.close()

        # new project for derived plan
        pid2 = ps.create_project(name="Derived Project")
        new_plan_id = pls.derive_from_foundation(
            plan1_id, pid2, new_cp_number="DERIVED-01"
        )

        new_plan = pls.get_plan(new_plan_id)
        assert new_plan is not None
        assert new_plan["cp_number"] == "DERIVED-01"
        assert new_plan["phase"] == "production"
        assert new_plan["foundation_source_id"] == plan1_id
        assert new_plan["is_safe_launch"] == 0
        assert new_plan["status"] == "draft"

        # verify steps copied
        conn = db.get_connection()
        try:
            steps = conn.execute(
                "SELECT * FROM process_steps WHERE plan_id = ?", (new_plan_id,)
            ).fetchall()
            assert len(steps) == 1
            assert steps[0]["step_name"] == "Assembly"
        finally:
            conn.close()

        # verify items copied
        conn = db.get_connection()
        try:
            items = conn.execute(
                "SELECT * FROM cp_items WHERE plan_id = ?", (new_plan_id,)
            ).fetchall()
            assert len(items) == 1
            assert items[0]["char_number"] == "CHAR-001"
            assert items[0]["special_classification"] == "CC"
            assert items[0]["specification"] == "10±0.5"
            assert items[0]["control_method_type"] == "SPC"
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
# item_service  (5)
# ═══════════════════════════════════════════════════════════════════════════════


class TestItemService:
    def test_create_item(self, db_path, plan, step):
        """创建控制项"""
        item_id = its.create_item(
            step["id"],
            plan["id"],
            char_number="CH-001",
            char_type="product",
            specification="100mm",
            control_method_type="manual",
        )
        item = its.get_item(item_id)
        assert item is not None
        assert item["char_number"] == "CH-001"
        assert item["char_type"] == "product"
        assert item["specification"] == "100mm"

    def test_update_item(self, db_path, plan, step):
        """更新 control_method_type"""
        item_id = its.create_item(
            step["id"], plan["id"], char_number="CH-002", control_method_type="manual"
        )
        ok = its.update_item(item_id, control_method_type="SPC")
        assert ok is True
        item = its.get_item(item_id)
        assert item["control_method_type"] == "SPC"

    def test_list_items_by_step(self, db_path, plan, step):
        """按步骤过滤"""
        # create another step
        conn = db.get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
                "VALUES (?, ?, ?, ?)",
                (plan["id"], "30", "Inspection", 1),
            )
            step2_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()

        its.create_item(step["id"], plan["id"], char_number="A-1")
        its.create_item(step["id"], plan["id"], char_number="A-2")
        its.create_item(step2_id, plan["id"], char_number="B-1")

        step1_items = its.list_items_by_step(step["id"])
        assert len(step1_items) == 2

        step2_items = its.list_items_by_step(step2_id)
        assert len(step2_items) == 1
        assert step2_items[0]["char_number"] == "B-1"

    def test_special_char_items(self, db_path, plan, step):
        """创建 1 个 none + 1 个 CC，验证只返回 CC"""
        its.create_item(
            step["id"],
            plan["id"],
            char_number="NORM",
            special_classification="none",
        )
        its.create_item(
            step["id"],
            plan["id"],
            char_number="CRIT",
            special_classification="CC",
        )

        specials = its.get_special_char_items(plan["id"])
        assert len(specials) == 1
        assert specials[0]["char_number"] == "CRIT"
        assert specials[0]["special_classification"] == "CC"

    def test_batch_update_order(self, db_path, plan, step):
        """创建 3 项，交换顺序"""
        id1 = its.create_item(
            step["id"], plan["id"], char_number="Z", sort_order=0
        )
        id2 = its.create_item(
            step["id"], plan["id"], char_number="A", sort_order=1
        )
        id3 = its.create_item(
            step["id"], plan["id"], char_number="M", sort_order=2
        )

        # swap: reverse the order
        its.batch_update_order([id3, id2, id1])

        items = its.list_items(plan["id"])
        assert items[0]["id"] == id3
        assert items[0]["sort_order"] == 0
        assert items[1]["id"] == id2
        assert items[1]["sort_order"] == 1
        assert items[2]["id"] == id1
        assert items[2]["sort_order"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
# reaction_service  (3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestReactionService:
    def test_create_template(self, db_path):
        """创建模板"""
        tid = rs.create_template(
            name="Stop & Sort",
            stop_process="Stop line immediately",
            product_disposition="100% sort",
            notify_who="QA Lead",
            recovery_condition="5 samples OK",
        )
        tpl = rs.get_template(tid)
        assert tpl is not None
        assert tpl["name"] == "Stop & Sort"
        assert tpl["stop_process"] == "Stop line immediately"

    def test_default_templates(self, db_path):
        """设 2 个模板，1 个 is_default=1，验证过滤"""
        rs.create_template(name="Regular", is_default=0)
        rs.create_template(name="Standard", is_default=1)
        rs.create_template(name="Extra", is_default=1)

        defaults = rs.get_default_templates()
        assert len(defaults) == 2
        names = {t["name"] for t in defaults}
        assert names == {"Standard", "Extra"}

    def test_delete_template(self, db_path):
        """删除后列表为空"""
        tid = rs.create_template(name="Temp")
        assert len(rs.list_templates()) == 1
        ok = rs.delete_template(tid)
        assert ok is True
        assert rs.list_templates() == []


# ═══════════════════════════════════════════════════════════════════════════════
# approval_service  (3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestApprovalService:
    def test_create_approval(self, db_path, plan):
        """创建签署记录"""
        aid = asrv.create_approval(plan["id"], "prepared", "John Doe")
        approvals = asrv.list_approvals(plan["id"])
        assert len(approvals) == 1
        assert approvals[0]["approval_type"] == "prepared"
        assert approvals[0]["name"] == "John Doe"

    def test_sign_approval(self, db_path, plan):
        """签署后 signed_at 不为空"""
        aid = asrv.create_approval(plan["id"], "approved", "Jane Smith")
        ok = asrv.sign_approval(aid)
        assert ok is True

        approvals = asrv.list_approvals(plan["id"])
        assert approvals[0]["signed_at"] is not None

    def test_team_members(self, db_path, plan):
        """添加和删除团队成员"""
        mid1 = asrv.add_team_member(plan["id"], "Alice", role="Engineer", department="QE")
        mid2 = asrv.add_team_member(plan["id"], "Bob", role="Manager", department="Prod")

        members = asrv.list_team_members(plan["id"])
        assert len(members) == 2

        ok = asrv.remove_team_member(mid1)
        assert ok is True

        remaining = asrv.list_team_members(plan["id"])
        assert len(remaining) == 1
        assert remaining[0]["name"] == "Bob"
