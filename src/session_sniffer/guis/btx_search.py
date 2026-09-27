"""BTXSniffer global player search (Ctrl+F).

Searches by username, IP, country, note or tag through:
- the players of the current session (live),
- every player ever met (session logs, indexed in the background),
- the personal notes / tags.
Linked IPs (same player) are shown as a single result. Also used by the in-game mini window.
"""

import json
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from session_sniffer.constants.local import RESOURCES_DIR_PATH, SESSIONS_LOGGING_DIR_PATH
from session_sniffer.constants.standard import LOCAL_TZ
from session_sniffer.guis.btx_notes import TAGS, PlayerLinks, PlayerNotes, tag_color
from session_sniffer.player.registry import PlayersRegistry

TAG_ORDER = {'dangereux': 0, 'relou': 1, 'ami': 2}


def tag_rank(ip: str) -> int:
    """Sort key: Dangereux, then Relou, then Ami, then untagged."""
    return TAG_ORDER.get(PlayerNotes.get_tag(ip), len(TAG_ORDER))


def _timestamp(value: object) -> float:
    if isinstance(value, datetime):
        with suppress(OverflowError, OSError, ValueError):
            return value.timestamp()
    return 0.0


# ---------- index of every player ever met ----------


@dataclass
class IndexedPlayer:
    """What the session logs know about one IP."""

    ip: str
    usernames: list[str] = field(default_factory=list)
    last_seen: float = 0.0
    country: str = ''


class _IndexSignals(QObject):
    updated = Signal()


class PlayerIndex:
    """Background index of the session logs (rebuilt when older than MAX_AGE seconds)."""

    MAX_AGE = 90.0
    signals: _IndexSignals | None = None
    _lock = threading.Lock()
    _players: dict[str, IndexedPlayer] = {}  # noqa: RUF012
    _built_at = 0.0
    _building = False

    @classmethod
    def _signals(cls) -> _IndexSignals:
        if cls.signals is None:
            cls.signals = _IndexSignals()
        return cls.signals

    @classmethod
    def is_ready(cls) -> bool:
        return cls._built_at > 0

    @classmethod
    def ensure_fresh(cls) -> None:
        """Start a background rebuild if the index is missing or old."""
        signals = cls._signals()
        with cls._lock:
            if cls._building or time.monotonic() - cls._built_at < cls.MAX_AGE and cls._built_at:
                return
            cls._building = True

        def work() -> None:
            players: dict[str, IndexedPlayer] = {}
            with suppress(OSError):
                for json_file in SESSIONS_LOGGING_DIR_PATH.rglob('*.json'):
                    try:
                        data = json.loads(json_file.read_text(encoding='utf-8', errors='replace'))
                    except (OSError, ValueError):
                        continue
                    if not isinstance(data, dict):
                        continue
                    for section in ('connected', 'disconnected'):
                        section_players = data.get(section)
                        if not isinstance(section_players, dict):
                            continue
                        for ip, info in section_players.items():
                            if isinstance(info, dict):
                                cls._merge(players, str(ip), info)
            with cls._lock:
                cls._players = players
                cls._built_at = time.monotonic()
                cls._building = False
            with suppress(RuntimeError):
                signals.updated.emit()

        threading.Thread(target=work, name='BTXPlayerIndex', daemon=True).start()

    @staticmethod
    def _merge(players: dict[str, IndexedPlayer], ip: str, info: dict) -> None:
        seen = 0.0
        raw = info.get('Last Seen') or info.get('First Seen')
        if isinstance(raw, str):
            with suppress(ValueError):
                parsed = datetime.fromisoformat(raw)
                seen = (parsed if parsed.tzinfo else parsed.replace(tzinfo=LOCAL_TZ)).timestamp()
        entry = players.get(ip)
        if entry is None:
            entry = players[ip] = IndexedPlayer(ip=ip)
        names = info.get('Usernames')
        if isinstance(names, list):
            for name in names:
                name = str(name).strip()  # noqa: PLW2901
                if name and name not in entry.usernames:
                    entry.usernames.append(name)
        if seen >= entry.last_seen:
            entry.last_seen = seen
            country = info.get('Country')
            if isinstance(country, str) and country not in {'', '...', 'N/A'}:
                entry.country = country

    @classmethod
    def snapshot(cls) -> dict[str, IndexedPlayer]:
        with cls._lock:
            return dict(cls._players)


