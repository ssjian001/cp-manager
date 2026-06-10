# CP Manager — 功能交付文档

> 基于 AIAG Control Plan 1st Edition (2024) 的独立控制计划管理桌面应用
> 路径: `~/Desktop/AI/xiangmu/cp-manager-py/`
> 语言: Python 3.11 + PySide6 6.11.0 + SQLite (sqlite3) + openpyxl
> 状态: ✅ 已交付 (P1-P4, 7 commits, 45 tests)

## 启动

```bash
cd ~/Desktop/AI/xiangmu/cp-manager-py
.venv/bin/python main.py
```

测试：`.venv/bin/python -m pytest tests/ -q`

## 界面

8 个页面，通过左侧侧边栏导航：

| 页面 | 功能 |
|------|------|
| **仪表盘** | 项目选择、新建项目、控制计划列表（6列）、统计卡片（总计划/控制项/SL活跃/特殊特性）、双击跳转 CP 编辑器、导出 Excel |
| **控制计划编辑器** | 三阶段切换按钮、左侧过程步骤列表、右侧 12 列控制项目表格、添加/删除步骤或控制项、从模板派生、变更记录查看 |
| **Safe Launch** | 选择控制计划、启动/完成/归零重启、倒计时+进度条、加强措施列表、退出条件 |
| **反应计划库** | 6 个预设模板、添加/编辑/删除/设为默认、四要素结构化（停线/处置/通知/恢复） |
| **审计检查** | 25 项清单自动检查、颜色标记结果（绿/红/黄/灰）、统计栏、CSV 导出 |
| **评审签署** | 核心团队管理、编制/审核/批准签署记录、状态流转（draft→review→approved→obsolete） |
| **设置** | Catppuccin Latte/Mocha 双主题切换、关于信息 |

## 数据模型

10 张表，DB 路径 `~/.cp-manager/cp-manager.db`：

| 表 | 说明 |
|----|------|
| `projects` | 项目/产品信息（零件号、供应商、联系人） |
| `control_plans` | 控制计划（三阶段、Safe Launch、Foundation来源、状态） |
| `process_steps` | 过程步骤（OP10/OP20，设备，排序） |
| `cp_items` | 控制项目（12列+RESP+EP/MP验证，CP 1st Edition 2024） |
| `reaction_templates` | 反应计划模板库（四要素结构化） |
| `team_members` | 核心团队成员 |
| `approvals` | 评审签署记录（编制/审核/批准） |
| `change_records` | 变更记录 |
| `settings` | 配置（含主题偏好） |
| `schema_version` | 版本控制 |

### 控制项目关键字段

```
char_type: product / process            ← 产品特性/过程特性分行！
special_classification: none/CC/SC/KPC/OSC/HI/custom
control_method_type: SPC/EP/MP/visual/manual/auto
ep_verification_freq: str               ← EP/MP时必须填写
reaction_plan: str                      ← 完整四要素描述
```

### Safe Launch 关键字段

```
is_safe_launch: 0/1
safe_launch_start/end: datetime
safe_launch_duration_days: defaults to 90
safe_launch_fail_count: int            ← 归零重启时递增
safe_launch_exit_criteria: text
```

### 状态流转

```
draft ──[提交审核]──→ review ──[批准]──→ approved
   ↑──────────[提交审核]──────────↓
 any ──[作废]──→ obsolete
```

## 核心设计决策

- ⚠️ **主题系统**：Catppuccin Latte/Mocha，`import styles.theme as _t` 动态引用，拒绝 `from theme import X`（冻结快照）
- ⚠️ **QWidget 背景**：全局 QSS 用 `{BG_BASE}`，不设 `transparent`（Windows 透白）
- ⚠️ **启动顺序**：`os.environ` 设 Fusion → `QApplication` → `QProxyStyle` → `db.init_db()` → `set_theme()` → `setStyleSheet()` → `apply_palette()` → 最后才创建窗口
- ⚠️ **INSERT OR IGNORE**：幂等初始化，`INSERT OR IGNORE INTO schema_version VALUES(1)`
- ⚠️ **Excel 导出**：AIAG 标准 15 列格式，含 2024 新增 RESP/EP/MP 验证列

## 测试概况

45 个测试全部通过（0.9s）：

| 文件 | 测试数 | 覆盖 |
|------|--------|------|
| `tests/test_services.py` | 23 | project/plan/item/reaction/approval 服务层 |
| `tests/test_audit.py` | 5 | 审计引擎 25 项检查 |
| `tests/test_export.py` | 4 | Excel 导出格式 |
| `tests/test_p4.py` | 13 | step/change/presets/approval workflow |

## 文件清单

37 个 .py 文件，9286 行代码：

```
main.py                     # 入口
styles/theme.py             # 1081行 QSS
db/database.py + schema.sql # 10 张表
services/ (7个)              # 48 个函数
views/ (8个 + 3个 editors)   # 全部页面
core/audit_engine.py        # 25 项审计
core/presets.py             # 6 个预设模板
export/excel_export.py      # AIAG Excel 导出
widgets/sidebar.py          # 8 个导航项
tests/ (4个)                 # 45 个测试
```
