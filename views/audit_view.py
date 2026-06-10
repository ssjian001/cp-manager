"""Audit View — 审计检查页面"""

from __future__ import annotations

import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class AuditView(QWidget):
    """审计检查页面：选择控制计划 → 执行 25 项审计 → 展示结果。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._results: list[dict] = []

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    # ─────────────────────────────────────────────────────────────────────
    #  UI construction
    # ─────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("审计检查")
        title.setProperty("class", "pageTitle")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        desc = QLabel("基于 CP 1st Edition / iFactory 标准的 25 项审计清单自动检查")
        desc.setStyleSheet(f"color: {_t.FG_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        # ── Toolbar: plan selector + audit button ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        plan_label = QLabel("选择控制计划:")
        plan_label.setStyleSheet(f"color: {_t.FG_PRIMARY};")
        toolbar.addWidget(plan_label)

        self._plan_combo = QComboBox()
        self._plan_combo.setMinimumWidth(280)
        toolbar.addWidget(self._plan_combo)

        self._audit_btn = QPushButton("开始审计")
        self._audit_btn.setProperty("class", "primaryBtn")
        self._audit_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                border-radius: 4px;
                padding: 6px 20px;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #4c83f7;
            }}
            """
        )
        self._audit_btn.clicked.connect(self._on_run_audit)
        toolbar.addWidget(self._audit_btn)

        self._refresh_btn = QPushButton("刷新列表")
        self._refresh_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {_t.SURFACE0};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.SURFACE1};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: {_t.SURFACE1};
            }}
            """
        )
        self._refresh_btn.clicked.connect(self._refresh_plan_list)
        toolbar.addWidget(self._refresh_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # ── Results table ──
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["类别", "检查项", "结果", "详情"])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
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
        layout.addWidget(self._table, stretch=1)

        # ── Stats bar ──
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._stats_total = QLabel("总计: 0")
        self._stats_total.setStyleSheet(f"color: {_t.FG_PRIMARY}; font-weight: bold;")
        stats_layout.addWidget(self._stats_total)

        self._stats_pass = QLabel("通过: 0")
        self._stats_pass.setStyleSheet(f"color: {_t.SUCCESS}; font-weight: bold;")
        stats_layout.addWidget(self._stats_pass)

        self._stats_fail = QLabel("失败: 0")
        self._stats_fail.setStyleSheet(f"color: {_t.DANGER}; font-weight: bold;")
        stats_layout.addWidget(self._stats_fail)

        self._stats_warn = QLabel("警告: 0")
        self._stats_warn.setStyleSheet(f"color: {_t.WARNING}; font-weight: bold;")
        stats_layout.addWidget(self._stats_warn)

        self._stats_skip = QLabel("跳过: 0")
        self._stats_skip.setStyleSheet(f"color: {_t.FG_MUTED}; font-weight: bold;")
        stats_layout.addWidget(self._stats_skip)

        stats_layout.addStretch()

        self._export_btn = QPushButton("导出报告")
        self._export_btn.setProperty("class", "action")
        self._export_btn.setStyleSheet(
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
        self._export_btn.clicked.connect(self._on_export)
        stats_layout.addWidget(self._export_btn)

        layout.addLayout(stats_layout)

    # ─────────────────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────────────────

    def refresh_plan_list(self) -> None:
        """刷新控制计划下拉列表。"""
        self._refresh_plan_list()

    # ─────────────────────────────────────────────────────────────────────
    #  Internal
    # ─────────────────────────────────────────────────────────────────────

    def _refresh_plan_list(self) -> None:
        """从数据库加载所有控制计划到 ComboBox。"""
        import services.plan_service as plan_svc

        self._plan_combo.clear()
        try:
            rows = plan_svc.get_plan_list_all()
        except Exception as exc:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"加载控制计划列表失败: {exc}")
            return

        for row in rows:
            label = f"[#{row['id']}] {row['cp_number'] or '(无编号)'} — {row['project_name'] or '?'} ({row['phase']})"
            self._plan_combo.addItem(label, userData=row["id"])

    def _on_run_audit(self) -> None:
        """执行审计。"""
        plan_id = self._plan_combo.currentData()
        if plan_id is None:
            return

        from core.audit_engine import audit_control_plan

        try:
            self._results = audit_control_plan(plan_id)
        except ValueError as exc:
            self._results = []
            self._table.setRowCount(1)
            item = QTableWidgetItem(str(exc))
            item.setForeground(Qt.GlobalColor.red)
            self._table.setItem(0, 0, item)
            self._update_stats()
            return
        except Exception as exc:
            import traceback
            traceback.print_exc()
            self._results = []
            QMessageBox.critical(self, "错误", f"审计执行失败: {exc}")
            self._update_stats()
            return

        self._populate_table()
        self._update_stats()

    def _populate_table(self) -> None:
        """将 25 项检查结果填入表格。"""
        self._table.setRowCount(len(self._results))

        for row, r in enumerate(self._results):
            # 类别
            cat_item = QTableWidgetItem(r.get("category", ""))
            self._table.setItem(row, 0, cat_item)

            # 检查项
            check_item = QTableWidgetItem(r.get("check", ""))
            self._table.setItem(row, 1, check_item)

            # 结果（颜色标记）
            result_text = r.get("result", "")
            result_item = QTableWidgetItem(result_text)
            result_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color_map = {
                "pass": _t.SUCCESS,
                "fail": _t.DANGER,
                "warning": _t.WARNING,
                "skip": _t.FG_MUTED,
            }
            bg_map = {
                "pass": _t.SUCCESS,
                "fail": _t.DANGER,
                "warning": _t.WARNING,
                "skip": _t.FG_MUTED,
            }
            color = color_map.get(result_text, _t.FG_PRIMARY)
            result_item.setForeground(Qt.GlobalColor.white)
            result_item.setBackground(
                self._parse_color(color)
            )
            self._table.setItem(row, 2, result_item)

            # 详情
            detail_item = QTableWidgetItem(r.get("detail", ""))
            self._table.setItem(row, 3, detail_item)

    def _parse_color(self, hex_color: str):
        """Parse hex color string into QColor."""
        from PySide6.QtGui import QColor

        hex_color = hex_color.strip()
        if hex_color.startswith("#"):
            return QColor(hex_color)
        # Handle rgba() — extract values
        if hex_color.startswith("rgba("):
            import re

            m = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", hex_color)
            if m:
                return QColor(
                    int(m.group(1)),
                    int(m.group(2)),
                    int(m.group(3)),
                    int(float(m.group(4)) * 255),
                )
        return QColor(hex_color)

    def _update_stats(self) -> None:
        """更新底部统计数据。"""
        total = len(self._results)
        pass_count = sum(1 for r in self._results if r.get("result") == "pass")
        fail_count = sum(1 for r in self._results if r.get("result") == "fail")
        warn_count = sum(1 for r in self._results if r.get("result") == "warning")
        skip_count = sum(1 for r in self._results if r.get("result") == "skip")

        self._stats_total.setText(f"总计: {total}")
        self._stats_pass.setText(f"通过: {pass_count}")
        self._stats_fail.setText(f"失败: {fail_count}")
        self._stats_warn.setText(f"警告: {warn_count}")
        self._stats_skip.setText(f"跳过: {skip_count}")

    def _on_export(self) -> None:
        """导出审计报告为 CSV 文件。"""
        if not self._results:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出审计报告", "audit_report.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        import csv

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["类别", "检查项", "结果", "详情"])
                for r in self._results:
                    writer.writerow([
                        r.get("category", ""),
                        r.get("check", ""),
                        r.get("result", ""),
                        r.get("detail", ""),
                    ])
        except Exception as exc:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"导出失败: {exc}")
            return

        QMessageBox.information(self, "导出成功", f"审计报告已导出到:\n{path}")

    # ─────────────────────────────────────────────────────────────────────
    #  Theme refresh
    # ─────────────────────────────────────────────────────────────────────

    def _on_theme_changed(self, _name: str) -> None:
        """刷新内联样式。"""
        # Title
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        # Audit button
        self._audit_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                border-radius: 4px;
                padding: 6px 20px;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #4c83f7;
            }}
            """
        )

        # Refresh button
        self._refresh_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {_t.SURFACE0};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.SURFACE1};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: {_t.SURFACE1};
            }}
            """
        )

        # Export button
        self._export_btn.setStyleSheet(
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

        # Stats labels
        self._stats_total.setStyleSheet(f"color: {_t.FG_PRIMARY}; font-weight: bold;")
        self._stats_pass.setStyleSheet(f"color: {_t.SUCCESS}; font-weight: bold;")
        self._stats_fail.setStyleSheet(f"color: {_t.DANGER}; font-weight: bold;")
        self._stats_warn.setStyleSheet(f"color: {_t.WARNING}; font-weight: bold;")
        self._stats_skip.setStyleSheet(f"color: {_t.FG_MUTED}; font-weight: bold;")

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

        # Repopulate table to refresh result colors
        if self._results:
            self._populate_table()
