"""PlanEditor — 控制计划表头编辑对话框

QDialog，用于创建新控制计划和编辑表头信息（对应 AIAG CP H1-H13）。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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


class PlanEditor(QDialog):
    """控制计划表头编辑对话框。

    字段（对应 AIAG CP 表头 H1-H13）：
        cp_number, part_number, part_name, supplier, supplier_code,
        contact_person, contact_phone, core_team, phase, foundation_source_id

    公开 API：
        get_data() -> dict
        set_data(data: dict) -> None
    """

    def __init__(
        self,
        project_id: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("控制计划表头编辑")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)

        self._project_id = project_id

        self._setup_ui()
        self._load_project_info()
        self._load_foundation_sources()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("控制计划表头信息")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Form ──
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._cp_number = QLineEdit()
        self._cp_number.setPlaceholderText("如: CP-001")
        form.addRow("CP编号:", self._cp_number)

        self._part_number = QLineEdit()
        self._part_number.setPlaceholderText("从项目自动填充，可修改")
        form.addRow("零件号:", self._part_number)

        self._part_name = QLineEdit()
        self._part_name.setPlaceholderText("从项目自动填充，可修改")
        form.addRow("零件名称:", self._part_name)

        self._supplier = QLineEdit()
        self._supplier.setPlaceholderText("从项目自动填充，可修改")
        form.addRow("供应商:", self._supplier)

        self._supplier_code = QLineEdit()
        form.addRow("供应商代码:", self._supplier_code)

        self._contact_person = QLineEdit()
        form.addRow("联系人:", self._contact_person)

        self._contact_phone = QLineEdit()
        form.addRow("联系人电话:", self._contact_phone)

        self._core_team = QTextEdit()
        self._core_team.setPlaceholderText("核心团队成员，逗号分隔（如: 张三, 李四, 王五）")
        self._core_team.setMaximumHeight(80)
        form.addRow("核心团队:", self._core_team)

        self._phase = QComboBox()
        self._phase.addItems(["Prototype", "Pre-Launch", "Production"])
        form.addRow("阶段:", self._phase)

        self._foundation_source = QComboBox()
        self._foundation_source.addItem("无（创建空白计划）", None)
        form.addRow("Foundation 来源:", self._foundation_source)

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

    def _load_project_info(self) -> None:
        """从 projects 表读取项目信息并填充字段。"""
        import services.project_service as ps

        try:
            project = ps.get_project(self._project_id)
        except Exception:
            return
        if not project:
            return

        if project["part_number"]:
            self._part_number.setText(project["part_number"] or "")
        if project["part_name"]:
            self._part_name.setText(project["part_name"] or "")
        if project["supplier"]:
            self._supplier.setText(project["supplier"] or "")
        if project["supplier_code"]:
            self._supplier_code.setText(project["supplier_code"] or "")
        if project["contact_person"]:
            self._contact_person.setText(project["contact_person"] or "")
        if project["contact_phone"]:
            self._contact_phone.setText(project["contact_phone"] or "")

    def _load_foundation_sources(self) -> None:
        """加载可用的 Foundation 控制计划（同项目下已有的计划）。"""
        import services.plan_service as plan_svc

        try:
            plans = plan_svc.list_plans_for_foundation(self._project_id)
        except Exception:
            plans = []

        for plan in plans:
            cp_label = plan['cp_number'] or f"CP-{plan['id']:04d}"
            label = f"{cp_label} ({plan['phase']})"
            self._foundation_source.addItem(label, plan["id"])

    # ── Public API ──

    def get_data(self) -> dict:
        """获取所有表头字段数据。"""
        phase_map = {
            "Prototype": "prototype",
            "Pre-Launch": "pre_launch",
            "Production": "production",
        }
        return {
            "cp_number": self._cp_number.text().strip(),
            "part_number": self._part_number.text().strip(),
            "part_name": self._part_name.text().strip(),
            "supplier": self._supplier.text().strip(),
            "supplier_code": self._supplier_code.text().strip(),
            "contact_person": self._contact_person.text().strip(),
            "contact_phone": self._contact_phone.text().strip(),
            "core_team": self._core_team.toPlainText().strip(),
            "phase": phase_map.get(self._phase.currentText(), "prototype"),
            "foundation_source_id": self._foundation_source.currentData(),
        }

    def set_data(self, data: dict) -> None:
        """编辑模式填充已有数据。"""
        if "cp_number" in data and data["cp_number"]:
            self._cp_number.setText(data["cp_number"])
        if "part_number" in data and data["part_number"]:
            self._part_number.setText(data["part_number"])
        if "part_name" in data and data["part_name"]:
            self._part_name.setText(data["part_name"])
        if "supplier" in data and data["supplier"]:
            self._supplier.setText(data["supplier"])
        if "supplier_code" in data and data["supplier_code"]:
            self._supplier_code.setText(data["supplier_code"])
        if "contact_person" in data and data["contact_person"]:
            self._contact_person.setText(data["contact_person"])
        if "contact_phone" in data and data["contact_phone"]:
            self._contact_phone.setText(data["contact_phone"])
        if "core_team" in data and data["core_team"]:
            self._core_team.setPlainText(data["core_team"])
        if "phase" in data:
            phase_map = {"prototype": "Prototype", "pre_launch": "Pre-Launch", "production": "Production"}
            phase_label = phase_map.get(data["phase"], "Prototype")
            idx = self._phase.findText(phase_label)
            if idx >= 0:
                self._phase.setCurrentIndex(idx)
        if "foundation_source_id" in data and data["foundation_source_id"]:
            # Try to find the matching foundation item
            for i in range(self._foundation_source.count()):
                if self._foundation_source.itemData(i) == data["foundation_source_id"]:
                    self._foundation_source.setCurrentIndex(i)
                    break

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
