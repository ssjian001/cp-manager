"""Reaction Library View — 反应计划库页面"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class _ReactionTemplateDialog(QDialog):
    """反应计划模板编辑对话框。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑反应计划模板")
        self.setMinimumWidth(450)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("反应计划模板")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)

        self._name = QLineEdit()
        form.addRow("模板名:", self._name)

        self._stop_process = QComboBox()
        self._stop_process.addItems(["是", "否"])
        form.addRow("停线决策:", self._stop_process)

        self._product_disposition = QLineEdit()
        form.addRow("产品处置:", self._product_disposition)

        self._notify_who = QLineEdit()
        form.addRow("通知对象:", self._notify_who)

        self._recovery_condition = QLineEdit()
        form.addRow("恢复条件:", self._recovery_condition)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
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

    def get_data(self) -> dict[str, str]:
        return {
            "name": self._name.text(),
            "stop_process": self._stop_process.currentText(),
            "product_disposition": self._product_disposition.text(),
            "notify_who": self._notify_who.text(),
            "recovery_condition": self._recovery_condition.text(),
        }

    def set_data(self, data: dict[str, str]) -> None:
        if "name" in data:
            self._name.setText(data["name"])
        if "stop_process" in data:
            idx = self._stop_process.findText(data["stop_process"])
            if idx >= 0:
                self._stop_process.setCurrentIndex(idx)
        if "product_disposition" in data:
            self._product_disposition.setText(data["product_disposition"])
        if "notify_who" in data:
            self._notify_who.setText(data["notify_who"])
        if "recovery_condition" in data:
            self._recovery_condition.setText(data["recovery_condition"])

    def _on_theme_changed(self, _name: str) -> None:
        for bb in self.findChildren(QDialogButtonBox):
            bb.setStyleSheet(
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


class ReactionLibraryView(QWidget):
    """反应计划库页面。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("反应计划库")
        title.setProperty("class", "pageTitle")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._add_btn = QPushButton("+ 添加")
        self._add_btn.setProperty("class", "primaryBtn")
        self._add_btn.setStyleSheet(
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
        self._add_btn.clicked.connect(self._on_add)
        toolbar.addWidget(self._add_btn)

        self._edit_btn = QPushButton("编辑")
        self._edit_btn.setStyleSheet(
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
        self._edit_btn.clicked.connect(self._on_edit)
        toolbar.addWidget(self._edit_btn)

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
        toolbar.addWidget(self._delete_btn)

        toolbar.addStretch()

        self._set_default_btn = QPushButton("设为默认")
        self._set_default_btn.setProperty("class", "action")
        self._set_default_btn.setStyleSheet(
            f"""
            QPushButton[class="action"] {{
                background: {_t.BG_INPUT};
                color: {_t.ACCENT};
                border: 1px solid {_t.ACCENT};
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
            }}
            QPushButton[class="action"]:hover {{
                background: {_t.BG_HOVER};
            }}
            """
        )
        self._set_default_btn.clicked.connect(self._on_set_default)
        toolbar.addWidget(self._set_default_btn)

        layout.addLayout(toolbar)

        # ── Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "模板名", "停线决策", "产品处置", "通知对象", "恢复条件", "是否默认",
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
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
        layout.addWidget(self._table, stretch=1)

    def _on_add(self) -> None:
        dlg = _ReactionTemplateDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, key in enumerate(["name", "stop_process", "product_disposition",
                                       "notify_who", "recovery_condition"]):
                item = QTableWidgetItem(data.get(key, ""))
                self._table.setItem(row, col, item)
            # "是否默认" column
            item = QTableWidgetItem("否")
            self._table.setItem(row, 5, item)

    def _on_edit(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        data = {
            "name": self._table.item(row, 0).text() if self._table.item(row, 0) else "",
            "stop_process": self._table.item(row, 1).text() if self._table.item(row, 1) else "",
            "product_disposition": self._table.item(row, 2).text() if self._table.item(row, 2) else "",
            "notify_who": self._table.item(row, 3).text() if self._table.item(row, 3) else "",
            "recovery_condition": self._table.item(row, 4).text() if self._table.item(row, 4) else "",
        }
        dlg = _ReactionTemplateDialog(self)
        dlg.set_data(data)
        if dlg.exec():
            new_data = dlg.get_data()
            for col, key in enumerate(["name", "stop_process", "product_disposition",
                                       "notify_who", "recovery_condition"]):
                item = QTableWidgetItem(new_data.get(key, ""))
                self._table.setItem(row, col, item)

    def _on_delete(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            self._table.removeRow(row)

    def _on_set_default(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        # Clear all "是否默认" to "否"
        for r in range(self._table.rowCount()):
            item = self._table.item(r, 5)
            if item:
                item.setText("否")
        # Set current row to "是"
        item = QTableWidgetItem("是")
        self._table.setItem(row, 5, item)

    def _on_theme_changed(self, _name: str) -> None:
        """刷新内联样式。"""
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        # Buttons
        self._add_btn.setStyleSheet(
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
        self._edit_btn.setStyleSheet(
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
        self._set_default_btn.setStyleSheet(
            f"""
            QPushButton[class="action"] {{
                background: {_t.BG_INPUT};
                color: {_t.ACCENT};
                border: 1px solid {_t.ACCENT};
                border-radius: 6px;
                padding: 4px 12px;
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
