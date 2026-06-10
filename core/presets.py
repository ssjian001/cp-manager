"""Reaction plan preset templates.

When the reaction_templates table is empty, these presets are auto-inserted
on application startup (called from main.py after db.init_db()).
"""

DEFAULT_REACTION_TEMPLATES = [
    {
        "name": "尺寸不合格",
        "stop_process": "停线，隔离可疑品",
        "product_disposition": "从上次合格品开始隔离，100%挑选",
        "notify_who": "通知线长和质量管理员",
        "recovery_condition": "根因查明并采取纠正措施后，经质量确认可恢复",
        "is_default": 1,
    },
    {
        "name": "外观缺陷",
        "stop_process": "继续生产，加强检验",
        "product_disposition": "从上次全检合格品开始隔离，100%目视检查",
        "notify_who": "通知班组长",
        "recovery_condition": "连续20件无缺陷后恢复正常检验",
        "is_default": 0,
    },
    {
        "name": "SPC失控",
        "stop_process": "停线，等待质量判定",
        "product_disposition": "隔离上次校准以来的所有产品",
        "notify_who": "通知质量工程师和生产经理",
        "recovery_condition": "重新校准量具，SPC点回到控制限内",
        "is_default": 1,
    },
    {
        "name": "EP/MP防错失效",
        "stop_process": "立即停线",
        "product_disposition": "从上次EP/MP验证合格品开始全部隔离",
        "notify_who": "通知质量经理和设备工程师",
        "recovery_condition": "防错装置修复并验证有效后恢复",
        "is_default": 0,
    },
    {
        "name": "安全特性不合格",
        "stop_process": "立即停线，启动8D",
        "product_disposition": "全部隔离，等待MRB判定（返工/报废/让步）",
        "notify_who": "通知质量总监、客户质量代表",
        "recovery_condition": "8D纠正措施验证有效，客户批准后恢复",
        "is_default": 1,
    },
    {
        "name": "来料异常",
        "stop_process": "继续生产（使用替代物料或库存）",
        "product_disposition": "隔离可疑批次来料，标识待检",
        "notify_who": "通知SQE和采购",
        "recovery_condition": "替代来料验证合格或供应商提供合格替换品",
        "is_default": 0,
    },
]


def ensure_reaction_templates() -> int:
    """Ensure preset reaction plan templates exist in the database.

    Returns:
        Number of templates inserted (0 if templates already exist).
    """
    import services.reaction_service as rs

    existing = rs.list_templates()
    if existing:
        return 0

    count = 0
    for tpl in DEFAULT_REACTION_TEMPLATES:
        rs.create_template(**tpl)
        count += 1
    return count
