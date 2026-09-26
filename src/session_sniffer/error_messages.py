"""GUI dialog/message-box text formatting.

This module contains functions that build user-facing text intended ONLY for GUI dialogs/message boxes
(e.g., messages shown via the app's message box / dialog helpers).
"""

from typing import TYPE_CHECKING

from session_sniffer.constants.standalone import GITHUB_VERSIONS_URL, TITLE
from session_sniffer.text_utils import pluralize

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from session_sniffer.networking.interface import SelectedInterfaceRow
    from session_sniffer.player.userip import UserIPConflict


def format_type_error(
    obj: object,
    expected_types: type | tuple[type, ...],
    suffix: str = '',
) -> str:
    """Generate a formatted error message for a type mismatch.

    Args:
        obj: The object whose type is being checked.
        expected_types: The expected type(s) for the object.
        suffix: An optional suffix to append to the error message.

    Returns:
        The formatted error message.
    """
    actual_type = type(obj).__name__

    if isinstance(expected_types, tuple):
        expected_types_names = ' | '.join(expected_type.__name__ for expected_type in expected_types)
        expected_type_count = len(expected_types)
    else:
        expected_types_names = expected_types.__name__
        expected_type_count = 1

    plural_suffix = '' if expected_type_count == 1 else 's'
    return f'Expected type{plural_suffix} {expected_types_names}, got {actual_type} instead.{suffix}'


def ensure_instance[T](obj: object, expected_types: type[T] | tuple[type[T], ...]) -> T:
    """Ensure an object is an instance of the expected type.

    Args:
        obj: The object to validate.
        expected_types: The expected type(s) for `obj`.

    Returns:
        The same object, typed as `T`.

    Raises:
        TypeError: If `obj` is not an instance of `expected_types`.
    """
    if not isinstance(obj, expected_types):
        raise TypeError(format_type_error(obj, expected_types))
    return obj  # type: ignore[return-value]


def format_invalid_datetime_columns_settings_message() -> str:
    """Format the Settings.ini error shown when all datetime columns are disabled."""
    return '\n        ERREUR dans ton fichier "Settings.ini" personnalisé :\n\n        Au moins un de ces paramètres doit être à la valeur "True" :\n        <GUI_COLUMNS_DATETIME_SHOW_DATE>\n        <GUI_COLUMNS_DATETIME_SHOW_TIME>\n        <GUI_COLUMNS_DATETIME_SHOW_ELAPSED_TIME>\n\n        Les valeurs par défaut vont être appliquées pour corriger ce problème.\n    '


def format_failed_check_for_updates_message(
    *,
    exception_name: str,
    http_code: str,
) -> str:
    """Format the retry/abort message shown when update checks fail."""
    return f'\n        ERREUR :\n            Impossible de vérifier les mises à jour.\n\n            DEBUG :\n                Exception : {exception_name}\n                Code HTTP : {http_code}\n\n        Vérifie ta connexion internet et que tu as accès à :\n        {GITHUB_VERSIONS_URL}\n\n        Abandonner :\n            Quitter et ouvrir la page GitHub "{TITLE}" pour\n            télécharger la dernière version.\n        Réessayer :\n            Vérifier à nouveau les mises à jour.\n        Ignorer :\n            Continuer avec la version actuelle (déconseillé).\n    '


def format_geolite2_download_flags_failed_message(
    *,
    failed_flags: list[str],
    geolite2_release_api_url: str,
) -> str:
    """Format the message shown when one or more GeoLite2 assets have no version/download URL."""
    flags_str = "', '".join(failed_flags)
    return f'\n        ERREUR :\n            Échec du téléchargement de la base MaxMind GeoLite2 "{flags_str}"{pluralize(len(failed_flags))}.\n\n        DEBUG :\n            GITHUB_RELEASE_API__GEOLITE2__URL={geolite2_release_api_url}\n            failed_fetching_flag_list={failed_flags}\n\n        Ces bases MaxMind GeoLite2{pluralize(len(failed_flags))} ne seront pas mises à jour.\n    '


