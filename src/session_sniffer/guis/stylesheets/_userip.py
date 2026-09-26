"""UserIP manager, settings panel, IP range builder, and color swatch QSS."""

# =============================================================================
# USERIP MANAGER STYLES
# =============================================================================

SUBNET_DESC_LABEL_STYLESHEET = 'color: #a293ad; font-style: italic;'

COLOR_SWATCH_GROUP_HEADER_STYLESHEET = 'color: #f36bcf; font-size: 8pt; font-weight: bold; padding: 4px 0px 1px 2px;'

COLOR_SWATCH_SEPARATOR_STYLESHEET = 'color: #342046;'

SETTINGS_SEPARATOR_STYLESHEET = 'background-color: rgba(239, 61, 192, 0.2); border: none;'

COLOR_BUTTON_EMPTY_STYLESHEET = (
    'QPushButton#ColorPickerButton, QPushButton#DatabaseColorButton {'
    ' background-color: transparent;'
    ' border: 1px solid #555;'
    ' border-radius: 4px;'
    ' min-width: 52px;'
    ' max-width: 52px;'
    ' min-height: 26px;'
    ' max-height: 26px;'
    ' padding: 0px;'
    ' margin: 0px;'
    '}'
    ' QPushButton#ColorPickerButton:hover, QPushButton#DatabaseColorButton:hover { border-color: #ef3dc0; }'
)


def color_swatch_button_stylesheet(bg_color: str, text_color: str, border_width: int, border_color: str) -> str:
    """Return the QSS for a color swatch button in the SVG color picker."""
    return (
        f'background-color: {bg_color}; color: {text_color};'
        f' border: {border_width}px solid {border_color}; border-radius: 2px;'
        ' font-size: 8pt; font-weight: bold; text-align: center;'
    )


def color_button_filled_stylesheet(color_name: str) -> str:
    """Return the QSS for a color preview button showing the given `color_name`."""
    return (
        'QPushButton#ColorPickerButton, QPushButton#DatabaseColorButton {'
        f' background-color: {color_name};'
        ' border: 1px solid #555;'
        ' border-radius: 4px;'
        ' min-width: 52px;'
        ' max-width: 52px;'
        ' min-height: 26px;'
        ' max-height: 26px;'
        ' padding: 0px;'
        ' margin: 0px;'
        '}'
        ' QPushButton#ColorPickerButton:hover, QPushButton#DatabaseColorButton:hover { border-color: #ffffff; }'
    )


# =============================================================================
# USERIP MANAGER SETTINGS PANEL STYLES
# =============================================================================

USERIP_SETTINGS_CONTAINER_STYLESHEET = """
#SettingsContainer {
    border: 2px solid #5c3d6c;
    border-radius: 8px;
    background: transparent;
}
"""

USERIP_SETTINGS_TOGGLE_STYLESHEET = """
QPushButton {
    background: transparent;
    border: none;
    color: #ef3dc0;
    font-size: 11pt;
    font-weight: bold;
    text-align: left;
    padding: 4px 8px;
}
QPushButton:hover {
    color: #f36ccf;
}
"""

USERIP_SETTINGS_BODY_STYLESHEET = """
QLabel {
    color: #c7a6cf;
    font-size: 10pt;
    font-weight: normal;
    background: transparent;
}
QComboBox, QLineEdit, QDoubleSpinBox {
    background: #291937;
    color: #e7c4ee;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 10pt;
    min-height: 22px;
}
QComboBox:hover, QLineEdit:hover, QDoubleSpinBox:hover {
    border-color: #ef3dc0;
}
QComboBox:disabled, QLineEdit:disabled, QDoubleSpinBox:disabled {
    background: #222;
    color: #555;
    border-color: #342046;
}
QLineEdit:focus {
    border-color: #ef3dc0;
    background: #333;
}
QPushButton {
    background: #342046;
    color: #e7c4ee;
    border: 1px solid #555;
    border-radius: 4px;
    font-size: 10pt;
    min-width: 28px;
    min-height: 24px;
    padding: 2px 6px;
}
QPushButton:hover {
    background: #ef3dc0;
    color: white;
    border-color: #ef3dc0;
}
"""

# =============================================================================
# IP RANGE BUILDER DIALOG STYLES
# =============================================================================

IP_RANGE_PREVIEW_VALID_STYLESHEET = 'font-family: Consolas, "Courier New", monospace; font-size: 10pt; padding: 6px; color: #80c080;'
IP_RANGE_PREVIEW_ERROR_STYLESHEET = 'font-family: Consolas, "Courier New", monospace; font-size: 10pt; padding: 6px; color: #e06060;'
IP_RANGE_PREVIEW_EMPTY_STYLESHEET = 'font-family: Consolas, "Courier New", monospace; font-size: 10pt; padding: 6px; color: #a293ad;'
