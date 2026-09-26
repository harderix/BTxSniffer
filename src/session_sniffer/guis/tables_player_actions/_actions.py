"""Discord report, clipboard, ping, and block-IP actions for session table context menus."""

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QClipboard, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
    QWidget,
)

from session_sniffer.constants.local import RESOURCES_DIR_PATH
from session_sniffer.constants.standalone import MAX_PORT, MIN_PORT
from session_sniffer.error_messages import ensure_instance
from session_sniffer.guis.app import app
from session_sniffer.guis.ping_window import PingWindow
from session_sniffer.guis.port_scanner_window import PortScannerWindow
from session_sniffer.guis.stylesheets import SVG_ICON_CONTEXT_MENU_STYLESHEET
from session_sniffer.guis.tables_player_actions._format import (
    format_bool,
    format_loss_pct,
    format_ms,
    format_text,
    userip_database_text,
)
from session_sniffer.guis.userip_manager_helpers import IPRangeBuilderDialog
from session_sniffer.networking.ping import PingMode
from session_sniffer.settings.settings import Settings
from session_sniffer.text_utils import pluralize

if TYPE_CHECKING:
    from session_sniffer.models.player import Player


def build_discord_player_report(player: Player) -> str:
    """Build a Discord-formatted player info report string."""
    lines: list[str] = []
    lines.append(f'## Rapport joueur — `{player.ip}`')
    lines.append('')

    # Player Info
    lines.append('**Infos joueur**')
    lines.append(f'> **Adresse IP :** `{player.ip}`')
    hostname = format_text(player.reverse_dns.hostname)
    lines.append(f'> **Nom d\'hôte :** `{hostname}`')
    usernames = ', '.join(player.usernames) if player.usernames else 'N/A'
    lines.append(f'> **Pseudo{pluralize(len(player.usernames))} :** {usernames}')
    lines.append(f'> **Premier port :** {player.ports.first}  |  **Dernier port :** {player.ports.last}')
    middle_ports = ', '.join(map(str, player.ports.middle))
    if middle_ports:
        lines.append(f'> **Ports intermédiaires :** {middle_ports}')
    db_text = userip_database_text(player)
    if db_text != 'No':
        lines.append(f'> **Base UserIP :** {db_text}')
    first_seen = player.datetime.first_seen.strftime('%Y-%m-%d %H:%M:%S')
    last_seen = player.datetime.last_seen.strftime('%Y-%m-%d %H:%M:%S')
    lines.append(f'> **Première vue :** {first_seen}  |  **Dernière vue :** {last_seen}')
    lines.append('')

    # Location
    country = format_text(player.iplookup.geolite2.country)
    country_code = format_text(player.iplookup.geolite2.country_code)
    continent = format_text(player.iplookup.ipapi.continent)
    region = format_text(player.iplookup.ipapi.region)
    city = format_text(player.iplookup.geolite2.city)
    timezone = format_text(player.iplookup.ipapi.time_zone)
    lines.append('**Localisation**')
    country_display = f'{country} ({country_code})' if country != 'N/A' and country_code != 'N/A' else country
    lines.append(f'> **Pays :** {country_display}')
    if continent != 'N/A':
        lines.append(f'> **Continent :** {continent}')
    if region != 'N/A':
        lines.append(f'> **Région :** {region}')
    if city != 'N/A':
        lines.append(f'> **Ville :** {city}')
    if timezone != 'N/A':
        lines.append(f'> **Fuseau horaire :** {timezone}')
    lines.append('')

    # Network
    isp = format_text(player.iplookup.ipapi.isp)
    org = format_text(player.iplookup.ipapi.org)
    asn = format_text(player.iplookup.ipapi.asn)
    as_name = format_text(player.iplookup.ipapi.as_name)
    mobile = format_bool(player.iplookup.ipapi.mobile)
    proxy = format_bool(player.iplookup.ipapi.proxy)
    hosting = format_bool(player.iplookup.ipapi.hosting)
    lines.append('**Réseau**')
    if isp != 'N/A':
        lines.append(f'> **FAI :** {isp}')
    if org not in {'N/A', isp}:
        lines.append(f'> **Organisation :** {org}')
    if asn != 'N/A':
        as_display = f'{asn} ({as_name})' if as_name != 'N/A' else asn
        lines.append(f'> **AS :** {as_display}')
    lines.append(f'> **Mobile :** {mobile}  |  **Proxy/VPN/Tor :** {proxy}  |  **Hébergeur :** {hosting}')
    lines.append('')

    # Ping
    avg_rtt = format_ms(player.ping.rtt_avg)
    packet_loss = format_loss_pct(player.ping.packet_loss)
    lines.append('**Ping**')
    lines.append(f'> **RTT moyen :** {avg_rtt}  |  **Perte de paquets :** {packet_loss}')

    return '\n'.join(lines)


