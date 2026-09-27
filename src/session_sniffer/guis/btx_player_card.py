"""BTXSniffer player card ("Fiche joueur").

Scans every saved session log for one IP address and shows, in a single window:
- tab "Résumé": how many times you met the player, on how many different days, the total
  time spent together, the first and last encounter, the note / tag and the latest encounters;
- tab "Détails de l'IP": the network / lookup information already collected by the sniffer,
  which can be copied line by line or all at once.

Only one card is open at a time: opening another player replaces the current one.
"""

import ipaddress
import json
import threading
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QInputDialog,
    QMessageBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from session_sniffer.constants.local import RESOURCES_DIR_PATH, SESSIONS_LOGGING_DIR_PATH
from session_sniffer.constants.standard import LOCAL_TZ
from session_sniffer.guis.btx_notes import TAGS, PlayerLinks, PlayerNotes, add_tag_menu, edit_player_note
from session_sniffer.player.registry import PlayersRegistry

MAX_ENCOUNTERS_SHOWN = 50
_UNRESOLVED = {'', '...', 'N/A', 'None'}

# (section, [(session-log key, French label)])
IP_DETAIL_FIELDS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    (
        'Connexion',
        (
            ('IP Address', 'Adresse IP'),
            ('Hostname', "Nom d'hôte"),
            ('Ports', 'Ports'),
            ('First Port', 'Premier port'),
            ('Last Port', 'Dernier port'),
        ),
    ),
    (
        'Localisation (approximative)',
        (
            ('Continent', 'Continent'),
            ('Country', 'Pays'),
            ('Country Code', 'Code pays'),
            ('Region', 'Région'),
            ('City', 'Ville'),
            ('Time Zone', 'Fuseau horaire'),
            ('Currency', 'Devise'),
        ),
    ),
    (
        'Fournisseur',
        (
            ('ISP', 'FAI'),
            ('ASN / ISP', 'ASN / FAI'),
            ('Organization', 'Organisation'),
            ('AS', 'AS'),
            ('ASN', 'Nom AS'),
        ),
    ),
    (
        'Type de connexion',
        (
            ('Mobile', 'Réseau mobile'),
            ('VPN', 'VPN / Proxy'),
            ('Hosting', 'Hébergeur / serveur'),
        ),
    ),
)
_DETAIL_KEYS = {key for _section, fields in IP_DETAIL_FIELDS for key, _label in fields}


@dataclass
class Encounter:
    """One sniffer session in which the player was seen."""

    start: datetime
    end: datetime | None
    seconds: float
    usernames: list[str]
    ip: str = ''


@dataclass
class PlayerCardData:
    """Everything known about one IP across all session logs."""

    ip: str
    encounters: list[Encounter] = field(default_factory=list)
    usernames: list[str] = field(default_factory=list)
    ips: list[str] = field(default_factory=list)  # every IP linked to this player
    details_by_ip: dict[str, dict[str, object]] = field(default_factory=dict)
    # other IPs where one of the usernames was seen (possible new box / VPN): (ip, last seen, usernames)
    suggestions: list[tuple[str, datetime | None, list[str]]] = field(default_factory=list)

    @property
    def latest_ip(self) -> str:
        return self.encounters[0].ip if self.encounters and self.encounters[0].ip else self.ip

    @property
    def details(self) -> dict[str, object]:
        return self.details_by_ip.get(self.latest_ip) or self.details_by_ip.get(self.ip) or {'IP Address': self.ip}

    def ip_stats(self, ip: str) -> tuple[int, datetime | None]:
        """(number of encounters, last seen) for one of the linked IPs."""
        mine = [e for e in self.encounters if e.ip == ip]
        return len(mine), max(((e.end or e.start) for e in mine), default=None)

    @property
    def country(self) -> str:
        return _text(self.details.get('Country'))

    @property
    def city(self) -> str:
        return _text(self.details.get('City'))

    @property
    def isp(self) -> str:
        return _text(self.details.get('ASN / ISP')) or _text(self.details.get('ISP'))

    @property
    def total_seconds(self) -> float:
        return sum(e.seconds for e in self.encounters)

    @property
    def days(self) -> set[date]:
        return {e.start.date() for e in self.encounters}

    @property
    def first_seen(self) -> datetime | None:
        return min((e.start for e in self.encounters), default=None)

    @property
    def last_seen(self) -> datetime | None:
        return max(((e.end or e.start) for e in self.encounters), default=None)


