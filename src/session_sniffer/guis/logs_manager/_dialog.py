"""Logs Manager dialog — main entry point combining all log tabs."""

from typing import TYPE_CHECKING, override

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from session_sniffer.constants.local import (
    DEBUG_LOG_PATH,
    DETECTION_LOGGING_PATH,
    PROTECTION_LOGGING_PATH,
    RESOURCES_DIR_PATH,
    SESSIONS_LOGGING_DIR_PATH,
    USERIP_LOGGING_PATH,
)
from session_sniffer.constants.standalone import TITLE
from session_sniffer.guis.logs_manager._csv_tab import CsvLogTab, CsvLogTabConfig
from session_sniffer.guis.logs_manager._helpers import backup_file
from session_sniffer.guis.logs_manager._sessions_tab import SessionsLogTab
from session_sniffer.guis.logs_manager._text_tab import TextLogTab
from session_sniffer.guis.stylesheets import DIALOG_BUTTON_STYLESHEET, DIALOG_DANGER_BUTTON_STYLESHEET
from session_sniffer.guis.utils import resize_window_for_screen, scale_by_ui, set_dialog_window_flags
from session_sniffer.rendering_core.renderer import SESSIONS_LOGGING_PATH
from session_sniffer.settings import Settings
from session_sniffer.utils import cleanup_session_logs

if TYPE_CHECKING:
    from PySide6.QtGui import QShowEvent