def copy_player_info_for_discord(player: Player) -> None:
    """Copy a Discord-formatted player info report to the system clipboard."""
    clipboard = ensure_instance(app.clipboard(), QClipboard)
    clipboard.setText(build_discord_player_report(player))


def copy_players_info_for_discord(players: list[Player]) -> None:
    """Copy Discord-formatted reports for multiple players, separated by a divider."""
    clipboard = ensure_instance(app.clipboard(), QClipboard)
    separator = '\n\n---\n\n'
    clipboard.setText(separator.join(build_discord_player_report(player) for player in players))


def ping_ip(target: str | list[str]) -> None:
    """Run a continuous ICMP ping to the specified target host(s) in the Ping Diagnostics window."""
    PingWindow.open_window(target, mode=PingMode.ICMP)


def web_ping(target: str | list[str]) -> None:
    """Run a multi-vantage distributed HTTP ping via Check-Host.net in the Ping Diagnostics window."""
    PingWindow.open_window(target, mode=PingMode.WEB)


def scan_ports_ip(target: str | list[str]) -> None:
    """Open the Port Scanner window pre-configured for the target host(s)."""
    PortScannerWindow.open_window(target)


def tcp_port_ping(parent: QWidget, ip: str) -> None:
    """Run a TCP port connectivity check to a host on a user-specified port indefinitely."""
    port_string, success = QInputDialog.getText(parent, 'Input Port', 'Enter the port number to check TCP connectivity:')

    if not success:
        return

    port_string = port_string.strip()

    if not port_string.isdigit():
        QMessageBox.warning(parent, 'Erreur', 'Aucun numéro de port valide.')
        return

    port = int(port_string)

    if not MIN_PORT <= port <= MAX_PORT:
        QMessageBox.warning(parent, 'Erreur', 'Entre un numéro de port valide entre 1 et 65535.')
        return

    PingWindow.open_window(ip, mode=PingMode.TCP, port=port)


def tcp_port_ping_multi(parent: QWidget, ip_addresses: list[str]) -> None:
    """Ask for a port once, then run a TCP port connectivity check for each IP on that same port."""
    port_string, success = QInputDialog.getText(parent, 'Input Port', 'Enter the port number to check TCP connectivity:')

    if not success:
        return

    port_string = port_string.strip()

    if not port_string.isdigit():
        QMessageBox.warning(parent, 'Erreur', 'Aucun numéro de port valide.')
        return

    port = int(port_string)

    if not MIN_PORT <= port <= MAX_PORT:
        QMessageBox.warning(parent, 'Erreur', 'Entre un numéro de port valide entre 1 et 65535.')
        return

    PingWindow.open_window(ip_addresses, mode=PingMode.TCP, port=port)


def create_multi_tcp_ping_menu(
    parent: QWidget,
    ip_addresses: list[str],
    ping_menu: QMenu,
    *,
    icon_name: str = 'ping.svg',
) -> QMenu:
    """Create and attach a 'TCP Port Ping' submenu for multiple IP addresses to *ping_menu*."""
    tcp_menu = QMenu('Ping de port TCP', ping_menu)
    icon = QIcon(str(RESOURCES_DIR_PATH / 'icons' / icon_name))
    tcp_menu.setIcon(icon)
    tcp_menu.setStyleSheet(SVG_ICON_CONTEXT_MENU_STYLESHEET)
    tcp_menu.setToolTipsVisible(True)

    tcp_one_action = QAction(icon, 'Un port pour tous', tcp_menu)
    tcp_one_action.setToolTip('Demander un port une seule fois, puis pinger en TCP toutes les IP sélectionnées sur ce port.')

    def _do_tcp_ping_multi() -> None:
        tcp_port_ping_multi(parent, ip_addresses)

    tcp_one_action.triggered.connect(_do_tcp_ping_multi)
    tcp_menu.addAction(tcp_one_action)

    tcp_individual_action = QAction(icon, 'Un port par IP', tcp_menu)
    tcp_individual_action.setToolTip('Demander un port différent pour chaque IP sélectionnée.')

    def _do_tcp_ping_individual() -> None:
        for ip_address in ip_addresses:
            tcp_port_ping(parent, ip_address)

    tcp_individual_action.triggered.connect(_do_tcp_ping_individual)
    tcp_menu.addAction(tcp_individual_action)

    ping_menu.addMenu(tcp_menu)
    return tcp_menu


