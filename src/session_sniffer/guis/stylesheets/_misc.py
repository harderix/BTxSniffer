"""Miscellaneous QSS: Discord popups, section headers, main window, settings labels, splash screen."""

# =============================================================================
# DISCORD DIALOG STYLES
# =============================================================================

DISCORD_POPUP_MAIN_STYLESHEET = """
background-color: #382145;  /* Dark blueish background */
border-radius: 15px;        /* Rounded corners */
color: white;
""".strip()

DISCORD_POPUP_EXIT_BUTTON_STYLESHEET = """
font-size: 8pt;
color: white;
background-color: #ff4c4c;  /* Light red background */
border-radius: 15px;        /* Make it circular */
""".strip()

DISCORD_POPUP_JOIN_BUTTON_STYLESHEET = """
font-size: 10pt;
padding: 7px;
background-color: #f258c9;  /* Discord blue */
color: white;
border-radius: 10px;
border: none;
""".strip()

# =============================================================================
# SECTION TABLE HEADER STYLES
# =============================================================================

SECTION_CLEAR_BUTTON_STYLESHEET = 'font-weight: 700; font-size: 9pt;'

SECTION_HEADER_SEPARATOR_STYLESHEET = 'background-color: rgba(255,255,255,0.55); border: none; max-width: 1px; min-width: 1px; margin: 6px 6px;'

# =============================================================================
# MAIN WINDOW STYLES
# =============================================================================

GTA5_STATUS_LABEL_STYLESHEET = 'QLabel { background: transparent; padding: 6px 28px 6px 16px; font-size: 10pt; }'

# =============================================================================
# SETTINGS DIALOG STYLES
# =============================================================================

DISCORD_INFO_LABEL_STYLESHEET = (
    'QLabel {'
    'background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #321e3e, stop:1 #2b1a35);'
    'border: 1px solid #4f345c;'
    'border-left: 4px solid #f258c9;'
    'border-radius: 10px;'
    'padding: 12px 14px;'
    'color: #f7a1e0;'
    'line-height: 1.35;'
    '}'
)

WEBSERVER_HELP_LABEL_STYLESHEET = (
    'QLabel {'
    'background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #321e3e, stop:1 #2b1a35);'
    'border: 1px solid #4f345c;'
    'border-left: 4px solid #f25ecb;'
    'border-radius: 10px;'
    'padding: 12px 14px;'
    'color: #f7a1e0;'
    'line-height: 1.35;'
    '}'
)

WEBHOOK_NOTE_LABEL_STYLESHEET = 'color: #888; font-size: 8pt;'

LOOKY_INFO_LABEL_STYLESHEET = (
    'QLabel {'
    'background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #321e3e, stop:1 #2b1a35);'
    'border: 1px solid #4f345c;'
    'border-left: 4px solid #7a31f6;'
    'border-radius: 10px;'
    'padding: 12px 14px;'
    'color: #f7a1e0;'
    'line-height: 1.35;'
    '}'
)

LOOKY_ACCOUNT_CARD_STYLESHEET = 'QFrame#lookyAccountCard {background: rgba(75, 23, 155, 0.12);border: 1px solid #3b2a71;border-radius: 8px;padding: 4px;}'

INTERFACE_INFO_CARD_STYLESHEET = (
    'QGroupBox {'
    'background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #321e3e, stop:1 #2b1a35);'
    'border: 1px solid #4f345c;'
    'border-left: 4px solid #ec1ab4;'
    'border-radius: 8px;'
    'margin-top: 14px;'
    'padding-top: 12px;'
    '}'
    'QGroupBox::title {'
    'subcontrol-origin: margin;'
    'subcontrol-position: top left;'
    'left: 10px; padding: 2px 8px;'
    'background: #ec1ab4;'
    'color: #ffffff;'
    'border-radius: 4px;'
    'font-weight: bold;'
    '}'
)

INTERFACE_INFO_VALUE_LABEL_STYLESHEET = 'color: #f25ecb; font-weight: bold; padding: 2px 6px;background: rgba(236, 26, 180, 0.10); border-radius: 3px;'

