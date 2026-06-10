"""Settings View — 设置页面"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

import styles.theme as _t
import db.database as db


class SettingsView(QWidget):
    """设置页面：主题切换 + 关于信息。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        _t.theme_host.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)

        # ── Page title ──
        title = QLabel("设置")
        title.setProperty("class", "pageTitle")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
        )
        layout.addWidget(title)

        # ── Appearance section ──
        appearance_group = QGroupBox("外观")
        appearance_group.setStyleSheet(
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 6px;
                margin-top: 16px;
                padding: 20px 16px 16px 16px;
                font-weight: bold;
                font-size: 14px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        appearance_layout = QVBoxLayout(appearance_group)
        appearance_layout.setSpacing(12)

        # Theme selector
        theme_row = QHBoxLayout()
        theme_label = QLabel("主题:")
        theme_label.setStyleSheet(
            f"color: {_t.FG_PRIMARY}; font-size: 13px; font-weight: 500;"
        )
        theme_row.addWidget(theme_label)

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Latte (浅色)", "Mocha (深色)"])
        # Set current
        current = _t.current_theme()
        self._theme_combo.setCurrentIndex(0 if current == "light" else 1)
        self._theme_combo.setMinimumWidth(200)
        self._theme_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {_t.BG_INPUT};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 24px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {_t.SURFACE2};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid {_t.BORDER};
            }}
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {_t.SUBTEXT0};
            }}
            QComboBox QAbstractItemView {{
                background: {_t.BG_BASE};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                selection-background-color: {_t.SURFACE0};
                selection-color: {_t.FG_PRIMARY};
                outline: none;
            }}
            """
        )
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed_combo)
        theme_row.addWidget(self._theme_combo)
        theme_row.addStretch()

        appearance_layout.addLayout(theme_row)

        # Theme preview hint
        hint = QLabel("更改主题会立即生效并持久化到数据库。")
        hint.setStyleSheet(
            f"color: {_t.FG_MUTED}; font-size: 11px; font-style: italic; background: transparent;"
        )
        appearance_layout.addWidget(hint)

        layout.addWidget(appearance_group)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_t.BORDER};")
        layout.addWidget(sep)

        # ── About section ──
        about_group = QGroupBox("关于")
        about_group.setStyleSheet(
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 6px;
                margin-top: 16px;
                padding: 20px 16px 16px 16px;
                font-weight: bold;
                font-size: 14px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        about_layout = QVBoxLayout(about_group)
        about_layout.setSpacing(8)

        about_lines = [
            ("应用名称:", "CP Manager — 控制计划管理器"),
            ("版本:", "1.0.0"),
            ("基于:", "AIAG Control Plan 1st Edition (2024)"),
            ("技术栈:", "Python 3.11 + PySide6 6.11 + SQLite"),
            ("版权:", "© 2024-2026 Nous Research"),
        ]
        for label_text, value_text in about_lines:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet(
                f"color: {_t.FG_SECONDARY}; font-size: 13px; background: transparent;"
            )
            val = QLabel(value_text)
            val.setStyleSheet(
                f"color: {_t.FG_PRIMARY}; font-size: 13px; background: transparent;"
            )
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            about_layout.addLayout(row)

        layout.addWidget(about_group)
        layout.addStretch()

    def _on_theme_changed_combo(self, index: int) -> None:
        """主题选择下拉框切换。"""
        theme_name = "dark" if index == 1 else "light"

        _t.set_theme(theme_name)
        db.save_setting("theme", theme_name)

        app = QApplication.instance()
        if app:
            app.setStyleSheet(_t.get_stylesheet())
            _t.apply_palette()
            from PySide6.QtCore import Qt as QtCore
            scheme = QtCore.ColorScheme.Dark if theme_name == "dark" else QtCore.ColorScheme.Light
            app.styleHints().setColorScheme(scheme)

    def _on_theme_changed(self, _name: str) -> None:
        """主题刷新（订阅 theme_host）。"""
        # Title
        title_item = self.layout().itemAt(0)
        if title_item and title_item.widget():
            title_item.widget().setStyleSheet(
                f"font-size: 22px; font-weight: bold; color: {_t.FG_PRIMARY};"
            )

        # Groups
        group_style = (
            f"""
            QGroupBox {{
                background: {_t.BG_CARD};
                border: 1px solid {_t.BORDER};
                border-radius: 6px;
                margin-top: 16px;
                padding: 20px 16px 16px 16px;
                font-weight: bold;
                font-size: 14px;
                color: {_t.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                padding: 0 6px;
                color: {_t.FG_PRIMARY};
            }}
            """
        )
        for gb in self.findChildren(QGroupBox):
            gb.setStyleSheet(group_style)

        # Theme combo
        self._theme_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {_t.BG_INPUT};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 24px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {_t.SURFACE2};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid {_t.BORDER};
            }}
            QComboBox::down-arrow {{
                width: 10px;
                height: 10px;
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {_t.SUBTEXT0};
            }}
            QComboBox QAbstractItemView {{
                background: {_t.BG_BASE};
                color: {_t.FG_PRIMARY};
                border: 1px solid {_t.BORDER};
                border-radius: 4px;
                selection-background-color: {_t.SURFACE0};
                selection-color: {_t.FG_PRIMARY};
                outline: none;
            }}
            """
        )
