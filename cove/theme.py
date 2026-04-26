"""Cove visual theme.

Mirrors the design tokens used by cove-screen-recorder so all Cove apps
share one identity: deep near-black surfaces, a teal accent, mono labels,
section blocks with a 1px border, and an accent action button.
"""

# Palette --------------------------------------------------------------
ACCENT = "#50e6cf"
ACCENT_2 = "#3ddc97"
ACCENT_SOFT = "rgba(80, 230, 207, 0.14)"
ACCENT_RING = "rgba(80, 230, 207, 0.35)"
REC = "#ff5f6d"
REC_SOFT = "rgba(255, 95, 109, 0.14)"
REC_RING = "rgba(255, 95, 109, 0.35)"
WARN = "#ffb454"
WARN_SOFT = "rgba(255, 180, 84, 0.10)"
WARN_RING = "rgba(255, 180, 84, 0.35)"

BG = "#0b0b10"
BG_GRAD_1 = "#0d0d14"
BG_GRAD_2 = "#0a0a0f"
SURFACE = "#13131b"
SURFACE_2 = "#181822"
SURFACE_3 = "#1f1f2b"
SURFACE_4 = "#262635"

BORDER = "rgba(255, 255, 255, 0.06)"
BORDER_STRONG = "rgba(255, 255, 255, 0.10)"
BORDER_STRONGER = "rgba(255, 255, 255, 0.16)"

TEXT = "#ececf1"
TEXT_DIM = "#9a9aae"
TEXT_FAINT = "#6b6b80"

# Translated to opaque hex equivalents for places where Qt won't render
# rgba into a stylesheet rule (it does, but we keep these around for
# QPalette and progress-bar chunks).
ACCENT_HEX_DIM = "#1d2c2a"
BORDER_HEX = "#1a1a22"
BORDER_HEX_STRONG = "#23232d"