SETTINGS_RESTART_BANNER_STYLESHEET = (
    'QFrame#restartNoticeBanner {'
    'background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #321e3e, stop:1 #2b1a35);'
    'border: 1px solid #4f345c;'
    'border-left: 4px solid #f59e0b;'
    'border-radius: 6px;'
    '}'
)

# =============================================================================
# SPLASH SCREEN STYLES
# =============================================================================

SPLASH_SCREEN_STYLESHEET = 'background-color: #26172f;'

SPLASH_TITLE_LABEL_STYLESHEET = 'color: #eddcf2; background: transparent; font-size: 20pt; font-weight: bold;'

SPLASH_SUBTITLE_LABEL_STYLESHEET = 'color: #815a94; background: transparent; font-size: 11pt;'

SPLASH_SUBTITLE_READY_STYLESHEET = 'color: #44cc66; background: transparent; font-size: 11pt;'

SPLASH_LOG_AREA_STYLESHEET = 'QTextEdit {  background-color: #1e1224;  color: #ac79b9;  border: 1px solid #3c244a;  border-radius: 6px;  padding: 8px;}'

# =============================================================================
# DEPENDENCY PROMPT DIALOG STYLES
# =============================================================================

DEPENDENCY_PROMPT_DIALOG_STYLESHEET = 'QDialog { background-color: transparent; }'

DEPENDENCY_PROMPT_FRAME_STYLESHEET = (
    'QFrame#dependencyPromptFrame {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #352041, stop:1 #25162e);'
    '    border: 1px solid #533364;'
    '    border-radius: 14px;'
    '}'
)

DEPENDENCY_PROMPT_ICON_CONTAINER_STYLESHEET = (
    'QFrame#dependencyPromptIconContainer {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(245, 95, 205, 0.20), stop:1 rgba(214, 17, 161, 0.10));'
    '    border: 1px solid rgba(245, 95, 205, 0.35);'
    '    border-radius: 10px;'
    '}'
)

DEPENDENCY_PROMPT_KICKER_LABEL_STYLESHEET = (
    'color: #f55fcd;'
    'background: transparent;'
    'font-size: 8pt;'
    'font-weight: 700;'
    'letter-spacing: 1px;'
)

DEPENDENCY_PROMPT_TITLE_LABEL_STYLESHEET = (
    'color: #f9effa;'
    'background: transparent;'
    'font-size: 15pt;'
    'font-weight: 700;'
    'letter-spacing: 0.3px;'
)

DEPENDENCY_PROMPT_CLOSE_BUTTON_STYLESHEET = (
    'QPushButton#dependencyPromptCloseButton {'
    '    background: transparent;'
    '    color: #8a629e;'
    '    border: none;'
    '    border-radius: 6px;'
    '    font-size: 11pt;'
    '    font-weight: 700;'
    '    min-width: 26px;'
    '    max-width: 26px;'
    '    min-height: 26px;'
    '    max-height: 26px;'
    '}'
    'QPushButton#dependencyPromptCloseButton:hover {'
    '    background: rgba(231, 76, 60, 0.22);'
    '    color: #ffffff;'
    '}'
    'QPushButton#dependencyPromptCloseButton:pressed {'
    '    background: rgba(231, 76, 60, 0.38);'
    '}'
)

DEPENDENCY_PROMPT_INFO_CARD_STYLESHEET = (
    'QFrame#dependencyPromptInfoCard {'
    '    background: rgba(31, 18, 38, 0.75);'
    '    border: 1px solid #422752;'
    '    border-radius: 10px;'
    '}'
)

DEPENDENCY_PROMPT_MESSAGE_LABEL_STYLESHEET = 'color: #e1c2e8; background: transparent; font-size: 9.5pt;'

DEPENDENCY_PROMPT_ACTION_BUTTON_STYLESHEET = (
    'QPushButton {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ec18b4, stop:1 #c61096);'
    '    color: #ffffff;'
    '    border: 1px solid #f041c1;'
    '    border-radius: 8px;'
    '    padding: 7px 26px;'
    '    font-weight: 700;'
    '    font-size: 9.5pt;'
    '    letter-spacing: 0.3px;'
    '}'
    'QPushButton:hover {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef38be, stop:1 #cf119c);'
    '    border: 1px solid #fc7eda;'
    '    color: #ffffff;'
    '}'
    'QPushButton:pressed {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c61096, stop:1 #d0119d);'
    '    border: 1px solid #ec1ab4;'
    '}'
)

