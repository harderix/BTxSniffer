"""Combo rule editor, detections manager, and country selector QSS."""

# =============================================================================
# COMBO RULE / DETECTIONS MANAGER STYLES
# =============================================================================

GROUPBOX_STYLE = """
    QGroupBox {
        font-weight: bold;
        border: 1px solid #59336c;
        border-radius: 8px;
        margin-top: 14px;
        padding-top: 25px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #26172f, stop:1 #190f1f);
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 15px;
        top: 0px;
        padding: 4px 14px;
        color: #5de8fb;
        background-color: #331f3f;
        border: 1px solid #59336c;
        border-radius: 6px;
    }

    /* Make inner container widgets transparent so the group box gradient shows through */
    QGroupBox QWidget {
        background-color: transparent;
    }

    /* Re-specify backgrounds for form controls that need them */
    QGroupBox QComboBox,
    QGroupBox QLineEdit,
    QGroupBox QTextEdit,
    QGroupBox QPlainTextEdit {
        background-color: #1b1024;
        border: 1px solid #3a234e;
        border-radius: 4px;
        color: #efd7f3;
        padding: 4px 8px;
        min-height: 24px;
        font-size: 9pt;
    }
    QGroupBox QSpinBox,
    QGroupBox QDoubleSpinBox {
        background-color: #1b1024;
        border: 1px solid #3a234e;
        border-radius: 4px;
        color: #efd7f3;
        padding: 2px 4px;
        min-height: 24px;
        min-width: 100px;
        font-size: 9pt;
    }
    QGroupBox QPushButton {
        min-height: 26px;
        background-color: #331f3f;
        border: 1px solid #59336c;
        border-radius: 4px;
        color: #efd7f3;
        font-size: 9pt;
    }
    QGroupBox QPushButton:hover {
        background-color: #3f264e;
    }
    QGroupBox QComboBox:focus,
    QGroupBox QSpinBox:focus,
    QGroupBox QDoubleSpinBox:focus,
    QGroupBox QLineEdit:focus {
        border: 1px solid #ff2bd6;
    }
    QGroupBox QComboBox QAbstractItemView {
        background-color: #26172f;
        border: 1px solid #59336c;
        border-radius: 4px;
        padding: 2px 1px;
        selection-background-color: #3f264e;
        outline: none;
    }
    QGroupBox QComboBox QAbstractItemView::item {
        min-height: 20px;
        padding: 2px 6px;
        margin: 1px 0px;
        border-radius: 3px;
        border: none;
    }
    QGroupBox QComboBox QAbstractItemView::item:hover {
        background-color: #372044;
        border-radius: 3px;
        padding: 2px 6px;
    }
    QGroupBox QComboBox QAbstractItemView::item:selected {
        background-color: #ff2bd6;
        color: white;
        border-radius: 3px;
        padding: 2px 6px;
    }
    QGroupBox QCheckBox::indicator {
        width: 14px;
        height: 14px;
        background-color: #1b1024;
        border: 1px solid #3a234e;
        border-radius: 3px;
    }
    QGroupBox QCheckBox::indicator:hover {
        border-color: #ff2bd6;
    }
    QGroupBox QCheckBox::indicator:checked {
        background-color: #ff2bd6;
        border-color: #ff2bd6;
    }
"""

LIST_WIDGET_STYLE = """
    QListWidget {
        background: #23152b;
        border: 1px solid #3f264e;
        border-radius: 4px;
        padding: 5px;
        font-family: 'Consolas', 'Courier New', monospace;
    }
    QListWidget::item {
        padding: 5px;
        border-radius: 3px;
    }
    QListWidget::item:hover {
        background: #372044;
    }
    QListWidget::item:selected {
        background: #ff2bd6;
        color: white;
    }
"""

SECTION_SEPARATOR_LABEL_STYLESHEET = """
    color: #5de8fb;
    font-size: 9pt;
    font-weight: bold;
    padding: 6px 12px;
    margin-top: 8px;
    margin-bottom: 4px;
    background-color: #211329;
    border: 1px solid #3f264e;
    border-radius: 4px;
"""

DESC_LABEL_STYLESHEET = 'color: #65eafb; font-style: italic; font-size: 10pt; padding: 5px;'

HINT_LABEL_STYLESHEET = 'color: #a293ad; font-style: italic; padding-bottom: 4px;'

BOLD_LABEL_STYLESHEET = 'font-weight: bold;'

RELAY_FILTER_WARNING_STYLESHEET = (
    'QWidget { background-color: #3a2400; border: 1px solid #c87800; border-radius: 6px; padding: 2px; }'
    'QLabel { border: none; }'
    'QPushButton { border: 1px solid #c87800; border-radius: 4px; background-color: #5a3a00;'
    ' color: #ffcc66; padding: 4px 10px; font-weight: bold; }'
    'QPushButton:hover { background-color: #7a5200; }'
)

WARNING_ICON_LABEL_STYLESHEET = 'font-size: 18pt; border: none;'

WARNING_TEXT_LABEL_STYLESHEET = 'color: #ffcc66; border: none;'

DETECTIONS_MANAGER_HEADER_STYLESHEET = (
    'font-size: 16pt; font-weight: bold; color: #5de8fb; padding: 10px;'
    'background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1c0f23, stop:0.5 #301a3d, stop:1 #1c0f23);'
    'border-radius: 6px; border: 1px solid #3f264e;'
)

# =============================================================================
# COUNTRY SELECTOR COMBO STYLES
# =============================================================================

COUNTRY_SELECTOR_COMBO_STYLESHEET = """
    QComboBox {
        font-size: 11pt;
        padding: 6px 10px;
        min-height: 28px;
    }
    QComboBox QAbstractItemView {
        font-size: 10pt;
    }
"""
