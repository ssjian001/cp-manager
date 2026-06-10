"""Sidebar — 左侧导航面板"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class SidebarButton(QPushButton):
    """单个导航按钮（选中态高亮）。"""

    def __init__(self, text: str, page_index: int) -> None:
        super().__init__(text)
        self._page_index = page_index
        self.setProperty("class", "sidebarBtn")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(40)
        self.setStyleSheet(
            f"""
            QPushButton[class="sidebarBtn"] {{
                background: transparent;
                color: {_t.FG_SECONDARY};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton[class="sidebarBtn"]:hover {{
                background: {_t.BG_HOVER};
                color: {_t.FG_PRIMARY};
            }}
            QPushButton[class="sidebarBtn"]:checked {{
                background: {_t.BG_HOVER};
                color: {_t.FG_PRIMARY};
                font-weight: bold;
            }}
            """
        )

    @property
    def page_index(self) -> int:
        return self._page_index


class Sidebar(QWidget):
    """左侧导航面板，固定宽度 200px。"""

    nav_clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self.setFixedWidth(200)

        self._buttons: list[SidebarButton] = []
        self._current_index: int = 0

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        # ── Logo / title ──
        title = QLabel("CP Manager")
        title.setStyleSheet(
            f"""
            font-size: 16px;
            font-weight: bold;
            color: {_t.FG_PRIMARY};
            padding: 8px 8px 16px 8px;
            """
        )
        layout.addWidget(title)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_t.BORDER};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(8)

        # ── Navigation items ──
        nav_items = [
            "仪表盘",
            "控制计划",
            "Safe Launch",
            "反应计划库",
            "审计检查",
            "设置",
        ]
        for i, text in enumerate(nav_items):
            btn = SidebarButton(text, i)
            btn.clicked.connect(self._on_btn_clicked)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # ── Current project name (bottom) ──
        self._project_label = QLabel("当前项目: —")
        self._project_label.setStyleSheet(
            f"""
            color: {_t.FG_MUTED};
            font-size: 11px;
            padding: 8px;
            border-top: 1px solid {_t.BORDER};
            """
        )
        layout.addWidget(self._project_label)

        # Highlight first item
        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_btn_clicked(self) -> None:
        btn = self.sender()
        if not isinstance(btn, SidebarButton):
            return
        idx = btn.page_index
        if idx == self._current_index:
            return
        self._buttons[self._current_index].setChecked(False)
        self._buttons[idx].setChecked(True)
        self._current_index = idx
        self.nav_clicked.emit(idx)

    def set_current_index(self, index: int) -> None:
        """程序化切换导航项。"""
        if 0 <= index < len(self._buttons) and index != self._current_index:
            self._buttons[self._current_index].setChecked(False)
            self._buttons[index].setChecked(True)
            self._current_index = index

    def set_project_name(self, name: str) -> None:
        self._project_label.setText(f"当前项目: {name}")

    def _on_theme_changed(self, _name: str) -> None:
        """主题切换时刷新所有内联样式。"""
        for btn in self._buttons:
            btn.setStyleSheet(
                f"""
                QPushButton[class="sidebarBtn"] {{
                    background: transparent;
                    color: {_t.FG_SECONDARY};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    text-align: left;
                    font-size: 13px;
                }}
                QPushButton[class="sidebarBtn"]:hover {{
                    background: {_t.BG_HOVER};
                    color: {_t.FG_PRIMARY};
                }}
                QPushButton[class="sidebarBtn"]:checked {{
                    background: {_t.BG_HOVER};
                    color: {_t.FG_PRIMARY};
                    font-weight: bold;
                }}
                """
            )
        title_item = self.layout().itemAt(0)
        if title_item:
            w = title_item.widget()
            if isinstance(w, QLabel):
                w.setStyleSheet(
                    f"""
                    font-size: 16px;
                    font-weight: bold;
                    color: {_t.FG_PRIMARY};
                    padding: 8px 8px 16px 8px;
                    """
                )
        self._project_label.setStyleSheet(
            f"""
            color: {_t.FG_MUTED};
            font-size: 11px;
            padding: 8px;
            border-top: 1px solid {_t.BORDER};
            """
        )
        # Refresh sidebar background via property unpolish/polish
        self.style().unpolish(self)
        self.style().polish(self)
