"""ApprovalView — 评审签署页面

完整页面（非对话框），集成到侧边栏导航。
功能：团队管理、签署记录、控制计划状态推进。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
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

import services.approval_service as approval_svc
import services.plan_service as plan_svc
import styles.theme as _t


class ApprovalView(QWidget):
    """评审签署页面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_plan_id: int | None = None

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Page title ──
        title = QLabel("评审签署")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Top: Select control plan ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        top_label = QLabel("选择控制计划:")
        top_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 13px;"
        )
        top_bar.addWidget(top_label)

        self._plan_combo = QComboBox()
        self._plan_combo.setMinimumWidth(300)
        self._plan_combo.currentIndexChanged.connect(self._on_plan_changed)
        top_bar.addWidget(self._plan_combo)

        self._refresh_plan_btn = QPushButton("刷新")
        self._refresh_plan_btn.clicked.connect(self.refresh_plan_list)
        top_bar.addWidget(self._refresh_plan_btn)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        # ── Main area (three sections) ──
        main_layout = QHBoxLayout()
        main_layout.setSpacing(16)

        # Left: Team management
        self._setup_team_section(main_layout)

        # Middle: Approval records
        self._setup_approval_section(main_layout)

        # Right: Status section
        self._setup_status_section(main_layout)

        layout.addLayout(main_layout, stretch=1)

    # ── Team Management Section ──

    def _setup_team_section(self, parent_layout: QHBoxLayout) -> None:
        group = QGroupBox("核心团队")
        group.setStyleSheet(
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
        team_layout = QVBoxLayout(group)
        team_layout.setSpacing(6)

        self._team_table = QTableWidget()
        self._team_table.setColumnCount(4)
        self._team_table.setHorizontalHeaderLabels(["姓名", "角色", "部门", "操作"])
        self._team_table.setAlternatingRowColors(True)
        self._team_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._team_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._team_table.verticalHeader().setVisible(False)
        self._team_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._team_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._team_table.setStyleSheet(
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
        team_layout.addWidget(self._team_table, stretch=1)

        add_member_btn = QPushButton("+ 添加成员")
        add_member_btn.setProperty("class", "primaryBtn")
        add_member_btn.setStyleSheet(
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
        add_member_btn.clicked.connect(self._on_add_member)
        team_layout.addWidget(add_member_btn)

        parent_layout.addWidget(group, stretch=1)

    # ── Approval Records Section ──

    def _setup_approval_section(self, parent_layout: QHBoxLayout) -> None:
        group = QGroupBox("评审签署")
        group.setStyleSheet(
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
        appr_layout = QVBoxLayout(group)
        appr_layout.setSpacing(6)

        self._approval_table = QTableWidget()
        self._approval_table.setColumnCount(4)
        self._approval_table.setHorizontalHeaderLabels(
            ["类型", "姓名", "签署日期", "操作"]
        )
        self._approval_table.setAlternatingRowColors(True)
        self._approval_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._approval_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._approval_table.verticalHeader().setVisible(False)
        self._approval_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._approval_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._approval_table.setStyleSheet(
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
        appr_layout.addWidget(self._approval_table, stretch=1)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        add_prepared_btn = QPushButton("添加编制人")
        add_prepared_btn.clicked.connect(
            lambda: self._on_add_approval("prepared")
        )
        btn_row.addWidget(add_prepared_btn)

        add_reviewed_btn = QPushButton("添加审核人")
        add_reviewed_btn.clicked.connect(
            lambda: self._on_add_approval("reviewed")
        )
        btn_row.addWidget(add_reviewed_btn)

        add_approved_btn = QPushButton("添加批准人")
        add_approved_btn.clicked.connect(
            lambda: self._on_add_approval("approved")
        )
        btn_row.addWidget(add_approved_btn)

        btn_row.addStretch()
        appr_layout.addLayout(btn_row)

        parent_layout.addWidget(group, stretch=1)

    # ── Status Section ──

    def _setup_status_section(self, parent_layout: QHBoxLayout) -> None:
        group = QGroupBox("控制计划状态")
        group.setStyleSheet(
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
        status_layout = QVBoxLayout(group)
        status_layout.setSpacing(10)

        self._status_label = QLabel("当前状态: —")
        self._status_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 16px; font-weight: bold;"
        )
        status_layout.addWidget(self._status_label)

        # Status transition buttons
        self._submit_review_btn = QPushButton("提交审核 (draft → review)")
        self._submit_review_btn.clicked.connect(self._on_submit_review)
        status_layout.addWidget(self._submit_review_btn)

        self._approve_btn = QPushButton("批准 (review → approved)")
        self._approve_btn.clicked.connect(self._on_approve)
        status_layout.addWidget(self._approve_btn)

        self._obsolete_btn = QPushButton("作废 (any → obsolete)")
        self._obsolete_btn.setProperty("class", "dangerBtn")
        self._obsolete_btn.setStyleSheet(
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
        self._obsolete_btn.clicked.connect(self._on_obsolete)
        status_layout.addWidget(self._obsolete_btn)

        status_layout.addStretch()
        parent_layout.addWidget(group)

    # ── Team Slots ──

    def _on_add_member(self) -> None:
        if self._current_plan_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个控制计划。")
            return

        name, ok = QInputDialog.getText(self, "添加成员", "成员姓名:")
        if not ok or not name.strip():
            return

        role, ok = QInputDialog.getText(self, "添加成员", "角色 (如: 工程师):")
        role = role.strip() if ok else ""

        dept, ok = QInputDialog.getText(self, "添加成员", "部门:")
        dept = dept.strip() if ok else ""

        approval_svc.add_team_member(
            self._current_plan_id,
            name=name.strip(),
            role=role,
            department=dept,
        )
        self._refresh_team()

    def _on_remove_member(self, member_id: int) -> None:
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除此团队成员吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        approval_svc.remove_team_member(member_id)
        self._refresh_team()

    # ── Approval Slots ──

    def _on_add_approval(self, approval_type: str) -> None:
        if self._current_plan_id is None:
            QMessageBox.warning(self, "提示", "请先选择一个控制计划。")
            return

        type_label = {"prepared": "编制人", "reviewed": "审核人", "approved": "批准人"}
        name, ok = QInputDialog.getText(
            self, f"添加{type_label[approval_type]}", "姓名:"
        )
        if not ok or not name.strip():
            return

        approval_svc.create_approval(
            self._current_plan_id,
            approval_type=approval_type,
            name=name.strip(),
        )
        self._refresh_approvals()

    def _on_sign(self, approval_id: int) -> None:
        """签署当前登录用户（实际应用中可改为认证用户）。"""
        approval_svc.sign_approval(approval_id)
        self._refresh_approvals()

    def _on_delete_approval(self, approval_id: int) -> None:
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除此签署记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        approval_svc.delete_approval(approval_id)
        self._refresh_approvals()

    # ── Status Transition Slots ──

    def _on_submit_review(self) -> None:
        if self._current_plan_id is None:
            return
        plan = plan_svc.get_plan(self._current_plan_id)
        if not plan:
            return
        if plan["status"] not in ("draft",):
            QMessageBox.warning(self, "提示", "只有草稿状态可以提交审核。")
            return

        # Check: at least one "prepared" approval exists
        approvals = approval_svc.list_approvals(self._current_plan_id)
        has_prepared = any(a["approval_type"] == "prepared" for a in approvals)
        if not has_prepared:
            QMessageBox.warning(
                self, "提示", "请至少添加一位编制人后再提交审核。"
            )
            return

        plan_svc.update_plan(self._current_plan_id, status="review")
        self._refresh_status()

    def _on_approve(self) -> None:
        if self._current_plan_id is None:
            return
        plan = plan_svc.get_plan(self._current_plan_id)
        if not plan:
            return
        if plan["status"] not in ("review",):
            QMessageBox.warning(self, "提示", "只有审核中状态可以批准。")
            return

        # Check: at least one "approved" approval with signature
        approvals = approval_svc.list_approvals(self._current_plan_id)
        has_signed_approved = any(
            a["approval_type"] == "approved" and a["signed_at"]
            for a in approvals
        )
        if not has_signed_approved:
            QMessageBox.warning(
                self, "提示", "请至少有一位批准人签署后再批准。"
            )
            return

        plan_svc.update_plan(self._current_plan_id, status="approved")

        # Record change
        import services.change_service as change_svc
        change_svc.record_change(
            self._current_plan_id,
            "控制计划已批准",
            changed_by="系统",
        )

        self._refresh_status()

    def _on_obsolete(self) -> None:
        if self._current_plan_id is None:
            return
        reply = QMessageBox.question(
            self, "确认作废", "确定要将此控制计划作废吗？此操作不可逆。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        plan_svc.update_plan(self._current_plan_id, status="obsolete")

        import services.change_service as change_svc
        change_svc.record_change(
            self._current_plan_id,
            "控制计划已作废",
            changed_by="系统",
        )

        self._refresh_status()

    # ── Refresh Methods ──

    def refresh_plan_list(self) -> None:
        """重新加载控制计划列表（供外部调用）。"""
        self._plan_combo.blockSignals(True)
        current = self._plan_combo.currentText()
        self._plan_combo.clear()
        self._plan_combo.addItem("— 请选择控制计划 —", None)

        import services.project_service as ps
        projects = ps.list_projects()
        for proj in projects:
            plans = plan_svc.list_plans(proj["id"])
            for p in plans:
                cp_label = p['cp_number'] or f"CP-{p['id']:04d}"
                label = f"[{proj['name']}] {cp_label} ({p['phase']})"
                self._plan_combo.addItem(label, p["id"])

        # Restore selection
        idx = self._plan_combo.findText(current)
        if idx >= 0:
            self._plan_combo.setCurrentIndex(idx)
        self._plan_combo.blockSignals(False)

        self._on_plan_changed()

    def _on_plan_changed(self) -> None:
        plan_id = self._plan_combo.currentData()
        self._current_plan_id = plan_id
        self._refresh_team()
        self._refresh_approvals()
        self._refresh_status()

    def _refresh_team(self) -> None:
        """刷新团队成员表格。"""
        self._team_table.setRowCount(0)
        if self._current_plan_id is None:
            return

        members = approval_svc.list_team_members(self._current_plan_id)
        for i, m in enumerate(members):
            self._team_table.insertRow(i)
            self._team_table.setItem(i, 0, QTableWidgetItem(m["name"]))
            self._team_table.setItem(i, 1, QTableWidgetItem(m.get("role", "")))
            self._team_table.setItem(i, 2, QTableWidgetItem(m.get("department", "")))

            # Delete button
            del_btn = QPushButton("删除")
            del_btn.setProperty("class", "dangerBtn")
            del_btn.setStyleSheet(
                f"""
                QPushButton[class="dangerBtn"] {{
                    background: {_t.DANGER};
                    color: {_t.BG_BASE};
                    border: 1px solid {_t.DANGER};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                }}
                QPushButton[class="dangerBtn"]:hover {{
                    background: #e02e55;
                }}
                """
            )
            del_btn.clicked.connect(
                lambda checked, mid=m["id"]: self._on_remove_member(mid)
            )
            self._team_table.setCellWidget(i, 3, del_btn)

    def _refresh_approvals(self) -> None:
        """刷新签署记录表格。"""
        self._approval_table.setRowCount(0)
        if self._current_plan_id is None:
            return

        type_map = {
            "prepared": "编制",
            "reviewed": "审核",
            "approved": "批准",
        }
        approvals = approval_svc.list_approvals(self._current_plan_id)
        for i, a in enumerate(approvals):
            self._approval_table.insertRow(i)
            self._approval_table.setItem(
                i, 0, QTableWidgetItem(type_map.get(a["approval_type"], a["approval_type"]))
            )
            self._approval_table.setItem(i, 1, QTableWidgetItem(a["name"]))
            self._approval_table.setItem(
                i, 2, QTableWidgetItem(a.get("signed_at", "") or "—")
            )

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 0, 2, 0)
            action_layout.setSpacing(4)

            if not a.get("signed_at"):
                sign_btn = QPushButton("签署")
                sign_btn.setProperty("class", "primaryBtn")
                sign_btn.setStyleSheet(
                    f"""
                    QPushButton[class="primaryBtn"] {{
                        background: {_t.ACCENT};
                        color: {_t.BG_BASE};
                        border: 1px solid {_t.ACCENT};
                        border-radius: 4px;
                        padding: 2px 8px;
                        font-size: 11px;
                    }}
                    QPushButton[class="primaryBtn"]:hover {{
                        background: #4c83f7;
                    }}
                    """
                )
                sign_btn.clicked.connect(
                    lambda checked, aid=a["id"]: self._on_sign(aid)
                )
                action_layout.addWidget(sign_btn)

            del_btn = QPushButton("删除")
            del_btn.setProperty("class", "dangerBtn")
            del_btn.setStyleSheet(
                f"""
                QPushButton[class="dangerBtn"] {{
                    background: {_t.DANGER};
                    color: {_t.BG_BASE};
                    border: 1px solid {_t.DANGER};
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                }}
                QPushButton[class="dangerBtn"]:hover {{
                    background: #e02e55;
                }}
                """
            )
            del_btn.clicked.connect(
                lambda checked, aid=a["id"]: self._on_delete_approval(aid)
            )
            action_layout.addWidget(del_btn)

            self._approval_table.setCellWidget(i, 3, action_widget)

    def _refresh_status(self) -> None:
        """刷新状态显示与按钮可用性。"""
        if self._current_plan_id is None:
            self._status_label.setText("当前状态: —")
            self._submit_review_btn.setEnabled(False)
            self._approve_btn.setEnabled(False)
            self._obsolete_btn.setEnabled(False)
            return

        plan = plan_svc.get_plan(self._current_plan_id)
        if not plan:
            return

        status_map = {
            "draft": "草稿",
            "review": "审核中",
            "approved": "已批准",
            "obsolete": "已废弃",
        }
        status_cn = status_map.get(plan["status"], plan["status"])
        self._status_label.setText(f"当前状态: {status_cn}")

        # Update button enable states
        self._submit_review_btn.setEnabled(plan["status"] == "draft")
        self._approve_btn.setEnabled(plan["status"] == "review")
        self._obsolete_btn.setEnabled(plan["status"] not in ("obsolete",))

    # ── Theme ──

    def _on_theme_changed(self, _name: str) -> None:
        """主题切换时刷新所有内联样式。"""
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        # Top bar label
        top_layout_item = self.layout().itemAt(1)
        if top_layout_item and top_layout_item.layout():
            top_label_w = top_layout_item.layout().itemAt(0)
            if top_label_w and top_label_w.widget():
                top_label_w.widget().setStyleSheet(
                    f"color: {_t.FG_PRIMARY}; font-size: 13px;"
                )

        # Group boxes
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

        # Tables
        table_style = (
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
        self._team_table.setStyleSheet(table_style)
        self._approval_table.setStyleSheet(table_style)

        # Primary + danger buttons
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
        self._obsolete_btn.setStyleSheet(danger_style)
        self._status_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 16px; font-weight: bold;"
        )

        # Refresh team and approval table cell buttons (they get rebuilt)
        self._refresh_team()
        self._refresh_approvals()