DEPENDENCY_PROMPT_STATUS_CARD_STYLESHEET = (
    'QFrame#dependencyPromptStatusCard {'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(25, 14, 32, 0.95), stop:1 rgba(35, 19, 45, 0.85));'
    '    border: 1px solid rgba(245, 95, 205, 0.28);'
    '    border-radius: 9px;'
    '}'
)

DEPENDENCY_PROMPT_STATUS_TITLE_STYLESHEET = 'color: #f7a1e0; background: transparent; font-size: 9pt; font-weight: 700;'

DEPENDENCY_PROMPT_STATUS_SUBTITLE_STYLESHEET = 'color: #8f66a4; background: transparent; font-size: 8pt;'

DEPENDENCY_PROMPT_STATUS_BADGE_STYLESHEET = (
    'color: #3dd68c;'
    'background: rgba(61, 214, 140, 0.12);'
    'border: 1px solid rgba(61, 214, 140, 0.35);'
    'border-radius: 4px;'
    'padding: 2px 7px;'
    'font-size: 7.5pt;'
    'letter-spacing: 0.5px;'
    'font-weight: 800;'
)

DEPENDENCY_PROMPT_FOOTER_HINT_STYLESHEET = 'color: #78518b; background: transparent; font-size: 8pt;'

DEPENDENCY_PROMPT_EXIT_BUTTON_STYLESHEET = (
    'QPushButton {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #372144, stop:1 #271730);'
    '    color: #cfa7d9;'
    '    border: 1px solid #523163;'
    '    border-radius: 7px;'
    '    padding: 6px 18px;'
    '    font-weight: 700;'
    '    font-size: 9pt;'
    '}'
    'QPushButton:hover {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4c2d5e, stop:1 #331f3f);'
    '    border: 1px solid #74488a;'
    '    color: #ffffff;'
    '}'
    'QPushButton:pressed {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #271730, stop:1 #372144);'
    '    border: 1px solid #3e254d;'
    '}'
)

# =============================================================================
# UPDATE DOWNLOAD DIALOG STYLES
# =============================================================================

UPDATE_DOWNLOAD_DIALOG_STYLESHEET = 'QDialog {  background-color: transparent;}'

UPDATE_DOWNLOAD_FRAME_STYLESHEET = (
    'QFrame#updateDownloadFrame {  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,      stop:0 #352041, stop:1 #25162e);  border: 1px solid #533364;  border-radius: 14px;}'
)

UPDATE_DOWNLOAD_TITLE_LABEL_STYLESHEET = 'color: #f9effa;background: transparent;letter-spacing: 0.5px;'

UPDATE_DOWNLOAD_DIVIDER_STYLESHEET = 'background: rgba(255, 255, 255, 0.07);min-height: 1px;max-height: 1px;border: none;'

UPDATE_DOWNLOAD_VERSION_CARD_CURRENT_STYLESHEET = (
    'QFrame#updateDownloadVersionCardCurrent {  background: rgba(33, 19, 41, 0.55);  border: 1px solid #472a57;  border-radius: 10px;}'
)

UPDATE_DOWNLOAD_VERSION_CARD_NEW_STYLESHEET = (
    'QFrame#updateDownloadVersionCardNew {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 rgba(245, 95, 205, 0.18), stop:1 rgba(214, 17, 161, 0.08));'
    '  border: 1px solid #f048c3;'
    '  border-radius: 10px;'
    '}'
)

UPDATE_DOWNLOAD_VERSION_CARD_LABEL_MUTED_STYLESHEET = 'color: #956ea8;background: transparent;font-size: 12px;letter-spacing: 0.6px;font-weight: 700;'

UPDATE_DOWNLOAD_VERSION_CARD_LABEL_ACCENT_STYLESHEET = 'color: #f55fcd;background: transparent;font-size: 12px;letter-spacing: 0.6px;font-weight: 700;'

UPDATE_DOWNLOAD_VERSION_CARD_BADGE_STABLE_STYLESHEET = (
    'color: #3dd68c;background: rgba(61, 214, 140, 0.12);border: 1px solid rgba(61, 214, 140, 0.35);'
    'border-radius: 4px;padding: 1px 5px;font-size: 9.5px;letter-spacing: 0.4px;font-weight: 700;'
)

