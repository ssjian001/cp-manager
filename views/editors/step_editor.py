"""StepEditor — 过程步骤编辑对话框"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class StepEditor(QDialog):
    """过程步骤编辑对话框。

    字段:
        step_number: 步骤编号 (如 OP10, OP20)
        step_name: 步骤名称
        equipment: 设备/夹具/工具
        description: 描述 (可选)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑过程步骤")
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("过程步骤编辑")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Form ──
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._step_number = QLineEdit()
        self._step_number.setPlaceholderText("如: OP10, OP20")
        form.addRow("步骤编号:", self._step_number)

        self._step_name = QLineEdit()
        self._step_name.setPlaceholderText("如: 机加工, 装配")
        form.addRow("步骤名称:", self._step_name)

        self._equipment = QLineEdit()
        self._equipment.setPlaceholderText("如: CNC 机床 #101")
        form.addRow("设备/夹具/工具:", self._equipment)

        self._description = QTextEdit()
        self._description.setPlaceholderText("输入步骤描述（可选）...")
        self._description.setMaximumHeight(100)
        form.addRow("描述:", self._description)

        layout.addLayout(form)

        # ── Button box ──
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

    # ── Public API ──

    def get_data(self) -> dict[str, str]:
        """获取表单数据。"""
        return {
            "step_number": self._step_number.text(),
            "step_name": self._step_name.text(),
            "equipment": self._equipment.text(),
            "description": self._description.toPlainText(),
        }

    def set_data(self, data: dict[str, str]) -> None:
        """用已有数据填充表单。"""
        if "step_number" in data:
            self._step_number.setText(data["step_number"])
        if "step_name" in data:
            self._step_name.setText(data["step_name"])
        if "equipment" in data:
            self._equipment.setText(data["equipment"])
        if "description" in data:
            self._description.setPlainText(data["description"])

    # ── Theme ──

    def _on_theme_changed(self, _name: str) -> None:
        """主题刷新。"""
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

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