# ---------- search ----------


@dataclass
class SearchResult:
    """One player (possibly several linked IPs)."""

    ip: str  # representative IP (connected one first)
    ips: list[str]
    usernames: list[str]
    online: bool
    in_session: bool
    last_seen: float
    country: str
    port: int | None = None


def search_players(text: str, *, limit: int = 50, include_history: bool = True, exclude_ips: set[str] | None = None) -> list[SearchResult]:
    """Find players matching *text* (username, IP, country, note, tag)."""
    text = text.strip().lower()
    if not text:
        return []
    PlayerIndex.ensure_fresh()
    exclude_ips = exclude_ips or set()

    # gather everything we know, per IP
    known: dict[str, dict] = {}
    if include_history:
        for ip, indexed in PlayerIndex.snapshot().items():
            known[ip] = {'names': list(indexed.usernames), 'seen': indexed.last_seen, 'country': indexed.country, 'online': False, 'session': False, 'port': None}
    for player in PlayersRegistry.get_all_players():
        entry = known.setdefault(player.ip, {'names': [], 'seen': 0.0, 'country': '', 'online': False, 'session': False, 'port': None})
        for name in player.usernames:
            if name not in entry['names']:
                entry['names'].insert(0, name)
        entry['seen'] = max(entry['seen'], _timestamp(player.datetime.last_seen))
        entry['online'] = PlayersRegistry.is_player_connected(player)
        entry['session'] = True
        entry['port'] = getattr(getattr(player, 'ports', None), 'last', None)
        country = str(player.iplookup.geolite2.country)
        if country not in {'', '...', 'N/A', 'None'}:
            entry['country'] = country
    if include_history:
        for ip in PlayerNotes.search(text):
            known.setdefault(ip, {'names': [], 'seen': 0.0, 'country': '', 'online': False, 'session': False, 'port': None})

    # match, then fold linked IPs into one result
    groups: dict[tuple[str, ...], list[str]] = {}
    for ip, entry in known.items():
        haystack = ' '.join([ip, *entry['names'], entry['country'], PlayerNotes.search_text(ip)]).lower()
        if text in haystack:
            members = PlayerLinks.group_of(ip)
            groups.setdefault(tuple(sorted(members)), members)

    results: list[SearchResult] = []
    for members in groups.values():
        infos = [(ip, known[ip]) for ip in members if ip in known]
        if not infos:
            infos = [(members[0], {'names': [], 'seen': 0.0, 'country': '', 'online': False, 'session': False, 'port': None})]
        infos.sort(key=lambda pair: (not pair[1]['online'], not pair[1]['session'], -pair[1]['seen']))
        rep_ip, rep = infos[0]
        if rep_ip in exclude_ips:
            continue
        names: list[str] = []
        for _ip, info in infos:
            names += [n for n in info['names'] if n not in names]
        results.append(
            SearchResult(
                ip=rep_ip,
                ips=list(members),
                usernames=names,
                online=rep['online'],
                in_session=rep['session'],
                last_seen=max(info['seen'] for _ip, info in infos),
                country=next((info['country'] for _ip, info in infos if info['country']), ''),
                port=rep['port'],
            ),
        )
    results.sort(key=lambda r: (not r.online, tag_rank(r.ip), -r.last_seen))
    return results[:limit]


def format_last_seen(timestamp: float) -> str:
    if not timestamp:
        return ''
    seen = datetime.fromtimestamp(timestamp, tz=LOCAL_TZ)
    days = (datetime.now(tz=LOCAL_TZ).date() - seen.date()).days
    if days <= 0:
        return f"aujourd'hui {seen:%H:%M}"
    if days == 1:
        return f'hier {seen:%H:%M}'
    return f'{seen:%d/%m/%Y}'