UPDATE_DOWNLOAD_VERSION_CARD_BADGE_PRERELEASE_STYLESHEET = (
    'color: #f5a76c;background: rgba(245, 167, 108, 0.12);border: 1px solid rgba(245, 167, 108, 0.35);'
    'border-radius: 4px;padding: 1px 5px;font-size: 9.5px;letter-spacing: 0.4px;font-weight: 700;'
)

UPDATE_DOWNLOAD_VERSION_CARD_VALUE_MUTED_STYLESHEET = 'color: #d9bde0;background: transparent;font-size: 17px;font-weight: 700;'

UPDATE_DOWNLOAD_VERSION_CARD_VALUE_ACCENT_STYLESHEET = 'color: #f9effa;background: transparent;font-size: 17px;font-weight: 700;'

UPDATE_DOWNLOAD_VERSION_CARD_DATE_STYLESHEET = 'color: #8a629e;background: transparent;font-family: Consolas, "Courier New", monospace;'

UPDATE_DOWNLOAD_VERSION_CARD_SHA_STYLESHEET = 'color: #8a629e;background: transparent;font-family: Consolas, "Courier New", monospace;font-size: 11.5px;'

UPDATE_DOWNLOAD_VERSION_ARROW_STYLESHEET = 'color: #f048c3;background: transparent;font-weight: 800;'

UPDATE_DOWNLOAD_STATUS_LABEL_STYLESHEET = 'color: #c494d0;background: transparent;'

UPDATE_DOWNLOAD_SIZE_PILL_STYLESHEET = 'QFrame#updateDownloadSizePill {  background: rgba(33, 19, 41, 0.65);  border: 1px solid #472a57;  border-radius: 12px;}'

UPDATE_DOWNLOAD_SIZE_LABEL_STYLESHEET = 'color: #e2c2ea;background: transparent;font-family: Consolas, "Courier New", monospace;font-weight: 600;'

UPDATE_DOWNLOAD_PROGRESS_BAR_STYLESHEET = (
    'QProgressBar {'
    '  background-color: #1a0f20;'
    '  border: 1px solid #3c244a;'
    '  border-radius: 10px;'
    '  text-align: center;'
    '  color: #f9effa;'
    '  font-weight: 700;'
    '  font-size: 11pt;'
    '  min-height: 26px;'
    '}'
    'QProgressBar::chunk {'
    '  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '      stop:0 #d611a1, stop:0.5 #f048c3, stop:1 #ff7fdd);'
    '  border-radius: 8px;'
    '  margin: 2px;'
    '}'
)

UPDATE_DOWNLOAD_CANCEL_BUTTON_STYLESHEET = (
    'QPushButton {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #4a2030, stop:1 #2a1018);'
    '  color: #f0d8dd;'
    '  border: 1px solid #7a3040;'
    '  border-radius: 8px;'
    '  padding: 7px 22px;'
    '  font-weight: 700;'
    '  font-size: 10pt;'
    '  letter-spacing: 0.5px;'
    '  min-width: 80px;'
    '}'
    'QPushButton:hover {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #6a2838, stop:1 #3a1820);'
    '  border: 1px solid #b04050;'
    '  color: #ffffff;'
    '}'
    'QPushButton:pressed {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #2a1018, stop:1 #4a2030);'
    '  border: 1px solid #5a2030;'
    '  padding-top: 8px;'
    '  padding-bottom: 6px;'
    '}'
)

UPDATE_DOWNLOAD_SKIP_BUTTON_STYLESHEET = (
    'QPushButton {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #372144, stop:1 #271730);'
    '  color: #deb9e7;'
    '  border: 1px solid #5a356d;'
    '  border-radius: 8px;'
    '  padding: 7px 22px;'
    '  font-weight: 700;'
    '  font-size: 10pt;'
    '  letter-spacing: 0.5px;'
    '  min-width: 80px;'
    '}'
    'QPushButton:hover {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #4c2d5e, stop:1 #331f3f);'
    '  border: 1px solid #804e99;'
    '  color: #ffffff;'
    '}'
    'QPushButton:pressed {'
    '  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '      stop:0 #271730, stop:1 #372144);'
    '  border: 1px solid #472a57;'
    '  padding-top: 8px;'
    '  padding-bottom: 6px;'
    '}'
)

