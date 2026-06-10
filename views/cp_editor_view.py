"""CP Editor View — 控制计划编辑器页面"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from views.editors.cp_item_editor import CpItemEditor
from views.editors.plan_editor import PlanEditor
from views.editors.step_editor import StepEditor

import styles.theme as _t


class CpEditorView(QWidget):
    """控制计划编辑器页面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_plan_id: int | None = None
        self._current_step_id: int | None = None

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # ── Top bar: phase toggle + CP info ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self._phases = ["Prototype", "Pre-Launch", "Production"]
        self._phase_buttons: list[QPushButton] = []
        for phase in self._phases:
            btn = QPushButton(phase)
            btn.setCheckable(True)
            btn.setProperty("class", "phaseBtn")
            btn.setStyleSheet(
                f"""
                QPushButton[class="phaseBtn"] {{
                    background: {_t.SURFACE0};
                    color: {_t.FG_SECONDARY};
                    border: 1px solid {_t.BORDER};
                    border-radius: 4px;
                    padding: 6px 16px;
                }}
                QPushButton[class="phaseBtn"]:checked {{
                    background: {_t.ACCENT};
                    color: {_t.BG_BASE};
                    border: 1px solid {_t.ACCENT};
                    font-weight: bold;
                }}
                QPushButton[class="phaseBtn"]:hover {{
                    background: {_t.SURFACE1};
                }}
                """
            )
            btn.clicked.connect(self._on_phase_clicked)
            self._phase_buttons.append(btn)
            top_bar.addWidget(btn)

        top_bar.addSpacing(24)

        self._cp_info_label = QLabel("CP编号: —  版本: —")
        self._cp_info_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 13px;"
        )
        top_bar.addWidget(self._cp_info_label)
        top_bar.addStretch()

        layout.addLayout(top_bar)

        # ── Middle: process steps list (left) + items table (right) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: process steps
        steps_group = QGroupBox("过程步骤")
        steps_group.setStyleSheet(
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                margin-top: 14px;
                padding: 14px 12px 12px 12px;
                font-weight: bold;
                font-size: 13px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        steps_layout = QVBoxLayout(steps_group)
        steps_layout.setSpacing(6)

        self._step_list = QListWidget()
        self._step_list.setAlternatingRowColors(True)
        self._step_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {_t.BG_DARK};
                alternate-background-color: {_t.BG_CARD};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
            }}
            QListWidget::item:selected {{
                background-color: {_t.BG_HOVER};
            }}
            """
        )
        self._step_list.currentRowChanged.connect(self._on_step_changed)
        steps_layout.addWidget(self._step_list, stretch=1)

        # Right: control items table
        items_group = QGroupBox("控制项目")
        items_group.setStyleSheet(
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                margin-top: 14px;
                padding: 14px 12px 12px 12px;
                font-weight: bold;
                font-size: 13px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        items_layout = QVBoxLayout(items_group)
        items_layout.setSpacing(6)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(12)
        self._items_table.setHorizontalHeaderLabels([
            "过程编号", "过程名", "特性编号", "特性描述", "特殊特性",
            "规格", "测量方法", "样本量", "频率", "控制方法",
            "RESP", "反应计划",
        ])
        self._items_table.setAlternatingRowColors(True)
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._items_table.setStyleSheet(
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
                padding: 4px 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            """
        )
        self._items_table.setProperty("class", "compactTable")
        items_layout.addWidget(self._items_table, stretch=1)

        splitter.addWidget(steps_group)
        splitter.addWidget(items_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # Set steps group initial width
        splitter.setSizes([200, 600])

        layout.addWidget(splitter, stretch=1)

        # ── Bottom buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._add_step_btn = QPushButton("+ 添加过程步骤")
        self._add_step_btn.setProperty("class", "primaryBtn")
        self._add_step_btn.setStyleSheet(
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
        self._add_step_btn.clicked.connect(self._on_add_step)
        btn_layout.addWidget(self._add_step_btn)

        self._add_item_btn = QPushButton("+ 添加控制项")
        self._add_item_btn.setProperty("class", "primaryBtn")
        self._add_item_btn.setStyleSheet(
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
        self._add_item_btn.clicked.connect(self._on_add_item)
        btn_layout.addWidget(self._add_item_btn)

        btn_layout.addStretch()

        self._delete_btn = QPushButton("删除")
        self._delete_btn.setProperty("class", "dangerBtn")
        self._delete_btn.setStyleSheet(
            f"""
            QPushButton[class="dangerBtn"] {{
                background: {_t.DANGER};
                color: {_t.BG_BASE};
                border: 1px solid {_t.DANGER};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton[class="dangerBtn"]:hover {{
                background: #e02e55;
            }}
            """
        )
        self._delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self._delete_btn)

        btn_layout.addStretch()

        self._from_template_btn = QPushButton("从模板创建")
        self._from_template_btn.setProperty("class", "action")
        self._from_template_btn.setStyleSheet(
            f"""
            QPushButton[class="action"] {{
                background: {_t.BG_INPUT};
                color: {_t.ACCENT};
                border: 1px solid {_t.ACCENT};
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton[class="action"]:hover {{
                background: {_t.BG_HOVER};
            }}
            """
        )
        self._from_template_btn.clicked.connect(self._on_from_template)
        btn_layout.addWidget(self._from_template_btn)

        self._change_log_btn = QPushButton("变更记录")
        self._change_log_btn.setProperty("class", "action")
        self._change_log_btn.setStyleSheet(
            f"""
            QPushButton[class="action"] {{
                background: {_t.BG_INPUT};
                color: {_t.ACCENT};
                border: 1px solid {_t.ACCENT};
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton[class="action"]:hover {{
                background: {_t.BG_HOVER};
            }}
            """
        )
        self._change_log_btn.clicked.connect(self._on_change_log)
        btn_layout.addWidget(self._change_log_btn)

        layout.addLayout(btn_layout)

        # Connect signals
        self._add_step_btn.clicked.connect(self._on_add_step)
        self._add_item_btn.clicked.connect(self._on_add_item)
        self._delete_btn.clicked.connect(self._on_delete)

    # ── Slots ──

    def _on_phase_clicked(self) -> None:
        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        for b in self._phase_buttons:
            b.setChecked(b is btn)
        # Update DB
        if self._current_plan_id is not None:
            import services.plan_service as plan_svc
            idx = self._phase_buttons.index(btn)
            phase_key = ["prototype", "pre_launch", "production"][idx]
            plan_svc.update_plan(self._current_plan_id, phase=phase_key)

    def _on_step_changed(self, row: int) -> None:
        if row >= 0:
            item = self._step_list.item(row)
            if item:
                self._current_step_id = item.data(Qt.ItemDataRole.UserRole)
        else:
            self._current_step_id = None
        # Refresh items — only show items for the selected step
        self._refresh_items()

    def _on_add_step(self) -> None:
        if self._current_plan_id is None:
            QMessageBox.warning(self, "提示", "请先打开一个控制计划。")
            return
        dlg = StepEditor(self)
        if dlg.exec():
            data = dlg.get_data()
            step_number = data.get("step_number", "").strip()
            step_name = data.get("step_name", "").strip()
            if not step_number or not step_name:
                QMessageBox.warning(self, "提示", "步骤编号和名称不能为空。")
                return
            equipment = data.get("equipment", "")
            import db.database as db
            conn = db.get_connection()
            try:
                row = conn.execute(
                    "SELECT MAX(sort_order) FROM process_steps WHERE plan_id=?",
                    (self._current_plan_id,),
                ).fetchone()
                sort = (row[0] or 0) + 1
                cur = conn.execute(
                    "INSERT INTO process_steps (plan_id, step_number, step_name, equipment, sort_order) VALUES (?,?,?,?,?)",
                    (self._current_plan_id, step_number, step_name, equipment, sort),
                )
                conn.commit()
                new_id = cur.lastrowid
            finally:
                conn.close()
            text = f"{step_number} - {step_name}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, new_id)
            self._step_list.addItem(item)
            # Select the new step
            self._step_list.setCurrentItem(item)

    def _on_add_item(self) -> None:
        if self._current_step_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个过程步骤。")
            return
        dlg = CpItemEditor(self)
        if dlg.exec():
            data = dlg.get_data()
            import services.item_service as item_svc
            item_id = item_svc.create_item(
                step_id=self._current_step_id,
                plan_id=self._current_plan_id,
                **data,
            )
            # Refresh the table
            self._refresh_items()

    def _on_delete(self) -> None:
        # If table has selected rows → delete items
        selected_rows = self._items_table.selectionModel().selectedRows()
        if selected_rows:
            reply = QMessageBox.question(
                self, "确认删除", "确定要删除选中的控制项吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            import services.item_service as item_svc
            for idx in sorted([r.row() for r in selected_rows], reverse=True):
                item = self._items_table.item(idx, 2)  # char_number column
                if item and item.data(Qt.ItemDataRole.UserRole) is not None:
                    item_id = item.data(Qt.ItemDataRole.UserRole)
                    item_svc.delete_item(item_id)
            self._refresh_items()
            return

        # No table selection → delete selected process step
        current_step_item = self._step_list.currentItem()
        if current_step_item is None:
            QMessageBox.warning(self, "提示", "请选择要删除的过程步骤或控制项。")
            return

        step_id = current_step_item.data(Qt.ItemDataRole.UserRole)
        if step_id is None:
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除步骤 \"{current_step_item.text()}\" 及其所有控制项吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        import services.step_service as step_svc
        step_svc.delete_step(step_id)
        row = self._step_list.currentRow()
        self._step_list.takeItem(row)
        self._current_step_id = None
        self._refresh_items()

    # ── Public API ──

    def load_plan(self, plan_id: int) -> None:
        """加载指定控制计划到编辑器。"""
        self._current_plan_id = plan_id
        self._current_step_id = None

        import services.plan_service as plan_svc
        import db.database as db

        plan = plan_svc.get_plan(plan_id)
        if not plan:
            self._cp_info_label.setText("CP编号: —  状态: —")
            self._step_list.clear()
            self._items_table.setRowCount(0)
            return

        # Update phase buttons
        phase_map = {"prototype": 0, "pre_launch": 1, "production": 2}
        idx = phase_map.get(plan["phase"], 0)
        for i, btn in enumerate(self._phase_buttons):
            btn.setChecked(i == idx)

        # Update CP info
        self._cp_info_label.setText(
            f"CP编号: {plan['cp_number'] or '—'}  状态: {plan['status']}"
        )

        # Load process steps
        self._step_list.clear()
        conn = db.get_connection()
        try:
            steps = conn.execute(
                "SELECT id, step_number, step_name FROM process_steps WHERE plan_id=? ORDER BY sort_order",
                (plan_id,),
            ).fetchall()
        finally:
            conn.close()
        for step in steps:
            text = f"{step['step_number']} - {step['step_name']}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, step["id"])
            self._step_list.addItem(item)

        # Select the first step
        if self._step_list.count() > 0:
            self._step_list.setCurrentRow(0)

        # Load all control items
        self._refresh_items()

    def _refresh_items(self) -> None:
        """刷新控制项目表格。"""
        self._items_table.setRowCount(0)
        if self._current_plan_id is None:
            return
        import services.item_service as item_svc
        import db.database as db

        # If a step is selected, only show items for that step
        if self._current_step_id is not None:
            items = item_svc.list_items_by_step(self._current_step_id)
        else:
            items = item_svc.list_items(self._current_plan_id)

        # Get step map for display
        conn = db.get_connection()
        try:
            steps = {
                r["id"]: r
                for r in conn.execute(
                    "SELECT id, step_number, step_name FROM process_steps WHERE plan_id=?",
                    (self._current_plan_id,),
                ).fetchall()
            }
        finally:
            conn.close()

        for i, item_data in enumerate(items):
            self._items_table.insertRow(i)
            step = steps.get(item_data["step_id"], {})

            # Col 0-1: process info
            step_num_item = QTableWidgetItem(step.get("step_number", ""))
            step_num_item.setData(Qt.ItemDataRole.UserRole, item_data["id"])
            self._items_table.setItem(i, 0, step_num_item)
            self._items_table.setItem(i, 1, QTableWidgetItem(step.get("step_name", "")))

            # Col 2-11: control item fields
            fields = [
                "char_number", "char_description", "special_classification",
                "specification", "measurement_method", "sample_size",
                "sample_frequency", "control_method_type", "responsible", "reaction_plan",
            ]
            for col, key in enumerate(fields):
                val = item_data.get(key, "") or ""
                cell = QTableWidgetItem(str(val))
                cell.setData(Qt.ItemDataRole.UserRole, item_data["id"])
                self._items_table.setItem(i, col + 2, cell)

            # Special characteristic row highlight
            if item_data.get("special_classification", "none") != "none":
                for col in range(12):
                    cell = self._items_table.item(i, col)
                    if cell:
                        cell.setBackground(QColor(_t.YELLOW + "40"))  # light yellow

    # ── Foundation Derivation & Change Log ──

    def _on_from_template(self) -> None:
        """从 Foundation 模板派生新的控制计划。"""
        if self._current_plan_id is None:
            QMessageBox.warning(self, "提示", "请先打开一个控制计划作为目标项目参考。")
            return

        # Get the project_id of current plan
        import services.plan_service as plan_svc
        plan = plan_svc.get_plan(self._current_plan_id)
        if not plan:
            return
        project_id = plan["project_id"]

        dlg = PlanEditor(project_id, self)
        if dlg.exec():
            data = dlg.get_data()
            foundation_source_id = data.get("foundation_source_id")

            if foundation_source_id is None:
                QMessageBox.warning(self, "提示", "请选择一个 Foundation 来源模板。")
                return

            try:
                new_plan_id = plan_svc.derive_from_foundation(
                    foundation_plan_id=foundation_source_id,
                    new_project_id=project_id,
                    new_cp_number=data.get("cp_number", ""),
                )

                # Update core_team on the new plan
                if data.get("core_team"):
                    plan_svc.update_plan(new_plan_id, core_team=data["core_team"])

                # Record change
                import services.change_service as change_svc
                change_svc.record_change(
                    new_plan_id,
                    f"从 Foundation CP #{foundation_source_id} 派生创建",
                    changed_by="系统",
                )

                # Load the new plan
                self.load_plan(new_plan_id)
                QMessageBox.information(self, "成功", "已从 Foundation 模板派生创建新控制计划。")
            except Exception as exc:
                QMessageBox.critical(self, "错误", f"派生失败: {exc}")

    def _on_change_log(self) -> None:
        """显示变更记录对话框。"""
        if self._current_plan_id is None:
            QMessageBox.warning(self, "提示", "请先打开一个控制计划。")
            return

        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QLabel,
        )

        import services.change_service as change_svc

        changes = change_svc.list_changes(self._current_plan_id)

        dlg = QDialog(self)
        dlg.setWindowTitle("变更记录")
        dlg.setMinimumSize(600, 400)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(f"变更记录 — CP #{self._current_plan_id}")
        title_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title_label)

        if not changes:
            empty_label = QLabel("暂无变更记录。")
            empty_label.setStyleSheet(f"color: {_t.FG_MUTED}; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty_label, stretch=1)
        else:
            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["变更时间", "描述", "操作人"])
            table.setAlternatingRowColors(True)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setStretchLastSection(True)
            table.setStyleSheet(
                f"""
                QTableWidget {{
                    background: {_t.BG_BASE};
                    alternate-background-color: {_t.MANTLE};
                    color: {_t.FG_PRIMARY};
                    border: 1px solid {_t.BORDER};
                    border-radius: 4px;
                    gridline-color: {_t.BORDER_LIGHT};
                }}
                QHeaderView::section {{
                    background: {_t.MANTLE};
                    color: {_t.FG_PRIMARY};
                    border: none;
                    border-right: 1px solid {_t.BORDER_LIGHT};
                    border-bottom: 1px solid {_t.BORDER_LIGHT};
                    padding: 4px 6px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                """
            )

            for i, ch in enumerate(changes):
                table.insertRow(i)
                table.setItem(i, 0, QTableWidgetItem(ch.get("changed_at", "")))
                table.setItem(i, 1, QTableWidgetItem(ch.get("description", "")))
                table.setItem(i, 2, QTableWidgetItem(ch.get("changed_by", "")))

            layout.addWidget(table, stretch=1)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(dlg.reject)
        btn_box.setStyleSheet(
            f"""
            QDialogButtonBox QPushButton {{
                background: {_t.SURFACE0};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.SURFACE1};
                border-radius: 4px;
                padding: 6px 16px;
                min-height: 20px;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background: {_t.SURFACE1};
            }}
            """
        )
        layout.addWidget(btn_box)

        dlg.exec()

    # ── Theme ──

    def _on_theme_changed(self, _name: str) -> None:
        """刷新所有内联样式。"""
        # Phase buttons
        style_phase = (
            f"""
            QPushButton[class="phaseBtn"] {{
                background: {_t.SURFACE0};
                color: {_t.FG_SECONDARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton[class="phaseBtn"]:checked {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                font-weight: bold;
            }}
            QPushButton[class="phaseBtn"]:hover {{
                background: {_t.SURFACE1};
            }}
            """
        )
        for btn in self._phase_buttons:
            btn.setStyleSheet(style_phase)

        # CP info
        self._cp_info_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 13px;"
        )

        # Groups
        group_style = (
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                margin-top: 14px;
                padding: 14px 12px 12px 12px;
                font-weight: bold;
                font-size: 13px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        for gb in self.findChildren(QGroupBox):
            gb.setStyleSheet(group_style)

        # Step list
        self._step_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {_t.BG_DARK};
                alternate-background-color: {_t.BG_CARD};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
            }}
            QListWidget::item:selected {{
                background-color: {_t.BG_HOVER};
            }}
            """
        )

        # Items table
        self._items_table.setStyleSheet(
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
                padding: 4px 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            """
        )

        # Buttons
        primary_style = (
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
        danger_style = (
            f"""
            QPushButton[class="dangerBtn"] {{
                background: {_t.DANGER};
                color: {_t.BG_BASE};
                border: 1px solid {_t.DANGER};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton[class="dangerBtn"]:hover {{
                background: #e02e55;
            }}
            """
        )
        self._add_step_btn.setStyleSheet(primary_style)
        self._add_item_btn.setStyleSheet(primary_style)
        self._delete_btn.setStyleSheet(danger_style)