def _text(value: object) -> str:
    if value is None or isinstance(value, bool):
        return ''
    text = str(value).strip()
    return '' if text in _UNRESOLVED else text


def _is_resolved(value: object) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (list, tuple)):
        return bool(value)
    return bool(_text(value))


def format_detail_value(value: object) -> str:
    """Format a lookup value for display ('Oui'/'Non' for booleans, lists joined)."""
    if isinstance(value, bool):
        return 'Oui' if value else 'Non'
    if isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value)
    return _text(value)


def _parse_dt(raw: object) -> datetime | None:
    if not isinstance(raw, str):
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return value.astimezone(LOCAL_TZ) if value.tzinfo else value.replace(tzinfo=LOCAL_TZ)


def _parse_seconds(raw: object) -> float:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return max(0.0, float(raw))
    return 0.0


def _str_list(raw: object) -> list[str]:
    return [str(x) for x in raw if str(x).strip()] if isinstance(raw, list) else []


def collect_player_card(ip: str, folder: Path = SESSIONS_LOGGING_DIR_PATH) -> PlayerCardData:
    """Scan every JSON session log under *folder* and gather the history of *ip* and of its linked IPs."""
    members = PlayerLinks.group_of(ip)
    member_set = set(members)
    card = PlayerCardData(ip=ip, ips=list(members))
    infos: dict[str, list[tuple[datetime, dict]]] = {member: [] for member in members}
    name_sightings: dict[str, dict[str, tuple[datetime, set[str]]]] = {}  # lower name -> ip -> (last seen, names)

    for json_file in folder.rglob('*.json'):
        try:
            data = json.loads(json_file.read_text(encoding='utf-8', errors='replace'))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        seen_in_file: set[str] = set()
        for section in ('connected', 'disconnected'):
            players = data.get(section)
            if not isinstance(players, dict):
                continue
            for player_ip, info in players.items():
                if not isinstance(info, dict):
                    continue
                player_ip = str(player_ip)  # noqa: PLW2901
                names = _str_list(info.get('Usernames'))
                start = _parse_dt(info.get('First Seen'))
                if start is None:
                    continue
                end = _parse_dt(info.get('Last Seen'))
                if names:
                    for name in names:
                        per_ip = name_sightings.setdefault(name.lower(), {})
                        last, known = per_ip.get(player_ip, (start, set()))
                        per_ip[player_ip] = (max(last, end or start), known | set(names))
                if player_ip not in member_set or player_ip in seen_in_file:
                    continue
                seen_in_file.add(player_ip)
                seconds = _parse_seconds(info.get('T. Session Time'))
                if not seconds and end is not None:
                    seconds = max(0.0, (end - start).total_seconds())
                card.encounters.append(Encounter(start=start, end=end, seconds=seconds, usernames=names, ip=player_ip))
                infos[player_ip].append((start, info))

    # lookup details per IP: oldest first, so the most recent resolved value wins
    for member, member_infos in infos.items():
        details: dict[str, object] = {}
        for _start, info in sorted(member_infos, key=lambda pair: pair[0]):
            for key in _DETAIL_KEYS:
                value = info.get(key)
                if _is_resolved(value):
                    details[key] = value
        details.setdefault('IP Address', member)
        card.details_by_ip[member] = details

    card.encounters.sort(key=lambda e: e.start, reverse=True)
    recent_first: dict[str, None] = {}
    for encounter in card.encounters:
        for name in encounter.usernames:
            recent_first.setdefault(name, None)
    card.usernames = list(recent_first)

    # same username seen on other IPs -> suggest linking them
    suggestions: dict[str, tuple[datetime, set[str]]] = {}
    for name in card.usernames:
        for other_ip, (last, names) in name_sightings.get(name.lower(), {}).items():
            if other_ip in member_set:
                continue
            previous = suggestions.get(other_ip)
            suggestions[other_ip] = (max(last, previous[0]) if previous else last, names | (previous[1] if previous else set()))
    card.suggestions = sorted(((sip, last, sorted(names)) for sip, (last, names) in suggestions.items()), key=lambda s: s[1] or datetime.min.replace(tzinfo=LOCAL_TZ), reverse=True)[:10]
    return card