UPDATE_DOWNLOAD_UPDATE_BUTTON_STYLESHEET = (
    'QPushButton {'
    '  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '      stop:0 #d611a1, stop:0.5 #ec1ab4, stop:1 #f55fcd);'
    '  color: #ffffff;'
    '  border: 1px solid #f048c3;'
    '  border-radius: 8px;'
    '  padding: 7px 24px;'
    '  font-weight: 700;'
    '  font-size: 10pt;'
    '  letter-spacing: 0.5px;'
    '  min-width: 90px;'
    '}'
    'QPushButton:hover {'
    '  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '      stop:0 #ed1eb6, stop:0.5 #f048c3, stop:1 #ff7fdd);'
    '  border: 1px solid #ff7fdd;'
    '  color: #ffffff;'
    '}'
    'QPushButton:pressed {'
    '  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '      stop:0 #c61096, stop:0.5 #ed1eb6, stop:1 #f048c3);'
    '  border: 1px solid #ec1ab4;'
    '  padding-top: 8px;'
    '  padding-bottom: 6px;'
    '}'
)

# =============================================================================
# LOOKY SYSTEM ACCOUNT CARD STYLES
# =============================================================================

LOOKY_CARD_LABEL_STYLESHEET = 'color: #c3b3ff; font-size: 10.5pt;'

LOOKY_CARD_VALUE_STYLESHEET = 'color: #d3c6f2; font-size: 10.5pt;'

# =============================================================================
# LOOKY SYSTEM CRAWLER DIALOG STYLES
# =============================================================================

LOOKY_CRAWLER_HEADER_STYLESHEET = (
    'font-size: 11pt;'
    'font-weight: 700;'
    'padding: 10px 14px;'
    'color: #d8b3ff;'
    'background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '    stop:0 #1c083a, stop:0.5 #2d0c69, stop:1 #1c083a);'
    'border: 1px solid #4b179b;'
    'border-radius: 8px;'
)

LOOKY_CRAWLER_LOG_STYLESHEET = (
    'QPlainTextEdit {'
    '    background-color: #0d091d;'
    '    color: #c3b3ff;'
    '    border: 1px solid #2b1772;'
    '    border-radius: 6px;'
    '    font-family: Consolas, "Courier New", monospace;'
    '    font-size: 10pt;'
    '    padding: 6px;'
    '    selection-background-color: #4b179b;'
    '}'
)

LOOKY_PROGRESS_BAR_STYLESHEET = (
    'QProgressBar {'
    '    background-color: #1a1226;'
    '    border: 1px solid #3b1d63;'
    '    border-radius: 7px;'
    '}'
    'QProgressBar::chunk {'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '        stop:0 #6b1fe2, stop:0.5 #a84dff, stop:1 #ec4899);'
    '    border-radius: 7px;'
    '}'
)

LOOKY_STATUS_LABEL_STYLESHEET = 'font-size: 10pt; padding: 4px;'

LOOKY_ACTION_BUTTON_STYLESHEET = (
    'QPushButton {'
    '    background-color: #1e0e32;'
    '    color: #c081ff;'
    '    border: 1px solid #591abd;'
    '    border-radius: 6px;'
    '    padding: 5px 16px;'
    '    font-weight: 600;'
    '}'
    'QPushButton:hover {'
    '    background-color: #2c155b;'
    '    border-color: #7a31f6;'
    '}'
    'QPushButton:pressed {'
    '    background-color: #4b179b;'
    '}'
)

LOOKY_PRIMARY_ACTION_BUTTON_STYLESHEET = (
    'QPushButton {'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '        stop:0 #6b1fe2, stop:0.5 #a84dff, stop:1 #ec4899);'
    '    color: #ffffff;'
    '    border: 1px solid #7a31f6;'
    '    border-radius: 7px;'
    '    padding: 10px 22px;'
    '    font-size: 10pt;'
    '    font-weight: 700;'
    '}'
    'QPushButton:hover {'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '        stop:0 #7a31f6, stop:0.5 #c081ff, stop:1 #f472b6);'
    '}'
    'QPushButton:pressed {'
    '    background: #4b179b;'
    '}'
)

