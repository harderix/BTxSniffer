"""Shared Looky System UI text and small helpers."""

from PySide6.QtGui import QAction  # noqa: TC002

from session_sniffer.constants.standalone import TITLE
from session_sniffer.models.player import Player
from session_sniffer.networking.looky_system import LookyState
from session_sniffer.rendering_core.types import CaptureState
from session_sniffer.settings import Settings

LOOKY_TITLE = f'{TITLE} - Looky System'
LOOKY_SETTINGS_AUTH_PATH = 'Settings → Looky System → Authentication'
LOOKY_SETTINGS_GENERAL_PATH = 'Settings → Looky System → General'

# Menu tooltips
LOOKY_MENU_TOOLTIP_API_KEY_MISSING = f'Looky System a besoin d\'une clé API. Ajoutes-en une dans {LOOKY_SETTINGS_AUTH_PATH}.'
LOOKY_MENU_TOOLTIP_API_KEY_INVALID_OR_NO_ACCESS = f'Ta clé API Looky System est invalide ou ton compte n\'a pas accès à l\'API. Mets à jour ta clé dans {LOOKY_SETTINGS_AUTH_PATH}.'
LOOKY_MENU_TOOLTIP_GTA5_NOT_RUNNING = 'Looky System ne fonctionne que quand GTA V est lancé.'
LOOKY_MENU_TOOLTIP_RESTRICTED_GTA5_NOT_RUNNING = "Looky System ne fonctionne qu'avec GTA V, qui n'est pas lancé."
LOOKY_MENU_TOOLTIP_RESTRICTED_NOT_GTA5_PROCESS = 'Looky System est limité aux IP de joueurs qui communiquent directement avec GTA V.'
LOOKY_MENU_TOOLTIP_DISABLED = f'Looky System est désactivé. Active-le dans {LOOKY_SETTINGS_GENERAL_PATH}.'

# Dialog / message-box warnings
LOOKY_WARNING_API_ACCESS_MISSING = "Ton compte Looky System n'a pas accès à l'API."
LOOKY_WARNING_API_KEY_MISSING = f'Looky System a besoin d\'une clé API.\n\nAjoute ta clé API dans {LOOKY_SETTINGS_AUTH_PATH}.'
LOOKY_WARNING_DISABLED = f'Looky System est désactivé.\n\nActive-le dans {LOOKY_SETTINGS_GENERAL_PATH}.'

# Log messages
LOOKY_LOG_API_KEY_INVALID = '[Looky System] Unable to connect: the API key appears to be invalid. Please update it in Settings.'
LOOKY_LOG_VERIFICATION_HTTP_FAILED_TEMPLATE = '[Looky System] Token verification failed: HTTP %s %s'


def configure_looky_action(
    action: QAction,
    default_tooltip: str | None = None,
    *,
    is_gta5_running: bool | None = None,
    check_gta5_restriction: bool = False,
    players: Player | list[Player] | None = None,
) -> None:
    """Configure the enabled status and tooltip of a Looky-related QAction.

    Avoids duplicating the gating logic and tooltip settings across multiple widgets and menus.
    """
    target_players: list[Player] | None = [players] if isinstance(players, Player) else players

    if not Settings.looky_enabled:
        action.setEnabled(False)
        action.setToolTip(LOOKY_MENU_TOOLTIP_DISABLED)
    elif not Settings.looky_api_key:
        action.setEnabled(False)
        action.setToolTip(LOOKY_MENU_TOOLTIP_API_KEY_MISSING)
    elif not LookyState.api_access:
        action.setEnabled(False)
        action.setToolTip(LOOKY_MENU_TOOLTIP_API_KEY_INVALID_OR_NO_ACCESS)
    elif is_gta5_running is False:
        action.setEnabled(False)
        action.setToolTip(LOOKY_MENU_TOOLTIP_GTA5_NOT_RUNNING)
    elif (check_gta5_restriction or target_players) and Settings.looky_exclusive_gta5_process and CaptureState.is_local_capture():
        if not CaptureState.gta5_is_running:
            action.setEnabled(False)
            action.setToolTip(LOOKY_MENU_TOOLTIP_RESTRICTED_GTA5_NOT_RUNNING)
        elif target_players and not any(player.is_gta5_process for player in target_players):
            action.setEnabled(False)
            action.setToolTip(LOOKY_MENU_TOOLTIP_RESTRICTED_NOT_GTA5_PROCESS)
        else:
            action.setEnabled(True)
            if default_tooltip is not None:
                action.setToolTip(default_tooltip)
    else:
        action.setEnabled(True)
        if default_tooltip is not None:
            action.setToolTip(default_tooltip)
