"""CP Manager — 控制计划管理器
入口文件：_FusionProxy + 持久化主题加载 + 全部 View 初始化
"""

import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)


class _FusionProxy(QProxyStyle):
    """拦截 standardPalette 防止 Windows 暗色系统主题污染 Fusion 调色板。

    Qt 6.5+ 在 Windows 上会读取系统主题覆盖 Fusion 的 palette，
    导致暗色模式污染亮色主题。此代理在每次 palette 请求时强制返回
    Fusion 原生的 palette。
    """

    def standardPalette(self) -> QPalette:
        return QStyleFactory.create("Fusion").standardPalette()


def main() -> None:
    # ── Rule 2: 在创建 QApplication 之前设置环境变量 ──
    # 1. 强制 Fusion 风格，忽略系统主题
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
    # 2. 禁用平台主题插件（Qt 平台抽象层）
    os.environ["QT_QPA_PLATFORMTHEME"] = ""

    # 3. 创建应用实例
    app = QApplication(sys.argv)

    # 4. 显式设置 Fusion 风格 + 代理
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyle(_FusionProxy())

    # 5. 初始化数据库
    import db.database as db
    db.init_db()

    # 6. 读取持久化的主题名称
    from styles.theme import set_theme, get_stylesheet, apply_palette
    theme_name = db.read_setting("theme") or "light"

    # 7. 设置主题样式表
    set_theme(theme_name)
    app.setStyleSheet(get_stylesheet())
    apply_palette()

    # 8-9. 根据主题设置 ColorScheme
    scheme = (
        Qt.ColorScheme.Dark if theme_name == "dark" else Qt.ColorScheme.Light
    )
    app.styleHints().setColorScheme(scheme)

    # 10. 创建主窗口并初始化所有页面
    from views.main_window import MainWindow
    from views.dashboard_view import DashboardView
    from views.cp_editor_view import CpEditorView
    from views.safe_launch_view import SafeLaunchView
    from views.settings_view import SettingsView
    from views.reaction_library_view import ReactionLibraryView
    from views.audit_view import AuditView

    window = MainWindow()

    # 11. 创建并添加页面
    dashboard = DashboardView()
    cp_editor = CpEditorView()
    safe_launch = SafeLaunchView()
    reaction_lib = ReactionLibraryView()
    audit_view = AuditView()
    audit_view.refresh_plan_list()
    settings = SettingsView()

    window.add_page("dashboard", dashboard)
    window.add_page("cp_editor", cp_editor)
    window.add_page("safe_launch", safe_launch)
    window.add_page("reaction_library", reaction_lib)
    window.add_page("audit", audit_view)
    window.add_page("settings", settings)

    # Connect dashboard double-click to navigate to CP editor
    dashboard.open_cp_editor.connect(lambda plan_id: (
        cp_editor.load_plan(plan_id),
        window.navigate_to("cp_editor"),
    ))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
