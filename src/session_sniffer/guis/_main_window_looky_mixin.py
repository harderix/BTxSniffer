"""Looky System menu-building and action handlers mixin for `MainWindow`."""

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QMenu, QMessageBox

from session_sniffer.constants.local import RESOURCES_DIR_PATH
from session_sniffer.guis.looky_text import (
    LOOKY_TITLE,
    configure_looky_action,
)
from session_sniffer.guis.tables_player_actions import show_crawlme_request
from session_sniffer.player.registry import PlayersRegistry
from session_sniffer.rendering_core.types import CaptureState
from session_sniffer.settings import Settings

if TYPE_CHECKING:
    from collections.abc import Callable


class LookyMixin(QMainWindow):
    """Looky System menu-building and action handlers mixin for `MainWindow`.

    Expects these attributes on the concrete class (set in `__init__`):
        `_looky_crawler_join_own_session_action`, `_looky_rescan_all_action`
    """

    # -- Attribute stubs for type checkers --
    _looky_crawler_join_own_session_action: QAction
    _looky_rescan_all_action: QAction
    _looky_submenu: QMenu

    if TYPE_CHECKING:
        _open_looky_website: Callable[[], None]

    def _build_looky_submenu(self, gta5_menu: QMenu) -> None:
        """Build the Looky System submenu and attach it to `gta5_menu`."""
        looky_submenu = gta5_menu.addMenu(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'eye.svg')), 'Looky System')
        if not looky_submenu:
            message = 'Failed to create Looky System submenu'
            raise RuntimeError(message)
        looky_submenu.setToolTipsVisible(True)
        looky_submenu.menuAction().setToolTip('Outils et raccourcis Looky System pour les sessions GTA5')
        self._looky_submenu = looky_submenu

        looky_open_website_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'website.svg')), 'Ouvrir le site', self)
        looky_open_website_action.setToolTip('Ouvrir le site Looky System dans ton navigateur')
        looky_open_website_action.triggered.connect(self._open_looky_website)
        looky_submenu.addAction(looky_open_website_action)

        looky_submenu.addSeparator()

        looky_crawler_join_own_session_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'bot.svg')), 'Appeler le crawler dans ma session', self)
        looky_crawler_join_own_session_action.setToolTip('Appeler le bot crawler pour trouver les pseudos des joueurs de ta session.')
        looky_crawler_join_own_session_action.triggered.connect(self._request_crawler_own_session)
        looky_submenu.addAction(looky_crawler_join_own_session_action)
        self._looky_crawler_join_own_session_action = looky_crawler_join_own_session_action

        looky_rescan_all_action = QAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'refresh.svg')), 'Rescanner tous les joueurs', self)
        looky_rescan_all_action.setToolTip('Rafraîchir immédiatement les données Looky System de tous les joueurs sans attendre la prochaine mise à jour auto.')
        looky_rescan_all_action.triggered.connect(self._rescan_all_looky_players)
        looky_submenu.addAction(looky_rescan_all_action)
        self._looky_rescan_all_action = looky_rescan_all_action

        looky_submenu.aboutToShow.connect(self._update_looky_actions)

    def _update_looky_actions(self) -> None:
        """Update enabled state and tooltips for Looky System submenu actions based on current settings."""
        configure_looky_action(
            self._looky_crawler_join_own_session_action,
            'Appeler le bot crawler pour trouver les pseudos des joueurs de ta session.',
            is_gta5_running=CaptureState.gta5_is_running,
        )
        configure_looky_action(
            self._looky_rescan_all_action,
            'Rafraîchir immédiatement les données Looky System de tous les joueurs sans attendre la prochaine mise à jour auto.',
            check_gta5_restriction=True,
        )

    def _request_crawler_own_session(self) -> None:
        """Request the Looky System crawler bot to join the current session."""
        show_crawlme_request(self)

    def _rescan_all_looky_players(self) -> None:
        """Reset the Looky System fetch timestamp for every player so `looky_core` re-fetches them immediately."""
        if (
            Settings.looky_exclusive_gta5_process
            and CaptureState.is_local_capture()
            and not CaptureState.gta5_is_running
        ):
            QMessageBox.warning(self, LOOKY_TITLE, "Looky System ne fonctionne qu'avec GTA V, qui n'est pas lancé.")
            return

        players = PlayersRegistry.get_default_sorted_players()
        count = 0
        for player in players:
            if Settings.looky_exclusive_gta5_process and CaptureState.is_local_capture() and not player.is_gta5_process:
                continue
            if player.looky_system.is_initialized:
                with player.looky_system.lock:
                    player.looky_system.last_fetched_at = 0.0
                count += 1

        if not count:
            QMessageBox.information(self, LOOKY_TITLE, "Aucun joueur Looky System à rescanner.\nAucun joueur n'a encore été récupéré.")
        else:
            noun = 'player' if count == 1 else 'players'
            QMessageBox.information(self, LOOKY_TITLE, f'{count} {noun} en file d\'attente pour le rescan Looky System.\nLes résultats se mettront à jour automatiquement.')
