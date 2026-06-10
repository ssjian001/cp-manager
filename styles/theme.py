"""
CP Manager — 统一主题系统 (Catppuccin Latte/Mocha)

本模块是 QSS 样式表的唯一来源（single source of truth）。
所有 UI 组件通过 `get_stylesheet()` 获取完整的应用样式。

用法:
    from styles.theme import get_stylesheet, set_theme, theme_host
    app.setStyleSheet(get_stylesheet())          # 启动时
    set_theme("dark")                             # 切换暗色
    theme_host.theme_changed.connect(my_refresh)  # 订阅刷新
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

# ═══════════════════════════════════════════════════════════════════
#  字体常量
# ═══════════════════════════════════════════════════════════════════

FONT_FAMILY: str = '"Segoe UI", "Noto Sans SC", "PingFang SC", sans-serif'
FONT_SIZE_NORMAL: int = 13

# ═══════════════════════════════════════════════════════════════════
#  Catppuccin 双色板 — Latte (light) / Mocha (dark)
# ═══════════════════════════════════════════════════════════════════

_PALETTES: dict[str, dict[str, str]] = {
    "light": dict(
        # Base neutrals (Catppuccin Latte)
        CRUST    = "#DCE0E8",
        MANTLE   = "#E6E9EF",
        BASE     = "#EFF1F5",
        SURFACE0 = "#CCD0DA",
        SURFACE1 = "#BCC0CC",
        SURFACE2 = "#ACB0BE",
        OVERLAY0 = "#9CA0B0",
        TEXT     = "#4C4F69",
        SUBTEXT0 = "#6C6F85",
        SUBTEXT1 = "#5C5F77",
        # Accent
        RED      = "#d20f39",
        PEACH    = "#fe640b",
        YELLOW   = "#df8e1d",
        GREEN    = "#40a02b",
        BLUE     = "#1e66f5",
        LAVENDER = "#7287fd",
        MAUVE    = "#8839ef",
        PINK     = "#ea76cb",
        TEAL     = "#179299",
        SKY      = "#04a5e5",
        # Semantic aliases
        BG_BASE      = "#EFF1F5",
        BG_DARK      = "#EFF1F5",
        BG_CARD      = "#FFFFFF",
        BG_INPUT     = "#EFF1F5",
        BG_HOVER     = "#BCC0CC",
        FG_PRIMARY   = "#4C4F69",
        FG_SECONDARY = "#5C5F77",
        FG_MUTED     = "#9CA0B0",
        BORDER       = "#CCD0DA",
        BORDER_LIGHT = "#DCE0E8",
        ACCENT       = "#1e66f5",
        SUCCESS      = "#40a02b",
        DANGER       = "#d20f39",
        WARNING      = "#df8e1d",
        # rgba helpers
        SELECTION_BG  = "rgba(30, 102, 245, 0.12)",
        DANGER_BG     = "rgba(210, 15, 57, 0.08)",
        DANGER_BG_HOV = "rgba(210, 15, 57, 0.14)",
    ),
    "dark": dict(
        # Base neutrals (Catppuccin Mocha)
        CRUST    = "#11111B",
        MANTLE   = "#181825",
        BASE     = "#1E1E2E",
        SURFACE0 = "#313244",
        SURFACE1 = "#45475A",
        SURFACE2 = "#585B70",
        OVERLAY0 = "#6C7086",
        TEXT     = "#CDD6F4",
        SUBTEXT0 = "#A6ADC8",
        SUBTEXT1 = "#BAC2DE",
        # Accent (keep same as light)
        RED      = "#d20f39",
        PEACH    = "#fe640b",
        YELLOW   = "#df8e1d",
        GREEN    = "#40a02b",
        BLUE     = "#1e66f5",
        LAVENDER = "#7287fd",
        MAUVE    = "#8839ef",
        PINK     = "#ea76cb",
        TEAL     = "#179299",
        SKY      = "#04a5e5",
        # Semantic aliases
        BG_BASE      = "#1E1E2E",
        BG_DARK      = "#1E1E2E",
        BG_CARD      = "#181825",
        BG_INPUT     = "#313244",
        BG_HOVER     = "#45475A",
        FG_PRIMARY   = "#CDD6F4",
        FG_SECONDARY = "#BAC2DE",
        FG_MUTED     = "#6C7086",
        BORDER       = "#313244",
        BORDER_LIGHT = "#45475A",
        ACCENT       = "#1e66f5",
        SUCCESS      = "#40a02b",
        DANGER       = "#d20f39",
        WARNING      = "#df8e1d",
        # rgba helpers — dark: higher alpha for visibility
        SELECTION_BG  = "rgba(30, 102, 245, 0.25)",
        DANGER_BG     = "rgba(210, 15, 57, 0.18)",
        DANGER_BG_HOV = "rgba(210, 15, 57, 0.28)",
    ),
}

# ═══════════════════════════════════════════════════════════════════
#  初始化：将 light 色板写入模块全局变量
# ═══════════════════════════════════════════════════════════════════

_current_theme: str = "light"

# 将 light 色板的所有 key 注入为模块级常量
globals().update(_PALETTES["light"])


# ═══════════════════════════════════════════════════════════════════
#  主题切换 Signal Host
# ═══════════════════════════════════════════════════════════════════

class _SignalHost(QObject):
    """模块级 Signal 发射器 — theme.py 不是 QObject，需要代理。"""
    theme_changed = Signal(str)   # 参数: "light" | "dark"

theme_host = _SignalHost()


# ═══════════════════════════════════════════════════════════════════
#  QSS 构建块
# ═══════════════════════════════════════════════════════════════════

def _build_qss() -> str:
    """根据当前模块全局常量生成完整 QSS（每次调用都重新求值）。"""
    return f"""
