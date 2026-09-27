"""Main window implementation for Session Sniffer."""

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QFont, QIcon, QShowEvent
from PySide6.QtWidgets import (
    QTabWidget,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from session_sniffer.background import wake_all_player_cores
from session_sniffer.background.events import gui_closed__event
from session_sniffer.constants.local import RESOURCES_DIR_PATH
from session_sniffer.constants.standalone import TITLE
from session_sniffer.core import terminate_script
from session_sniffer.gta5.suspend_manager import GTASuspendManager
from session_sniffer.guis._main_window_files_mixin import FilesMixin
from session_sniffer.guis._main_window_game_mixin import GameMixin
from session_sniffer.guis._main_window_looky_mixin import LookyMixin
from session_sniffer.guis._main_window_stats_mixin import StatsMixin
from session_sniffer.guis._session_table_section import SessionStatusBar, SessionTableSection
from session_sniffer.guis.discord_intro import DiscordIntro
from session_sniffer.guis.html_templates import generate_gui_header_html
from session_sniffer.guis.logs_manager import LogsManager
from session_sniffer.guis.ping_window import PingWindow
from session_sniffer.guis.player_resolver import PlayerResolverWindow
from session_sniffer.guis.port_scanner_window import PortScannerWindow
from session_sniffer.guis.settings_dialog import SettingsDialog
from session_sniffer.guis.stylesheets import MENU_BAR_STYLESHEET
from session_sniffer.guis.tables_player_actions.looky_system._looky_crawler_request_dialog import close_all_crawler_dialogs
from session_sniffer.guis.tables_player_actions.looky_system._looky_lookup_dialog import close_all_lookup_dialogs
from session_sniffer.guis.userip_manager import UserIPDatabasesManager
from session_sniffer.guis.utils import (
    apply_always_on_top,
    resize_window_for_screen,
    scale_by_ui,
    show_detailed_message,
    show_or_focus_window,
)
from session_sniffer.guis.worker_thread import GUIWorkerThread
from session_sniffer.models import GUIState
from session_sniffer.player.registry import PlayersRegistry, SessionHost
from session_sniffer.rdr2.suspend_manager import RDR2SuspendManager
from session_sniffer.rendering_core.status_bar_renderer import build_gui_status_text
from session_sniffer.rendering_core.types import CaptureState, GUIRenderingState, GUIUpdatePayload
from session_sniffer.settings import Settings
from session_sniffer.guis.player_leaderboard import PlayerLeaderboardWindow
from session_sniffer.guis.btx_overlay import OverlayController
from session_sniffer.guis.btx_extras_menu import add_backup_menu, add_theme_menu
from session_sniffer.guis.btx_player_card import open_player_card
from session_sniffer.guis.btx_search import GlobalSearchDialog, install_global_search
from session_sniffer.guis.btx_whats_new import WhatsNew

if TYPE_CHECKING:
    from collections.abc import Callable

    from session_sniffer.capture.packet_capture import CaptureHolder
    from session_sniffer.guis.detections_manager import DetectionsManagerDialog
    from session_sniffer.guis.table_model import SessionTableModel


@dataclass(frozen=True, slots=True)
class _MenuActions:
    """Menu bar QAction references."""

    toggle_capture: QAction
    change_interface: QAction


@dataclass(slots=True)
class _WindowState:
    """Mutable runtime state for the main window."""

    worker_thread: GUIWorkerThread
    window_being_moved: bool
    min_accepted_snapshot_version: int


class MainWindow(LookyMixin, GameMixin, StatsMixin, FilesMixin, QMainWindow):
    """Main Qt window that hosts session tables and control UI."""

    _actions: _MenuActions
    _connected: SessionTableSection
    _disconnected: SessionTableSection
    _tables_splitter: QSplitter
    _saved_splitter_sizes: list[int]
    _discord_intro_window: DiscordIntro | None

    def _on_splitter_moved(self, _position: int, _index: int) -> None:
        if self._connected.is_expanded and self._disconnected.is_expanded:
            self._saved_splitter_sizes = self._tables_splitter.sizes()

    def _update_splitter_visibility(self) -> None:
        self._connected.update_disconnected_players_state()
        if not Settings.gui_disconnected_players_enabled:
            self._disconnected.setVisible(False)
            self._disconnected.expand_button.setVisible(False)
            self._connected.collapse_button.setVisible(False)
            self._connected.expand_button.setVisible(False)
            self._connected.setVisible(True)
            self._tables_splitter.setVisible(True)
            return

        self._connected.collapse_button.setVisible(True)
        connected_expanded = self._connected.is_expanded
        disconnected_expanded = self._disconnected.is_expanded
        self._connected.setVisible(connected_expanded)
        self._connected.expand_button.setVisible(not connected_expanded)
        self._disconnected.setVisible(disconnected_expanded)
        self._disconnected.expand_button.setVisible(not disconnected_expanded)
        self._tables_splitter.setVisible(connected_expanded or disconnected_expanded)

        if connected_expanded and disconnected_expanded:
            if self._saved_splitter_sizes:
                total_height = sum(self._tables_splitter.sizes())
                saved_total = sum(self._saved_splitter_sizes)
                if saved_total > 0 and total_height > 0:
                    ratio = self._saved_splitter_sizes[0] / saved_total
                    connected_size = int(total_height * ratio)
                    disconnected_size = total_height - connected_size
                    self._tables_splitter.setSizes([connected_size, disconnected_size])
            else:
                total_height = sum(self._tables_splitter.sizes())
                if total_height > 0:
                    half_height = total_height // 2
                    self._tables_splitter.setSizes([half_height, total_height - half_height])

    def __init__(
        self,
        screen_size: tuple[int, int],
        capture_holder: CaptureHolder,
        on_change_interface: Callable[[], None],
        on_open_hotspot: Callable[[], None],
    ) -> None:
        """Initialize the main application window.

        Args:
            screen_size: Primary screen dimensions as (width, height) in pixels.
            capture_holder: Mutable reference to the active packet capture instance.
            on_change_interface: Callback invoked when the user requests an interface switch.
            on_open_hotspot: Callback invoked when the user requests the hotspot manager.
        """
        super().__init__()

        self.capture = capture_holder
        self._on_change_interface = on_change_interface
        self._on_open_hotspot = on_open_hotspot
        self._player_resolver_window = PlayerResolverWindow(self._select_connected_ips, self._deselect_connected_ips)
        self._detections_manager_window: DetectionsManagerDialog | None = None
        self._logs_manager_window: LogsManager | None = None
        self._settings_dialog_window: SettingsDialog | None = None
        self._userip_manager_window: UserIPDatabasesManager | None = None
        self._discord_intro_window: DiscordIntro | None = None
        self._leaderboard_window = None
        self._session_rate_graph_window = None
        self._session_pps_graph_window = None
        self._session_bps_graph_window = None
        self._packets_latency_graph_window = None
        self._country_breakdown_window = None
        self._reconnect_frequency_window = None
        self._session_timeline_window = None
        self._port_heatmap_window = None
        self._session_duration_window = None
        self._capture_statistics_window = None

        self.setWindowTitle(TITLE)
        self.setMinimumSize(scale_by_ui(1024), scale_by_ui(600))
        resize_window_for_screen(self, screen_size)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        menu_bar = self.menuBar()
        if not menu_bar:
            message = 'Failed to get menu bar'
            raise RuntimeError(message)
        menu_bar.setStyleSheet(MENU_BAR_STYLESHEET)

        capture_menu = menu_bar.addMenu('Capture')
        if not capture_menu:
            message = 'Failed to create Capture menu'
            raise RuntimeError(message)
        capture_menu.setToolTipsVisible(True)

        toggle_capture_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'stop.svg')), 'Arrêter la capture', self)
        toggle_capture_action.setToolTip('Arrêter la capture de paquets')
        toggle_capture_action.triggered.connect(self._toggle_capture)
        capture_menu.addAction(toggle_capture_action)

        capture_menu.addSeparator()

        change_interface_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'refresh.svg')), "Changer d'interface", self)
        change_interface_action.setToolTip('Arrêter la capture, choisir une autre interface réseau et relancer la capture')
        change_interface_action.triggered.connect(on_change_interface)
        capture_menu.addAction(change_interface_action)

        hotspot_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'wifi.svg')), 'Hotspot && partage', self)
        hotspot_action.setToolTip('Créer un hotspot Wi-Fi ou configurer le partage de connexion Internet (ICS) pour capturer le trafic des consoles')
        hotspot_action.triggered.connect(self._open_hotspot_manager)
        capture_menu.addAction(hotspot_action)

        self._build_game_menu(menu_bar)
        self._update_game_toolbar_visibility()

        tools_menu = menu_bar.addMenu('Outils')
        if not tools_menu:
            message = 'Failed to create Tools menu'
            raise RuntimeError(message)
        tools_menu.setToolTipsVisible(True)

        search_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'search.svg')), 'Rechercher un joueur…', self)
        search_action.setShortcut('Ctrl+F')
        search_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)  # the real Ctrl+F is installed on the window
        search_action.setToolTip('Chercher un joueur par pseudo, IP, pays, note ou étiquette (session + historique)')
        search_action.triggered.connect(lambda: GlobalSearchDialog.open(self, self._open_card_from_search))
        tools_menu.addAction(search_action)
        tools_menu.addSeparator()

        detections_manager_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'shield.svg')), 'Gestionnaire de détections', self)
        detections_manager_action.setToolTip('Configurer les détections, les notifications et les règles de protection')
        detections_manager_action.triggered.connect(self._open_detections_manager)
        tools_menu.addAction(detections_manager_action)

        userip_manager_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'database.svg')), 'Gestionnaire UserIP', self)
        userip_manager_action.setToolTip('Parcourir, modifier, ajouter et supprimer des entrées dans les bases UserIP')
        userip_manager_action.triggered.connect(self._open_userip_manager)
        tools_menu.addAction(userip_manager_action)

        logs_manager_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'Gestionnaire de logs', self)
        logs_manager_action.setToolTip('View, search, filter, and manage application log files')
        logs_manager_action.triggered.connect(self._open_logs_manager)
        tools_menu.addAction(logs_manager_action)

        tools_menu.addSeparator()

        leaderboard_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'trophy.svg')), 'Joueurs les plus vus', self)
        leaderboard_action.setToolTip('Voir le classement des joueurs les plus souvent croisés dans tes sessions')
        leaderboard_action.triggered.connect(self._open_player_leaderboard)
        tools_menu.addAction(leaderboard_action)

        tools_menu.addSeparator()
        overlay_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'eye.svg')), 'Mini-fenêtre en jeu', self)
        overlay_action.setToolTip('Afficher/masquer la petite fenêtre toujours au premier plan (aussi avec ton raccourci clavier)')
        overlay_action.triggered.connect(lambda: self._overlay_controller.toggle())
        tools_menu.addAction(overlay_action)
        overlay_settings_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'settings.svg')), 'Raccourci de la mini-fenêtre…', self)
        overlay_settings_action.setToolTip('Choisir la touche qui ouvre/ferme la mini-fenêtre, et son opacité')
        overlay_settings_action.triggered.connect(lambda: self._overlay_controller.open_settings())
        tools_menu.addAction(overlay_settings_action)
        tools_menu.addSeparator()

        port_scanner_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'port_scanner.svg')), 'Scanner de ports', self)
        port_scanner_action.setToolTip('Scanner les ports TCP et UDP en multi-thread avec détection des services')
        port_scanner_action.triggered.connect(self._open_port_scanner)
        tools_menu.addAction(port_scanner_action)

        ping_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'ping.svg')), 'Diagnostic ping', self)
        ping_action.setToolTip('Envoyer des pings ICMP, connexions TCP, tests UDP ou mesures de latence Web')
        ping_action.triggered.connect(self._open_ping_diagnostics)
        tools_menu.addAction(ping_action)

        statistics_menu = menu_bar.addMenu('Statistiques')
        if not statistics_menu:
            message = 'Failed to create Statistics menu'
            raise RuntimeError(message)
        statistics_menu.setToolTipsVisible(True)

        capture_health_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'chart.svg')), 'Statistiques de capture', self)
        capture_health_action.setToolTip('Nombre de redémarrages de capture et statistiques de latence des paquets')
        capture_health_action.triggered.connect(self._open_capture_health)
        statistics_menu.addAction(capture_health_action)

        session_rate_graph_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'speedometer.svg')), 'Graphique de la session', self)
        session_rate_graph_action.setToolTip('Graphiques PPS et BPS en direct pour toute la session')
        session_rate_graph_action.triggered.connect(self._open_session_rate_graph)
        statistics_menu.addAction(session_rate_graph_action)

        statistics_menu.addSeparator()

        session_timeline_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'calendar.svg')), 'Chronologie de la session', self)
        session_timeline_action.setToolTip('Diagramme montrant quand chaque joueur était présent')
        session_timeline_action.triggered.connect(self._open_session_timeline)
        statistics_menu.addAction(session_timeline_action)

        statistics_menu.addSeparator()

        country_breakdown_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'globe.svg')), 'Répartition par pays', self)
        country_breakdown_action.setToolTip("Classer les joueurs par pays d'origine")
        country_breakdown_action.triggered.connect(self._open_country_breakdown)
        statistics_menu.addAction(country_breakdown_action)

        reconnect_frequency_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'frequency.svg')), 'Fréquence de reconnexion', self)
        reconnect_frequency_action.setToolTip('Joueurs triés par nombre de reconnexions')
        reconnect_frequency_action.triggered.connect(self._open_reconnect_frequency)
        statistics_menu.addAction(reconnect_frequency_action)

        avg_session_duration_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'timer.svg')), 'Durée de session', self)
        avg_session_duration_action.setToolTip('Joueurs déconnectés classés par durée de session')
        avg_session_duration_action.triggered.connect(self._open_session_duration)
        statistics_menu.addAction(avg_session_duration_action)

        port_heatmap_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'heatmap.svg')), 'Carte des ports', self)
        port_heatmap_action.setToolTip('Classer les ports observés par fréquence sur tous les joueurs')
        port_heatmap_action.triggered.connect(self._open_port_heatmap)
        statistics_menu.addAction(port_heatmap_action)

        data_menu = menu_bar.addMenu('Données && fichiers')
        if not data_menu:
            message = 'Failed to create Data & Files menu'
            raise RuntimeError(message)
        data_menu.setToolTipsVisible(True)

        add_backup_menu(data_menu, self)  # BTX: backups / export / import of notes and tags
        data_menu.addSeparator()

        open_local_appdata_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier AppData Local', self)
        open_local_appdata_action.setToolTip("Ouvrir AppData\\Local\\Session Sniffer dans l'explorateur Windows")
        open_local_appdata_action.triggered.connect(self._open_local_appdata_folder)
        data_menu.addAction(open_local_appdata_action)

        open_roaming_appdata_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier AppData Roaming', self)
        open_roaming_appdata_action.setToolTip("Ouvrir AppData\\Roaming\\Session Sniffer dans l'explorateur Windows")
        open_roaming_appdata_action.triggered.connect(self._open_roaming_appdata_folder)
        data_menu.addAction(open_roaming_appdata_action)

        data_menu.addSeparator()

        open_userip_databases_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des bases UserIP', self)
        open_userip_databases_action.setToolTip('Ouvrir AppData\\Roaming\\Session Sniffer\\UserIP Databases')
        open_userip_databases_action.triggered.connect(self._open_userip_databases_folder)
        data_menu.addAction(open_userip_databases_action)

        open_user_scripts_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des scripts', self)
        open_user_scripts_action.setToolTip('Ouvrir AppData\\Roaming\\Session Sniffer\\scripts')
        open_user_scripts_action.triggered.connect(self._open_user_scripts_folder)
        data_menu.addAction(open_user_scripts_action)

        data_menu.addSeparator()

        debug_logs_submenu = data_menu.addMenu(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'bug.svg')), 'Logs de debug')
        if not debug_logs_submenu:
            message = 'Failed to create Debug Logs submenu'
            raise RuntimeError(message)
        debug_logs_submenu.setToolTipsVisible(True)
        debug_logs_submenu.menuAction().setToolTip('Open or browse the application debug log files')

        open_debug_logs_folder_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des logs de debug', self)
        open_debug_logs_folder_action.setToolTip('Open Local AppData\\Session Sniffer\\Debug')
        open_debug_logs_folder_action.triggered.connect(self._open_debug_logs_folder)
        debug_logs_submenu.addAction(open_debug_logs_folder_action)

        debug_logs_submenu.addSeparator()

        open_debug_log_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'debug.log', self)
        open_debug_log_action.setToolTip('Open Local AppData\\Session Sniffer\\Debug\\debug.log')
        open_debug_log_action.triggered.connect(self._open_debug_log_file)
        debug_logs_submenu.addAction(open_debug_log_action)

        open_crash_log_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'crash.log', self)
        open_crash_log_action.setToolTip('Open Local AppData\\Session Sniffer\\Debug\\crash.log')
        open_crash_log_action.triggered.connect(self._open_crash_log_file)
        debug_logs_submenu.addAction(open_crash_log_action)

        app_logs_submenu = data_menu.addMenu(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), "Logs de l'application")
        if not app_logs_submenu:
            message = 'Failed to create Application Logs submenu'
            raise RuntimeError(message)
        app_logs_submenu.setToolTipsVisible(True)
        app_logs_submenu.menuAction().setToolTip('Open or browse CSV application log files (detections, protection, UserIP)')

        open_logging_folder_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des logs', self)
        open_logging_folder_action.setToolTip('Open Local AppData\\Session Sniffer\\Logging')
        open_logging_folder_action.triggered.connect(self._open_logging_folder)
        app_logs_submenu.addAction(open_logging_folder_action)

        open_sessions_logs_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des sessions', self)
        open_sessions_logs_action.setToolTip('Open Local AppData\\Session Sniffer\\Logging\\Sessions')
        open_sessions_logs_action.triggered.connect(self._open_sessions_logging_folder)
        app_logs_submenu.addAction(open_sessions_logs_action)

        app_logs_submenu.addSeparator()

        open_detection_log_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'Detection_Logging.csv', self)
        open_detection_log_action.setToolTip('Open Local AppData\\Session Sniffer\\Logging\\Detection_Logging.csv')
        open_detection_log_action.triggered.connect(self._open_detection_log_file)
        app_logs_submenu.addAction(open_detection_log_action)

        open_protection_log_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'Protection_Logging.csv', self)
        open_protection_log_action.setToolTip('Open Local AppData\\Session Sniffer\\Logging\\Protection_Logging.csv')
        open_protection_log_action.triggered.connect(self._open_protection_log_file)
        app_logs_submenu.addAction(open_protection_log_action)

        open_userip_log_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'text_editor.svg')), 'UserIP_Logging.csv', self)
        open_userip_log_action.setToolTip('Open Local AppData\\Session Sniffer\\Logging\\UserIP_Logging.csv')
        open_userip_log_action.triggered.connect(self._open_userip_log_file)
        app_logs_submenu.addAction(open_userip_log_action)

        data_menu.addSeparator()

        open_settings_ini_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'file_settings.svg')), 'Ouvrir Settings.ini', self)
        open_settings_ini_action.setToolTip('Ouvrir AppData\\Roaming\\Session Sniffer\\Settings.ini')
        open_settings_ini_action.triggered.connect(self._open_settings_file)
        data_menu.addAction(open_settings_ini_action)

        settings_menu = menu_bar.addMenu('Paramètres')
        if not settings_menu:
            message = 'Failed to create Settings menu'
            raise RuntimeError(message)
        settings_menu.setToolTipsVisible(True)

        open_settings_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'settings.svg')), 'Ouvrir les paramètres', self)
        open_settings_action.setToolTip("Voir et modifier tous les paramètres de l'application")
        open_settings_action.triggered.connect(self._open_settings_dialog)
        settings_menu.addAction(open_settings_action)
        add_theme_menu(settings_menu, self)  # BTX: colour themes

        help_menu = menu_bar.addMenu('Aide')
        if not help_menu:
            message = 'Failed to create Help menu'
            raise RuntimeError(message)
        help_menu.setToolTipsVisible(True)

        discord_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'discord.svg')), 'Serveur Discord', self)
        discord_action.setToolTip('Rejoindre le serveur Discord BTX')
        discord_action.triggered.connect(self._join_discord)
        help_menu.addAction(discord_action)

        help_menu.addSeparator()
        self._whats_new = WhatsNew(self)
        whats_new_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'lightbulb.svg')), 'Quoi de neuf', self)
        whats_new_action.setToolTip('Voir les nouveautés des dernières versions de BTXSniffer')
        whats_new_action.triggered.connect(self._whats_new.show_now)
        help_menu.addAction(whats_new_action)

        check_updates_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'cloud_download.svg')), 'Vérifier les mises à jour', self)
        check_updates_action.setToolTip('Chercher une nouvelle version de BTXSniffer sur GitHub')
        check_updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(check_updates_action)

        repo_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'github.svg')), 'Page GitHub de BTXSniffer', self)
        repo_action.setToolTip('Ouvrir le dépôt GitHub de BTXSniffer (code source et versions)')
        repo_action.triggered.connect(self._open_project_repo)
        help_menu.addAction(repo_action)

        self._header = QLabel()
        self._header.setTextFormat(Qt.TextFormat.RichText)
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header.setWordWrap(True)
        self._header.setFont(QFont('Courier', 10, QFont.Weight.Bold))
        self._header.setToolTip(
            'BTXSniffer — basé sur Session Sniffer par BUZZARDGTA.\nLogiciel libre sous licence GNU GPLv3, fourni SANS AUCUNE GARANTIE.\nTu peux le redistribuer sous la même licence (voir le fichier COPYING).'
        )

        connected_column_names = [
            column for column in Settings.GUI_ALL_CONNECTED_COLUMNS if column in set(Settings.gui_columns_connected_shown) or column in Settings.GUI_FORCED_COLUMNS
        ]
        self._connected = SessionTableSection(
            is_connected=True,
            column_names=connected_column_names,
            clear_slot=self._clear_connected_players,
            parent=self,
        )
        self._connected.table_view.open_rate_graph_callback = self._player_resolver_window.high_rate_monitor.open_graph

        self._saved_splitter_sizes = []

        disconnected_column_names = [
            column for column in Settings.GUI_ALL_DISCONNECTED_COLUMNS if column in set(Settings.gui_columns_disconnected_shown) or column in Settings.GUI_FORCED_COLUMNS
        ]
        self._disconnected = SessionTableSection(
            is_connected=False,
            column_names=disconnected_column_names,
            clear_slot=self._clear_disconnected_players,
            parent=self,
        )

        self._tables_splitter = QSplitter(Qt.Orientation.Vertical, self)
        self._tables_splitter.setChildrenCollapsible(False)
        self._tables_splitter.setHandleWidth(scale_by_ui(6))
        self._tables_splitter.addWidget(self._connected)
        self._tables_splitter.addWidget(self._disconnected)
        self._tables_splitter.setStretchFactor(0, 1)
        self._tables_splitter.setStretchFactor(1, 1)
        self._tables_splitter.splitterMoved.connect(self._on_splitter_moved)

        self._status_bar = SessionStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._actions = _MenuActions(
            toggle_capture=toggle_capture_action,
            change_interface=change_interface_action,
        )

        main_layout.addSpacing(4)
        main_layout.addWidget(self._header)
        main_layout.addSpacing(14)

        # BTX: tabs — live session tables + a dedicated history of every player met in past sessions
        session_page = QWidget()
        session_layout = QVBoxLayout(session_page)
        session_layout.setContentsMargins(0, 6, 0, 0)
        session_layout.addWidget(self._tables_splitter, 1)
        session_layout.addWidget(self._connected.expand_button)
        session_layout.addWidget(self._disconnected.expand_button)

        self._history_widget: PlayerLeaderboardWindow | None = None
        self._history_page = QWidget()
        self._history_layout = QVBoxLayout(self._history_page)
        self._history_layout.setContentsMargins(0, 6, 0, 0)

        self._main_tabs = QTabWidget()
        self._main_tabs.addTab(session_page, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'user.svg')), 'Session en cours')
        self._main_tabs.addTab(self._history_page, QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'history.svg')), 'Historique des joueurs')
        self._main_tabs.setTabToolTip(1, 'Tous les joueurs croisés dans tes sessions, avec leurs infos (pseudo, IP, pays, FAI, première et dernière vue…)')
        self._main_tabs.currentChanged.connect(self._on_main_tab_changed)
        main_layout.addWidget(self._main_tabs, 1)

        # BTX: in-game mini window + global hotkey
        self._overlay_controller = OverlayController(self, self.open_history_search)
        # BTX: Ctrl+F = search any player (session, history, notes) and open their card
        self._open_card_from_search = lambda ip, names: open_player_card(self, ip, names)
        install_global_search(self, self._open_card_from_search)
        # BTX: after an update, show the release notes of the new version once
        QTimer.singleShot(2500, self._whats_new.maybe_show_after_update)

        self._connected.section_toggled.connect(self._update_splitter_visibility)
        self._disconnected.section_toggled.connect(self._update_splitter_visibility)

        if Settings.gui_remember_window_layout:
            gui_state = GUIState.load()
            if (
                gui_state.main_window_splitter_sizes
                and len(gui_state.main_window_splitter_sizes) == self._tables_splitter.count()
                and all(size > 0 for size in gui_state.main_window_splitter_sizes)
            ):
                self._saved_splitter_sizes = list(gui_state.main_window_splitter_sizes)
                self._tables_splitter.setSizes(self._saved_splitter_sizes)

            if gui_state.connected_table_column_widths:
                self._connected.table_view.apply_column_widths(gui_state.connected_table_column_widths)

            if gui_state.disconnected_table_column_widths:
                self._disconnected.table_view.apply_column_widths(gui_state.disconnected_table_column_widths)

        self._update_splitter_visibility()

        self.raise_()
        self.activateWindow()

        worker_thread = GUIWorkerThread()
        self._state = _WindowState(
            worker_thread=worker_thread,
            window_being_moved=False,
            min_accepted_snapshot_version=0,
        )
        self._state.worker_thread.update_signal.connect(self._update_gui)
        self._state.worker_thread.start()

        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(1_000)
        self._stats_timer.timeout.connect(self._tick_stats)
        self._stats_timer.start()

        self.installEventFilter(self)

        self._apply_always_on_top()

        self._update_header_capture_status()
        self._update_status_bar()

    def show_discord_intro(self) -> None:
        """Open the Discord intro dialog, retaining a reference to prevent garbage collection."""
        show_or_focus_window(self, '_discord_intro_window', DiscordIntro)

    @override
    def eventFilter(self, a0: QObject, a1: QEvent) -> bool:
        """Filter events to detect window movement."""
        if a0 == self and a1:
            event_type = a1.type()

            if event_type in (QEvent.Type.Move, QEvent.Type.Resize, QEvent.Type.WindowStateChange) and not self._state.window_being_moved:
                self._start_window_move()

            elif (
                event_type
                in (
                    QEvent.Type.WindowActivate,
                    QEvent.Type.WindowDeactivate,
                    QEvent.Type.NonClientAreaMouseButtonRelease,
                    QEvent.Type.Enter,
                    QEvent.Type.HoverEnter,
                )
                and self._state.window_being_moved
            ):
                self._end_window_move()

        return super().eventFilter(a0, a1)

    def _start_window_move(self) -> None:
        """Apply transparency when window movement/dragging starts."""
        self._state.window_being_moved = True
        if sys.platform == 'win32':
            self.setWindowOpacity(0.85)
        self._header.setEnabled(False)
        self._connected.set_all_enabled(enabled=False)
        self._disconnected.set_all_enabled(enabled=False)
        self._tables_splitter.setEnabled(False)
        status_bar = self.statusBar()
        if not status_bar:
            return
        status_bar.setEnabled(False)

    def _end_window_move(self) -> None:
        """Restore opacity and re-enable UI elements after window movement/dragging ends."""
        self._state.window_being_moved = False
        if sys.platform == 'win32':
            self.setWindowOpacity(1.0)
        self._header.setEnabled(True)
        self._connected.set_all_enabled(enabled=True)
        self._disconnected.set_all_enabled(enabled=True)
        self._tables_splitter.setEnabled(True)
        status_bar = self.statusBar()
        if not status_bar:
            return
        status_bar.setEnabled(True)

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Handle the main window close event and terminate background work."""
        if Settings.gui_remember_window_layout:
            gui_state = GUIState.load()
            if self._connected.is_expanded and self._disconnected.is_expanded:
                current_sizes = self._tables_splitter.sizes()
                if sum(current_sizes) > 0:
                    gui_state.main_window_splitter_sizes = current_sizes
            elif self._saved_splitter_sizes:
                gui_state.main_window_splitter_sizes = self._saved_splitter_sizes

            if self._connected.table_view.has_custom_column_widths:
                gui_state.connected_table_column_widths = self._connected.table_view.get_column_widths()
            else:
                gui_state.connected_table_column_widths = None

            if self._disconnected.table_view.has_custom_column_widths:
                gui_state.disconnected_table_column_widths = self._disconnected.table_view.get_column_widths()
            else:
                gui_state.disconnected_table_column_widths = None

            gui_state.save()

        gui_closed__event.set()
        wake_all_player_cores()
        self._player_resolver_window.close()
        if self._settings_dialog_window is not None:
            self._settings_dialog_window.close()
        if self._userip_manager_window is not None:
            self._userip_manager_window.close()
        if self._logs_manager_window is not None:
            self._logs_manager_window.close()
        if self._detections_manager_window is not None:
            self._detections_manager_window.close()
        if self._leaderboard_window is not None:
            self._leaderboard_window.close()
        if self._history_widget is not None:
            self._history_widget.close()
        self._overlay_controller.shutdown()

        PingWindow.close_window()
        PortScannerWindow.close_window()

        close_all_crawler_dialogs()
        close_all_lookup_dialogs()
        if self.capture.is_running():
            self.capture.stop()
        GTASuspendManager.shutdown()
        self._state.worker_thread.quit()
        self._state.worker_thread.wait()
        if a0 is not None:
            a0.accept()
        terminate_script('EXIT')

    @override
    def showEvent(self, a0: QShowEvent) -> None:
        """Handle the window show event and maximize if required."""
        super().showEvent(a0)
        if self.property('_should_maximize_on_show') is True:
            self.setProperty('_should_maximize_on_show', False)  # noqa: FBT003
            self.showMaximized()

    def _open_port_scanner(self) -> None:
        """Open the Port Scanner tool window."""
        PortScannerWindow.open_window()

    def _open_ping_diagnostics(self) -> None:
        """Open the Ping Diagnostics tool window."""
        PingWindow.open_window()

    def _update_gui(self, payload: GUIUpdatePayload) -> None:
        self._sync_capture_toggle_action()
        self._header.setText(payload.header_text)
        self._status_bar.set_texts(
            capture=payload.status_capture_text,
            config=payload.status_config_text,
            issues=payload.status_issues_text,
            performance=payload.status_performance_text,
        )

        if payload.column_config.connected_column_names != self._connected.table_model.column_names:
            self._connected.update_columns(payload.column_config.connected_column_names)
        if payload.column_config.disconnected_column_names != self._disconnected.table_model.column_names:
            self._disconnected.update_columns(payload.column_config.disconnected_column_names)

        connected_count_changed = self._connected.last_count != payload.connected_count
        disconnected_count_changed = self._disconnected.last_count != payload.disconnected_count

        if connected_count_changed:
            self._connected.update_current_count(payload.connected_count)

        self._connected.table_view.capture_selection()
        self._disconnected.table_view.capture_selection()

        connected_payload_ips: set[str] = set()
        for processed_data, compiled_colors in payload.connected_rows_with_colors:
            ip = self._connected.table_model.get_ip_from_data_safely(processed_data)
            connected_payload_ips.add(ip)

            disconnected_row_index = self._disconnected.table_model.get_row_index_by_ip(ip)
            if disconnected_row_index is not None:
                self._disconnected.table_model.delete_row(disconnected_row_index)

            connected_row_index = self._connected.table_model.get_row_index_by_ip(ip)
            if connected_row_index is None:
                self._connected.table_model.add_row_without_refresh(processed_data, compiled_colors)
            else:
                self._connected.table_model.update_row_without_refresh(connected_row_index, processed_data, compiled_colors)

        self._prune_missing_rows(self._connected.table_model, connected_payload_ips)

        if self._connected.table_view.isVisible():
            self._connected.table_view.sort_current_column()
            self._connected.table_view.check_initial_data_column_sizing()

        if disconnected_count_changed:
            self._disconnected.update_current_count(payload.disconnected_count)

        disconnected_payload_ips: set[str] = set()
        for processed_data, compiled_colors in payload.disconnected_rows_with_colors:
            ip = self._disconnected.table_model.get_ip_from_data_safely(processed_data)
            disconnected_payload_ips.add(ip)

            connected_row_index = self._connected.table_model.get_row_index_by_ip(ip)
            if connected_row_index is not None:
                self._connected.table_model.delete_row(connected_row_index)

            disconnected_row_index = self._disconnected.table_model.get_row_index_by_ip(ip)
            if disconnected_row_index is None:
                self._disconnected.table_model.add_row_without_refresh(processed_data, compiled_colors)
            else:
                self._disconnected.table_model.update_row_without_refresh(disconnected_row_index, processed_data, compiled_colors)

        self._prune_missing_rows(self._disconnected.table_model, disconnected_payload_ips)

        if self._disconnected.table_view.isVisible():
            self._disconnected.table_view.sort_current_column()
            self._disconnected.table_view.check_initial_data_column_sizing()

        self._connected.table_view.restore_selection()
        self._disconnected.table_view.restore_selection()

        self._connected.refresh_selection_count()
        self._disconnected.refresh_selection_count()

        self._connected.sync_paging_from_payload(
            total_count=payload.connected_count,
            rows_per_page=payload.connected_rows_per_page,
            page=payload.connected_page,
        )
        self._disconnected.sync_paging_from_payload(
            total_count=payload.disconnected_count,
            rows_per_page=payload.disconnected_rows_per_page,
            page=payload.disconnected_page,
        )

        self._sync_game_status()
        if Settings.is_gta5_feature_set():
            self._update_looky_actions()

        if self._capture_statistics_window is not None:
            self._capture_statistics_window.refresh()

    @staticmethod
    def _prune_missing_rows(model: SessionTableModel, ips_to_keep: set[str]) -> None:
        """Remove rows from the model whose IPs are not in the current payload."""
        stale_ips = set(model.get_all_ips()) - ips_to_keep
        for ip in stale_ips:
            model.remove_player_by_ip(ip)

    @override
    def _clear_session_host(self) -> None:
        """Manually clear the current session host and reset host detection state."""
        SessionHost.clear_session_host_data()

    @override
    def _redetect_session_host(self) -> None:
        """Clear the current session host and immediately re-evaluate host detection with notification on failure."""
        if not Settings.is_session_host_feature_set():
            QMessageBox.warning(self, TITLE, "La détection de l'hôte de session n'est pas disponible pour le mode de jeu actuel.")
            return

        if not Settings.gui_session_host_detection:
            QMessageBox.warning(self, TITLE, "La détection de l'hôte de session est désactivée dans les paramètres.\n\nActive-la dans les paramètres pour détecter l'hôte de la session.")
            return

        if CaptureState.is_local_capture():
            if Settings.is_gta5_feature_set() and not CaptureState.gta5_is_running:
                QMessageBox.warning(self, TITLE, "Grand Theft Auto V n'est pas lancé.")
                return
            if Settings.is_rdr2_feature_set() and not CaptureState.rdr2_is_running:
                QMessageBox.warning(self, TITLE, "Red Dead Redemption 2 n'est pas lancé.")
                return

        connected_players = PlayersRegistry.get_connected_players()
        if not connected_players:
            QMessageBox.information(self, TITLE, 'Aucun joueur connecté trouvé dans la session actuelle.')
            return

        SessionHost.clear_session_host_data()
        SessionHost.manual_redetect = True

        host_player = SessionHost.get_host_player(connected_players)
        SessionHost.manual_redetect = False
        SessionHost.search_player = False
        SessionHost.search_start_time = None

        if host_player is not None:
            text = f'Hôte de session détecté :\n\n{host_player.ip}'
            icon = QMessageBox.Icon.Information
        else:
            reason = SessionHost.last_rejection_reason or 'No connected player currently matches the session host criteria.'
            text = f'Impossible de trouver l\'hôte de session :\n\n{reason}'
            icon = QMessageBox.Icon.Warning

        show_detailed_message(self, TITLE, text, detailed_text=SessionHost.last_debug_details, icon=icon)

    def _apply_always_on_top(self) -> None:
        """Apply the always-on-top setting to the main window."""
        apply_always_on_top(self, Settings.gui_always_on_top)

    def _apply_table_sort_from_settings(self) -> None:
        """Apply configured table sort column and order to connected and disconnected tables."""
        self._connected.apply_sort_from_settings()
        self._disconnected.apply_sort_from_settings()

    def _apply_table_pagination_from_settings(self) -> None:
        """Apply configured table pagination rows per page to connected and disconnected tables."""
        self._connected.apply_pagination_from_settings()
        self._disconnected.apply_pagination_from_settings()

    def _sync_player_resolver_settings(self) -> None:
        """Synchronize Player Resolver background monitoring and refresh session table icons."""
        self._player_resolver_window.high_rate_monitor.apply_settings()
        self._player_resolver_window.player_identifier.apply_settings()
        if Settings.high_rate_monitor_run_in_background:
            self._player_resolver_window.high_rate_monitor.start_monitoring()
        elif not self._player_resolver_window.isVisible():
            self._player_resolver_window.high_rate_monitor.stop_monitoring()
        self._connected.table_view.viewport().update()
        self._disconnected.table_view.viewport().update()

    def _open_settings_dialog(self) -> None:
        """Open the Settings window, or focus the existing one."""

        def _factory() -> SettingsDialog:
            window = SettingsDialog(None, self.capture.get(), self._on_change_interface)
            for callback in (
                self._update_game_toolbar_visibility,
                self._apply_always_on_top,
                self._update_splitter_visibility,
                self._apply_table_sort_from_settings,
                self._apply_table_pagination_from_settings,
                self._sync_player_resolver_settings,
            ):
                window.accepted.connect(callback)
            return window

        show_or_focus_window(self, '_settings_dialog_window', _factory)

    def _open_userip_manager(self) -> UserIPDatabasesManager:
        """Open the UserIP Databases Manager window, or focus the existing one."""
        return show_or_focus_window(self, '_userip_manager_window', lambda: UserIPDatabasesManager(None))

    def open_userip_manager_and_search(self, text: str) -> None:
        """Open the UserIP Databases Manager, activate global search, and populate the search field with `text`."""
        self._open_userip_manager().search_global(text)

    def _open_logs_manager(self) -> LogsManager:
        """Open the Logs Manager window, or focus the existing one."""
        return show_or_focus_window(self, '_logs_manager_window', lambda: LogsManager(None))

    def open_logs_manager_and_search_userip(self, text: str) -> None:
        """Open the Logs Manager on the UserIP Logging tab and filter by `text`."""
        self._open_logs_manager().search_in_userip_logging(text)

    def open_logs_manager_and_search_sessions(self, text: str) -> None:
        """Open the Logs Manager on the Sessions Logging tab and start a global search for `text`."""
        self._open_logs_manager().search_in_sessions_logging(text)

    @override
    def _open_player_resolver(self) -> None:
        """Open the Player Resolver window, or focus the existing one."""
        self._player_resolver_window.show_and_focus()

    def _update_header_capture_status(self) -> None:
        """Immediately update the header text to reflect current capture state."""
        self._header.setText(generate_gui_header_html(capture=self.capture.get()))

    def _update_status_bar(self) -> None:
        """Immediately render the status bar with current capture state."""
        capture_section, config_section, issues_section, performance_section = build_gui_status_text(
            capture=self.capture.get(),
            discord_rpc_manager=None,
        )
        self._status_bar.set_texts(
            capture=capture_section,
            config=config_section,
            issues=issues_section,
            performance=performance_section,
        )

    def open_history_search(self, text: str) -> None:
        """BTX: open the player history tab and search for *text* (called from the mini window)."""
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._main_tabs.setCurrentIndex(1)
        if self._history_widget is not None and text:
            self._history_widget._search_box.setText(text)  # noqa: SLF001

    def _on_main_tab_changed(self, index: int) -> None:
        """BTX: build and load the player history tab the first time it is opened."""
        if index != 1:
            return
        if self._history_widget is None:
            history = PlayerLeaderboardWindow(self._history_page)
            history.setWindowFlags(Qt.WindowType.Widget)
            history.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)  # noqa: FBT003
            history.setProperty('_should_maximize_on_show', False)  # noqa: FBT003
            history.setMinimumSize(0, 0)
            history._always_on_top_checkbox.setVisible(False)  # noqa: SLF001  # embedded: no separate window
            self._history_layout.addWidget(history)
            self._history_widget = history
            history.load_and_show()
        else:
            self._history_widget.show()

    def _sync_capture_toggle_action(self) -> None:
        """Synchronize the toggle capture action icon, text, and tooltip with the current capture state."""
        is_running = self.capture.is_running()
        expected_text = 'Arrêter la capture' if is_running else 'Démarrer la capture'
        if self._actions.toggle_capture.text() == expected_text:
            return

        if is_running:
            self._actions.toggle_capture.setText('Arrêter la capture')
            self._actions.toggle_capture.setIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'stop.svg')))
            self._actions.toggle_capture.setToolTip('Arrêter la capture de paquets')
        else:
            self._actions.toggle_capture.setText('Démarrer la capture')
            self._actions.toggle_capture.setIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'play.svg')))
            self._actions.toggle_capture.setToolTip('Démarrer la capture de paquets')

    def _toggle_capture(self) -> None:
        """Toggle the packet capture on/off."""
        if self.capture.is_running():
            self.capture.stop()
        else:
            self.capture.start()

        self._sync_capture_toggle_action()
        self._update_header_capture_status()
        self._update_status_bar()

    def set_interface_switching_mode(self, *, switching: bool) -> None:
        """Disable or re-enable the UI while an interface switch is in progress."""
        menu_bar = self.menuBar()
        if menu_bar:
            menu_bar.setEnabled(not switching)
        self._actions.change_interface.setEnabled(not switching)
        self._connected.set_all_enabled(enabled=not switching)
        self._disconnected.set_all_enabled(enabled=not switching)
        self._tables_splitter.setEnabled(not switching)
        status_bar = self.statusBar()
        if status_bar:
            status_bar.setEnabled(not switching)

    def set_change_interface_button_enabled(self, *, enabled: bool) -> None:
        """Enable or disable only the Change Interface toolbar button."""
        self._actions.change_interface.setEnabled(enabled)

    def reset_players_for_interface_switch(self) -> None:
        """Clear all player data in preparation for a new capture interface."""
        self._clear_connected_players()
        self._clear_disconnected_players()
        SessionHost.clear_history()
        SessionHost.players_pending_for_disconnection.clear()

    def set_capture_toggle_enabled(self, *, enabled: bool) -> None:
        """Enable or disable the Stop/Start Capture toolbar button."""
        self._actions.toggle_capture.setEnabled(enabled)

    def on_interface_switched(self) -> None:
        """Synchronize GUI state after the capture interface has been replaced."""
        self._update_game_toolbar_visibility()
        self._sync_capture_toggle_action()
        self._actions.toggle_capture.setEnabled(True)
        self._update_header_capture_status()
        self._update_status_bar()
        wake_all_player_cores()

    def _clear_connected_players(self) -> None:
        """Clear all connected players from the table and registry."""
        self._state.min_accepted_snapshot_version = GUIRenderingState.get_version() + 1
        connected_players = PlayersRegistry.get_default_sorted_players(include_connected=True, include_disconnected=False)
        connected_ips = {player.ip for player in connected_players}

        PlayersRegistry.clear_connected_players()
        SessionHost.players_pending_for_disconnection.clear()
        self._connected.clear_table()

        if connected_ips:
            for ip in connected_ips:
                GTASuspendManager.release_reasons_for_ip(ip)
                RDR2SuspendManager.release_reasons_for_ip(ip)

    def _clear_disconnected_players(self) -> None:
        """Clear all disconnected players from the table and registry."""
        self._state.min_accepted_snapshot_version = GUIRenderingState.get_version() + 1
        disconnected_players = PlayersRegistry.get_default_sorted_players(include_connected=False, include_disconnected=True)
        disconnected_ips = {player.ip for player in disconnected_players}

        PlayersRegistry.clear_disconnected_players()
        SessionHost.players_pending_for_disconnection = [player for player in SessionHost.players_pending_for_disconnection if player.ip not in disconnected_ips]
        self._disconnected.clear_table()

        if disconnected_ips:
            for ip in disconnected_ips:
                GTASuspendManager.release_reasons_for_ip(ip)
                RDR2SuspendManager.release_reasons_for_ip(ip)
