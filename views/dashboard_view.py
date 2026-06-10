"""Dashboard View — 仪表盘页面"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class _StatCard(QFrame):
    """统计卡片组件。"""

    def __init__(self, title: str, value: str = "—", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "stat-card")
        self.setFixedSize(180, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {_t.FG_SECONDARY}; font-size: 11px; background: transparent;"
        )
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setProperty("class", "stat-value")
        self._value_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 20px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(self._value_label)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)

    def refresh_style(self) -> None:
        self._title_label.setStyleSheet(
            f"color: {_t.FG_SECONDARY}; font-size: 11px; background: transparent;"
        )
        self._value_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 20px; font-weight: bold; background: transparent;"
        )
        self.style().unpolish(self)
        self.style().polish(self)


class DashboardView(QWidget):
    """仪表盘页面。"""

    open_cp_editor = Signal(int)  # control_plan_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Header row ──
        header = QHBoxLayout()
        title = QLabel("仪表盘")
        title.setProperty("class", "pageTitle")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        header.addWidget(title)
        header.addStretch()

        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(200)
        self._project_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {_t.BG_INPUT};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }}
            """
        )
        header.addWidget(self._project_combo)

        self._new_project_btn = QPushButton("+ 新建项目")
        self._new_project_btn.setProperty("class", "primaryBtn")
        self._new_project_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #4c83f7;
            }}
            """
        )
        header.addWidget(self._new_project_btn)
        layout.addLayout(header)

        # ── Stat cards row ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        self._stat_cards = {
            "total_plans": _StatCard("总控制计划数", "—"),
            "total_items": _StatCard("控制项数", "—"),
            "safe_launch_active": _StatCard("Safe Launch 活跃数", "—"),
            "special_chars": _StatCard("特殊特性数", "—"),
        }
        for card in self._stat_cards.values():
            cards_layout.addWidget(card)
        cards_layout.addStretch()
        layout.addLayout(cards_layout)

        # ── Control plan list ──
        list_label = QLabel("控制计划列表")
        list_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(list_label)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            ["CP编号", "零件号", "阶段", "状态", "Safe Launch", "创建日期"]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {_t.BG_BASE};
                alternate-background-color: {_t.MANTLE};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                gridline-color: {_t.BORDER_LIGHT};
                selection-background-color: {_t.SURFACE0};
                selection-color: {_t.FG_PRIMARY};
            }}
            QHeaderView::section {{
                background: {_t.MANTLE};
                color: {_t.FG_PRIMARY};
                border: none;
                border-right: 1px solid {_t.BORDER_LIGHT};
                border-bottom: 1px solid {_t.BORDER_LIGHT};
                padding: 6px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
            """
        )
        self._table.itemDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table, stretch=1)

    def _on_row_double_clicked(self, item: QTableWidgetItem) -> None:
        row = item.row()
        plan_id_item = self._table.item(row, 0)
        if plan_id_item and plan_id_item.data(Qt.ItemDataRole.UserRole) is not None:
            plan_id = plan_id_item.data(Qt.ItemDataRole.UserRole)
            self.open_cp_editor.emit(plan_id)

    def _on_theme_changed(self, _name: str) -> None:
        """刷新所有内联样式。"""
        title_item = self.layout().itemAt(0)
        if title_item:
            h_layout = title_item.layout()
            if h_layout:
                w = h_layout.itemAt(0)
                if w and w.widget():
                    w.widget().setStyleSheet(
                        f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
                    )
                # Combo box
                combo = self._project_combo
                combo.setStyleSheet(
                    f"""
                    QComboBox {{
                        background: {_t.BG_INPUT};
                        color: {_t.FG_PRIMARY};
                        border: 1px solid {_t.BORDER};
                        border-radius: 4px;
                        padding: 4px 8px;
                        min-height: 24px;
                    }}
                    """
                )
                # New project button
                self._new_project_btn.setStyleSheet(
                    f"""
                    QPushButton[class="primaryBtn"] {{
                        background: {_t.ACCENT};
                        color: {_t.BG_BASE};
                        border: 1px solid {_t.ACCENT};
                        border-radius: 4px;
                        padding: 6px 16px;
                    }}
                    QPushButton[class="primaryBtn"]:hover {{
                        background: #4c83f7;
                    }}
                    """
                )

        # Stat cards
        for card in self._stat_cards.values():
            card.refresh_style()

        # List label
        list_label_item = self.layout().itemAt(3)
        if list_label_item and list_label_item.widget():
            list_label_item.widget().setStyleSheet(
                f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        # Table
        self._table.setStyleSheet(
            f"""
            QTableWidget {{
                background: {_t.BG_BASE};
                alternate-background-color: {_t.MANTLE};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                gridline-color: {_t.BORDER_LIGHT};
                selection-background-color: {_t.SURFACE0};
                selection-color: {_t.FG_PRIMARY};
            }}
            QHeaderView::section {{
                background: {_t.MANTLE};
                color: {_t.FG_PRIMARY};
                border: none;
                border-right: 1px solid {_t.BORDER_LIGHT};
                border-bottom: 1px solid {_t.BORDER_LIGHT};
                padding: 6px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
            """
        )
