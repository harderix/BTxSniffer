"""LookyLookupDialog and show_looky_lookup helper."""

import logging
import time
from datetime import UTC
from http import HTTPStatus
from typing import TYPE_CHECKING, override

import requests
from pydantic import ValidationError
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from session_sniffer.guis._crashing_qthread import CrashingQThread
from session_sniffer.guis.looky_text import LOOKY_TITLE
from session_sniffer.guis.stylesheets import (
    LOOKY_ACTION_BUTTON_STYLESHEET,
    LOOKY_CRAWLER_HEADER_STYLESHEET,
)
from session_sniffer.guis.tables_player_actions._player_info_dialog_mixin import PlayerInfoDialogMixin
from session_sniffer.guis.tables_player_actions.looky_system._looky_helpers import check_looky_prerequisites
from session_sniffer.guis.utils import ActiveDialogRegistry, set_dialog_window_flags
from session_sniffer.networking.looky_system import (
    extract_rate_limit_message,
    extract_rate_limit_wait_seconds,
    lookup_ip,
)
from session_sniffer.settings.settings import Settings
from session_sniffer.text_utils import pluralize

if TYPE_CHECKING:
    from session_sniffer.models.looky_system import LookyPlayer
    from session_sniffer.models.player import Player

logger = logging.getLogger(__name__)


class _LookyFetchWorker(CrashingQThread):
    """Background thread that fetches Looky System IP lookup results for a given IP address."""

    fetch_succeeded: Signal = Signal()
    fetch_not_found: Signal = Signal()
    fetch_failed: Signal = Signal(str)  # error message

    def __init__(self, ip: str, api_key: str) -> None:
        super().__init__()
        self.ip = ip
        self._api_key = api_key
        self.results: list[LookyPlayer] = []

    @override
    def _run(self) -> None:
        """Fetch Looky System lookup results and emit the appropriate outcome signal."""
        try:
            results = lookup_ip(self.ip, self._api_key, Settings.looky_game_version.lower())
        except requests.HTTPError as e:
            logger.warning('Looky System IP lookup failed with HTTP error: %s', e)
            if e.response is not None and e.response.status_code == HTTPStatus.NOT_FOUND:
                self.fetch_not_found.emit()
            elif e.response is not None and e.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                message = extract_rate_limit_message(e)
                wait_seconds = extract_rate_limit_wait_seconds(e)
                self.fetch_failed.emit(f'Limite de requêtes : {message}. Réessaie dans {wait_seconds} seconde{pluralize(wait_seconds or 0)}.')
            else:
                status_code = e.response.status_code if e.response is not None else '?'
                self.fetch_failed.emit(f'Looky System API error: HTTP {status_code}')
            return
        except requests.RequestException as e:
            logger.warning('Looky System IP lookup failed with network error: %s', e)
            self.fetch_failed.emit(f'Échec de la requête Looky System : {e}')
            return
        except ValidationError as e:
            logger.warning('Looky System IP lookup failed with validation error: %s', e)
            self.fetch_failed.emit(f'Looky System response format unexpected: {e}')
            return
        self.results = results
        self.fetch_succeeded.emit()


class LookyLookupDialog(PlayerInfoDialogMixin):
    """Non-modal dialog that renders pre-fetched Looky System player results."""

    def __init__(self, parent: QWidget | None, player: Player, results: list[LookyPlayer]) -> None:
        """Render *results* for *player*."""
        super().__init__(parent)
        self._ip = player.ip
        set_dialog_window_flags(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setWindowTitle(LOOKY_TITLE)
        self._apply_standard_dialog_size()

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(8)

        self._add_header_label(
            outer_layout,
            f'Recherche — {player.ip}',
            '#1c083a',
            '#2d0c69',
        ).setStyleSheet(LOOKY_CRAWLER_HEADER_STYLESHEET)

        scroll_layout = self._init_scroll_area(outer_layout)

        for entry in results:
            title = entry.name or f'Rockstar ID : {entry.rockstarid}'
            group, form = self._make_group(title, accent='#4b179b')
            self._add_row(form, 'Rockstar ID', str(entry.rockstarid))
            self._add_row(form, 'Pseudo', entry.name)
            last_seen_dt = entry.lastSeen if entry.lastSeen.tzinfo is None else entry.lastSeen.astimezone(UTC)
            self._add_row(form, 'Last Seen', last_seen_dt.strftime('%Y-%m-%d %H:%M:%S UTC'))
            self._add_row(form, 'Dernier pays', entry.lastCountry)
            self._add_row(form, 'Modder', 'Yes' if entry.isModder else 'No')
            self._add_row(form, 'Enhanced', 'Yes' if entry.isEnhanced else 'No')
            self._add_row(form, 'Legacy', 'Yes' if entry.isLegacy else 'No')
            self._add_row(form, 'VPN', 'Yes' if entry.isVpn else 'No')
            scroll_layout.addWidget(group)

        scroll_layout.addStretch(1)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, parent=self)
        button_box.rejected.connect(self.reject)
        button_box.accepted.connect(self.accept)
        close_button = button_box.button(QDialogButtonBox.StandardButton.Close)
        if close_button:
            close_button.setCursor(Qt.CursorShape.PointingHandCursor)
            close_button.setStyleSheet(LOOKY_ACTION_BUTTON_STYLESHEET)
        outer_layout.addWidget(button_box)


_active_lookup_workers: set[_LookyFetchWorker] = set()
_active_dialogs: ActiveDialogRegistry[str, LookyLookupDialog] = ActiveDialogRegistry()


def close_all_lookup_dialogs() -> None:
    """Close and cleanly cancel all open Looky lookup dialogs."""
    _active_dialogs.close_all()


def show_looky_lookup(parent: QWidget, player: Player) -> None:
    """Validate and fetch Looky System IP lookup results for *player*; open a results dialog or show an error."""
    if _active_dialogs.focus(player.ip):
        return

    api_key = check_looky_prerequisites(parent, player=player)
    if api_key is None:
        return

    if any(active_worker.ip == player.ip for active_worker in _active_lookup_workers):
        return

    worker = _LookyFetchWorker(player.ip, api_key)

    def _on_fetch_succeeded() -> None:
        with player.looky_system.lock:
            player.looky_system.usernames = [entry.name for entry in worker.results]
            player.looky_system.rockstarids = [entry.rockstarid for entry in worker.results]
            player.looky_system.needs_refresh = False
            player.looky_system.last_fetched_at = time.monotonic()
            player.looky_system.is_initialized = True

        if not isValid(parent):
            return

        if not worker.results:
            QMessageBox.information(parent, LOOKY_TITLE, 'Aucun joueur trouvé pour cette IP sur Looky System.')
            return

        _active_dialogs.show_or_focus(player.ip, lambda: LookyLookupDialog(None, player, worker.results))

    def _on_fetch_not_found() -> None:
        if isValid(parent):
            QMessageBox.information(parent, LOOKY_TITLE, f'Aucun résultat\n\nAucun joueur ne correspond à "{player.ip}"')

    def _on_fetch_failed(message: str) -> None:
        if isValid(parent):
            QMessageBox.warning(parent, LOOKY_TITLE, f'Échec : {message}')

    worker.fetch_succeeded.connect(_on_fetch_succeeded)
    worker.fetch_not_found.connect(_on_fetch_not_found)
    worker.fetch_failed.connect(_on_fetch_failed)
    _active_lookup_workers.add(worker)
    worker.finished.connect(lambda: _active_lookup_workers.discard(worker))
    worker.finished.connect(worker.deleteLater)
    worker.start()
