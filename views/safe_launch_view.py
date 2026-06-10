"""Safe Launch View — Safe Launch 面板"""

from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class _SafeLaunchStatusCard(QFrame):
    """Safe Launch 状态卡片。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "stat-card")
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Title
        title = QLabel("Safe Launch 状态")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY}; background: transparent;"
        )
        layout.addWidget(title)

        # Status fields
        fields = [
            ("开始日期:", "—"),
            ("已过天数:", "—"),
            ("剩余天数:", "—"),
            ("失败次数:", "0"),
        ]
        self._field_labels: dict[str, QLabel] = {}
        for label_text, default_val in fields:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                f"color: {_t.FG_SECONDARY}; font-size: 12px; background: transparent;"
            )
            val = QLabel(default_val)
            val.setStyleSheet(
                f"color: {_t.FG_PRIMARY}; font-size: 13px; font-weight: bold; background: transparent;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            layout.addLayout(row)
            self._field_labels[label_text] = val

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {_t.SURFACE0};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: {_t.ACCENT};
                border-radius: 4px;
            }}
            """
        )
        layout.addWidget(self._progress_bar)

    def set_field(self, name: str, value: str) -> None:
        if name in self._field_labels:
            self._field_labels[name].setText(value)

    def set_progress(self, value: int) -> None:
        self._progress_bar.setValue(value)

    def refresh_style(self) -> None:
        for lbl in self._field_labels.values():
            lbl.setStyleSheet(
                f"color: {_t.FG_PRIMARY}; font-size: 13px; font-weight: bold; background: transparent;"
            )
        self._progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {_t.SURFACE0};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: {_t.ACCENT};
                border-radius: 4px;
            }}
            """
        )
        self.style().unpolish(self)
        self.style().polish(self)


class SafeLaunchView(QWidget):
    """Safe Launch 面板。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Top: title + plan selector ──
        top_bar = QHBoxLayout()
        title = QLabel("Safe Launch")
        title.setProperty("class", "pageTitle")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        top_bar.addWidget(title)
        top_bar.addStretch()

        plan_label = QLabel("选择控制计划:")
        plan_label.setStyleSheet(
            f"color: {_t.FG_SECONDARY}; font-size: 13px;"
        )
        top_bar.addWidget(plan_label)

        self._plan_combo = QComboBox()
        self._plan_combo.setMinimumWidth(250)
        self._plan_combo.setStyleSheet(
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
        top_bar.addWidget(self._plan_combo)
        layout.addLayout(top_bar)

        # ── Main content row ──
        content = QHBoxLayout()
        content.setSpacing(16)

        # Left: status card
        self._status_card = _SafeLaunchStatusCard()
        content.addWidget(self._status_card, stretch=1)

        # Right: exit criteria
        criteria_group = QGroupBox("退出条件")
        criteria_group.setStyleSheet(
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
        criteria_layout = QVBoxLayout(criteria_group)
        self._exit_criteria_text = QTextEdit()
        self._exit_criteria_text.setPlaceholderText("输入 Safe Launch 退出条件（如：连续 30 天无缺陷）...")
        self._exit_criteria_text.setStyleSheet(
            f"""
            QTextEdit {{
                background: {_t.BG_INPUT};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {_t.ACCENT};
            }}
            """
        )
        criteria_layout.addWidget(self._exit_criteria_text)
        content.addWidget(criteria_group, stretch=2)

        layout.addLayout(content)

        # ── Enhanced measures table ──
        measures_label = QLabel("加强措施列表")
        measures_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(measures_label)

        self._measures_table = QTableWidget()
        self._measures_table.setColumnCount(4)
        self._measures_table.setHorizontalHeaderLabels(["描述", "原频次", "加强频次", "RESP"])
        self._measures_table.setAlternatingRowColors(True)
        self._measures_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._measures_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._measures_table.verticalHeader().setVisible(False)
        self._measures_table.horizontalHeader().setStretchLastSection(True)
        self._measures_table.setStyleSheet(
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
        layout.addWidget(self._measures_table, stretch=1)

        # ── Action buttons ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._start_btn = QPushButton("▶ 启动 Safe Launch")
        self._start_btn.setProperty("class", "primaryBtn")
        self._start_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.SUCCESS};
                color: {_t.BG_BASE};
                border: 1px solid {_t.SUCCESS};
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #5fb85f;
            }}
            """
        )
        btn_layout.addWidget(self._start_btn)

        self._complete_btn = QPushButton("✓ 完成退出")
        self._complete_btn.setProperty("class", "primaryBtn")
        self._complete_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #4c83f7;
            }}
            """
        )
        btn_layout.addWidget(self._complete_btn)

        self._reset_btn = QPushButton("↺ 归零重启")
        self._reset_btn.setProperty("class", "dangerBtn")
        self._reset_btn.setStyleSheet(
            f"""
            QPushButton[class="dangerBtn"] {{
                background: {_t.DANGER};
                color: {_t.BG_BASE};
                border: 1px solid {_t.DANGER};
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton[class="dangerBtn"]:hover {{
                background: #e02e55;
            }}
            """
        )
        btn_layout.addWidget(self._reset_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_theme_changed(self, _name: str) -> None:
        """刷新内联样式。"""
        title_item = self.layout().itemAt(0)
        if title_item:
            hl = title_item.layout()
            if hl:
                w = hl.itemAt(0)
                if w and w.widget():
                    w.widget().setStyleSheet(
                        f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
                    )

        # Status card
        self._status_card.refresh_style()

        # Combo
        self._plan_combo.setStyleSheet(
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

        # Criteria group
        for gb in self.findChildren(QGroupBox):
            gb.setStyleSheet(
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

        # Exit criteria text
        self._exit_criteria_text.setStyleSheet(
            f"""
            QTextEdit {{
                background: {_t.BG_INPUT};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {_t.ACCENT};
            }}
            """
        )

        # Measures table
        self._measures_table.setStyleSheet(
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

        # Buttons
        self._start_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.SUCCESS};
                color: {_t.BG_BASE};
                border: 1px solid {_t.SUCCESS};
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #5fb85f;
            }}
            """
        )
        self._complete_btn.setStyleSheet(
            f"""
            QPushButton[class="primaryBtn"] {{
                background: {_t.ACCENT};
                color: {_t.BG_BASE};
                border: 1px solid {_t.ACCENT};
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton[class="primaryBtn"]:hover {{
                background: #4c83f7;
            }}
            """
        )
        self._reset_btn.setStyleSheet(
            f"""
            QPushButton[class="dangerBtn"] {{
                background: {_t.DANGER};
                color: {_t.BG_BASE};
                border: 1px solid {_t.DANGER};
                border-radius: 4px;
                padding: 8px 20px;
            }}
            QPushButton[class="dangerBtn"]:hover {{
                background: #e02e55;
            }}
            """
        )
