"""MainWindow — 主窗口 + Sidebar + QStackedWidget 导航"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from widgets.sidebar import Sidebar

import styles.theme as _t


class MainWindow(QMainWindow):
    """主窗口：左侧 Sidebar + 右侧 QStackedWidget 页面容器。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CP Manager — 控制计划管理器")
        self.resize(1280, 820)

        # ── Central widget ──
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Sidebar ──
        self._sidebar = Sidebar()
        layout.addWidget(self._sidebar)

        # ── Stacked widget ──
        self._stack = QStackedWidget()
        self._stack.setProperty("class", "bg-base")
        layout.addWidget(self._stack, stretch=1)

        # ── Connect sidebar navigation ──
        self._sidebar.nav_clicked.connect(self._stack.setCurrentIndex)

        # ── Subscribe theme ──
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

        self._pages: dict[str, QWidget] = {}

    # ────────────────────────────────────────────────────────────────
    #  Public API
    # ────────────────────────────────────────────────────────────────

    def add_page(self, name: str, widget: QWidget) -> None:
        """添加页面到 QStackedWidget，name 用于导航标识。"""
        self._pages[name] = widget
        self._stack.addWidget(widget)

    @property
    def sidebar(self) -> Sidebar:
        return self._sidebar

    @property
    def stack(self) -> QStackedWidget:
        return self._stack

    def navigate_to(self, name: str) -> None:
        """按页面名称导航。"""
        if name in self._pages:
            idx = self._stack.indexOf(self._pages[name])
            if idx >= 0:
                self._sidebar.set_current_index(idx)
                self._stack.setCurrentIndex(idx)

    def navigate_to_index(self, index: int) -> None:
        """按索引导航（0=仪表盘, 1=控制计划, ...）。"""
        if 0 <= index < self._stack.count():
            self._sidebar.set_current_index(index)
            self._stack.setCurrentIndex(index)

    # ────────────────────────────────────────────────────────────────
    #  Theme
    # ────────────────────────────────────────────────────────────────

    def _on_theme_changed(self, _name: str) -> None:
        """主题切换后刷新 main window 背景。"""
        self.style().unpolish(self)
        self.style().polish(self)