/* ════════════════════════════════════════════════════════════════
   CP Manager — 统一主题 QSS（由 theme.py 动态生成）
   色板: Catppuccin {_current_theme.title()}
   ════════════════════════════════════════════════════════════════ */

/* ── 全局 ── */
* {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_NORMAL}px;
    color: {FG_PRIMARY};
}}

QApplication,
QMainWindow,
QDialog,
QMessageBox {{
    background: {BG_BASE};
    color: {FG_PRIMARY};
}}

/* ── QWidget (generic) ── */
QWidget {{
    background: {BG_BASE};
    color: {FG_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: {BG_BASE};
}}

QScrollArea {{
    background: {BG_BASE};
}}

QScrollArea > QWidget {{
    background: {BG_BASE};
}}

QStackedWidget {{
    background: {BG_BASE};
}}

/* ── 侧边栏 ── */
QWidget[class="sidebar"] {{
    background: {MANTLE};
    border-right: 1px solid {BORDER};
}}

QFrame[class="topBar"] {{
    background: {BG_BASE};
    border-bottom: 1px solid {BORDER};
}}

/* ── 分组框 ── */
QGroupBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin-top: 14px;
    padding: 14px 12px 12px 12px;
    font-weight: bold;
    color: {FG_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {FG_PRIMARY};
}}

QGroupBox[class="editorSection"] {{
    font-weight: bold;
    font-size: {FONT_SIZE_NORMAL}px;
    margin-top: 8px;
}}

QGroupBox[class="editorSection"]::title {{
    subcontrol-origin: margin;
    left: 10px;
}}

/* ── 输入控件 ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
QDateEdit, QTimeEdit, QDateTimeEdit {{
    background: {BG_INPUT};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 10px;
    min-height: 20px;
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}

QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    background: {MANTLE};
    color: {FG_MUTED};
}}

QLineEdit::placeholder {{
    color: {FG_MUTED};
}}

QComboBox:hover {{
    border-color: {SURFACE2};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border-left: 1px solid {BORDER};
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {SUBTEXT0};
}}

QComboBox QAbstractItemView {{
    background: {BG_BASE};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    selection-background-color: {SURFACE0};
    selection-color: {FG_PRIMARY};
    outline: none;
}}

/* ── SpinBox 子控件 ── */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {BORDER};
    border-top-right-radius: 4px;
    background: transparent;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background: {SURFACE0};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 8px;
    height: 8px;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-bottom: 4px solid {SUBTEXT0};
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border-left: 1px solid {BORDER};
    border-bottom-right-radius: 4px;
    background: transparent;
}}

QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {SURFACE0};
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid {SUBTEXT0};
}}

/* ── 文本编辑框 ── */
QTextEdit, QPlainTextEdit {{
    background: {BG_INPUT};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
    selection-color: {BG_BASE};
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {ACCENT};
}}

QTextEdit:disabled, QPlainTextEdit:disabled {{
    background: {MANTLE};
    color: {FG_MUTED};
}}

/* ── 按钮 ── */
QPushButton {{
    background: {SURFACE0};
    color: {FG_PRIMARY};
    border: 1px solid {SURFACE1};
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 20px;
}}

QPushButton:hover {{
    background: {SURFACE1};
    border-color: {SURFACE2};
}}

QPushButton:pressed {{
    background: {SURFACE2};
    color: {BG_BASE};
}}

QPushButton:disabled {{
    background: {MANTLE};
    color: {FG_MUTED};
    border-color: {BORDER};
}}

QPushButton:checked {{
    background: {SURFACE1};
    border-color: {ACCENT};
}}

/* ── 主按钮 ── */
QPushButton[class="primaryBtn"],
QPushButton[class="primary"] {{
    background: {ACCENT};
    color: {BG_BASE};
    border: 1px solid {ACCENT};
}}

QPushButton[class="primaryBtn"]:hover,
QPushButton[class="primary"]:hover {{
    background: #4c83f7;
}}

QPushButton[class="primaryBtn"]:pressed,
QPushButton[class="primary"]:pressed {{
    background: #1554d1;
}}

/* ── 危险按钮 ── */
QPushButton[class="dangerBtn"],
QPushButton[class="danger"] {{
    background: {DANGER};
    color: {BG_BASE};
    border: 1px solid {DANGER};
}}

QPushButton[class="dangerBtn"]:hover,
QPushButton[class="danger"]:hover {{
    background: #e02e55;
}}

/* ── 暗色按钮 ── */
QPushButton[class="darkBtn"] {{
    background: {FG_PRIMARY};
    color: {BG_BASE};
    border: 1px solid {FG_PRIMARY};
}}

QPushButton[class="darkBtn"]:hover {{
    background: {SUBTEXT0};
    border-color: {SUBTEXT0};
}}

QPushButton[class="darkBtn"]:pressed {{
    background: {SUBTEXT1};
}}

/* ── 操作按钮 ── */
QPushButton[class="action"],
QToolButton[class="action"] {{
    background: {BG_INPUT};
    color: {ACCENT};
    border: 1px solid {ACCENT};
    border-radius: 6px;
    padding: 2px 12px;
    font-weight: bold;
    font-size: {FONT_SIZE_NORMAL}px;
}}

QPushButton[class="action"]:hover,
QToolButton[class="action"]:hover {{
    background: {BG_HOVER};
}}

QToolButton[class="action"]::menu-indicator {{
    image: none;
    width: 0;
}}

/* ── Dialog 按钮栏 ── */
QDialogButtonBox QPushButton {{
    background: {SURFACE0};
    color: {FG_PRIMARY};
    border: 1px solid {SURFACE1};
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 20px;
    min-width: 80px;
}}

QDialogButtonBox QPushButton:hover {{
    background: {SURFACE1};
}}

/* ── 表格 ── */
QTableWidget, QTableView {{
    background: {BG_BASE};
    alternate-background-color: {MANTLE};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    gridline-color: {BORDER_LIGHT};
    selection-background-color: {SURFACE0};
    selection-color: {FG_PRIMARY};
    outline: none;
}}

QTableWidget::item {{
    padding: 4px 8px;
}}

