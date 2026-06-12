"""Tests for AuditEngine — 7 test cases covering audit_control_plan()."""

from __future__ import annotations

import pytest
import db.database as db
import services.project_service as ps
import services.plan_service as pls
import services.item_service as its
import services.approval_service as asrv
from core.audit_engine import audit_control_plan


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Redirect DB to tmp_path so tests don't touch ~/.cp-manager/."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    db.init_db()
    yield test_db


@pytest.fixture
def project(db_path):
    """Create a fully populated project."""
    pid = ps.create_project(
        name="Audit Project",
        part_number="APN-001",
        part_name="Test Widget",
        supplier="Acme Corp",
        supplier_code="ACME",
        contact_person="John Doe",
        contact_phone="123-456-7890",
    )
    return ps.get_project(pid)


@pytest.fixture
def plan(db_path, project):
    """Create a control plan with signing and team members."""
    pid = pls.create_plan(
        project["id"],
        cp_number="CP-AUDIT-01",
        phase="production",
        status="draft",
    )
    # Add team members
    asrv.add_team_member(pid, "Alice", role="Engineer", department="QE")
    asrv.add_team_member(pid, "Bob", role="Manager", department="Prod")
    # Add approvals
    asrv.create_approval(pid, "prepared", "Alice")
    asrv.create_approval(pid, "approved", "Bob")
    return pls.get_plan(pid)