def online_ip(ips: list[str]) -> str | None:
    """The IP among *ips* that is connected in the current session, if any."""
    for member in ips:
        player = PlayersRegistry.get_player_by_ip(member)
        if player is not None and PlayersRegistry.is_player_connected(player):
            return member
    return None


# ---------- formatting ----------

_MONTHS = ('janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.')


def format_duration(seconds: float) -> str:
    """Human-readable French duration: '2 h 05 min', '12 min', '45 s'."""
    seconds = int(seconds)
    days, rest = divmod(seconds, 86_400)
    hours, rest = divmod(rest, 3_600)
    minutes, secs = divmod(rest, 60)
    if days:
        return f'{days} j {hours} h {minutes:02d} min'
    if hours:
        return f'{hours} h {minutes:02d} min'
    if minutes:
        return f'{minutes} min'
    return f'{secs} s'


def format_date(value: datetime | None, *, with_time: bool = True) -> str:
    """'26 sept. 2026 à 20:48'."""
    if value is None:
        return '—'
    text = f'{value.day} {_MONTHS[value.month - 1]} {value.year}'
    return f'{text} à {value:%H:%M}' if with_time else text


def format_relative(value: datetime | None) -> str:
    """'aujourd'hui', 'hier', 'il y a 3 jours', 'il y a 2 mois'…"""
    if value is None:
        return ''
    now = datetime.now(tz=LOCAL_TZ)
    days = (now.date() - value.date()).days
    if days <= 0:
        delta = (now - value).total_seconds()
        if delta < 120:
            return "à l'instant"
        if delta < 3_600:
            return f'il y a {int(delta // 60)} min'
        return f'il y a {int(delta // 3_600)} h'
    if days == 1:
        return 'hier'
    if days < 30:
        return f'il y a {days} jours'
    if days < 365:
        return f'il y a {days // 30} mois'
    years = days // 365
    return f'il y a {years} an{"s" if years > 1 else ""}'


def ip_details_text(ip: str, names: list[str], details: dict[str, object]) -> str:
    """Plain-text version of the 'Détails de l'IP' tab (for the clipboard)."""
    lines = [f'Détails de l\'IP {ip} — {", ".join(names) or "pseudo inconnu"}']
    for section, fields in IP_DETAIL_FIELDS:
        rows = [(label, format_detail_value(details.get(key))) for key, label in fields]
        rows = [(label, value) for label, value in rows if value]
        if rows:
            lines.append('')
            lines.append(f'[{section}]')
            lines += [f'{label} : {value}' for label, value in rows]
    return '\n'.join(lines)


# ---------- dialog ----------


class _Loader(QObject):
    loaded = Signal(object)


