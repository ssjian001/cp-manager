"""Audit Engine — 25项 CP 审计清单自动检查 (基于 CP 1st Edition / iFactory)."""

from __future__ import annotations

import db.database as db
from services.approval_service import list_approvals, list_team_members
from services.plan_service import get_plan

# ── Default "production-level" frequencies that CC/SC items should exceed ──
_LOW_FREQ_PATTERNS = {"每批", "1/批", "每班", "1/班", "每箱", "1/箱", "每托盘", "1/托盘", ""}

# ════════════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ════════════════════════════════════════════════════════════════════════════════


def _audit_result(
    check_id: int,
    category: str,
    check: str,
    result: str,
    detail: str,
) -> dict:
    return {
        "id": check_id,
        "category": category,
        "check": check,
        "result": result,
        "detail": detail,
    }


def _fetch_plan_data(plan_id: int) -> tuple:
    """Fetch plan, team_members, approvals, steps, items, items_by_step.

    Returns (plan, team_members, approvals, steps, items, items_by_step).
    On error raises ValueError.
    """
    plan = get_plan(plan_id)
    if not plan:
        raise ValueError(f"plan_id={plan_id} not found")

    team_members = list_team_members(plan_id)
    approvals = list_approvals(plan_id)

    conn = db.get_connection()
    try:
        steps_raw = conn.execute(
            "SELECT * FROM process_steps WHERE plan_id = ? ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        steps = [dict(r) for r in steps_raw]

        items_raw = conn.execute(
            "SELECT * FROM cp_items WHERE plan_id = ? ORDER BY sort_order",
            (plan_id,),
        ).fetchall()
        items = [dict(r) for r in items_raw]
    finally:
        conn.close()

    items_by_step: dict[int, list[dict]] = {}
    for item in items:
        items_by_step.setdefault(item["step_id"], []).append(item)

    return plan, team_members, approvals, steps, items, items_by_step


# ════════════════════════════════════════════════════════════════════════════════
#  Individual check functions
# ════════════════════════════════════════════════════════════════════════════════

# ── 文档控制 (5项) ────────────────────────────────────────────────────────────


def _check_doc_01(plan: dict, **_) -> dict:
    """1. 控制计划有编号"""
    cp = (plan.get("cp_number") or "").strip()
    return _audit_result(
        1, "文档控制", "控制计划有编号",
        "pass" if cp else "fail",
        f"编号: {cp or '(空)'}",
    )


def _check_doc_02(plan: dict, **_) -> dict:
    """2. 控制计划有创建/修订日期"""
    dt = plan.get("created_at") or ""
    return _audit_result(
        2, "文档控制", "控制计划有创建/修订日期",
        "pass" if dt else "fail",
        f"创建日期: {dt or '(空)'}",
    )


def _check_doc_03(plan: dict, team_members: list, **_) -> dict:
    """3. 有跨职能团队"""
    cnt = len(team_members)
    return _audit_result(
        3, "文档控制", "有跨职能团队（≥1 人）",
        "pass" if cnt >= 1 else "fail",
        f"团队成员数: {cnt}",
    )


def _check_doc_04(plan: dict, approvals: list, **_) -> dict:
    """4. 有签署记录"""
    cnt = len(approvals)
    return _audit_result(
        4, "文档控制", "有签署记录（≥1 条）",
        "pass" if cnt >= 1 else "fail",
        f"签署记录数: {cnt}",
    )


def _check_doc_05(**_) -> dict:
    """5. PFMEA 链接存在（跳过）"""
    return _audit_result(
        5, "文档控制", "PFMEA 链接存在",
        "skip",
        "本项目暂无 PFMEA 表，跳过检查",
    )


# ── 列完整性 (6项) ────────────────────────────────────────────────────────────


def _check_col_06(plan: dict, steps: list, items_by_step: dict, **_) -> dict:
    """6. 每个过程步骤至少有 1 个控制项"""
    empty_steps = [s for s in steps if s["id"] not in items_by_step or not items_by_step[s["id"]]]
    return _audit_result(
        6, "列完整性", "每个过程步骤至少有 1 个控制项",
        "pass" if not empty_steps else "fail",
        f"共 {len(steps)} 个步骤，{len(empty_steps)} 个无控制项: {[s['step_number'] for s in empty_steps]}" if empty_steps
        else f"共 {len(steps)} 个步骤，全部有控制项",
    )


def _check_col_07(plan: dict, items: list, **_) -> dict:
    """7. 所有控制项有特性描述"""
    empty = [i for i in items if not (i.get("char_description") or "").strip()]
    return _audit_result(
        7, "列完整性", "所有控制项有特性描述",
        "pass" if not empty else "fail",
        f"共 {len(items)} 项，{len(empty)} 项缺失",
    )


def _check_col_08(plan: dict, items: list, **_) -> dict:
    """8. 所有控制项有规格/公差"""
    empty = [i for i in items if not (i.get("specification") or "").strip()]
    return _audit_result(
        8, "列完整性", "所有控制项有规格/公差",
        "pass" if not empty else "fail",
        f"共 {len(items)} 项，{len(empty)} 项缺失",
    )


def _check_col_09(plan: dict, items: list, **_) -> dict:
    """9. 所有控制项有测量方法"""
    empty = [i for i in items if not (i.get("measurement_method") or "").strip()]
    return _audit_result(
        9, "列完整性", "所有控制项有测量方法",
        "pass" if not empty else "fail",
        f"共 {len(items)} 项，{len(empty)} 项缺失",
    )


def _check_col_10(plan: dict, items: list, **_) -> dict:
    """10. 所有控制项有样本量"""
    empty = [i for i in items if not (i.get("sample_size") or "").strip()]
    return _audit_result(
        10, "列完整性", "所有控制项有样本量",
        "pass" if not empty else "fail",
        f"共 {len(items)} 项，{len(empty)} 项缺失",
    )


def _check_col_11(plan: dict, items: list, **_) -> dict:
    """11. 所有控制项有样本频率"""
    empty = [i for i in items if not (i.get("sample_frequency") or "").strip()]
    return _audit_result(
        11, "列完整性", "所有控制项有样本频率",
        "pass" if not empty else "fail",
        f"共 {len(items)} 项，{len(empty)} 项缺失",
    )


# ── 特殊特性 (4项) ────────────────────────────────────────────────────────────


def _check_spec_12(plan: dict, items: list, **_) -> dict:
    """12. 特殊特性项有分类标记（空字符串不行，'none' 可以）"""
    bad = [i for i in items if i.get("special_classification") == ""]
    return _audit_result(
        12, "特殊特性", "特殊特性项有分类标记（不得为空字符串）",
        "pass" if not bad else "fail",
        f"{len(bad)} 项 special_classification 为空字符串",
    )


def _check_spec_13(plan: dict, items: list, **_) -> dict:
    """13. 特殊特性项有加强控制 — CC/SC 项的 sample_frequency 不为通用低频率"""
    ccsc = [i for i in items if i.get("special_classification") in ("CC", "SC")]
    if not ccsc:
        return _audit_result(13, "特殊特性", "CC/SC 项有加强控制（高采样频率）",
                             "skip", "无 CC/SC 项")
    low_freq = [
        i for i in ccsc
        if (i.get("sample_frequency") or "").strip().lower() in _LOW_FREQ_PATTERNS
    ]
    return _audit_result(
        13, "特殊特性", "CC/SC 项有加强控制（高采样频率）",
        "fail" if low_freq else "pass",
        f"CC/SC 共 {len(ccsc)} 项，{len(low_freq)} 项频率过低: {[i.get('char_number','?') for i in low_freq]}" if low_freq
        else f"CC/SC 共 {len(ccsc)} 项，全部频率合理",
    )


def _check_spec_14(plan: dict, items: list, **_) -> dict:
    """14. 特殊特性项有测量方法（special_classification != 'none' 的项必须有）"""
    special = [i for i in items if i.get("special_classification", "none") != "none"]
    missing = [i for i in special if not (i.get("measurement_method") or "").strip()]
    return _audit_result(
        14, "特殊特性", "特殊特性项有测量方法",
        "pass" if not missing else "fail",
        f"特殊特性共 {len(special)} 项，{len(missing)} 项缺失测量方法",
    )


def _check_spec_15(plan: dict, items: list, **_) -> dict:
    """15. 控制方法与特性匹配 — CC/SC 项建议用 SPC/EP/MP"""
    ccsc = [i for i in items if i.get("special_classification") in ("CC", "SC")]
    if not ccsc:
        return _audit_result(15, "特殊特性", "CC/SC 项控制方法建议为 SPC/EP/MP",
                             "skip", "无 CC/SC 项")
    recommended = {"SPC", "EP", "MP"}
    bad = [i for i in ccsc if i.get("control_method_type") not in recommended]
    return _audit_result(
        15, "特殊特性", "CC/SC 项控制方法建议为 SPC/EP/MP",
        "warning" if bad else "pass",
        f"CC/SC 共 {len(ccsc)} 项，{len(bad)} 项方法非推荐: {[i.get('char_number','?') for i in bad]}" if bad
        else f"CC/SC 共 {len(ccsc)} 项，全部方法推荐",
    )


# ── 反应计划 (5项) ────────────────────────────────────────────────────────────


def _check_rp_16(plan: dict, items: list, **_) -> dict:
    """16. 所有控制项有反应计划"""
    missing = [i for i in items if not (i.get("reaction_plan") or "").strip()]
    return _audit_result(
        16, "反应计划", "所有控制项有反应计划",
        "pass" if not missing else "fail",
        f"共 {len(items)} 项，{len(missing)} 项缺失",
    )


def _check_rp_17(plan: dict, items: list, **_) -> dict:
    """17. 反应计划包含停/续决策"""
    bad = [
        i for i in items
        if (i.get("reaction_plan") or "")
        and not any(kw in (i["reaction_plan"] or "") for kw in ("停", "继续", "stop"))
    ]
    total_with_rp = [i for i in items if (i.get("reaction_plan") or "").strip()]
    if not total_with_rp:
        return _audit_result(17, "反应计划", "反应计划包含停/续决策",
                             "skip", "无项目有反应计划")
    return _audit_result(
        17, "反应计划", "反应计划包含停/续决策",
        "warning" if bad else "pass",
        f"有反应计划共 {len(total_with_rp)} 项，{len(bad)} 项不含停/续关键词",
    )


def _check_rp_18(plan: dict, items: list, **_) -> dict:
    """18. 反应计划包含产品处置"""
    bad = [
        i for i in items
        if (i.get("reaction_plan") or "")
        and not any(kw in (i["reaction_plan"] or "") for kw in ("隔离", "挑选", "报废", "isolate"))
    ]
    total_with_rp = [i for i in items if (i.get("reaction_plan") or "").strip()]
    if not total_with_rp:
        return _audit_result(18, "反应计划", "反应计划包含产品处置",
                             "skip", "无项目有反应计划")
    return _audit_result(
        18, "反应计划", "反应计划包含产品处置",
        "warning" if bad else "pass",
        f"有反应计划共 {len(total_with_rp)} 项，{len(bad)} 项不含处置关键词",
    )


def _check_rp_19(plan: dict, items: list, **_) -> dict:
    """19. 反应计划包含通知对象"""
    bad = [
        i for i in items
        if (i.get("reaction_plan") or "")
        and not any(kw in (i["reaction_plan"] or "") for kw in ("通知", "notify"))
    ]
    total_with_rp = [i for i in items if (i.get("reaction_plan") or "").strip()]
    if not total_with_rp:
        return _audit_result(19, "反应计划", "反应计划包含通知对象",
                             "skip", "无项目有反应计划")
    return _audit_result(
        19, "反应计划", "反应计划包含通知对象",
        "warning" if bad else "pass",
        f"有反应计划共 {len(total_with_rp)} 项，{len(bad)} 项不含通知关键词",
    )


def _check_rp_20(plan: dict, items: list, **_) -> dict:
    """20. 反应计划包含恢复条件"""
    bad = [
        i for i in items
        if (i.get("reaction_plan") or "")
        and not any(kw in (i["reaction_plan"] or "") for kw in ("恢复", "resume"))
    ]
    total_with_rp = [i for i in items if (i.get("reaction_plan") or "").strip()]
    if not total_with_rp:
        return _audit_result(20, "反应计划", "反应计划包含恢复条件",
                             "skip", "无项目有反应计划")
    return _audit_result(
        20, "反应计划", "反应计划包含恢复条件",
        "warning" if bad else "pass",
        f"有反应计划共 {len(total_with_rp)} 项，{len(bad)} 项不含恢复关键词",
    )


# ── 生命周期 (5项) ────────────────────────────────────────────────────────────


def _check_life_21(**_) -> dict:
    """21. 控制计划状态不是 draft 才可能有修订（信息性）"""
    return _audit_result(
        21, "生命周期", "控制计划修订记录（信息性检查）",
        "skip",
        "此检查为信息性，不判定 pass/fail",
    )


def _check_life_22(plan: dict, approvals: list, **_) -> dict:
    """22. 控制计划有负责人（prepared 签署）"""
    prepared = [a for a in approvals if a.get("approval_type") == "prepared"]
    return _audit_result(
        22, "生命周期", "控制计划有负责人（prepared 签署）",
        "pass" if prepared else "fail",
        f"prepared 签署: {len(prepared)} 条",
    )


def _check_life_23(plan: dict, steps: list, **_) -> dict:
    """23. 过程步骤编号连续（OP10, OP20... 格式合理）"""
    import re
    if not steps:
        return _audit_result(23, "生命周期", "过程步骤编号连续",
                             "fail", "无过程步骤")
    # Check that all step_numbers match OP\d+ pattern
    pattern = re.compile(r"^(OP|op|Op)?\d+")
    bad = [s for s in steps if not pattern.match(s.get("step_number", ""))]
    return _audit_result(
        23, "生命周期", "过程步骤编号格式合理（如 OP10, OP20）",
        "fail" if bad else "pass",
        f"共 {len(steps)} 个步骤，{len(bad)} 个编号格式异常: {[s['step_number'] for s in bad]}" if bad
        else f"共 {len(steps)} 个步骤，编号格式均合理",
    )


def _check_life_24(plan: dict, items: list, **_) -> dict:
    """24. 没有重复的特性编号"""
    char_nums = [i.get("char_number", "") for i in items if i.get("char_number")]
    duplicates = {cn for cn in char_nums if char_nums.count(cn) > 1}
    return _audit_result(
        24, "生命周期", "没有重复的特性编号",
        "fail" if duplicates else "pass",
        f"重复编号: {sorted(duplicates)}" if duplicates else "所有编号唯一",
    )


def _check_life_25(plan: dict, items: list, **_) -> dict:
    """25. EP/MP 项有验证频次"""
    epmp = [i for i in items if i.get("control_method_type") in ("EP", "MP")]
    if not epmp:
        return _audit_result(25, "生命周期", "EP/MP 项有验证频次",
                             "skip", "无 EP/MP 项")
    missing = [
        i for i in epmp
        if not (i.get("ep_verification_freq") or "").strip()
    ]
    return _audit_result(
        25, "生命周期", "EP/MP 项有验证频次",
        "fail" if missing else "pass",
        f"EP/MP 共 {len(epmp)} 项，{len(missing)} 项缺失验证频次",
    )


# ════════════════════════════════════════════════════════════════════════════════
#  Check registry (ordered by ID)
# ════════════════════════════════════════════════════════════════════════════════

_CHECKS: list[dict] = [
    # (id, category, check, func)
    # 文档控制 (1-5)
    {"id": 1, "category": "文档控制", "check": "控制计划有编号", "func": _check_doc_01},
    {"id": 2, "category": "文档控制", "check": "控制计划有创建/修订日期", "func": _check_doc_02},
    {"id": 3, "category": "文档控制", "check": "有跨职能团队（≥1 人）", "func": _check_doc_03},
    {"id": 4, "category": "文档控制", "check": "有签署记录（≥1 条）", "func": _check_doc_04},
    {"id": 5, "category": "文档控制", "check": "PFMEA 链接存在", "func": _check_doc_05},
    # 列完整性 (6-11)
    {"id": 6, "category": "列完整性", "check": "每个过程步骤至少有 1 个控制项", "func": _check_col_06},
    {"id": 7, "category": "列完整性", "check": "所有控制项有特性描述", "func": _check_col_07},
    {"id": 8, "category": "列完整性", "check": "所有控制项有规格/公差", "func": _check_col_08},
    {"id": 9, "category": "列完整性", "check": "所有控制项有测量方法", "func": _check_col_09},
    {"id": 10, "category": "列完整性", "check": "所有控制项有样本量", "func": _check_col_10},
    {"id": 11, "category": "列完整性", "check": "所有控制项有样本频率", "func": _check_col_11},
    # 特殊特性 (12-15)
    {"id": 12, "category": "特殊特性", "check": "特殊特性项有分类标记（不得为空字符串）", "func": _check_spec_12},
    {"id": 13, "category": "特殊特性", "check": "CC/SC 项有加强控制（高采样频率）", "func": _check_spec_13},
    {"id": 14, "category": "特殊特性", "check": "特殊特性项有测量方法", "func": _check_spec_14},
    {"id": 15, "category": "特殊特性", "check": "CC/SC 项控制方法建议为 SPC/EP/MP", "func": _check_spec_15},
    # 反应计划 (16-20)
    {"id": 16, "category": "反应计划", "check": "所有控制项有反应计划", "func": _check_rp_16},
    {"id": 17, "category": "反应计划", "check": "反应计划包含停/续决策", "func": _check_rp_17},
    {"id": 18, "category": "反应计划", "check": "反应计划包含产品处置", "func": _check_rp_18},
    {"id": 19, "category": "反应计划", "check": "反应计划包含通知对象", "func": _check_rp_19},
    {"id": 20, "category": "反应计划", "check": "反应计划包含恢复条件", "func": _check_rp_20},
    # 生命周期 (21-25)
    {"id": 21, "category": "生命周期", "check": "控制计划修订记录（信息性）", "func": _check_life_21},
    {"id": 22, "category": "生命周期", "check": "控制计划有负责人（prepared 签署）", "func": _check_life_22},
    {"id": 23, "category": "生命周期", "check": "过程步骤编号格式合理（如 OP10, OP20）", "func": _check_life_23},
    {"id": 24, "category": "生命周期", "check": "没有重复的特性编号", "func": _check_life_24},
    {"id": 25, "category": "生命周期", "check": "EP/MP 项有验证频次", "func": _check_life_25},
]

# ════════════════════════════════════════════════════════════════════════════════
#  Public API
# ════════════════════════════════════════════════════════════════════════════════


def audit_control_plan(plan_id: int) -> list[dict]:
    """审计控制计划，返回 25 项检查结果列表。

    每项: {"id": int, "category": str, "check": str,
            "result": "pass"|"fail"|"warning"|"skip", "detail": str}

    Raises ValueError if plan_id not found.
    """
    plan, team_members, approvals, steps, items, items_by_step = _fetch_plan_data(plan_id)

    ctx = {
        "plan": plan,
        "team_members": team_members,
        "approvals": approvals,
        "steps": steps,
        "items": items,
        "items_by_step": items_by_step,
    }

    results: list[dict] = []
    for check in _CHECKS:
        try:
            result = check["func"](**ctx)
        except Exception as exc:
            result = _audit_result(
                check["id"], check["category"], check["check"],
                "fail", f"检查异常: {exc}",
            )
        results.append(result)

    return results