QTableWidget::item:selected {{
    background: {SURFACE0};
}}

QTableView[class="compactTable"],
QTableWidget[class="compactTable"] {{
    font-size: 12px;
    alternate-background-color: {MANTLE};
}}

/* ── 表头 ── */
QHeaderView::section {{
    background: {MANTLE};
    color: {FG_PRIMARY};
    border: none;
    border-right: 1px solid {BORDER_LIGHT};
    border-bottom: 1px solid {BORDER_LIGHT};
    padding: 6px 10px;
    font-weight: bold;
    font-size: 12px;
}}

QHeaderView::section:hover {{
    background: {BORDER_LIGHT};
}}

/* ── Tab ── */
QTabWidget::pane {{
    background: {BG_BASE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    top: -1px;
}}

QTabBar::tab {{
    background: {MANTLE};
    color: {SUBTEXT0};
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {BG_BASE};
    color: {ACCENT};
    font-weight: bold;
    border-bottom: 2px solid {ACCENT};
}}

QTabBar::tab:hover:!selected {{
    background: {BORDER_LIGHT};
    color: {FG_PRIMARY};
}}

/* ── 滚动条（垂直） ── */
QScrollBar:vertical {{
    background: {BG_BASE};
    width: 10px;
    margin: 0;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {SURFACE1};
    min-height: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {SURFACE2};
}}

QScrollBar::handle:vertical:pressed {{
    background: {OVERLAY0};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

/* ── 滚动条（水平） ── */
QScrollBar:horizontal {{
    background: {BG_BASE};
    height: 10px;
    margin: 0;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {SURFACE1};
    min-width: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {SURFACE2};
}}

QScrollBar::handle:horizontal:pressed {{
    background: {OVERLAY0};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── 标签 ── */
QLabel {{
    color: {FG_PRIMARY};
    background: transparent;
    border: none;
    padding: 0;
}}

QLabel[class="pageTitle"] {{
    font-size: 20px;
    font-weight: bold;
    color: {FG_PRIMARY};
}}

QLabel[class="sectionTitle"] {{
    font-size: 14px;
    font-weight: bold;
    padding: 4px;
}}

QLabel[class="smallText"] {{
    font-size: 12px;
}}

QLabel[class="hintText"] {{
    color: {SUBTEXT0};
    font-size: 12px;
}}

QLabel[class="blueBold"] {{
    font-weight: bold;
    color: {ACCENT};
}}

QLabel[class="filter-label"] {{
    color: {FG_PRIMARY};
    font-size: 12px;
    font-weight: bold;
}}

QLabel[class="panel-header"] {{
    color: {FG_PRIMARY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: bold;
}}

QLabel[class="text-bold"] {{
    color: {FG_PRIMARY};
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: bold;
}}

QLabel[class="subtext"] {{
    color: {FG_SECONDARY};
    font-size: 12px;
    font-weight: 500;
}}

QLabel[class="hint-label"] {{
    color: {FG_SECONDARY};
    font-size: 11px;
    border: none;
    background: transparent;
}}

QLabel[class="stat-value"] {{
    color: {FG_PRIMARY};
    font-size: 16px;
    font-weight: bold;
    border: none;
}}

QLabel[class="accent-label"] {{
    color: {ACCENT};
    font-size: 12px;
    font-weight: bold;
}}

QLabel[class="count-label"] {{
    color: {FG_SECONDARY};
}}

QLabel[class="filter-chip"] {{
    color: {FG_SECONDARY};
    font-size: 12px;
    font-weight: 500;
    background-color: {BG_HOVER};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 2px 6px;
}}

QLabel[class="empty-label"] {{
    color: {OVERLAY0};
    font-size: 14px;
}}

QLabel[class="separator"] {{
    background-color: {BORDER};
    border: none;
}}

QLabel[class="hint-italic"] {{
    color: {SUBTEXT0};
    font-size: 11px;
    font-style: italic;
}}

QLabel[class="body-text"] {{
    color: {TEXT};
    font-size: 12px;
}}

QLabel[class="section-label"] {{
    color: {TEXT};
    font-size: 12px;
    font-weight: bold;
}}

QLabel[class="detail-text"] {{
    color: {SUBTEXT0};
    font-size: 12px;
    padding: 4px 0;
}}

/* ── 复选框 ── */
QCheckBox {{
    color: {FG_PRIMARY};
    spacing: 8px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {SURFACE1};
    border-radius: 3px;
    background: {BG_BASE};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: none;
}}

QCheckBox::indicator:disabled {{
    background: {MANTLE};
    border-color: {BORDER_LIGHT};
}}

/* ── 单选按钮 ── */
QRadioButton {{
    color: {FG_PRIMARY};
    background: transparent;
    spacing: 8px;
}}

/* ── 菜单 ── */
QMenuBar {{
    background-color: {BG_CARD};
    color: {FG_PRIMARY};
    border-bottom: 1px solid {BORDER};
}}

QMenuBar::item:selected {{
    background-color: {BG_HOVER};
}}

QMenu {{
    background: {BG_BASE};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 0;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background: {SURFACE0};
    border-radius: 2px;
}}

QMenu::separator {{
    height: 1px;
    background: {BORDER_LIGHT};
    margin: 4px 8px;
}}

/* ── 工具提示 ── */
QToolTip {{
    background: {MANTLE};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* ── 进度条 ── */
QProgressBar {{
    background: {SURFACE0};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 4px;
}}

/* ── 状态栏 ── */
QStatusBar {{
    background: {MANTLE};
    color: {SUBTEXT0};
    border-top: 1px solid {BORDER_LIGHT};
    font-size: 12px;
    padding: 2px 8px;
}}

/* ── 分割器 ── */
QSplitter::handle {{
    background: {BORDER_LIGHT};
}}

QSplitter::handle:horizontal {{
    width: 1px;
}}

QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── 工具栏 ── */
QToolBar {{
    background-color: {BG_CARD};
    border-bottom: 1px solid {BORDER};
    spacing: 8px;
    padding: 4px 12px;
}}

QToolBar QToolButton {{
    background-color: transparent;
    color: {FG_PRIMARY};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: {FONT_SIZE_NORMAL}px;
    font-weight: 500;
}}

QToolBar QToolButton:hover {{
    background-color: {BG_HOVER};
    border-color: {BORDER};
}}

QToolBar QToolButton:pressed {{
    background-color: {SURFACE1};
}}

QToolBar QToolButton:disabled {{
    color: {FG_MUTED};
}}

QToolBar::separator {{
    width: 1px;
    background-color: {BORDER};
    margin: 4px 4px;
}}

/* ── 列表 ── */
QListWidget {{
    background-color: {BG_DARK};
    alternate-background-color: {BG_CARD};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
}}

QListWidget::item {{
    padding: 6px 8px;
}}

QListWidget::item:selected {{
    background-color: {BG_HOVER};
}}

QListWidget::item:alternate {{
    background-color: {BG_CARD};
}}

/* ── 背景容器 ── */
QWidget[class="bg-base"] {{
    background-color: {BG_BASE};
}}

QScrollArea[class="scroll-base"] {{
    background-color: {BG_BASE};
    border: none;
}}

QWidget[class="container-base"] {{
    background-color: {BG_BASE};
}}

/* ── 统计卡片容器 ── */
QFrame[class="stat-card"], QWidget[class="stat-card"] {{
    background-color: {MANTLE};
    border: 1px solid {SURFACE1};
    border-radius: 6px;
    padding: 8px;
}}

/* ── 卡片背景 ── */
QFrame[class="card-bg"], QWidget[class="card-bg"] {{
    background-color: {MANTLE};
    border: 1px solid {SURFACE1};
    border-radius: 16px;
}}

QWidget[class="card-bg-sm"] {{
    background-color: {MANTLE};
    border: 1px solid {SURFACE1};
    border-radius: 10px;
}}

/* ── 卡片容器 ── */
QWidget[class="card-container"] {{
    background-color: {BG_CARD};
    border-radius: 8px;
}}

QWidget[class="card-container"]:hover {{
    background-color: {BG_HOVER};
}}

/* ── 筛选栏 ── */
QWidget[class="filter-bar"] {{
    background-color: {BG_CARD};
    padding: 6px 20px;
    border-radius: 8px;
}}

QComboBox[class="filter-combo"] {{
    background-color: {BG_INPUT};
    color: {FG_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    min-height: 26px;
}}

/* ── 输入框文字变体 ── */
QLineEdit[class="field-text"] {{
    color: {TEXT};
    font-size: 12px;
}}

QLineEdit[class="field-text-sm"] {{
    color: {TEXT};
    font-size: 11px;
}}

/* ── 行背景 ── */
QWidget[class="row-surface"] {{
    background-color: {SURFACE0};
    border-radius: 4px;
}}

/* ── 结果行状态（动态 row-state 属性） ── */
QFrame[row-state="normal"]   {{
    background-color: {SURFACE0};
    border: 1px solid {SURFACE1};
    border-radius: 6px;
    padding: 4px;
}}

QFrame[row-state="attention"] {{
    background-color: {SELECTION_BG};
    border: 1px solid {ACCENT};
    border-radius: 6px;
    padding: 4px;
}}

QFrame[row-state="deleted"]   {{
    background-color: {SURFACE2};
    border: 1px solid {DANGER};
    border-radius: 6px;
    padding: 4px;
}}
"""


# ═══════════════════════════════════════════════════════════════════
#  公开 API
# ═══════════════════════════════════════════════════════════════════

# 预编译缓存
_COMPILED_STYLESHEET: str | None = None


def get_stylesheet() -> str:
    """获取完整的应用 QSS 样式表。

    Returns:
        当前主题（Latte / Mocha）的完整 QSS 字符串。
    """
    global _COMPILED_STYLESHEET
    if _COMPILED_STYLESHEET is None:
        _COMPILED_STYLESHEET = _build_qss()
    return _COMPILED_STYLESHEET


def set_theme(name: str) -> None:
    """切换主题（light / dark）。

    1. 用 globals().update() 重绑定所有颜色常量
    2. 清空 QSS 缓存
    3. 发射 theme_changed 信号
    """
    global _current_theme, _COMPILED_STYLESHEET
    if name not in _PALETTES:
        raise ValueError(f"Unknown theme: {name!r}, expected 'light' or 'dark'")
    if name == _current_theme:
        return

    _current_theme = name
    globals().update(_PALETTES[name])
    _COMPILED_STYLESHEET = None
    theme_host.theme_changed.emit(name)


def current_theme() -> str:
    """返回当前主题名称。"""
    return _current_theme


def apply_palette() -> None:
    """同步 QPalette 到当前主题色板。

    QSS 只覆盖匹配选择器的控件；QPalette 是 fallback 机制，
    控制 QSS 未覆盖的子控件（QCalendarWidget、QComboBox popup、
    QScrollArea viewport 等原生弹出窗口的背景和文字色）。
    必须在 set_theme() 之后、setStyleSheet() 之前调用。
    """
    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(BG_DARK))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(FG_PRIMARY))
    pal.setColor(QPalette.ColorRole.Base, QColor(BG_INPUT))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_CARD))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(MANTLE))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(FG_PRIMARY))
    pal.setColor(QPalette.ColorRole.Text, QColor(FG_PRIMARY))
    pal.setColor(QPalette.ColorRole.Button, QColor(SURFACE0))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(FG_PRIMARY))
    pal.setColor(QPalette.ColorRole.BrightText, QColor(RED))
    pal.setColor(QPalette.ColorRole.PlaceholderText, QColor(FG_MUTED))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(BASE))

    app.setPalette(pal)


def get_palette() -> dict[str, str]:
    """返回当前色板（只读副本）。"""
    return dict(_PALETTES[_current_theme])
