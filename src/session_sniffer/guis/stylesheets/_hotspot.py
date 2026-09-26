"""Hotspot and connection sharing QSS."""

HOTSPOT_CARD_STYLESHEET = """
QFrame#hotspotCard, QFrame#bridgeCard, QFrame#devicesCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #352041, stop:1 #25162e);
    border: 1px solid #422752;
    border-radius: 10px;
}

QFrame#hotspotCard QWidget#emptyDevicesWidget,
QFrame#devicesCard QWidget#emptyDevicesWidget,
QFrame#hotspotCard QCheckBox,
QFrame#bridgeCard QCheckBox,
QFrame#devicesCard QCheckBox {
    background: transparent;
    background-color: transparent;
}
""".strip()

HOTSPOT_CHECKBOX_STYLESHEET = """
QCheckBox {
    background: transparent;
    background-color: transparent;
    color: #c590d2;
    font-size: 8.5pt;
}

QCheckBox:hover {
    color: #efd7f3;
}
""".strip()

HOTSPOT_CARD_HEADER_STYLESHEET = """
QLabel {
    color: #f9effa;
    font-size: 11pt;
    font-weight: 700;
}
""".strip()

HOTSPOT_BADGE_ACTIVE_STYLESHEET = """
QLabel {
    color: #3dd68c;
    background: rgba(61, 214, 140, 0.12);
    border: 1px solid rgba(61, 214, 140, 0.35);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 8pt;
    font-weight: 800;
    letter-spacing: 0.5px;
}
""".strip()

HOTSPOT_BADGE_INACTIVE_STYLESHEET = """
QLabel {
    color: #c590d2;
    background: rgba(197, 144, 210, 0.12);
    border: 1px solid rgba(197, 144, 210, 0.30);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 8pt;
    font-weight: 800;
    letter-spacing: 0.5px;
}
""".strip()

HOTSPOT_BADGE_TRANSITION_STYLESHEET = """
QLabel {
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 8pt;
    font-weight: 800;
    letter-spacing: 0.5px;
}
""".strip()

HOTSPOT_PILL_INFO_STYLESHEET = """
QLabel {
    color: #f25ecb;
    background: rgba(242, 94, 203, 0.10);
    border: 1px solid rgba(242, 94, 203, 0.25);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 8pt;
    font-weight: 600;
}
""".strip()

HOTSPOT_FIELD_LABEL_STYLESHEET = """
QLabel {
    color: #c590d2;
    font-size: 9pt;
    font-weight: 600;
}
""".strip()

HOTSPOT_INPUT_STYLESHEET = """
QLineEdit, QComboBox {
    background-color: #1e1224;
    color: #eddcf2;
    border: 1px solid #3c244a;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 9pt;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #ec1ab4;
    background-color: #22142b;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
""".strip()

HOTSPOT_EMPTY_STATE_STYLESHEET = """
QLabel {
    color: #78518b;
    font-size: 9.5pt;
    font-weight: 500;
    background: transparent;
    background-color: transparent;
}
""".strip()

HOTSPOT_GUIDE_CONTAINER_STYLESHEET = """
QFrame#guideContainer {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #271730, stop:1 #1b1022);
    border: 1px solid #432852;
    border-radius: 14px;
}

QFrame#guideContainer QLabel {
    background: transparent;
    border: none;
}

QFrame#guideContainer QWidget,
QFrame#guideContainer QStackedWidget {
    background: transparent;
    background-color: transparent;
}
""".strip()

HOTSPOT_GUIDE_CARD_STYLESHEET = """
QFrame#guideOptionCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e1b39, stop:1 #211329);
    border: 1px solid #472a57;
    border-radius: 10px;
}

QFrame#guideOptionCard:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3a2348, stop:1 #2a1933);
    border: 1px solid #ec1ab4;
}

QFrame#guideOptionCard QLabel {
    background: transparent;
    border: none;
}
""".strip()

HOTSPOT_STEP_NUMBER_STYLESHEET = """
QLabel {
    color: #ffffff;
    background-color: #d3119f;
    border-radius: 11px;
    font-size: 8.5pt;
    font-weight: 800;
    min-width: 22px;
    max-width: 22px;
    min-height: 22px;
    max-height: 22px;
    qproperty-alignment: AlignCenter;
}
""".strip()
