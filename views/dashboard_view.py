"""Dashboard View — 仪表盘页面"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
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

        # Wire up signals
        self._new_project_btn.clicked.connect(self._on_new_project)
        self._project_combo.currentIndexChanged.connect(self._on_project_changed)

        # Initial data load
        self._refresh_projects()
        self._on_refresh()

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
        list_header = QHBoxLayout()
        list_label = QLabel("控制计划列表")
        list_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        list_header.addWidget(list_label)
        list_header.addStretch()

        self._export_excel_btn = QPushButton("导出 Excel")
        self._export_excel_btn.setProperty("class", "action")
        self._export_excel_btn.setStyleSheet(
            f"""
            QPushButton[class="action"] {{
                background: {_t.BG_INPUT};
                color: {_t.ACCENT};
                border: 1px solid {_t.ACCENT};
                border-radius: 6px;
                padding: 4px 14px;
                font-weight: bold;
            }}
            QPushButton[class="action"]:hover {{
                background: {_t.BG_HOVER};
            }}
            """
        )
        self._export_excel_btn.clicked.connect(self._on_export_excel)
        list_header.addWidget(self._export_excel_btn)

        layout.addLayout(list_header)

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

    # ── DB operations ──

    def _on_new_project(self) -> None:
        name, ok = QInputDialog.getText(self, "新建项目", "项目名称:")
        if ok and name.strip():
            import services.project_service as ps
            ps.create_project(name.strip())
            self._refresh_projects()
            # Select the newly created project
            self._project_combo.setCurrentIndex(
                self._project_combo.findText(name.strip())
            )
            self._on_refresh()

    def _on_project_changed(self, _index: int) -> None:
        self._on_refresh()

    def _refresh_projects(self) -> None:
        """重新加载项目列表到 ComboBox。"""
        self._project_combo.blockSignals(True)
        current = self._project_combo.currentText()
        self._project_combo.clear()
        import services.project_service as ps
        projects = ps.list_projects()
        for p in projects:
            self._project_combo.addItem(p["name"], p["id"])
        # Restore previous selection
        idx = self._project_combo.findText(current)
        if idx >= 0:
            self._project_combo.setCurrentIndex(idx)
        self._project_combo.blockSignals(False)

    def _on_refresh(self) -> None:
        """刷新仪表盘数据：统计卡片 + 控制计划列表。"""
        import services.project_service as ps
        import services.plan_service as pls
        import services.item_service as its
        import db.database as db

        # Get selected project
        project_id = self._project_combo.currentData()
        if project_id is None:
            # No project selected — show empty
            for card in self._stat_cards.values():
                card.set_value("—")
            self._table.setRowCount(0)
            return

        # Update stats
        stats = ps.get_project_stats(project_id)
        self._stat_cards["total_plans"].set_value(str(stats["plan_count"]))
        self._stat_cards["total_items"].set_value(str(stats["item_count"]))

        # Safe launch active count
        conn = db.get_connection()
        try:
            sl_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM control_plans "
                "WHERE project_id = ? AND is_safe_launch = 1",
                (project_id,),
            ).fetchone()["cnt"]
        finally:
            conn.close()
        self._stat_cards["safe_launch_active"].set_value(str(sl_count))

        # Special char count
        special_count = 0
        plans = pls.list_plans(project_id)
        for plan in plans:
            special_count += len(its.get_special_char_items(plan["id"]))
        self._stat_cards["special_chars"].set_value(str(special_count))

        # Load control plan table
        self._table.setRowCount(0)
        for i, plan in enumerate(plans):
            self._table.insertRow(i)

            cp_item = QTableWidgetItem(plan["cp_number"] or f"CP-{plan['id']:04d}")
            cp_item.setData(Qt.ItemDataRole.UserRole, plan["id"])
            self._table.setItem(i, 0, cp_item)

            # Part number from project
            project = ps.get_project(project_id)
            self._table.setItem(i, 1, QTableWidgetItem(
                project["part_number"] if project else ""
            ))

            # Phase
            phase_map = {"prototype": "Prototype", "pre_launch": "Pre-Launch", "production": "Production"}
            phase_val = plan.get("phase", "") or ""
            self._table.setItem(i, 2, QTableWidgetItem(
                phase_map.get(phase_val, phase_val)
            ))

            # Status
            status_map = {"draft": "草稿", "review": "审核中", "approved": "已批准", "obsolete": "已废弃"}
            status_val = plan.get("status", "") or ""
            self._table.setItem(i, 3, QTableWidgetItem(
                status_map.get(status_val, status_val)
            ))

            # Safe Launch
            sl_text = "是" if plan["is_safe_launch"] else "—"
            self._table.setItem(i, 4, QTableWidgetItem(sl_text))

            # Created date
            created = plan["created_at"] or ""
            self._table.setItem(i, 5, QTableWidgetItem(created))

    def _on_export_excel(self) -> None:
        """导出当前选中的控制计划为 Excel。"""
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选择一个控制计划")
            return
        plan_id_item = self._table.item(row, 0)
        if plan_id_item is None or plan_id_item.data(Qt.ItemDataRole.UserRole) is None:
            QMessageBox.information(self, "提示", "请先选择一个控制计划")
            return
        plan_id = plan_id_item.data(Qt.ItemDataRole.UserRole)

        from export.excel_export import export_control_plan

        # Build default filename
        plan_number = plan_id_item.text()
        default_name = f"CP_{plan_number}.xlsx"

        path, _ = QFileDialog.getSaveFileName(
            self, "导出控制计划", default_name, "Excel Files (*.xlsx)"
        )
        if not path:
            return

        try:
            export_control_plan(plan_id, path)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return

        QMessageBox.information(self, "导出成功", f"控制计划已导出到:\n{path}")

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

        # List label / export button
        list_header_item = self.layout().itemAt(3)
        if list_header_item and list_header_item.layout():
            hlayout = list_header_item.layout()
            label_w = hlayout.itemAt(0)
            if label_w and label_w.widget():
                label_w.widget().setStyleSheet(
                    f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY};"
                )
            # Export Excel button
            self._export_excel_btn.setStyleSheet(
                f"""
                QPushButton[class="action"] {{
                    background: {_t.BG_INPUT};
                    color: {_t.ACCENT};
                    border: 1px solid {_t.ACCENT};
                    border-radius: 6px;
                    padding: 4px 14px;
                    font-weight: bold;
                }}
                QPushButton[class="action"]:hover {{
                    background: {_t.BG_HOVER};
                }}
                """
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