def format_geolite2_update_initialize_error_message(
    *,
    update_exception: Exception | None,
    failed_url: str | None,
    http_code: int | str | None,
    initialize_exception: Exception | None,
) -> tuple[bool, str | None]:
    """Format the GeoLite2 initialization error summary.

    Returns:
        Tuple of (geoip2_enabled, message). If message is None, nothing should be shown.
    """
    show_error = False
    msgbox_message = ''

    if update_exception is not None:
        msgbox_message += f'Exception Error: {update_exception}\n\n'
        show_error = True

    if failed_url is not None:
        msgbox_message += f'Error: Failed fetching url: "{failed_url}".'
        if http_code is not None:
            msgbox_message += f' (http_code: {http_code})'
        msgbox_message += '\nImpossible de garder à jour la localisation des IP (pays, ville et ASN) de MaxMind GeoLite2.\n\n'
        show_error = True

    if initialize_exception is not None:
        msgbox_message += f'Exception Error: {initialize_exception}\n\n'
        msgbox_message += 'Désactivation de la localisation des IP (pays, ville et ASN) MaxMind GeoLite2.\n'
        msgbox_message += "Les pays, villes et ASN des joueurs ne s'afficheront pas dans les colonnes."
        geoip2_enabled = False
        show_error = True
    else:
        geoip2_enabled = True

    if not show_error:
        return geoip2_enabled, None

    return geoip2_enabled, msgbox_message.rstrip('\n')


def format_outdated_packages_message(
    *,
    app_title: str,
    outdated_packages: Sequence[tuple[str, object, str]],
) -> str:
    """Format the warning shown when project dependency specs and installed packages mismatch."""
    msgbox_message = "Les paquets suivants n'ont pas la bonne version :\n\n"

    for package_name, required_version, installed_version in outdated_packages:
        msgbox_message += f'{package_name} (requis {required_version}, installé {installed_version})\n'

    msgbox_message += f'\nGarder tes paquets synchronisés avec "{app_title}" assure le bon fonctionnement et évite les problèmes de compatibilité.'
    msgbox_message += '\n\nVeux-tu ignorer cet avertissement et continuer ?'
    return msgbox_message


def format_userip_ip_conflict_message(
    *,
    conflicts: Sequence[UserIPConflict],
    userip_databases_dir: Path,
) -> tuple[str, str | None]:
    """Format the error shown when one or more IPs exist in multiple UserIP databases.

    Returns:
        A tuple of (summary_message, detailed_text). If detailed_text is None, no details section is needed.
    """
    count = len(conflicts)
    if count == 1:
        conflict = conflicts[0]
        db1_name = conflict.existing_userip.db_path.relative_to(userip_databases_dir).with_suffix('')
        db2_name = conflict.conflicting_database_path.relative_to(userip_databases_dir).with_suffix('')
        usernames1 = ', '.join(conflict.existing_userip.usernames)
        msg = f'\n            ERREUR :\n                Conflit d\'IP entre bases UserIP\n\n            INFOS :\n                Une même IP ne peut pas être assignée à plusieurs\n                bases de données.\n                Les utilisateurs assignés à cette IP seront ignorés\n                tant que le conflit n\'est pas résolu.\n\n            DEBUG :\n                "{db1_name}":\n                {usernames1}={conflict.existing_userip.ip}\n\n                "{db2_name}":\n                {conflict.conflicting_username}={conflict.existing_userip.ip}\n        '
        return msg, None

    preview_lines: list[str] = []
    preview_count = min(count, 5)
    for conflict in conflicts[:preview_count]:
        db1_name = conflict.existing_userip.db_path.relative_to(userip_databases_dir).with_suffix('')
        db2_name = conflict.conflicting_database_path.relative_to(userip_databases_dir).with_suffix('')
        usernames1 = ', '.join(conflict.existing_userip.usernames)
        preview_lines.append(
            f'            "{db1_name}" ({usernames1}={conflict.existing_userip.ip})\n'
            f'            "{db2_name}" ({conflict.conflicting_username}={conflict.existing_userip.ip})',
        )

    preview_block = '\n\n'.join(preview_lines)
    remaining_count = count - preview_count
    remaining_suffix = f'\n\n            ... et {remaining_count} autres conflits (voir "Afficher les détails...").' if remaining_count > 0 else ''

    summary = f'\n        ERREUR :\n            Conflits d\'IP entre bases UserIP ({count} conflits détectés)\n\n        INFOS :\n            Une même IP ne peut pas être assignée à plusieurs\n            bases de données.\n            Les utilisateurs aux IP en conflit seront ignorés\n            tant que les conflits ne sont pas résolus.\n\n        DEBUG :\n{preview_block}{remaining_suffix}\n    '

    detailed_lines: list[str] = []
    max_detailed = min(count, 1000)
    for i, conflict in enumerate(conflicts[:max_detailed], start=1):
        db1_name = conflict.existing_userip.db_path.relative_to(userip_databases_dir).with_suffix('')
        db2_name = conflict.conflicting_database_path.relative_to(userip_databases_dir).with_suffix('')
        usernames1 = ', '.join(conflict.existing_userip.usernames)
        detailed_lines.append(
            f'[{i}] IP: {conflict.existing_userip.ip}\n'
            f'    "{db1_name}": {usernames1}\n'
            f'    "{db2_name}": {conflict.conflicting_username}\n',
        )
    if count > max_detailed:
        detailed_lines.append(f'... et {count - max_detailed} autres conflits (voir les logs de l\'application).\n')

    detailed_text = '\n'.join(detailed_lines)
    return summary, detailed_text


