# CP Manager — AIAG 控制计划管理器

基于 **AIAG Control Plan 1st Edition (2024)** 的独立控制计划管理桌面应用。

## 功能

- **三阶段控制计划**：Prototype → Pre-Launch → Production
- **12 列 AIAG 标准表体**：产品特性/过程特性分行编辑
- **Safe Launch 全流程**：启动、倒计时（默认 90 天）、加强措施、退出判定
- **25 项审计清单**：自动检查合规性，CSV 导出
- **Excel 导出**：AIAG 标准 15 列格式（含 2024 新增 RESP/EP/MP 验证列）
- **Foundation 模板派生**：从已有计划一键创建新计划
- **评审签署工作流**：draft → review → approved → obsolete
- **反应计划模板库**：6 个预设模板 + 自定义 CRUD
- **EP/MP 防错分类** + 特殊特性标记 (CC/SC/KPC/OSC/HI)
- **Catppuccin 双主题**：Latte（亮色）/ Mocha（暗色）

## 技术栈

- Python 3.11 + PySide6 6.11.0
- SQLite (sqlite3) + openpyxl
- 45 个单元测试（pytest）

## 快速开始

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install PySide6 openpyxl pytest

# 运行
python main.py

# 测试
python -m pytest tests/ -q
```

## 项目结构

```
main.py              # 入口
styles/theme.py      # Catppuccin 双主题系统
db/                  # SQLite schema + 连接
services/            # 7 个业务服务 (48 函数)
views/               # 8 个页面 + 3 个编辑对话框
core/                # 审计引擎 + 预设模板
export/              # AIAG Excel 导出
widgets/             # 侧边栏导航
tests/               # 45 个测试
```

## 数据存储

- 数据库：`~/.cp-manager/cp-manager.db`
- 10 张表：projects, control_plans, process_steps, cp_items, reaction_templates, team_members, approvals, change_records, settings, schema_version

## License

MIT
