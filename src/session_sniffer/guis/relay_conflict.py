"""Dialogs for resolving incompatible GTA5 relay detection settings."""

from typing import Literal

from PySide6.QtWidgets import QMessageBox, QWidget

from session_sniffer.constants.local import DETECTIONS_JSON_PATH
from session_sniffer.constants.standalone import TITLE
from session_sniffer.networking.third_party_servers import ThirdPartyServers
from session_sniffer.player.detections import GUIDetectionSettings
from session_sniffer.settings import Settings


def prompt_to_disable_gta5_relay_if_filtered(parent: QWidget | None, *, context: Literal['settings', 'startup']) -> bool:
    """Ask to disable GTA5 relay detection when the Take-Two Interactive or Microsoft relay IPs are filtered."""
    blocked_relays = [name for name in ('TAKETWO_INTERACTIVE', 'MICROSOFT') if name in Settings.capture_block_third_party_servers]

    if not (Settings.is_gta5_feature_set() and blocked_relays and GUIDetectionSettings.gta5_relay_enabled):
        return False

    blocked_names = [f"'{ThirdPartyServers[name].display_name}'" for name in blocked_relays]
    blocked_names_str = ' and '.join(blocked_names)

    if context == 'settings':
        detail = f'La détection des relais GTA5 est activée, mais le filtre de capture va maintenant bloquer les plages d\'IP de {blocked_names_str}.'
    else:
        detail = f'Réglages en conflit détectés :\n\nLa détection des relais GTA5 est activée, mais le filtre de capture bloque les plages d\'IP de {blocked_names_str}.'

    result = QMessageBox.question(
        parent,
        TITLE,
        f'{detail}\n\nLes IP relais seront ignorées avant que le moteur de capture ne les voie, donc la détection de relais ne se déclenchera jamais.\n\nVeux-tu désactiver automatiquement la détection des relais GTA5 ?',
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if result != QMessageBox.StandardButton.Yes:
        return False

    GUIDetectionSettings.gta5_relay_enabled = False
    GUIDetectionSettings.export_to_file(DETECTIONS_JSON_PATH)
    return True