QSS = f"""
/* Base ----------------------------------------------------------- */

QMainWindow, QDialog, QWidget#chrome {{
    background-color: {BG};
    color: {TEXT};
}}

QWidget {{
    background-color: transparent;
    color: {TEXT};
    font-family: "Geist", "Inter", "Segoe UI", "Cantarell", sans-serif;
    font-size: 10pt;
}}

QToolTip {{
    color: {TEXT};
    background-color: {SURFACE_2};
    border: 1px solid {BORDER_HEX_STRONG};
    padding: 4px 6px;
}}

/* Titlebar ------------------------------------------------------- */

QFrame#titlebar {{
    background-color: {BG};
    border-bottom: 1px solid {BORDER_HEX};
    min-height: 38px;
    max-height: 38px;
}}
QLabel#titlebarTitle {{
    color: {TEXT_DIM};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
}}
QLabel#titlebarTitle[role="primary"] {{ color: {TEXT}; }}
QLabel#titlebarVer {{
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
}}
QFrame#titlebarMark {{
    background-color: {SURFACE};
    border: 1px solid {BORDER_HEX_STRONG};
    border-radius: 6px;
    min-width: 22px; max-width: 22px;
    min-height: 22px; max-height: 22px;
}}
QPushButton#winBtn {{
    background-color: transparent;
    color: {TEXT_FAINT};
    border: none;
    border-radius: 6px;
    min-width: 30px; max-width: 30px;
    min-height: 26px; max-height: 26px;
    font-size: 11pt;
    padding: 0;
}}
QPushButton#winBtn:hover {{
    background-color: {SURFACE};
    color: {TEXT};
}}
QPushButton#winBtnClose:hover {{
    background-color: #ff5f5733;
    color: #ff8a82;
}}

/* Hero / titles -------------------------------------------------- */

QLabel[role="hero-h1"] {{
    color: {TEXT};
    font-size: 18pt;
    font-weight: 600;
    letter-spacing: -0.5px;
}}
QLabel[role="hero-sub"] {{
    color: {TEXT_DIM};
    font-size: 10pt;
}}
QLabel[role="section-label"] {{
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QLabel[role="muted"] {{ color: {TEXT_DIM}; }}
QLabel[role="faint"] {{ color: {TEXT_FAINT}; }}
QLabel[role="warn"] {{ color: {WARN}; }}
QLabel[role="error"] {{ color: {REC}; }}
QLabel[role="mono"] {{
    color: {TEXT_DIM};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
}}

/* Status pill ---------------------------------------------------- */

QLabel#statusPill {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT};
    border: 1px solid {ACCENT_RING};
    border-radius: 12px;
    padding: 4px 12px;
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
QLabel#statusPill[state="paused"] {{
    background-color: {WARN_SOFT};
    color: {WARN};
    border-color: {WARN_RING};
}}
QLabel#statusPill[state="error"] {{
    background-color: {REC_SOFT};
    color: {REC};
    border-color: {REC_RING};
}}
QLabel#statusPill[state="off"] {{
    background-color: rgba(255,255,255,0.04);
    color: {TEXT_FAINT};
    border-color: {BORDER_HEX};
}}

/* Section block -------------------------------------------------- */

QFrame[role="section"] {{
    background-color: {SURFACE};
    border: 1px solid {BORDER_HEX};
    border-radius: 12px;
}}

/* Stats strip ---------------------------------------------------- */

QFrame#statsStrip {{
    background-color: {SURFACE};
    border: 1px solid {BORDER_HEX};
    border-radius: 10px;
}}
QFrame#statCell {{
    background-color: transparent;
    border-right: 1px solid {BORDER_HEX};
}}
QFrame#statCellLast {{ background-color: transparent; }}
QLabel#statKey {{
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 7.5pt;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
QLabel#statValue {{
    color: {TEXT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 11pt;
}}

/* Buttons -------------------------------------------------------- */

QPushButton {{
    background-color: {SURFACE_2};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_HEX};
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 9.5pt;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {SURFACE_3};
    color: {TEXT};
    border-color: {BORDER_HEX_STRONG};
}}
QPushButton:disabled {{
    background-color: {SURFACE};
    color: {TEXT_FAINT};
    border-color: {BORDER_HEX};
}}

QPushButton[kind="accent"] {{
    background-color: {ACCENT};
    color: #07120f;
    border: 1px solid rgba(255,255,255,0.08);
    font-weight: 600;
}}
QPushButton[kind="accent"]:hover {{
    background-color: #6cebd6;
}}
QPushButton[kind="accent"]:disabled {{
    background-color: {ACCENT_HEX_DIM};
    color: {TEXT_FAINT};
}}

QPushButton[kind="danger"] {{
    background-color: {REC};
    color: #fff;
    border: 1px solid rgba(255,255,255,0.08);
    font-weight: 600;
}}
QPushButton[kind="danger"]:hover {{
    background-color: #ff7a86;
}}

QPushButton[kind="outline"] {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT};
    border: 1px solid {ACCENT_RING};
}}
QPushButton[kind="outline"]:hover {{
    background-color: rgba(80,230,207,0.22);
    color: #fff;
}}

QPushButton#iconBtn {{
    background-color: {SURFACE_2};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_HEX};
    border-radius: 8px;
    min-width: 32px; max-width: 32px;
    min-height: 32px; max-height: 32px;
    padding: 0;
}}
QPushButton#iconBtn:hover {{
    color: {TEXT};
    border-color: {BORDER_HEX_STRONG};
    background-color: {SURFACE_3};
}}

/* Inputs --------------------------------------------------------- */

QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox, QTimeEdit {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER_HEX};
    border-radius: 8px;
    padding: 4px 10px;
    min-height: 22px;
    selection-background-color: {ACCENT};
    selection-color: #07120f;
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9.5pt;
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QComboBox:focus, QTimeEdit:focus {{
    border-color: {ACCENT};
    background-color: {SURFACE_3};
}}
QSpinBox::up-button, QSpinBox::down-button,
QTimeEdit::up-button, QTimeEdit::down-button {{
    background-color: transparent;
    border: none;
    width: 14px;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER_HEX_STRONG};
    selection-background-color: {ACCENT_SOFT};
    selection-color: {ACCENT};
}}

/* Checkbox ------------------------------------------------------- */

QCheckBox {{ spacing: 8px; color: {TEXT}; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER_HEX_STRONG};
    background-color: {SURFACE};
    border-radius: 4px;
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

/* Tree / table --------------------------------------------------- */

QTreeView, QTreeWidget {{
    background-color: {SURFACE};
    alternate-background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER_HEX};
    border-radius: 12px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {ACCENT};
    show-decoration-selected: 1;
    outline: 0;
}}
QHeaderView::section {{
    background-color: {SURFACE};
    color: {TEXT_FAINT};
    border: none;
    border-bottom: 1px solid {BORDER_HEX};
    padding: 8px 10px;
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}}
QTreeView::item, QTreeWidget::item {{
    padding: 7px 4px;
    border: none;
    border-bottom: 1px solid {BORDER_HEX};
}}
QTreeView::item:selected, QTreeWidget::item:selected {{
    background-color: {ACCENT_SOFT};
    color: {TEXT};
}}

/* Progress bar --------------------------------------------------- */

QProgressBar {{
    background-color: {SURFACE_2};
    border: 1px solid {BORDER_HEX};
    border-radius: 5px;
    text-align: center;
    color: {TEXT_DIM};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8.5pt;
    height: 16px;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
    margin: 1px;
}}

/* Slider --------------------------------------------------------- */

QSlider::groove:horizontal {{
    background: {SURFACE_2};
    height: 4px; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px; margin: -6px 0;
    border-radius: 7px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}

/* Scrollbar ------------------------------------------------------ */

QScrollBar:vertical, QScrollBar:horizontal {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{ width: 10px; }}
QScrollBar:horizontal {{ height: 10px; }}
QScrollBar::handle {{
    background: rgba(255,255,255,0.06);
    border-radius: 5px;
    min-width: 24px; min-height: 24px;
}}
QScrollBar::handle:hover {{ background: rgba(255,255,255,0.12); }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* Menu ----------------------------------------------------------- */

QMenu {{
    background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER_HEX_STRONG};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
QMenu::item:selected {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT};
}}
QMenu::separator {{
    background-color: {BORDER_HEX};
    height: 1px;
    margin: 4px 8px;
}}

/* Footer --------------------------------------------------------- */

QFrame#footer {{
    background-color: {BG};
    border-top: 1px solid {BORDER_HEX};
    min-height: 44px;
    max-height: 44px;
}}
QLabel#footerLabel {{
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QLabel#footerKey {{
    color: {TEXT_DIM};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
}}
QLabel#footerKey b {{ color: {TEXT}; font-weight: 500; }}
QLabel#footerPlatform {{
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
}}

/* Group box (used in dialogs) ----------------------------------- */

QGroupBox {{
    border: 1px solid {BORDER_HEX};
    border-radius: 10px;
    margin-top: 16px;
    padding: 14px 12px 10px 12px;
    color: {TEXT_FAINT};
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 8pt;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}}

/* Info badge (small "i" with tooltip) --------------------------- */

QLabel#infoBadge {{
    color: {TEXT_FAINT};
    background-color: {SURFACE_2};
    border: 1px solid {BORDER_HEX_STRONG};
    border-radius: 10px;
    font-family: "Geist Mono", "JetBrains Mono", monospace;
    font-size: 9pt;
    font-style: italic;
}}
QLabel#infoBadge:hover {{
    color: {ACCENT};
    border-color: {ACCENT_RING};
}}

/* Dialog header label ------------------------------------------- */

QLabel#dialogTitle {{
    color: {TEXT};
    font-size: 13pt;
    font-weight: 600;
    letter-spacing: -0.3px;
}}
QLabel#dialogSubtitle {{
    color: {TEXT_DIM};
    font-size: 9.5pt;
}}
"""