def format_arp_spoofing_failed_message(
    selected_interface: SelectedInterfaceRow,
    error_details: str | None,
) -> str:
    """Format an ARP spoofing failure message for display in a message box.

    Returns:
        A formatted error message string ready for display.
    """
    interface_vendor_name = 'N/A' if selected_interface.vendor_name is None else selected_interface.vendor_name
    error_details_output = f'\n{error_details}' if error_details else ''

    return (
        f'L\'ARP Spoofing n\'a pas pu démarrer.\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nDÉTAILS DE L\'INTERFACE :\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nNom : {selected_interface.name}\nDescription : {selected_interface.description}\nIP de la passerelle : {selected_interface.gateway_ip or "N/A"}\nAdresse IP : {selected_interface.ip_address}\nAdresse MAC : {selected_interface.mac_address}\nFabricant : {interface_vendor_name}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nDIAGNOSTIC :\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nErreur : {error_details_output}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nCAUSES FRÉQUENTES :\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n• Carte réseau partagée/pontée (le plus fréquent)\n• Entrée ARP obsolète (l\'appareil cible {selected_interface.ip_address} a changé d\'adresse IP)\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nRECOMMANDATIONS :\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n• Si la carte "{selected_interface.name}" est partagée/pontée, désactive l\'ARP Spoofing dans l\'écran de sélection de l\'interface réseau et réessaie\n• Si possible, essaie de sniffer l\'appareil cible {selected_interface.ip_address} sur une autre carte réseau (ex. Wi-Fi au lieu d\'Ethernet)'
    )


def format_capture_interrupted_message() -> str:
    """Format the warning shown when packet capture exits unexpectedly."""
    return (
        "La capture de paquets s'est arrêtée de façon inattendue.\n\nC'est probablement dû à ta carte réseau qui a été retirée ou désactivée.\n\nSélectionne une interface réseau pour reprendre la capture."
    )


def format_npcap_required_message() -> str:
    """Format the initial NPCAP-required notification shown when Npcap is missing."""
    return (
        'BTXSniffer a besoin du pilote de capture Npcap pour surveiller et analyser le trafic réseau sous Windows.\n\n'
        "BTXSniffer télécharge l'installeur officiel depuis npcap.com et va l'ouvrir : accepte la demande "
        "d'administrateur, puis clique sur « Install ». L'app reprend toute seule une fois Npcap installé."
    )


def format_game_solo_session_process_not_running_message(game_name: str) -> str:
    """Format the warning shown when Solo Public Session is triggered but the game process is not running."""
    return f'{game_name} n\'est pas lancé.\n\nLance {game_name} avant d\'utiliser cette fonction.'


def format_game_solo_session_suspend_failed_message(game_name: str) -> str:
    """Format the error shown when the game process suspend attempt fails."""
    return f'Impossible de suspendre le processus {game_name}.\n\nEssaie de lancer BTXSniffer en tant qu\'administrateur.'