class LogsManager(QDialog):
    """Non-modal dialog for viewing, searching, filtering, and managing application log files."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Build the Logs Manager dialog with tabs for each log file type."""
        super().__init__(parent)
        self.setWindowTitle(f'Gestionnaire de logs - {TITLE}')
        set_dialog_window_flags(self)
        self.setMinimumSize(scale_by_ui(880), scale_by_ui(520))
        resize_window_for_screen(self)

        root_layout = QVBoxLayout(self)

        # --- Tab widget ---
        tabs = QTabWidget()

        self._userip_tab = CsvLogTab(
            CsvLogTabConfig(
                file_path=USERIP_LOGGING_PATH,
                expected_headers=('Database', 'Usernames', 'IP', 'Date', 'Time', 'Country'),
                default_sort_columns=('Date', 'Time'),
                stretch_column=1,
                column_min_widths={5: 160},
            ),
        )
        tabs.addTab(self._userip_tab, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'database.svg')), 'Log UserIP')

        self._detection_tab = CsvLogTab(
            CsvLogTabConfig(
                file_path=DETECTION_LOGGING_PATH,
                expected_headers=('Detection', 'Usernames', 'IP', 'Date', 'Time', 'Country'),
                default_sort_columns=('Date', 'Time'),
                stretch_column=1,
                column_min_widths={0: 220, 5: 160},
            ),
        )
        tabs.addTab(self._detection_tab, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'bell.svg')), 'Journal des détections')
        self._protection_tab = CsvLogTab(
            CsvLogTabConfig(
                file_path=PROTECTION_LOGGING_PATH,
                expected_headers=('Detection', 'Usernames', 'IP', 'Date', 'Time', 'Country'),
                default_sort_columns=('Date', 'Time'),
                stretch_column=1,
                column_min_widths={0: 220, 5: 160},
            ),
        )
        tabs.addTab(self._protection_tab, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'shield.svg')), 'Log de protection')
        self._debug_tab = TextLogTab(file_path=DEBUG_LOG_PATH)
        tabs.addTab(self._debug_tab, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'bug.svg')), 'Log de debug')
        self._sessions_tab = SessionsLogTab(sessions_dir=SESSIONS_LOGGING_DIR_PATH)
        tabs.addTab(self._sessions_tab, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Logs de sessions')

        self._tabs = tabs
        root_layout.addWidget(tabs, stretch=1)

        # --- Bottom button row ---
        button_row = QHBoxLayout()
        button_row.addStretch()

        purge_all_button = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'remove.svg')), ' Vider tous les logs')
        purge_all_button.setStyleSheet(DIALOG_DANGER_BUTTON_STYLESHEET)
        purge_all_button.setToolTip("Effacer TOUS les fichiers de log d'un coup (des sauvegardes sont créées avant)")
        purge_all_button.clicked.connect(self.purge_all_logs)
        button_row.addWidget(purge_all_button)

        clean_empty_button = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'clear_all.svg')), ' Nettoyer les sessions vides')
        clean_empty_button.setStyleSheet(DIALOG_BUTTON_STYLESHEET)
        clean_empty_button.setToolTip('Supprimer les logs de session vides et les dossiers vides (garde la session active)')
        clean_empty_button.clicked.connect(self.clean_empty_sessions)
        button_row.addWidget(clean_empty_button)

        close_button = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'close.svg')), ' Fermer')
        close_button.setStyleSheet(DIALOG_BUTTON_STYLESHEET)
        close_button.setToolTip('Fermer le gestionnaire de logs')
        close_button.clicked.connect(self.close)
        button_row.addWidget(close_button)

        root_layout.addLayout(button_row)

    # ------------------------------------------------------------------
    # Programmatic search entry points
    # ------------------------------------------------------------------

    def search_in_userip_logging(self, text: str) -> None:
        """Switch to the UserIP Logging tab and apply `text` as the search filter."""
        self._tabs.setCurrentWidget(self._userip_tab)
        self._userip_tab.set_search(text)

    def search_in_sessions_logging(self, text: str) -> None:
        """Switch to the Sessions Logging tab and start a global search for `text`."""
        self._tabs.setCurrentWidget(self._sessions_tab)
        self._sessions_tab.set_search_global(text)

    # ------------------------------------------------------------------
    # Clean empty sessions
    # ------------------------------------------------------------------

    def clean_empty_sessions(self) -> None:
        """Manually clean up empty session log files and empty directories."""
        files_deleted, folders_deleted = cleanup_session_logs(
            sessions_dir=SESSIONS_LOGGING_DIR_PATH,
            delete_empty_files=True,
            delete_empty_folders=True,
            gui_sessions_logging=Settings.gui_sessions_logging,
            active_session_path=SESSIONS_LOGGING_PATH.with_suffix('.json'),
        )
        QMessageBox.information(
            self,
            TITLE,
            f'Logs de session vides nettoyés :\n\n  • Fichiers supprimés : {files_deleted}\n  • Dossiers supprimés : {folders_deleted}',
        )

    # ------------------------------------------------------------------
    # Purge all
    # ------------------------------------------------------------------

    def purge_all_logs(self) -> None:
        """Purge all CSV log files and debug.log after strong confirmation."""
        reply = QMessageBox.warning(
            self,
            TITLE,
            'Ceci va vider TOUS les fichiers de log :\n\n  • UserIP_Logging.csv\n  • Detection_Logging.csv\n  • Protection_Logging.csv\n  • debug.log\n\nDes sauvegardes (.bak) seront créées avant.\nTu es sûr ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        purged: list[str] = []
        errors: list[str] = []

        for path in (USERIP_LOGGING_PATH, DETECTION_LOGGING_PATH, PROTECTION_LOGGING_PATH, DEBUG_LOG_PATH):
            if not path.exists():
                continue
            backup_file(path)
            path.write_text('', encoding='utf-8')
            purged.append(path.name)

        self._userip_tab.load_data()
        self._detection_tab.load_data()
        self._protection_tab.load_data()
        self._debug_tab.load_data()

        parts: list[str] = []
        if purged:
            parts.append(f'Vidés : {", ".join(purged)}')
        if errors:
            parts.append(f'Erreurs : {"; ".join(errors)}')
        if not parts:
            parts.append('Aucun fichier de log à vider.')

        QMessageBox.information(self, TITLE, '\n'.join(parts))

    @override
    def showEvent(self, a0: QShowEvent) -> None:
        """Handle the window show event and maximize if required."""
        super().showEvent(a0)
        if self.property('_should_maximize_on_show') is True:
            self.setProperty('_should_maximize_on_show', False)  # noqa: FBT003
            self.showMaximized()