LOOKY_LIST_WIDGET_STYLESHEET = (
    'QListWidget {'
    '    background-color: #0d091d;'
    '    color: #c3b3ff;'
    '    border: 1px solid #2b1772;'
    '    border-radius: 6px;'
    '    padding: 4px;'
    '    font-family: Consolas, "Courier New", monospace;'
    '    font-size: 9pt;'
    '    outline: 0;'
    '}'
    'QListWidget::item {'
    '    padding: 6px 8px;'
    '    border-radius: 4px;'
    '}'
    'QListWidget::item:hover {'
    '    background-color: #1e0e32;'
    '}'
    'QListWidget::item:selected {'
    '    background-color: #4b179b;'
    '    color: #ffffff;'
    '}'
)

LOOKY_BODY_LABEL_STYLESHEET = 'color: #d3c6f2; font-size: 12pt; padding: 2px;'

# =============================================================================
# LOOKY SYSTEM REFRESH REVIEW DIALOG STYLES
# =============================================================================

LOOKY_REVIEW_DIALOG_STYLESHEET = 'QDialog {    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,        stop:0 #1a0c30, stop:1 #0f091d);}'

LOOKY_REVIEW_TABLE_STYLESHEET = (
    'QTreeWidget {'
    '    background-color: #0d091d;'
    '    color: #d3c6f2;'
    '    border: 1px solid #2b1772;'
    '    border-radius: 8px;'
    '    font-family: Consolas, "Courier New", monospace;'
    '    font-size: 9pt;'
    '    padding: 4px;'
    '    outline: 0;'
    '    alternate-background-color: #130e25;'
    '}'
    'QTreeWidget::item {'
    '    padding: 5px 6px;'
    '    border-bottom: 1px solid rgba(43, 23, 114, 0.3);'
    '}'
    'QTreeWidget::item:hover {'
    '    background-color: #1e0e32;'
    '}'
    'QTreeWidget::item:selected {'
    '    background-color: #4b179b;'
    '    color: #ffffff;'
    '}'
    'QTreeWidget::indicator {'
    '    width: 16px;'
    '    height: 16px;'
    '}'
    'QTreeWidget::indicator:unchecked {'
    '    border: 1px solid #591abd;'
    '    border-radius: 4px;'
    '    background-color: #1a1226;'
    '}'
    'QTreeWidget::indicator:unchecked:hover {'
    '    border: 1px solid #a84dff;'
    '    background-color: #23183e;'
    '}'
    'QTreeWidget::indicator:checked {'
    '    border: 1px solid #a84dff;'
    '    border-radius: 4px;'
    '    background-color: #7a31f6;'
    '    image: none;'
    '}'
    'QTreeWidget::indicator:checked:hover {'
    '    border: 1px solid #c081ff;'
    '    background-color: #893cf9;'
    '}'
    'QHeaderView::section {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '        stop:0 #2d0c69, stop:1 #1c083a);'
    '    color: #d8b3ff;'
    '    border: 1px solid #4b179b;'
    '    padding: 6px 10px;'
    '    font-weight: 700;'
    '    font-size: 8pt;'
    '}'
)

LOOKY_REVIEW_SUMMARY_STYLESHEET = (
    'QFrame {'
    '    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,'
    '        stop:0 rgba(75, 23, 155, 0.15), stop:1 rgba(30, 14, 50, 0.25));'
    '    border: 1px solid #3b2a71;'
    '    border-radius: 10px;'
    '    padding: 10px 14px;'
    '}'
)

LOOKY_REVIEW_SELECT_BUTTON_STYLESHEET = (
    'QPushButton {'
    '    background-color: #1e0e32;'
    '    color: #c081ff;'
    '    border: 1px solid #591abd;'
    '    border-radius: 6px;'
    '    padding: 4px 14px;'
    '    font-weight: 600;'
    '    font-size: 8pt;'
    '}'
    'QPushButton:hover {'
    '    background-color: #2c155b;'
    '    border-color: #7a31f6;'
    '}'
    'QPushButton:pressed {'
    '    background-color: #4b179b;'
    '}'
)