def result_text(result: SearchResult) -> str:
    """One-line label (+ note line) used by the search window and the mini window."""
    tag = PlayerNotes.get_tag(result.ip)
    badge = f'{TAGS[tag][2]} ' if tag in TAGS else ''
    names = ', '.join(result.usernames[:3]) or result.ip
    status = '🟢 en ligne' if result.online else ('🔴 parti' if result.in_session else f'vu {format_last_seen(result.last_seen)}')
    extra = f'  (+{len(result.ips) - 1} IP)' if len(result.ips) > 1 else ''
    line = f'{badge}{names}  ·  {result.ip}{extra}  ·  {status}'
    note = PlayerNotes.get(result.ip)
    if note:
        short = note.replace('\n', ' ')
        line += f'\n      📝 {short if len(short) <= 60 else short[:59] + "…"}'  # noqa: PLR2004
    return line


# ---------- window ----------


class GlobalSearchDialog(QDialog):
    """Ctrl+F: find any player (session, history, notes) and open their card."""

    _instance: 'GlobalSearchDialog | None' = None

    def __init__(self, parent: QWidget | None, open_card: Callable[[str, list[str]], None]) -> None:
        super().__init__(parent)
        self._open_card = open_card
        self.setWindowTitle('Rechercher un joueur')
        self.setWindowIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'search.svg')))
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, on=False)
        self.resize(620, 480)

        layout = QVBoxLayout(self)
        self._input = QLineEdit()
        self._input.setPlaceholderText('Pseudo, IP, pays, note ou étiquette (ex. « dangereux »)…')
        self._input.setClearButtonEnabled(True)
        self._input.textChanged.connect(lambda _t: self._debounce.start())
        self._input.returnPressed.connect(self._open_first)
        layout.addWidget(self._input)

        self._status = QLabel()
        self._status.setStyleSheet('color: #b9a3c9; font-size: 11px;')
        layout.addWidget(self._status)

        self._list = QListWidget()
        self._list.setWordWrap(True)
        self._list.itemActivated.connect(self._open_item)
        layout.addWidget(self._list, 1)

        hint = QLabel('Entrée ou double-clic : ouvrir la fiche du joueur.')
        hint.setStyleSheet('color: #b9a3c9; font-size: 11px;')
        layout.addWidget(hint)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(150)
        self._debounce.timeout.connect(self._run)
        PlayerIndex._signals().updated.connect(self._run)  # noqa: SLF001
        PlayerIndex.ensure_fresh()
        self._run()

    @classmethod
    def open(cls, parent: QWidget | None, open_card: Callable[[str, list[str]], None]) -> None:  # noqa: A003
        dialog = cls._instance
        if dialog is not None:
            try:
                dialog.isVisible()
            except RuntimeError:
                dialog = None
        if dialog is None:
            dialog = cls._instance = cls(parent, open_card)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        dialog._input.setFocus()  # noqa: SLF001
        dialog._input.selectAll()  # noqa: SLF001

    def _run(self) -> None:
        with suppress(RuntimeError):
            text = self._input.text().strip()
            self._list.clear()
            loading = '' if PlayerIndex.is_ready() else '  (chargement de l\'historique…)'
            if not text:
                self._status.setText(f'Tape au moins une lettre.{loading}')
                return
            results = search_players(text)
            self._status.setText(f'{len(results)} joueur(s) trouvé(s){loading}')
            for result in results:
                item = QListWidgetItem(result_text(result))
                color = tag_color(result.ip)
                if color:
                    item.setForeground(QColor(color))
                item.setToolTip('IP : ' + ', '.join(result.ips))
                item.setData(Qt.ItemDataRole.UserRole, (result.ip, result.usernames))
                self._list.addItem(item)
            if results:
                self._list.setCurrentRow(0)

    def _open_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self._open_card(data[0], list(data[1]))

    def _open_first(self) -> None:
        item = self._list.currentItem() or self._list.item(0)
        if item is not None:
            self._open_item(item)


def install_global_search(window: QWidget, open_card: Callable[[str, list[str]], None]) -> QShortcut:
    """Ctrl+F anywhere in *window* opens the player search."""
    shortcut = QShortcut(QKeySequence('Ctrl+F'), window)
    shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
    shortcut.activated.connect(lambda: GlobalSearchDialog.open(window, open_card))
    return shortcut
