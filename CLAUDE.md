# CLAUDE.md — CP Manager (控制计划管理器)

基于 AIAG Control Plan 1st Edition (2024) 的独立控制计划管理工具。

## 运行
```bash
cd ~/Desktop/AI/xiangmu/cp-manager-py
.venv/bin/python main.py
```
- 测试：`.venv/bin/python -m pytest tests/ -q`

## 技术栈
- Python 3.11 + PySide6 6.11.0 + SQLite (sqlite3) + openpyxl
- 架构：控制计划三阶段(Prototype/Pre-Launch/Production) + Safe Launch
- 主题：Catppuccin Latte/Mocha 双主题（styles/theme.py）
- DB：10 张表，~/.cp-manager/cp-manager.db

## 项目结构
```
main.py              # 入口（_FusionProxy + 持久化主题加载）
styles/
  theme.py           # 主题系统
views/
  main_window.py     # 主窗口 + 侧边栏导航
  dashboard_view.py  # 仪表盘
  cp_editor_view.py  # 控制计划编辑器（12列表格）
  safe_launch_view.py # Safe Launch 面板
  settings_view.py   # 设置（主题切换）
views/editors/
  cp_item_editor.py  # 控制项目编辑对话框
  plan_header_editor.py # 控制计划表头编辑
services/
  project_service.py
  plan_service.py
  item_service.py
  reaction_service.py
  approval_service.py
db/
  database.py        # SQLite 连接
  schema.sql         # DDL
widgets/
  sidebar.py         # 侧边栏
core/
  constants.py       # 常量
```

## 主题系统
- 遵循 skill:software-development/pyside6-theme-setup 的 6 条强制规则
- styles/theme.py — Catppuccin Latte/Mocha 双色板
- 所有内联 setStyleSheet 必须 `import styles.theme as _t` 动态引用
- 主题切换入口：Settings → 下拉框

## 已知 Qt 坑
- QWidget 全局背景不能用 transparent → 必须用主题基色
- 主题必须在创建第一个 widget 之前加载 → 持久化到 DB，启动前读取
- from theme import X 冻结快照 → 必须用 import theme as _t
- QScrollArea viewport QSS 管不到 → 必须用 QPalette + autoFillBackground
- Windows 暗色系统主题污染 → Fusion + QProxyStyle + 动态 setColorScheme
- QPushButton transparent + border:none 在 Windows 上不可见 → 必须有可见背景
- QSS 不支持 #RRGGBBAA 8 位 hex → 用 rgba()
- setProperty 动态属性不改视觉 → unpolish + polish

## 开发规范
- Schema 第一：新功能先读 db/schema.sql 确认列名
- 语法先行：每写完一个文件立即 py_compile 验证
- 提交单位：每个逻辑单元单独 commit
- 编辑模式：用 patch 不用 write_file
- 显式列名：SELECT 避免用 *
