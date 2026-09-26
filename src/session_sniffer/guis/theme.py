"""BTX neon dark theme for BTXSniffer (based on Session Sniffer by BUZZARDGTA)."""

from PySide6.QtGui import QColor, QPalette

from session_sniffer.constants.local import RESOURCES_DIR_PATH
from session_sniffer.guis.stylesheets._menus import SHARED_QMENU_RIGHT_ARROW_STYLESHEET

_SCALE_THRESHOLD_LARGE = 0.85
_SCALE_THRESHOLD_MEDIUM = 0.75


def get_dark_palette() -> QPalette:
    """Return a unified dark QPalette for Qt widgets and window decorations."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor('#1b1024'))
    palette.setColor(QPalette.ColorRole.WindowText, QColor('#efd7f3'))
    palette.setColor(QPalette.ColorRole.Base, QColor('#100a16'))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor('#22142e'))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor('#1b1024'))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor('#efd7f3'))
    palette.setColor(QPalette.ColorRole.Text, QColor('#efd7f3'))
    palette.setColor(QPalette.ColorRole.Button, QColor('#2a1938'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.BrightText, QColor('#ffffff'))
    palette.setColor(QPalette.ColorRole.Link, QColor('#ff2bd6'))
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#ff2bd6'))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
    return palette


def get_stylesheet(ui_scale: float = 1.0) -> str:
    """Return the custom PySide6 stylesheet.

    Args:
        ui_scale: The UI scale factor from `compute_ui_scale`. Controls font
            sizes throughout the stylesheet so the UI reads clearly at every
            supported screen resolution.

    Returns:
        The QSS stylesheet as a string.
    """
    branch_vline_path = (RESOURCES_DIR_PATH / 'icons' / 'branch_vline.svg').as_posix()
    branch_more_path = (RESOURCES_DIR_PATH / 'icons' / 'branch_more.svg').as_posix()
    branch_end_path = (RESOURCES_DIR_PATH / 'icons' / 'branch_end.svg').as_posix()
    chevron_right_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_right.svg').as_posix()
    chevron_right_disabled_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_right_disabled.svg').as_posix()
    chevron_right_more_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_right_more.svg').as_posix()
    chevron_right_end_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_right_end.svg').as_posix()
    chevron_down_more_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_down_more.svg').as_posix()
    chevron_down_end_path = (RESOURCES_DIR_PATH / 'icons' / 'chevron_down_end.svg').as_posix()
    arrow_up_path = (RESOURCES_DIR_PATH / 'icons' / 'arrow_up.svg').as_posix()
    arrow_down_path = (RESOURCES_DIR_PATH / 'icons' / 'arrow_down.svg').as_posix()
    check_path = (RESOURCES_DIR_PATH / 'icons' / 'check.svg').as_posix()
    close_path = (RESOURCES_DIR_PATH / 'icons' / 'close.svg').as_posix()

    # Scale the base font size proportionally to the screen resolution.
    # 10pt is the design baseline (2K / 1.0 scale).  Smaller screens get
    # proportionally smaller text so nothing overflows or clips.
    if ui_scale >= _SCALE_THRESHOLD_LARGE:
        base_font_pt = 10
    elif ui_scale >= _SCALE_THRESHOLD_MEDIUM:
        base_font_pt = 9
    else:
        base_font_pt = 8

    css = (
        """
    /* Main Background */
    QMainWindow, QDialog, QWidget {
        background-color: #100a16;
        color: #efd7f3;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: {base_font_pt}pt;
    }

    QDialog#InterfaceSelectionDialog {
        background-color: #180b1f;
    }
    QDialog#InterfaceSelectionDialog QStackedWidget,
    QDialog#InterfaceSelectionDialog QStackedWidget > QWidget,
    QDialog#InterfaceSelectionDialog QWidget#HotspotManagerWidget {
        background: transparent;
        background-color: transparent;
    }

    /* Tooltips */
    QToolTip {
        background-color: #1b1024;
        color: #efd7f3;
        border: 1px solid #2e1c3e;
        padding: 4px;
        border-radius: 4px;
    }

    /* Buttons */
    QPushButton {
        background-color: #2a1938;
        color: #ffffff;
        border: 1px solid #3a234e;
        border-radius: 4px;
        padding: 6px 16px;
    }
    QPushButton:hover {
        background-color: #3a234e;
        border-color: #ff2bd6;
    }
    QPushButton:pressed {
        background-color: #1b1024;
        border-color: #ff2bd6;
    }
    QPushButton:disabled {
        background-color: #170e20;
        color: #685874;
        border-color: #261733;
    }

    QPushButton[danger="true"] {
        border: 1px solid #7a3b3b;
        color: #e07070;
    }
    QPushButton[danger="true"]:hover {
        background-color: #3d2222;
        border-color: #e55353;
        color: #ff8888;
    }
    QPushButton[danger="true"]:pressed {
        background-color: #2b1515;
        border-color: #e55353;
    }

    /* Input Fields */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
        background-color: #1b1024;
        color: #efd7f3;
        border: 1px solid #3a234e;
        border-radius: 4px;
        padding: 4px 8px;
    }

    QPlainTextEdit {
        font-family: Consolas, 'Courier New', 'Lucida Console', monospace;
    }

    QAbstractItemView QLineEdit, QAbstractItemView QSpinBox, QAbstractItemView QDoubleSpinBox, QAbstractItemView QComboBox {
        padding: 0px 4px;
        margin: 0px;
        border-radius: 0px;
    }

    /* QSpinBox, QDoubleSpinBox {
        max-width removed to allow auto-sizing for prefixes/suffixes
    } */

    /* Checkboxes */
    QCheckBox {
        spacing: 8px;
        color: #efd7f3;
    }
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border: 1px solid #3a234e;
        border-radius: 3px;
        background-color: #1b1024;
    }
    QCheckBox::indicator:hover {
        border: 1px solid #ff2bd6;
    }
    QCheckBox::indicator:checked {
        background-color: #ff2bd6;
        border: 1px solid #ff2bd6;
        image: url("{check_path}");
    }
    QCheckBox::indicator:disabled {
        background-color: #2a1938;
        border: 1px solid #3a234e;
    }

    /* Radio Buttons */
    QRadioButton {
        spacing: 8px;
        color: #efd7f3;
    }
    QRadioButton::indicator {
        width: 14px;
        height: 14px;
        border: 1px solid #3a234e;
        border-radius: 8px;
        background-color: #1b1024;
    }
    QRadioButton::indicator:hover {
        border: 1px solid #ff2bd6;
    }
    QRadioButton::indicator:checked {
        border: 1px solid #ff2bd6;
        background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #ff2bd6, stop:0.45 #ff2bd6, stop:0.52 #1b1024, stop:1 #1b1024);
    }
    QRadioButton::indicator:checked:hover {
        border: 1px solid #ff00bb;
        background-color: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #ff00bb, stop:0.45 #ff00bb, stop:0.52 #1b1024, stop:1 #1b1024);
    }
    QRadioButton::indicator:disabled {
        background-color: #2a1938;
        border: 1px solid #3a234e;
    }

    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
        selection-background-color: #ff2bd6;
    }
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #ff2bd6;
    }
    QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
        background-color: #100a16;
        color: #685874;
    }

    /* SpinBox Buttons */
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 16px;
        background-color: transparent;
        border-left: 1px solid #2e1c3e;
        border-bottom: 1px solid #2e1c3e;
        border-top-right-radius: 3px;
    }
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
        background-color: rgba(255, 255, 255, 0.1);
    }

    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: padding;
        subcontrol-position: bottom right;
        width: 16px;
        background-color: transparent;
        border-left: 1px solid #2e1c3e;
        border-bottom-right-radius: 3px;
    }
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
        background-color: rgba(255, 255, 255, 0.1);
    }

    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: url("{arrow_up_path}");
        width: 7px;
        height: 7px;
    }

    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: url("{arrow_down_path}");
        width: 7px;
        height: 7px;
    }

    /* ComboBox Dropdown */
    QComboBox {
        padding: 3px 6px;
    }
    QComboBox:hover, QComboBox:on {
        border-color: #ff2bd6;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        background-color: transparent;
        border-left: 1px solid #2e1c3e;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
    }
    QComboBox::drop-down:hover {
        background-color: rgba(255, 255, 255, 0.08);
    }
    QComboBox::down-arrow {
        image: url("{arrow_down_path}");
        width: 7px;
        height: 7px;
    }
    QComboBox QAbstractItemView {
        background-color: #22142e;
        border: 1px solid #3a234e;
        border-radius: 4px;
        padding: 2px 1px;
        outline: none;
        color: #efd7f3;
        selection-background-color: #ff2bd6;
    }
    QComboBox QAbstractItemView::item {
        min-height: 20px;
        padding: 2px 6px;
        margin: 1px 0px;
        border-radius: 3px;
        border: none;
        border-bottom: none;
        background-color: transparent;
        color: #efd7f3;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #2a1938;
        color: #ffffff;
        border-radius: 3px;
        padding: 2px 6px;
        border: none;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #ff2bd6;
        color: #ffffff;
        border-radius: 3px;
        padding: 2px 6px;
        border: none;
    }
    QComboBox QAbstractItemView::item:selected:hover {
        background-color: #ff00bb;
        color: #ffffff;
        border-radius: 3px;
        padding: 2px 6px;
        border: none;
    }
    QComboBox QAbstractItemView::item:focus {
        background-color: #ff2bd6;
        color: #ffffff;
        border-radius: 3px;
        padding: 2px 6px;
        border: none;
        outline: none;
    }

    /* Tables */
    QTableView, QTreeView, QListView {
        background-color: #1b1024;
        alternate-background-color: #22142e;
        color: #efd7f3;
        gridline-color: #2e1c3e;
        border: 1px solid #2e1c3e;
        selection-background-color: rgba(215, 0, 158, 0.18);
        selection-color: #ffffff;
        outline: none;
        show-decoration-selected: 0;
    }
    QHeaderView::section {
        background-color: #2a1938;
        color: #5de8fb;
        padding: 4px;
        border: 1px solid #2e1c3e;
        font-weight: bold;
    }
    QHeaderView::up-arrow {
        image: url("{arrow_up_path}");
        width: 9px;
        height: 9px;
        margin-left: -7px;
        margin-right: 6px;
    }
    QHeaderView::down-arrow {
        image: url("{arrow_down_path}");
        width: 9px;
        height: 9px;
        margin-left: -7px;
        margin-right: 6px;
    }
    QTableView::item, QTreeView::item, QListView::item {
        border-bottom: 1px solid #2e1c3e;
        background-color: transparent;
        padding-left: 0px;
        padding-right: 0px;
        margin-left: 0px;
        margin-right: 0px;
        text-indent: 0px;
    }
    QTableView::item:hover {
        background-color: rgba(255, 255, 255, 0.05);
        padding-left: 0px;
        margin-left: 0px;
    }
    QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {
        background-color: rgba(215, 0, 158, 0.18);
        color: #ffffff;
        padding-left: 0px;
        padding-right: 0px;
        margin-left: 0px;
        margin-right: 0px;
        text-indent: 0px;
    }
    QTableView::item:selected:hover {
        background-color: rgba(215, 0, 158, 0.35);
        padding-left: 0px;
        margin-left: 0px;
    }
    QTableView::item:focus, QTreeView::item:focus, QListView::item:focus {
        background-color: rgba(215, 0, 158, 0.45);
        border: none;
        outline: none;
        color: #ffffff;
        padding-left: 0px;
        padding-right: 0px;
        margin-left: 0px;
        margin-right: 0px;
        text-indent: 0px;
    }

    QTreeView {
        gridline-color: transparent;
    }

    QTreeView::item {
        border: none;
        border-left: none;
        outline: none;
    }
    QTreeView::item:hover {
        background-color: #2a1938;
    }
    QTreeView::item:selected:hover {
        background-color: #c61096;
    }

    QTreeView::branch {
        background: transparent;
        border: none;
        border-image: none;
        image: none;
    }
    QTreeView::branch:hover {
        background-color: #2a1938;
    }
    QTreeView::branch:selected {
        background-color: #462857;
    }
    QTreeView::branch:selected:hover {
        background-color: #c61096;
    }

    QTreeView::branch:has-siblings:!adjoins-item {
        border-image: none;
        image: url("{branch_vline_path}");
    }

    QTreeView::branch:has-siblings:adjoins-item {
        border-image: none;
        image: url("{branch_more_path}");
    }

    QTreeView::branch:!has-children:!has-siblings:adjoins-item {
        border-image: none;
        image: url("{branch_end_path}");
    }

    QTreeView::branch:!has-children:!has-siblings:!adjoins-item {
        border-image: none;
        image: none;
    }

    QTreeView::branch:has-children:!has-siblings:closed {
        border-image: none;
        image: url("{chevron_right_end_path}");
    }

    QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url("{chevron_right_more_path}");
    }

    QTreeView::branch:has-children:!has-siblings:open {
        border-image: none;
        image: url("{chevron_down_end_path}");
    }

    QTreeView::branch:open:has-children:has-siblings {
        border-image: none;
        image: url("{chevron_down_more_path}");
    }

    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background-color: #1b1024;
        width: 12px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background-color: #3c2450;
        min-height: 20px;
        border-radius: 4px;
        margin: 2px;
    }
    QScrollBar::handle:vertical:hover {
        background-color: #6a5977;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
        background: none;
        height: 0px;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        border: none;
        background-color: #1b1024;
        height: 12px;
        margin: 0px;
    }
    QScrollBar::handle:horizontal {
        background-color: #3c2450;
        min-width: 20px;
        border-radius: 4px;
        margin: 2px;
    }
    QScrollBar::handle:horizontal:hover {
        background-color: #6a5977;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        border: none;
        background: none;
        width: 0px;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: none;
    }

    /* Tab Widget */
    QTabWidget::pane {
        border: 1px solid #2e1c3e;
        background-color: #1b1024;
    }
    QTabBar::tab {
        background-color: #2a1938;
        color: #daa5e5;
        padding: 8px 16px;
        border: 1px solid #3a234e;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #1b1024;
        color: #ffffff;
        border-top: 2px solid #ff2bd6;
        font-weight: bold;
    }
    QTabBar::tab:hover:!selected {
        background-color: #3a234e;
        color: #ffffff;
    }
    QTabBar::close-button {
        image: url("{close_path}");
        subcontrol-position: right;
        subcontrol-origin: padding;
        width: 14px;
        height: 14px;
        margin-right: 4px;
        border-radius: 3px;
    }
    QTabBar::close-button:hover {
        background-color: rgba(255, 255, 255, 0.15);
    }
    QTabBar::close-button:pressed {
        background-color: rgba(235, 75, 75, 0.45);
    }

    /* Group Box */
    QGroupBox {
        border: 1px solid #2e1c3e;
        border-radius: 4px;
        border-top-left-radius: 0px;
        margin-top: 26px;
        padding-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: -1px;
        top: 0px;
        padding: 4px 12px;
        background-color: #22142e;
        color: #5de8fb;
        border: 1px solid #2e1c3e;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-size: 11pt;
        font-weight: bold;
    }

    /* Menu Bar */
    QMenuBar {
        background-color: #22142e;
        color: #efd7f3;
        border-bottom: 1px solid #5de8fb;
        padding: 2px 4px;
        spacing: 2px;
    }
    QMenuBar::item {
        padding: 5px 14px;
        border-radius: 4px;
        background: transparent;
    }
    QMenuBar::item:selected {
        background-color: #3a234e;
    }
    QMenuBar::item:pressed {
        background-color: #4f306a;
    }
    QMenuBar::item:disabled {
        color: #685874;
        background: transparent;
    }
    QMenu {
        background-color: #22142e;
        color: #efd7f3;
        border: 1px solid #3a234e;
        border-radius: 4px;
        padding: 4px 6px;
    }
    QMenu::item {
        padding: 6px 24px 6px 8px;
    }
    QMenu::item:selected {
        background-color: #3a234e;
        border-radius: 3px;
    }
    QMenu::icon {
        padding-left: 8px;
    }
    QMenu::item:disabled {
        color: #685874;
        background-color: transparent;
    }
    QMenu::item:disabled:selected {
        color: #685874;
        background-color: transparent;
    }
    QMenu::separator {
        height: 1px;
        background: #2e1c3e;
        margin: 4px 10px;
    }
    """
        + SHARED_QMENU_RIGHT_ARROW_STYLESHEET
        + """

    /* Toolbar */
    QToolBar {
        background-color: #22142e;
        border-bottom: 1px solid #5de8fb;
        padding: 4px;
    }
    QToolButton {
        padding: 4px;
        border-radius: 4px;
    }
    QToolButton:hover {
        background-color: #3a234e;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #22142e;
        color: #efd7f3;
        border-top: 1px solid #5de8fb;
        padding: 4px 8px;
        min-height: 24px;
        font-size: {base_font_pt}pt;
    }
    QStatusBar::item {
        border: none;
    }

    /* Splitter */
    QSplitter {
        background-color: transparent;
    }
    QSplitter::handle {
        background-color: #2a1938;
        border-radius: 2px;
    }
    QSplitter::handle:hover {
        background-color: #ff2bd6;
    }
    QSplitter::handle:pressed {
        background-color: #ff00bb;
    }
    QSplitter::handle:horizontal {
        margin: 0px 1px;
    }
    QSplitter::handle:vertical {
        margin: 1px 0px;
    }

    /* Labels */
    QLabel {
        background-color: transparent;
        color: #efd7f3;
        font-size: {base_font_pt}pt;
    }
    """
    )
    css = css.replace('{branch_vline_path}', branch_vline_path)
    css = css.replace('{branch_more_path}', branch_more_path)
    css = css.replace('{branch_end_path}', branch_end_path)
    css = css.replace('{chevron_right_more_path}', chevron_right_more_path)
    css = css.replace('{chevron_right_path}', chevron_right_path)
    css = css.replace('{chevron_right_disabled_path}', chevron_right_disabled_path)
    css = css.replace('{chevron_right_end_path}', chevron_right_end_path)
    css = css.replace('{chevron_down_more_path}', chevron_down_more_path)
    css = css.replace('{chevron_down_end_path}', chevron_down_end_path)
    css = css.replace('{arrow_up_path}', arrow_up_path)
    css = css.replace('{arrow_down_path}', arrow_down_path)
    css = css.replace('{check_path}', check_path)
    css = css.replace('{close_path}', close_path)
    return css.replace('{base_font_pt}', str(base_font_pt))
