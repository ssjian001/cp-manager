"""CpItemEditor — 控制项目编辑对话框"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t


class CpItemEditor(QDialog):
    """控制项目编辑对话框。

    表单字段:
        char_number, char_type, char_description, special_classification,
        specification, tolerance, measurement_method, gauge_id,
        sample_size, sample_frequency, control_method_type,
        ep_verification_freq, ep_verification_method, responsible, reaction_plan, notes
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑控制项目")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("控制项目编辑")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Form ──
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._char_number = QLineEdit()
        form.addRow("特性编号:", self._char_number)

        self._char_type = QComboBox()
        self._char_type.addItems(["product", "process"])
        form.addRow("特性类型:", self._char_type)

        self._char_description = QLineEdit()
        form.addRow("特性描述:", self._char_description)

        self._special_classification = QComboBox()
        self._special_classification.addItems([
            "none", "CC", "SC", "KPC", "OSC", "HI", "custom",
        ])
        form.addRow("特殊特性分类:", self._special_classification)

        self._specification = QLineEdit()
        form.addRow("规格:", self._specification)

        self._tolerance = QLineEdit()
        form.addRow("公差:", self._tolerance)

        self._measurement_method = QLineEdit()
        form.addRow("测量方法:", self._measurement_method)

        self._gauge_id = QLineEdit()
        form.addRow("量具编号:", self._gauge_id)

        self._sample_size = QLineEdit()
        form.addRow("样本量:", self._sample_size)

        self._sample_frequency = QLineEdit()
        form.addRow("频率:", self._sample_frequency)

        self._control_method_type = QComboBox()
        self._control_method_type.addItems(["SPC", "EP", "MP", "visual", "manual", "auto"])
        self._control_method_type.currentTextChanged.connect(self._on_control_method_changed)
        form.addRow("控制方法类型:", self._control_method_type)

        # EP/MP verification fields (shown conditionally)
        self._ep_vf_layout = QHBoxLayout()
        self._ep_verification_freq = QLineEdit()
        self._ep_verification_freq.setPlaceholderText("验证频次")
        self._ep_vf_layout.addWidget(self._ep_verification_freq)
        self._ep_verification_method = QLineEdit()
        self._ep_verification_method.setPlaceholderText("验证方法")
        self._ep_vf_layout.addWidget(self._ep_verification_method)
        form.addRow("EP/MP 验证:", self._ep_vf_layout)
        self._ep_vf_layout_widget: QWidget | None = None

        self._responsible = QLineEdit()
        form.addRow("RESP:", self._responsible)

        # Reaction plan
        rp_row = QHBoxLayout()
        self._reaction_plan = QTextEdit()
        self._reaction_plan.setPlaceholderText("输入反应计划...")
        self._reaction_plan.setMaximumHeight(80)
        rp_row.addWidget(self._reaction_plan, stretch=1)

        self._template_btn = QPushButton("从模板库选择")
        self._template_btn.setProperty("class", "action")
        self._template_btn.setStyleSheet(
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
        self._template_btn.clicked.connect(self._on_select_template)
        rp_row.addWidget(self._template_btn)
        form.addRow("反应计划:", rp_row)

        self._notes = QLineEdit()
        form.addRow("备注:", self._notes)

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

        # Initialize EP/MP fields visibility
        self._on_control_method_changed(self._control_method_type.currentText())

    def _on_control_method_changed(self, method: str) -> None:
        """当控制方法变化时，显示/隐藏 EP/MP 验证字段。"""
        show = method in ("EP", "MP")
        label_item = None
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.layout():
                fl = item.layout()
                if isinstance(fl, QFormLayout):
                    # Find the row index for EP/MP
                    for r in range(fl.rowCount()):
                        fi = fl.itemAt(r, QFormLayout.ItemRole.LabelRole)
                        if fi and fi.widget() and "EP/MP" in fi.widget().text():
                            label_item = fi.widget()
                            break
                    break

        self._ep_verification_freq.setVisible(show)
        self._ep_verification_method.setVisible(show)
        if label_item:
            label_item.setVisible(show)

    def _on_select_template(self) -> None:
        """从模板库选择反应计划（placeholder）。"""
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "选择反应计划模板", "模板名称:")
        if ok and text:
            self._reaction_plan.setPlainText(text)

    # ── Public API ──

    def get_data(self) -> dict[str, str]:
        """获取表单数据。"""
        return {
            "char_number": self._char_number.text(),
            "char_type": self._char_type.currentText(),
            "char_description": self._char_description.text(),
            "special_classification": self._special_classification.currentText(),
            "specification": self._specification.text(),
            "tolerance": self._tolerance.text(),
            "measurement_method": self._measurement_method.text(),
            "gauge_id": self._gauge_id.text(),
            "sample_size": self._sample_size.text(),
            "sample_frequency": self._sample_frequency.text(),
            "control_method_type": self._control_method_type.currentText(),
            "ep_verification_freq": self._ep_verification_freq.text(),
            "ep_verification_method": self._ep_verification_method.text(),
            "responsible": self._responsible.text(),
            "reaction_plan": self._reaction_plan.toPlainText(),
            "notes": self._notes.text(),
        }

    def set_data(self, data: dict[str, str]) -> None:
        """用已有数据填充表单。"""
        if "char_number" in data:
            self._char_number.setText(data["char_number"])
        if "char_type" in data:
            idx = self._char_type.findText(data["char_type"])
            if idx >= 0:
                self._char_type.setCurrentIndex(idx)
        if "char_description" in data:
            self._char_description.setText(data["char_description"])
        if "special_classification" in data:
            idx = self._special_classification.findText(data["special_classification"])
            if idx >= 0:
                self._special_classification.setCurrentIndex(idx)
        if "specification" in data:
            self._specification.setText(data["specification"])
        if "tolerance" in data:
            self._tolerance.setText(data["tolerance"])
        if "measurement_method" in data:
            self._measurement_method.setText(data["measurement_method"])
        if "gauge_id" in data:
            self._gauge_id.setText(data["gauge_id"])
        if "sample_size" in data:
            self._sample_size.setText(data["sample_size"])
        if "sample_frequency" in data:
            self._sample_frequency.setText(data["sample_frequency"])
        if "control_method_type" in data:
            idx = self._control_method_type.findText(data["control_method_type"])
            if idx >= 0:
                self._control_method_type.setCurrentIndex(idx)
        if "ep_verification_freq" in data:
            self._ep_verification_freq.setText(data["ep_verification_freq"])
        if "ep_verification_method" in data:
            self._ep_verification_method.setText(data["ep_verification_method"])
        if "responsible" in data:
            self._responsible.setText(data["responsible"])
        if "reaction_plan" in data:
            self._reaction_plan.setPlainText(data["reaction_plan"])
        if "notes" in data:
            self._notes.setText(data["notes"])

    def _on_theme_changed(self, _name: str) -> None:
        """主题刷新。"""
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 18px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        self._template_btn.setStyleSheet(
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

        # Button box
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
