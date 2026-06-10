"""CP Editor View — 控制计划编辑器页面"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from views.editors.cp_item_editor import CpItemEditor

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

    def _on_step_changed(self, row: int) -> None:
        if row >= 0:
            item = self._step_list.item(row)
            if item:
                self._current_step_id = item.data(Qt.ItemDataRole.UserRole)
        else:
            self._current_step_id = None

    def _on_add_step(self) -> None:
        # Placeholder — will be wired to DB service later
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "添加过程步骤", "步骤名称:")
        if ok and text:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, -1)  # temp id
            self._step_list.addItem(item)

    def _on_add_item(self) -> None:
        if self._current_step_id is None:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先选择一个过程步骤。")
            return
        dlg = CpItemEditor(self)
        if dlg.exec():
            data = dlg.get_data()
            # Placeholder: append to table
            row = self._items_table.rowCount()
            self._items_table.insertRow(row)
            for col, key in enumerate([
                "char_number", "char_description", "special_classification",
                "specification", "measurement_method", "sample_size",
                "sample_frequency", "control_method_type", "responsible",
                "reaction_plan",
            ]):
                val = data.get(key, "")
                item = QTableWidgetItem(str(val))
                self._items_table.setItem(row, col + 2, item)

    def _on_delete(self) -> None:
        # Placeholder
        pass

    # ── Public API ──

    def load_plan(self, plan_id: int) -> None:
        """加载指定控制计划到编辑器。"""
        self._current_plan_id = plan_id
        self._cp_info_label.setText(f"CP编号: CP-{plan_id:04d}  版本: 1.0")

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
