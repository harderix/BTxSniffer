"""GTA5 suspend button and Looky System crawler progress dialog QSS."""

# =============================================================================
# GTA5 MANUAL SUSPEND BUTTON STYLES
# =============================================================================

GTA5_MANUAL_SUSPEND_IDLE_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(230, 126, 34, 0.18), stop:1 rgba(211, 84, 0, 0.28));
    color: #f0a030;
    border: 1px solid rgba(230, 126, 34, 0.65);
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(230, 126, 34, 0.45), stop:1 rgba(211, 84, 0, 0.55));
    border: 1px solid rgba(230, 126, 34, 1.0);
    color: #ffd080;
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(211, 84, 0, 0.65), stop:1 rgba(230, 126, 34, 0.75));
    padding-top: 4px;
    padding-left: 9px;
}
QPushButton:disabled {
    color: rgba(150, 100, 50, 0.45);
    border: 1px solid rgba(150, 100, 50, 0.28);
    background: transparent;
}
""".strip()

GTA5_SOLO_SESSION_ACTIVE_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c61096, stop:1 #c61096);
    color: #f8a0e1;
    border: 1px solid #f542c5;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: bold;
}
QPushButton:disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c61096, stop:1 #c61096);
    color: #f990dd;
    border: 1px solid #d912a4;
}
""".strip()

GTA5_MANUAL_SUSPEND_ACTIVE_STYLESHEET = """
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c0392b, stop:1 #96281b);
    color: #ffffff;
    border: 1px solid #e74c3c;
    border-radius: 4px;
    padding: 3px 8px;
    font-weight: bold;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
    border: 1px solid #ff6b5b;
    color: #f9effa;
}
QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #96281b, stop:1 #c0392b);
    padding-top: 4px;
    padding-left: 9px;
}
""".strip()

# =============================================================================
# CRAWLER PROGRESS DIALOG STYLES
# =============================================================================

CRAWLER_TARGET_INFO_LABEL_STYLESHEET = 'background-color: #281831;color: #c3b3ff;border: 1px solid #7a31f6;border-radius: 4px;padding: 6px 8px;'
