"""BTXSniffer player card ("Fiche joueur").

Scans every saved session log for one IP address and shows, in a single window:
how many times you met the player, on how many different days, the total time spent
together, the first and last encounter, the known usernames, the personal note / tag,
and the list of the latest encounters.
"""

import json
import threading
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QVBoxLayout,
    QWidget,
)

from session_sniffer.constants.local import RESOURCES_DIR_PATH, SESSIONS_LOGGING_DIR_PATH
from session_sniffer.constants.standard import LOCAL_TZ
from session_sniffer.guis.btx_notes import TAGS, PlayerNotes, add_tag_menu, edit_player_note

MAX_ENCOUNTERS_SHOWN = 50
_UNRESOLVED = {'', '...', 'N/A'}


@dataclass
class Encounter:
    """One sniffer session in which the player was seen."""

    start: datetime
    end: datetime | None
    seconds: float
    usernames: list[str]


@dataclass
class PlayerCardData:
    """Everything known about one IP across all session logs."""

    ip: str
    encounters: list[Encounter] = field(default_factory=list)
    usernames: list[str] = field(default_factory=list)
    country: str = ''
    city: str = ''
    isp: str = ''

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
    """Scan every JSON session log under *folder* and gather the history of *ip*."""
    card = PlayerCardData(ip=ip)
    latest_meta: datetime | None = None
    seen_names: dict[str, None] = {}

    for json_file in folder.rglob('*.json'):
        info = None
        with suppress(OSError, ValueError, TypeError):
            data = json.loads(json_file.read_text(encoding='utf-8', errors='replace'))
            if isinstance(data, dict):
                for section in ('connected', 'disconnected'):
                    players = data.get(section)
                    if isinstance(players, dict) and isinstance(players.get(ip), dict):
                        info = players[ip]
                        break
        if info is None:
            continue

        start = _parse_dt(info.get('First Seen'))
        if start is None:
            continue
        end = _parse_dt(info.get('Last Seen'))
        seconds = _parse_seconds(info.get('T. Session Time'))
        if not seconds and end is not None:
            seconds = max(0.0, (end - start).total_seconds())
        names = _str_list(info.get('Usernames'))
        card.encounters.append(Encounter(start=start, end=end, seconds=seconds, usernames=names))

        for name in names:
            seen_names.setdefault(name, None)

        # keep lookup info from the most recent session that has it
        if latest_meta is None or start >= latest_meta:
            latest_meta = start
            for attr, keys in (('country', ('Country',)), ('city', ('City',)), ('isp', ('ASN / ISP', 'ISP'))):
                for key in keys:
                    value = info.get(key)
                    if isinstance(value, str) and value not in _UNRESOLVED:
                        setattr(card, attr, value)
                        break

    card.encounters.sort(key=lambda e: e.start, reverse=True)
    # most recent usernames first
    recent_first: dict[str, None] = {}
    for encounter in card.encounters:
        for name in encounter.usernames:
            recent_first.setdefault(name, None)
    card.usernames = list(recent_first) or list(seen_names)
    return card


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


class PlayerCardDialog(QDialog):
    """Window showing the full history of one player."""

    _open: dict[str, 'PlayerCardDialog'] = {}

    def __init__(
        self,
        ip: str,
        names: list[str] | None = None,
        parent: QWidget | None = None,
        on_changed: Callable[[], object] | None = None,
    ) -> None:
        super().__init__(parent)
        self._ip = ip
        self._names = list(names or [])
        self._on_changed = on_changed
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, on=False)
        self.setWindowIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'player.svg')))
        self.setWindowTitle(f'Fiche joueur — {", ".join(self._names) or ip}')
        self.resize(620, 640)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        # header: name + tag + ip
        self._title = QLabel()
        self._title.setTextFormat(Qt.TextFormat.RichText)
        self._title.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._title)
        self._subtitle = QLabel()
        self._subtitle.setStyleSheet('color: #b9a3c9;')
        self._subtitle.setWordWrap(True)
        self._subtitle.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._subtitle)

        # stat tiles
        grid = QGridLayout()
        grid.setSpacing(8)
        self._tile_count = _StatTile('Croisé')
        self._tile_days = _StatTile('Jours différents')
        self._tile_total = _StatTile('Temps total ensemble')
        self._tile_avg = _StatTile('Moyenne par session')
        self._tile_first = _StatTile('Première rencontre')
        self._tile_last = _StatTile('Dernière rencontre')
        for i, tile in enumerate((self._tile_count, self._tile_days, self._tile_total, self._tile_avg, self._tile_first, self._tile_last)):
            grid.addWidget(tile, i // 3, i % 3)
        root.addLayout(grid)

        # note
        self._note = QLabel()
        self._note.setWordWrap(True)
        self._note.setTextFormat(Qt.TextFormat.PlainText)
        self._note.setStyleSheet('padding: 8px; border: 1px dashed rgba(63, 240, 255, 0.45); border-radius: 6px;')
        root.addWidget(self._note)

        # encounters table
        encounters_label = QLabel('Dernières rencontres')
        encounters_label.setStyleSheet('font-weight: 600;')
        root.addWidget(encounters_label)
        self._table = QTableWidget(0, 3, self)
        self._table.setHorizontalHeaderLabels(['Date', 'Durée', 'Pseudo'])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setWordWrap(False)
        v_header = self._table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        h_header = self._table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        root.addWidget(self._table, 1)

        # buttons
        buttons = QHBoxLayout()
        copy_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'copy.svg')), 'Copier')
        copy_menu = QMenu(copy_btn)
        copy_menu.addAction("Copier l'IP", lambda: QGuiApplication.clipboard().setText(self._ip))
        copy_menu.addAction('Copier le pseudo', lambda: QGuiApplication.clipboard().setText(', '.join(self._names)))
        copy_menu.addAction('Copier la fiche', self._copy_summary)
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

        self._data: PlayerCardData | None = None
        self._loader = _Loader(self)
        self._loader.loaded.connect(self._apply)
        self._render_header()
        self._load()

    # ----- public -----

    @classmethod
    def open_for(
        cls,
        ip: str,
        names: list[str] | None = None,
        parent: QWidget | None = None,
        on_changed: Callable[[], object] | None = None,
    ) -> 'PlayerCardDialog':
        """Open (or bring to front) the card of *ip*."""
        existing = cls._open.get(ip)
        if existing is not None:
            with suppress(RuntimeError):
                existing.showNormal()
                existing.raise_()
                existing.activateWindow()
                existing._load()  # noqa: SLF001
                return existing
        dialog = cls(ip, names, parent, on_changed)
        cls._open[ip] = dialog
        dialog.destroyed.connect(lambda _obj=None, key=ip: cls._open.pop(key, None))
        dialog.show()
        return dialog

    # ----- loading -----

    def _load(self) -> None:
        for tile in (self._tile_count, self._tile_days, self._tile_total, self._tile_avg, self._tile_first, self._tile_last):
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
        if not isinstance(data, PlayerCardData):
            return
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
        if not data.encounters:
            self._table.insertRow(0)
            empty = QTableWidgetItem('Aucune rencontre enregistrée pour ce joueur.')
            self._table.setItem(0, 0, empty)
            self._table.setSpan(0, 0, 1, 3)
        self._table.clearSelection()
        self._table.setCurrentCell(-1, -1)
        self._render_header()

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
            place = ', '.join(p for p in (self._data.city, self._data.country) if p)
            if place:
                parts.append(f'Lieu (approx.) : {place}')
            if self._data.isp:
                parts.append(f'FAI : {self._data.isp}')
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