@pytest.fixture
def step(plan):
    """Create a process step."""
    conn = db.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO process_steps (plan_id, step_number, step_name, equipment, sort_order) "
            "VALUES (?, ?, ?, ?, ?)",
            (plan["id"], "OP10", "Machining", "CNC-01", 0),
        )
        conn.commit()
        step_id = cur.lastrowid
        # Create second step — empty (no items)
        conn.execute(
            "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
            "VALUES (?, ?, ?, ?)",
            (plan["id"], "OP20", "Inspection", 1),
        )
        conn.commit()
        return db.get_connection().execute(
            "SELECT * FROM process_steps WHERE id = ?", (step_id,)
        ).fetchone()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestAuditEngine:
    def test_audit_empty_plan(self, db_path):
        """空计划 — 大部分检查应为 fail（无步骤、无控制项、无签署等）"""
        # Create minimal project + plan with nothing extra
        pid = ps.create_project(name="Empty")
        plan_id = pls.create_plan(pid, cp_number="CP-EMPTY")
        results = audit_control_plan(plan_id)

        # We have 25 checks total
        assert len(results) == 25

        # Key fails we expect on an empty plan:
        # doc_01: cp_number present → pass
        assert results[0]["result"] == "pass"  # has cp_number
        # doc_02: created_at always set by DB → pass
        assert results[1]["result"] == "pass"  # has created_at
        # doc_03: no team members → fail
        assert results[2]["result"] == "fail"
        # doc_04: no approvals → fail
        assert results[3]["result"] == "fail"
        # doc_05: PFMEA skip
        assert results[4]["result"] == "skip"

        # col_06: no steps at all → pass (0 steps, 0 empty steps)
        assert results[5]["result"] == "pass"

        # col_07..11: no items → pass (0 items, 0 missing)
        for idx in range(6, 11):
            assert results[idx]["result"] == "pass"

        # life_23: no steps → fail
        assert results[22]["result"] == "fail"
        # life_22: no prepared → fail
        assert results[21]["result"] == "fail"

    def test_audit_complete_plan(self, db_path, plan, step):
        """填满所有字段的计划 — 大部分应为 pass"""
        # Add items with all fields filled
        its.create_item(
            step["id"], plan["id"],
            char_number="CH-001",
            char_type="product",
            char_description="Diameter",
            special_classification="CC",
            specification="10.0",
            tolerance="0.5",
            measurement_method="Caliper",
            gauge_id="G-001",
            sample_size="5",
            sample_frequency="1/hr",
            control_method_type="SPC",
            reaction_plan="停线通知主管挑选隔离恢复OK",
            responsible="Alice",
        )
        # Second item — normal
        its.create_item(
            step["id"], plan["id"],
            char_number="CH-002",
            char_type="process",
            char_description="Temperature",
            special_classification="none",
            specification="200°C",
            tolerance="5°C",
            measurement_method="Thermometer",
            gauge_id="G-002",
            sample_size="1",
            sample_frequency="每批",
            control_method_type="manual",
            reaction_plan="停线通知主管",
            responsible="Bob",
        )

        results = audit_control_plan(plan["id"])
        assert len(results) == 25

        # doc_01: has cp_number → pass
        assert results[0]["result"] == "pass"
        # doc_03: has 2 team members → pass
        assert results[2]["result"] == "pass"
        # doc_04: has 2 approvals → pass
        assert results[3]["result"] == "pass"

        # col_06: step OP20 has no items → fail
        assert results[5]["result"] == "fail"
        # col_07: both items have description → pass
        assert results[6]["result"] == "pass"
        # col_08: both items have spec → pass
        assert results[7]["result"] == "pass"
        # col_09: both items have measurement_method → pass
        assert results[8]["result"] == "pass"

        # spec_12: no empty special_classification → pass
        assert results[11]["result"] == "pass"
        # spec_13: CC item has sample_frequency "1/hr" → pass
        assert results[12]["result"] == "pass"
        # spec_14: CC item has measurement_method → pass
        assert results[13]["result"] == "pass"
        # spec_15: CC item uses SPC → pass
        assert results[14]["result"] == "pass"

        # rp_16: both items have reaction_plan → pass
        assert results[15]["result"] == "pass"
        # rp_17: has reaction plans with "停" keyword → pass
        assert results[16]["result"] == "pass"
        # rp_18: item2 "停线通知主管" lacks disposal keywords → warning
        assert results[17]["result"] == "warning"
        # rp_19: has "通知" keyword → pass
        assert results[18]["result"] == "pass"
        # rp_20: item2 lacks "恢复" keyword → warning
        assert results[19]["result"] == "warning"

        # life_22: has prepared → pass
        assert results[21]["result"] == "pass"
        # life_23: step "OP10" matches pattern → pass
        assert results[22]["result"] == "pass"
        # life_24: no duplicates → pass
        assert results[23]["result"] == "pass"
        # life_25: no EP/MP items → skip
        assert results[24]["result"] == "skip"

    def test_audit_special_chars(self, db_path, plan, step):
        """有 CC 特殊特性但缺少测量方法的，应 warning (check #15)"""
        # Create CC item with manual control method (non-recommended)
        its.create_item(
            step["id"], plan["id"],
            char_number="CH-CC-01",
            char_type="product",
            char_description="Critical diameter",
            special_classification="CC",
            specification="10.0±0.1",
            measurement_method="Caliper",
            control_method_type="manual",  # SPC/EP/MP recommended → warning
            sample_size="5",
            sample_frequency="1/hr",
        )

        results = audit_control_plan(plan["id"])

        # spec_15: CC with manual → warning
        assert results[14]["result"] == "warning", f"Expected warning, got {results[14]['result']}"
        assert "非推荐" in results[14]["detail"]

    def test_audit_duplicate_char_number(self, db_path, plan, step):
        """重复特性编号，应 fail"""
        its.create_item(
            step["id"], plan["id"],
            char_number="DUP-001",
            specification="10",
        )
        its.create_item(
            step["id"], plan["id"],
            char_number="DUP-001",  # duplicate!
            specification="20",
        )

        results = audit_control_plan(plan["id"])

        # life_24: duplicate char numbers → fail
        assert results[23]["result"] == "fail", f"Expected fail, got {results[23]['result']}"
        assert "重复" in results[23]["detail"] or "DUP-001" in results[23]["detail"]

    def test_audit_ep_without_verification(self, db_path, plan, step):
        """EP 方法但没有验证频次，应 fail"""
        its.create_item(
            step["id"], plan["id"],
            char_number="EP-001",
            control_method_type="EP",
            # ep_verification_freq intentionally missing
            specification="10",
            measurement_method="Gauge",
            sample_size="3",
            sample_frequency="每批",
        )

        results = audit_control_plan(plan["id"])

        # life_25: EP without verification freq → fail
        assert results[24]["result"] == "fail", f"Expected fail, got {results[24]['result']}"
        assert "缺失验证频次" in results[24]["detail"]

    def test_audit_plan_not_found(self, db_path):
        """不存在的 plan_id → ValueError"""
        import re
        with pytest.raises(ValueError, match=re.escape("plan_id=99999 not found")):
            audit_control_plan(99999)

    def test_audit_all_items_missing_fields(self, db_path, plan, step):
        """所有控制项缺描述/规格/测量方法/样本量/频率 → 全部 fail"""
        its.create_item(
            step["id"], plan["id"],
            # No char_description, specification, measurement_method,
            # sample_size, sample_frequency
            char_number="BAD-01",
        )

        results = audit_control_plan(plan["id"])

        # col_07: missing char_description → fail
        assert results[6]["result"] == "fail"
        # col_08: missing specification → fail
        assert results[7]["result"] == "fail"
        # col_09: missing measurement_method → fail
        assert results[8]["result"] == "fail"
        # col_10: missing sample_size → fail
        assert results[9]["result"] == "fail"
        # col_11: missing sample_frequency → fail
        assert results[10]["result"] == "fail"

    def test_audit_empty_special_classification(self, db_path, plan, step):
        """special_classification 为 NULL → spec_12 pass (NULL ≠ 空字符串)；
        但 spec_14 会跳过（NULL 视为 none）"""
        its.create_item(
            step["id"], plan["id"],
            char_number="NULL-SPEC",
            # special_classification not set (DB default is 'none', but
            # the CHECK constraint prevents empty string anyway)
            specification="10",
            measurement_method="Gauge",
            sample_size="1",
            sample_frequency="每批",
        )

        results = audit_control_plan(plan["id"])
        # spec_12: with default 'none' → pass since 'none' != ''
        assert results[11]["result"] == "pass"

    def test_audit_sc_item_low_frequency(self, db_path, plan, step):
        """SC 项用低频率 -> spec_13 fail"""
        its.create_item(
            step["id"], plan["id"],
            char_number="SC-LOW",
            special_classification="SC",
            specification="10",
            measurement_method="Gauge",
            sample_size="5",
            sample_frequency="每批",  # low frequency
        )

        results = audit_control_plan(plan["id"])
        assert results[12]["result"] == "fail", f"Expected fail, got {results[12]['result']}"

    def test_audit_cc_sc_without_measurement(self, db_path, plan, step):
        """特殊特性项缺少测量方法 -> spec_14 fail"""
        its.create_item(
            step["id"], plan["id"],
            char_number="CC-NO-MEAS",
            special_classification="CC",
            specification="10",
            # measurement_method missing
            sample_size="5",
            sample_frequency="1/hr",
        )

        results = audit_control_plan(plan["id"])
        assert results[13]["result"] == "fail", f"Expected fail, got {results[13]['result']}"
        assert "缺失测量方法" in results[13]["detail"]

    def test_audit_cc_sc_recommended_method(self, db_path, plan, step):
        """CC/SC 用 SPC/EP/MP -> spec_15 pass"""
        its.create_item(
            step["id"], plan["id"],
            char_number="CC-SPC",
            special_classification="CC",
            specification="10",
            measurement_method="Caliper",
            control_method_type="SPC",
            sample_size="5",
            sample_frequency="1/hr",
        )

        results = audit_control_plan(plan["id"])
        assert results[14]["result"] == "pass", f"Expected pass, got {results[14]['result']}"

    def test_audit_steps_bad_numbering(self, db_path, plan):
        """步骤编号格式不合理 -> life_23 fail"""
        conn = db.get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO process_steps (plan_id, step_number, step_name, sort_order) "
                "VALUES (?, ?, ?, ?)",
                (plan["id"], "bad-format", "Weird Step", 0),
            )
            conn.commit()
        finally:
            conn.close()

        results = audit_control_plan(plan["id"])
        assert results[22]["result"] == "fail", f"Expected fail, got {results[22]['result']}"

    def test_audit_ep_with_verification(self, db_path, plan, step):
        """EP 方法且有验证频次 -> life_25 pass"""
        its.create_item(
            step["id"], plan["id"],
            char_number="EP-OK",
            control_method_type="EP",
            ep_verification_freq="每班",
            specification="10",
            measurement_method="Gauge",
            sample_size="3",
            sample_frequency="每批",
        )

        results = audit_control_plan(plan["id"])
        assert results[24]["result"] == "pass", f"Expected pass, got {results[24]['result']}"

    def test_audit_reaction_no_stop_keyword(self, db_path, plan, step):
        """反应计划不含停/续关键词 -> rp_17 warning"""
        its.create_item(
            step["id"], plan["id"],
            char_number="RP-NO-STOP",
            specification="10",
            measurement_method="Gauge",
            sample_size="1",
            sample_frequency="1/hr",
            reaction_plan="通知主管处理",
        )

        its.create_item(
            step["id"], plan["id"],
            char_number="RP-NO-STOP2",
            specification="20",
            measurement_method="Gauge",
            sample_size="1",
            sample_frequency="1/hr",
            reaction_plan="重新检验",
        )

        results = audit_control_plan(plan["id"])
        assert results[16]["result"] == "warning", f"Expected warning, got {results[16]['result']}"

    def test_audit_rp_17_no_reaction_plan_at_all(self, db_path, plan, step):
        """所有项都没有反应计划 -> rp_17 skip"""
        its.create_item(
            step["id"], plan["id"],
            char_number="NO-RP",
            specification="10",
            # no reaction_plan
        )

        results = audit_control_plan(plan["id"])
        # rp_16: missing reaction_plan -> fail
        assert results[15]["result"] == "fail"
        # rp_17: none have reaction_plan -> skip
        assert results[16]["result"] == "skip"
