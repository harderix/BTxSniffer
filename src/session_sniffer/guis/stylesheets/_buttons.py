"""Dialog and compact button QSS."""

# =============================================================================
# DIALOG BUTTON STYLES
# =============================================================================

DIALOG_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(223, 251, 254, 0.12), stop:1 rgba(220, 168, 230, 0.18));
    color: #dffbfe;
    border: 1px solid rgba(82, 45, 101, 0.6);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 9pt;
    font-weight: bold;
    min-height: 28px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(237, 34, 183, 0.25), stop:1 rgba(209, 17, 158, 0.35));
    border: 1px solid rgba(237, 34, 183, 0.8);
    color: #ffffff;
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(209, 17, 158, 0.45), stop:1 rgba(237, 34, 183, 0.55));
    border: 1px solid rgba(209, 17, 158, 1.0);
}

QPushButton:disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(72, 44, 97, 0.15), stop:1 rgba(54, 33, 73, 0.20));
    color: #6f5d7b;
    border: 1px solid rgba(72, 44, 97, 0.3);
}
""".strip()

DIALOG_PRIMARY_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ec1ab4, stop:1 #c61096);
    color: #ffffff;
    border: 1px solid rgba(237, 34, 183, 0.7);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 9pt;
    font-weight: bold;
    min-height: 28px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ef3cbf, stop:1 #ec1ab4);
    border: 1px solid rgba(239, 60, 191, 0.9);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c61096, stop:1 #c61096);
    border: 1px solid rgba(198, 16, 150, 1.0);
}

QPushButton:disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(72, 44, 97, 0.15), stop:1 rgba(54, 33, 73, 0.20));
    color: #6f5d7b;
    border: 1px solid rgba(72, 44, 97, 0.3);
}
""".strip()

DIALOG_DANGER_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(192, 57, 43, 0.7), stop:1 rgba(146, 43, 33, 0.8));
    color: #ffffff;
    border: 1px solid rgba(192, 57, 43, 0.6);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 9pt;
    font-weight: bold;
    min-height: 28px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(231, 76, 60, 0.8), stop:1 rgba(192, 57, 43, 0.9));
    border: 1px solid rgba(231, 76, 60, 0.9);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(146, 43, 33, 0.9), stop:1 rgba(120, 35, 27, 1.0));
    border: 1px solid rgba(146, 43, 33, 1.0);
}

QPushButton:disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(72, 44, 97, 0.15), stop:1 rgba(54, 33, 73, 0.20));
    color: #6f5d7b;
    border: 1px solid rgba(72, 44, 97, 0.3);
}
""".strip()

# =============================================================================
# COMPACT BUTTON STYLE (shared across settings widgets)
# =============================================================================

COMPACT_BUTTON_STYLESHEET = (
    'QPushButton { background-color: #22142a; color: #c59acf; border: 1px solid #3c234a;'
    ' border-radius: 6px; padding: 6px 16px; font-size: 8pt; font-weight: bold; }'
    ' QPushButton:hover { background-color: #2c1a37; color: #ffffff; border: 1px solid #614171; }'
    ' QPushButton:pressed { background-color: #1b1021; color: #ffffff; border: 1px solid #ec1ab4; }'
    ' QPushButton:disabled { background-color: #160d1b; color: #412757; border: 1px solid #22142a; }'
)

COMPACT_DANGER_BUTTON_STYLESHEET = (
    'QPushButton { background-color: #2a1618; color: #d67a83; border: 1px solid #422528;'
    ' border-radius: 6px; padding: 6px 16px; font-size: 8pt; font-weight: bold; }'
    ' QPushButton:hover { background-color: #3b1f22; color: #ffffff; border: 1px solid #5c3237; }'
    ' QPushButton:pressed { background-color: #1c0e10; color: #ffffff; border: 1px solid #e74c3c; }'
    ' QPushButton:disabled { background-color: #161111; color: #4d3839; border: 1px solid #21191a; }'
)

# =============================================================================
# GRAPH POPOUT BUTTON STYLES
# =============================================================================

GRAPH_BPS_POPOUT_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(0, 187, 212, 0.15),
        stop:1 rgba(0, 148, 167, 0.25));
    color: #6febfb;
    border: 1px solid rgba(0, 187, 212, 0.45);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 8pt;
    font-weight: 600;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(0, 225, 255, 0.35),
        stop:1 rgba(0, 187, 212, 0.50));
    border: 1px solid #00e1ff;
    color: #ffffff;
}
QPushButton:pressed {
    background: rgba(0, 148, 167, 0.65);
    border: 1px solid #0094a7;
    color: #ffffff;
}
""".strip()

GRAPH_PPS_POPOUT_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(76, 175, 80, 0.15),
        stop:1 rgba(56, 142, 60, 0.25));
    color: #a5d6a7;
    border: 1px solid rgba(76, 175, 80, 0.45);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 8pt;
    font-weight: 600;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(105, 240, 174, 0.35),
        stop:1 rgba(76, 175, 80, 0.50));
    border: 1px solid #69f0ae;
    color: #ffffff;
}
QPushButton:pressed {
    background: rgba(56, 142, 60, 0.65);
    border: 1px solid #388e3c;
    color: #ffffff;
}
""".strip()

GRAPH_LATENCY_POPOUT_BUTTON_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 152, 0, 0.15),
        stop:1 rgba(230, 81, 0, 0.25));
    color: #ffcc80;
    border: 1px solid rgba(255, 152, 0, 0.45);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 8pt;
    font-weight: 600;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 171, 64, 0.35),
        stop:1 rgba(255, 152, 0, 0.50));
    border: 1px solid #ffab40;
    color: #ffffff;
}
QPushButton:pressed {
    background: rgba(230, 81, 0, 0.65);
    border: 1px solid #e65100;
    color: #ffffff;
}
""".strip()