def udp_port_ping(parent: QWidget, ip: str) -> None:
    """Run a UDP port reachability check to a host on a user-specified port."""
    port_string, success = QInputDialog.getText(parent, 'Input Port', 'Enter the port number to check UDP reachability:')

    if not success:
        return

    port_string = port_string.strip()

    if not port_string.isdigit():
        QMessageBox.warning(parent, 'Erreur', 'Aucun numéro de port valide.')
        return

    port = int(port_string)

    if not MIN_PORT <= port <= MAX_PORT:
        QMessageBox.warning(parent, 'Erreur', 'Entre un numéro de port valide entre 1 et 65535.')
        return

    PingWindow.open_window(ip, mode=PingMode.UDP, port=port)


def udp_port_ping_multi(parent: QWidget, ip_addresses: list[str]) -> None:
    """Ask for a port once, then run a UDP port reachability check for each IP on that same port."""
    port_string, success = QInputDialog.getText(parent, 'Input Port', 'Enter the port number to check UDP reachability:')

    if not success:
        return

    port_string = port_string.strip()

    if not port_string.isdigit():
        QMessageBox.warning(parent, 'Erreur', 'Aucun numéro de port valide.')
        return

    port = int(port_string)

    if not MIN_PORT <= port <= MAX_PORT:
        QMessageBox.warning(parent, 'Erreur', 'Entre un numéro de port valide entre 1 et 65535.')
        return

    PingWindow.open_window(ip_addresses, mode=PingMode.UDP, port=port)


def create_multi_udp_ping_menu(
    parent: QWidget,
    ip_addresses: list[str],
    ping_menu: QMenu,
    *,
    icon_name: str = 'ping.svg',
) -> QMenu:
    """Create and attach a 'UDP Port Ping' submenu for multiple IP addresses to *ping_menu*."""
    udp_menu = QMenu('Ping de port UDP', ping_menu)
    icon = QIcon(str(RESOURCES_DIR_PATH / 'icons' / icon_name))
    udp_menu.setIcon(icon)
    udp_menu.setStyleSheet(SVG_ICON_CONTEXT_MENU_STYLESHEET)
    udp_menu.setToolTipsVisible(True)

    udp_one_action = QAction(icon, 'Un port pour tous', udp_menu)
    udp_one_action.setToolTip('Demander un port une seule fois, puis pinger en UDP toutes les IP sélectionnées sur ce port.')

    def _do_udp_ping_multi() -> None:
        udp_port_ping_multi(parent, ip_addresses)

    udp_one_action.triggered.connect(_do_udp_ping_multi)
    udp_menu.addAction(udp_one_action)

    udp_individual_action = QAction(icon, 'Un port par IP', udp_menu)
    udp_individual_action.setToolTip('Demander un port différent pour chaque IP sélectionnée.')

    def _do_udp_ping_individual() -> None:
        for ip_address in ip_addresses:
            udp_port_ping(parent, ip_address)

    udp_individual_action.triggered.connect(_do_udp_ping_individual)
    udp_menu.addAction(udp_individual_action)

    ping_menu.addMenu(udp_menu)
    return udp_menu


def block_ip_as_range(parent: QWidget, ip_address: str) -> str | None:
    """Open the IP Range Builder dialog pre-filled with *ip_address* and add the result to the blocked IPs setting.

    Returns the raw range string that was added, or `None` if the user cancelled or the entry already exists.
    """
    dialog = IPRangeBuilderDialog(parent, initial_ip=ip_address)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None

    entry = dialog.result_entry()
    if not entry:
        return None

    if entry not in Settings.capture_blocked_ips:
        Settings.capture_blocked_ips = (*Settings.capture_blocked_ips, entry)
        Settings.rewrite_settings_file()
        Settings.rebuild_blocked_ip_ranges()

    return entry


def filter_player_isp(parent: QWidget, isp_name: str) -> str | None:
    """Prompt to add *isp_name* to the filtered ISPs setting.

    Returns the ISP string that was added, or `None` if the user cancelled or the entry already exists.
    """
    cleaned_name, success = QInputDialog.getText(
        parent,
        'Filter ISP / ASN',
        'Exclude players whose ISP or ASN matches this name from the session:\n(Case-insensitive substring match)',
        text=isp_name,
    )
    if not success:
        return None

    entry = cleaned_name.strip()
    if not entry:
        return None

    if entry not in Settings.capture_filtered_isps:
        Settings.capture_filtered_isps = (*Settings.capture_filtered_isps, entry)
        Settings.rewrite_settings_file()

    return entry