class _StatTile(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName('btxStatTile')
        self.setStyleSheet(
            '#btxStatTile { border: 1px solid rgba(255, 43, 214, 0.45); border-radius: 8px;'
            ' background: rgba(255, 43, 214, 0.06); }',
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        caption = QLabel(title)
        caption.setStyleSheet('color: #b9a3c9; font-size: 11px; border: none; background: transparent;')
        self.value = QLabel('…')
        self.value.setStyleSheet('color: #3ff0ff; font-size: 18px; font-weight: 600; border: none; background: transparent;')
        self.sub = QLabel('')
        self.sub.setStyleSheet('color: #b9a3c9; font-size: 11px; border: none; background: transparent;')
        layout.addWidget(caption)
        layout.addWidget(self.value)
        layout.addWidget(self.sub)

    def set(self, value: str, sub: str = '') -> None:
        self.value.setText(value)
        self.sub.setText(sub)
        self.sub.setVisible(bool(sub))


def _readonly_table(columns: list[str], parent: QWidget) -> QTableWidget:
    table = QTableWidget(0, len(columns), parent)
    table.setHorizontalHeaderLabels(columns)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setWordWrap(False)
    v_header = table.verticalHeader()
    if v_header:
        v_header.setVisible(False)
    return table


class PlayerCardDialog(QDialog):
    """Window showing the full history of one player (only one open at a time)."""

    _instance: 'PlayerCardDialog | None' = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ip = ''
        self._names: list[str] = []
        self._on_changed: Callable[[], object] | None = None
        self._data: PlayerCardData | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, on=False)
        self.setWindowIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'player.svg')))
        self.resize(640, 680)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        # header: name + tag + ip (common to both tabs)
        self._title = QLabel()
        self._title.setTextFormat(Qt.TextFormat.RichText)
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._title)
        self._subtitle = QLabel()
        self._subtitle.setStyleSheet('color: #b9a3c9;')
        self._subtitle.setWordWrap(True)
        self._subtitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._subtitle)

        self._tabs = QTabWidget(self)
        root.addWidget(self._tabs, 1)
        self._tabs.addTab(self._build_summary_tab(), QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'player.svg')), 'Résumé')
        self._tabs.addTab(self._build_details_tab(), QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'globe.svg')), "Détails de l'IP")
        self._tabs.addTab(self._build_ips_tab(), QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'link.svg')), 'Adresses IP')

        # buttons
        buttons = QHBoxLayout()
        copy_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'copy.svg')), 'Copier')
        copy_menu = QMenu(copy_btn)
        copy_menu.addAction("Copier l'IP", lambda: QGuiApplication.clipboard().setText(self._current_ip()))
        copy_menu.addAction('Copier le pseudo', lambda: QGuiApplication.clipboard().setText(', '.join(self._names)))
        copy_menu.addSeparator()
        copy_menu.addAction('Copier la fiche (résumé)', self._copy_summary)
        copy_menu.addAction("Copier les détails de l'IP", self._copy_details)
        copy_btn.setMenu(copy_menu)
        note_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'edit.svg')), 'Note…')
        note_btn.clicked.connect(self._edit_note)
        tag_btn = QPushButton('Étiquette')
        tag_btn.clicked.connect(lambda: self._show_tag_menu(tag_btn))
        refresh_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'refresh.svg')), 'Actualiser')
        refresh_btn.clicked.connect(self._load)
        close_btn = QPushButton('Fermer')
        close_btn.clicked.connect(self.close)
        for button in (copy_btn, note_btn, tag_btn, refresh_btn):
            buttons.addWidget(button)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        root.addLayout(buttons)

        self._loader = _Loader(self)
        self._loader.loaded.connect(self._apply)

        # live "connected now" status of the linked IPs
        self._status_timer = QTimer(self)
        self._status_timer.setInterval(3000)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start()

    # ----- tabs -----

    def _build_summary_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)
        self._tile_count = _StatTile('Croisé')
        self._tile_days = _StatTile('Jours différents')
        self._tile_total = _StatTile('Temps total ensemble')
        self._tile_avg = _StatTile('Moyenne par session')
        self._tile_first = _StatTile('Première rencontre')
        self._tile_last = _StatTile('Dernière rencontre')
        self._tiles = (self._tile_count, self._tile_days, self._tile_total, self._tile_avg, self._tile_first, self._tile_last)
        for i, tile in enumerate(self._tiles):
            grid.addWidget(tile, i // 3, i % 3)
        layout.addLayout(grid)

        self._note = QLabel()
        self._note.setWordWrap(True)
        self._note.setTextFormat(Qt.TextFormat.PlainText)
        self._note.setStyleSheet('padding: 8px; border: 1px dashed rgba(63, 240, 255, 0.45); border-radius: 6px;')
        layout.addWidget(self._note)

        encounters_label = QLabel('Dernières rencontres')
        encounters_label.setStyleSheet('font-weight: 600;')
        layout.addWidget(encounters_label)
        self._table = _readonly_table(['Date', 'Durée', 'Pseudo', 'IP'], page)
        self._table.setAlternatingRowColors(True)
        h_header = self._table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table, 1)
        return page

    def _build_details_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        self._details_ip_row = QWidget()
        ip_row = QHBoxLayout(self._details_ip_row)
        ip_row.setContentsMargins(0, 0, 0, 0)
        ip_row.addWidget(QLabel('IP :'))
        self._details_ip = QComboBox()
        self._details_ip.currentIndexChanged.connect(self._on_details_ip_changed)
        ip_row.addWidget(self._details_ip, 1)
        layout.addWidget(self._details_ip_row)

        self._details = _readonly_table(['Info', 'Valeur'], page)
        self._details.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._details.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._details.customContextMenuRequested.connect(self._details_menu)
        self._details.doubleClicked.connect(lambda index: self._copy_detail_row(index.row()))
        h_header = self._details.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self._details, 1)

        bottom = QHBoxLayout()
        hint = QLabel('Double-clic ou clic droit pour copier une ligne. Infos récupérées par BTXSniffer pendant tes sessions.')
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #b9a3c9; font-size: 11px;')
        copy_all = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'copy.svg')), 'Tout copier')
        copy_all.clicked.connect(self._copy_details)
        bottom.addWidget(hint, 1)
        bottom.addWidget(copy_all)
        layout.addLayout(bottom)
        return page

    def _build_ips_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(8)
        info = QLabel(
            "Si ce joueur change d'IP (nouvelle box, VPN…), relie ses IP : une seule fiche, "
            'la même note et la même étiquette sur toutes ses IP, et tu vois sur laquelle il est connecté.',
        )
        info.setWordWrap(True)
        info.setStyleSheet('color: #b9a3c9;')
        layout.addWidget(info)

        self._ips = _readonly_table(['IP', 'Statut', 'Rencontres', 'Dernière vue'], page)
        self._ips.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._ips.doubleClicked.connect(lambda index: self._show_ip_details(index.row()))
        h_header = self._ips.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._ips, 1)

        row = QHBoxLayout()
        link_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'link.svg')), 'Relier une autre IP…')
        link_btn.clicked.connect(self._ask_link)
        self._unlink_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'remove.svg')), "Délier l'IP sélectionnée")
        self._unlink_btn.clicked.connect(self._unlink_selected)
        row.addWidget(link_btn)
        row.addWidget(self._unlink_btn)
        row.addStretch(1)
        layout.addLayout(row)

        self._suggestions = QLabel()
        self._suggestions.setWordWrap(True)
        self._suggestions.setTextFormat(Qt.TextFormat.RichText)
        self._suggestions.linkActivated.connect(self._link_from_suggestion)
        self._suggestions.setStyleSheet('padding: 8px; border: 1px dashed rgba(63, 240, 255, 0.45); border-radius: 6px;')
        layout.addWidget(self._suggestions)
        return page

    # ----- public -----

    @classmethod
    def open_for(
        cls,
        ip: str,
        names: list[str] | None = None,
        parent: QWidget | None = None,
        on_changed: Callable[[], object] | None = None,
    ) -> 'PlayerCardDialog':
        """Show the card of *ip*, replacing the player shown in the already-open card if any."""
        dialog = cls._instance
        if dialog is not None:
            try:
                dialog.isVisible()
            except RuntimeError:  # underlying C++ object already deleted
                dialog = None
        if dialog is None:
            dialog = cls(parent)
            cls._instance = dialog
            dialog.destroyed.connect(cls._forget)
        dialog.set_player(ip, names, on_changed)
        if dialog.isMinimized():
            dialog.showNormal()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    @classmethod
    def _forget(cls, *_args: object) -> None:
        cls._instance = None

    def set_player(self, ip: str, names: list[str] | None = None, on_changed: Callable[[], object] | None = None) -> None:
        """Switch the card to another player."""
        self._ip = ip
        self._names = list(names or [])
        self._on_changed = on_changed
        self._data = None
        self._tabs.setCurrentIndex(0)
        self.setWindowTitle(f'Fiche joueur — {", ".join(self._names) or ip}')
        self._table.setRowCount(0)
        self._details.setRowCount(0)
        self._ips.setRowCount(0)
        self._suggestions.setText('')
        self._render_header()
        self._load()

    # ----- loading -----

    def _load(self) -> None:
        for tile in self._tiles:
            tile.set('…')
        loader = self._loader
        ip = self._ip

        def work() -> None:
            try:
                data = collect_player_card(ip)
            except Exception:  # noqa: BLE001 - never crash the UI because of a bad log file
                data = PlayerCardData(ip=ip)
            with suppress(RuntimeError):
                loader.loaded.emit(data)

        threading.Thread(target=work, name='BTXPlayerCard', daemon=True).start()

    def _apply(self, data: object) -> None:
        if not isinstance(data, PlayerCardData) or data.ip != self._ip:
            return  # result of a player that was replaced in the meantime
        self._data = data
        if data.usernames:
            self._names = data.usernames
            self.setWindowTitle(f'Fiche joueur — {", ".join(self._names[:3])}')
        count = len(data.encounters)
        self._tile_count.set(f'{count} fois', 'session' if count == 1 else 'sessions')
        self._tile_days.set(str(len(data.days)))
        self._tile_total.set(format_duration(data.total_seconds) if count else '—')
        self._tile_avg.set(format_duration(data.total_seconds / count) if count else '—')
        self._tile_first.set(format_date(data.first_seen, with_time=False), format_relative(data.first_seen))
        self._tile_last.set(format_date(data.last_seen, with_time=False), format_relative(data.last_seen))

        self._table.setRowCount(0)
        for encounter in data.encounters[:MAX_ENCOUNTERS_SHOWN]:
            row = self._table.rowCount()
            self._table.insertRow(row)
            date_item = QTableWidgetItem(format_date(encounter.start))
            date_item.setToolTip(format_relative(encounter.start))
            duration_item = QTableWidgetItem(format_duration(encounter.seconds))
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            names_item = QTableWidgetItem(', '.join(encounter.usernames) or '—')
            self._table.setItem(row, 0, date_item)
            self._table.setItem(row, 1, duration_item)
            self._table.setItem(row, 2, names_item)
            self._table.setItem(row, 3, QTableWidgetItem(encounter.ip))
        if not data.encounters:
            self._table.insertRow(0)
            self._table.setItem(0, 0, QTableWidgetItem('Aucune rencontre enregistrée pour ce joueur.'))
            self._table.setSpan(0, 0, 1, 4)
        self._table.setColumnHidden(3, len(data.ips) < 2)  # noqa: PLR2004
        self._table.clearSelection()
        self._table.setCurrentCell(-1, -1)

        # details: one entry per linked IP (connected one, else most recent, first)
        current = online_ip(data.ips) or data.latest_ip
        ordered = [current] + [member for member in data.ips if member != current]
        self._details_ip.blockSignals(True)  # noqa: FBT003
        self._details_ip.clear()
        for member in ordered:
            self._details_ip.addItem(member, member)
        self._details_ip.blockSignals(False)  # noqa: FBT003
        self._details_ip_row.setVisible(len(ordered) > 1)
        self._fill_details(data.details_by_ip.get(current, {'IP Address': current}))

        self._fill_ips()
        self._render_header()

    def _on_details_ip_changed(self, _index: int) -> None:
        member = self._details_ip.currentData()
        if self._data is not None and member:
            self._fill_details(self._data.details_by_ip.get(member, {'IP Address': member}))

    def _current_ip(self) -> str:
        """Connected IP if the player is online, else the most recent one."""
        if self._data is None:
            return self._ip
        return online_ip(self._data.ips) or self._data.latest_ip

    def _selected_details_ip(self) -> str:
        return str(self._details_ip.currentData() or (self._data.latest_ip if self._data else self._ip))

    def _show_ip_details(self, row: int) -> None:
        item = self._ips.item(row, 0)
        if item is None:
            return
        index = self._details_ip.findData(item.text())
        if index >= 0:
            self._details_ip.setCurrentIndex(index)
        self._tabs.setCurrentIndex(1)

    # ----- linked IPs -----

    def _fill_ips(self) -> None:
        data = self._data
        if data is None:
            return
        self._tabs.setTabText(2, f'Adresses IP ({len(data.ips)})')
        self._ips.setRowCount(0)
        connected = online_ip(data.ips)
        for member in data.ips:
            row = self._ips.rowCount()
            self._ips.insertRow(row)
            count, last = data.ip_stats(member)
            ip_item = QTableWidgetItem(member)
            status = QTableWidgetItem('🟢 Connecté maintenant' if member == connected else ('Dernière IP connue' if member == data.latest_ip else '—'))
            if member == connected:
                status.setForeground(QColor('#39ff88'))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._ips.setItem(row, 0, ip_item)
            self._ips.setItem(row, 1, status)
            self._ips.setItem(row, 2, count_item)
            self._ips.setItem(row, 3, QTableWidgetItem(format_date(last) if last else '—'))
        self._unlink_btn.setEnabled(len(data.ips) > 1)

        if data.suggestions:
            links = []
            for sip, last, names in data.suggestions[:5]:
                when = format_relative(last) if last else ''
                links.append(f'<a href="{sip}" style="color:#3ff0ff;">{sip}</a> ({_escape(", ".join(names[:2]))}{" · " + when if when else ""})')
            self._suggestions.setText('💡 <b>Même pseudo vu sur d\'autres IP</b> — clique pour les relier :<br>' + '<br>'.join(links))
            self._suggestions.setVisible(True)
        else:
            self._suggestions.setVisible(False)

    def _refresh_status(self) -> None:
        if self._data is None or not self.isVisible():
            return
        self._render_header()
        connected = online_ip(self._data.ips)
        for row in range(self._ips.rowCount()):
            ip_item, status = self._ips.item(row, 0), self._ips.item(row, 1)
            if ip_item is None or status is None:
                continue
            is_on = ip_item.text() == connected
            status.setText('🟢 Connecté maintenant' if is_on else ('Dernière IP connue' if ip_item.text() == self._data.latest_ip else '—'))
            status.setForeground(QColor('#39ff88') if is_on else self._ips.palette().text().color())

    def _link(self, other_ip: str) -> None:
        other_ip = other_ip.strip()
        try:
            ipaddress.ip_address(other_ip)
        except ValueError:
            QMessageBox.warning(self, 'Relier une IP', f'« {other_ip} » n\'est pas une adresse IP valide.')
            return
        if self._data is not None and other_ip in self._data.ips:
            return
        PlayerLinks.link(self._ip, other_ip)
        self._changed()
        self._load()
        self._tabs.setCurrentIndex(2)

    def _link_from_suggestion(self, href: str) -> None:
        self._link(href)

    def _ask_link(self) -> None:
        choices = [f'{sip}   —   {", ".join(names[:2])}' for sip, _last, names in (self._data.suggestions if self._data else [])]
        text, ok = QInputDialog.getItem(
            self,
            'Relier une IP',
            "IP à relier à ce joueur (tape-la ou choisis une IP où son pseudo a été vu) :",
            choices,
            0,
            True,  # noqa: FBT003 - editable
        )
        if ok and text.strip():
            self._link(text.split()[0])

    def _unlink_selected(self) -> None:
        row = self._ips.currentRow()
        item = self._ips.item(row, 0) if row >= 0 else None
        if item is None:
            QMessageBox.information(self, 'Délier une IP', 'Choisis une IP dans la liste.')
            return
        target = item.text()
        PlayerLinks.unlink(target)
        if target == self._ip and self._data is not None:
            remaining = [member for member in self._data.ips if member != target]
            if remaining:
                self._ip = remaining[0]
        self._changed()
        self._load()

    def _fill_details(self, details: dict[str, object]) -> None:
        table = self._details
        table.clearSpans()
        table.setRowCount(0)
        section_font = QFont(table.font())
        section_font.setBold(True)
        for section, fields in IP_DETAIL_FIELDS:
            rows = [(label, format_detail_value(details.get(key))) for key, label in fields]
            rows = [(label, value) for label, value in rows if value]
            if not rows:
                continue
            header_row = table.rowCount()
            table.insertRow(header_row)
            header = QTableWidgetItem(section)
            header.setFont(section_font)
            header.setForeground(QColor('#ff2bd6'))
            header.setFlags(Qt.ItemFlag.ItemIsEnabled)
            header.setData(Qt.ItemDataRole.UserRole, 'section')
            table.setItem(header_row, 0, header)
            table.setSpan(header_row, 0, 1, 2)
            for label, value in rows:
                row = table.rowCount()
                table.insertRow(row)
                label_item = QTableWidgetItem(label)
                label_item.setForeground(QColor('#b9a3c9'))
                value_item = QTableWidgetItem(value)
                value_item.setToolTip(value)
                table.setItem(row, 0, label_item)
                table.setItem(row, 1, value_item)
        if table.rowCount() == 0:
            table.insertRow(0)
            table.setItem(0, 0, QTableWidgetItem("Pas encore d'infos pour cette IP."))
            table.setSpan(0, 0, 1, 2)

    # ----- details copy -----

    def _detail_row(self, row: int) -> tuple[str, str] | None:
        label = self._details.item(row, 0)
        value = self._details.item(row, 1)
        if label is None or value is None or label.data(Qt.ItemDataRole.UserRole) == 'section':
            return None
        return label.text(), value.text()

    def _copy_detail_row(self, row: int) -> None:
        pair = self._detail_row(row)
        if pair is not None:
            QGuiApplication.clipboard().setText(pair[1])

    def _details_menu(self, pos: QPoint) -> None:
        index = self._details.indexAt(pos)
        rows = sorted({i.row() for i in self._details.selectedIndexes()} | ({index.row()} if index.isValid() else set()))
        pairs = [pair for row in rows if (pair := self._detail_row(row)) is not None]
        menu = QMenu(self)
        if index.isValid() and (pair := self._detail_row(index.row())) is not None:
            menu.addAction(f'Copier la valeur  ({pair[1][:40]})', lambda: QGuiApplication.clipboard().setText(pair[1]))
            menu.addAction('Copier la ligne', lambda: QGuiApplication.clipboard().setText(f'{pair[0]} : {pair[1]}'))
        if len(pairs) > 1:
            menu.addAction(
                f'Copier les {len(pairs)} lignes sélectionnées',
                lambda: QGuiApplication.clipboard().setText('\n'.join(f'{a} : {b}' for a, b in pairs)),
            )
        if menu.actions():
            menu.addSeparator()
        menu.addAction('Tout copier', self._copy_details)
        menu.exec(self._details.viewport().mapToGlobal(pos))

    def _copy_details(self) -> None:
        member = self._selected_details_ip()
        details = self._data.details_by_ip.get(member, {'IP Address': member}) if self._data is not None else {'IP Address': self._ip}
        QGuiApplication.clipboard().setText(ip_details_text(member, self._names, details))

    # ----- header / note / tag -----

    def _render_header(self) -> None:
        tag = PlayerNotes.get_tag(self._ip)
        names = ', '.join(self._names) if self._names else 'Pseudo inconnu'
        badge = ''
        if tag in TAGS:
            label, color, _badge = TAGS[tag]
            badge = f'&nbsp;&nbsp;<span style="color:{color}; font-size:13px;">● {label}</span>'
        self._title.setText(f'<span style="font-size:20px; font-weight:700; color:#ff2bd6;">{_escape(names)}</span>{badge}')

        parts = [f'IP : {self._ip}']
        if self._data is not None:
            connected = online_ip(self._data.ips)
            if connected:
                parts = [f'🟢 Connecté maintenant sur {connected}']
            else:
                parts = [f'Hors ligne · dernière IP : {self._data.latest_ip}']
            if len(self._data.ips) > 1:
                parts.append(f'{len(self._data.ips)} IP reliées')
            shown = self._data.details_by_ip.get(connected or self._data.latest_ip, {})
            place = ', '.join(p for p in (_text(shown.get('City')), _text(shown.get('Country'))) if p)
            if place:
                parts.append(f'Lieu (approx.) : {place}')
            isp = _text(shown.get('ASN / ISP')) or _text(shown.get('ISP'))
            if isp:
                parts.append(f'FAI : {isp}')
            if len(self._data.usernames) > 1:
                parts.append(f'{len(self._data.usernames)} pseudos connus')
        self._subtitle.setText('   •   '.join(parts))

        note = PlayerNotes.get(self._ip)
        self._note.setText(f'📝 {note}' if note else '📝 Pas de note. Clique sur « Note… » pour en ajouter une.')

    def _edit_note(self) -> None:
        if edit_player_note(self, self._ip, self._names):
            self._changed()

    def _show_tag_menu(self, anchor: QPushButton) -> None:
        menu = QMenu(self)
        sub = add_tag_menu(menu, self._ip, self._names, self._changed)
        sub.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))

    def _changed(self) -> None:
        self._render_header()
        if self._on_changed is not None:
            with suppress(RuntimeError):
                self._on_changed()

    def _copy_summary(self) -> None:
        data = self._data
        lines = [f'Joueur : {", ".join(self._names) or "?"} ({self._ip})']
        tag = PlayerNotes.get_tag(self._ip)
        if tag in TAGS:
            lines.append(f'Étiquette : {TAGS[tag][0]}')
        if data is not None and data.encounters:
            lines += [
                f'Croisé {len(data.encounters)} fois, sur {len(data.days)} jour(s) différent(s)',
                f'Temps total ensemble : {format_duration(data.total_seconds)}',
                f'Première rencontre : {format_date(data.first_seen)}',
                f'Dernière rencontre : {format_date(data.last_seen)}',
            ]
        note = PlayerNotes.get(self._ip)
        if note:
            lines.append(f'Note : {note}')
        QGuiApplication.clipboard().setText('\n'.join(lines))


def _escape(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def open_player_card(
    parent: QWidget | None,
    ip: str,
    names: list[str] | None = None,
    on_changed: Callable[[], object] | None = None,
) -> None:
    """Convenience helper used by the context menus."""
    PlayerCardDialog.open_for(ip, names, parent, on_changed)
