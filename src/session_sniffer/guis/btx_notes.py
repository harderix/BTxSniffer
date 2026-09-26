"""BTXSniffer personal notes on players.

Notes are stored per IP address in AppData/Roaming/<app>/btx_player_notes.json, so they are kept
between sessions and shown again every time the same player is met.
"""

import json
import threading
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QInputDialog, QMenu, QWidget

from session_sniffer.constants.local import APP_DIR_ROAMING

NOTES_PATH = APP_DIR_ROAMING / 'btx_player_notes.json'
MAX_NOTE_LENGTH = 500

# Player tags: key -> (label, color, badge)
TAGS: dict[str, tuple[str, str, str]] = {
    'ami': ('Ami', '#39ff88', '[Ami]'),
    'dangereux': ('Dangereux', '#ff3860', '[Dangereux]'),
    'relou': ('Relou', '#ffd23f', '[Relou]'),
}


class PlayerNotes:
    """Thread-safe, file-backed store of notes keyed by IP address."""

    _lock = threading.Lock()
    _notes: dict[str, dict[str, str]] | None = None

    @classmethod
    def _load(cls) -> dict[str, dict[str, str]]:
        if cls._notes is None:
            cls._notes = {}
            with suppress(OSError, ValueError, TypeError):
                data = json.loads(NOTES_PATH.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    cls._notes = {
                        str(ip): {
                            'note': str(entry.get('note', '')),
                            'tag': str(entry.get('tag', '')) if entry.get('tag') in TAGS else '',
                            'names': str(entry.get('names', '')),
                            'updated': str(entry.get('updated', '')),
                        }
                        for ip, entry in data.items()
                        if isinstance(entry, dict) and (entry.get('note') or entry.get('tag') in TAGS)
                    }
        return cls._notes

    @classmethod
    def _save(cls) -> None:
        with suppress(OSError):
            NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
            NOTES_PATH.write_text(json.dumps(cls._load(), ensure_ascii=False, indent=2), encoding='utf-8')

    @classmethod
    def get(cls, ip: str) -> str:
        """Return the note for *ip*, or an empty string."""
        with cls._lock:
            entry = cls._load().get(ip)
            return entry['note'] if entry else ''

    @classmethod
    def get_tag(cls, ip: str) -> str:
        """Return the tag key ('ami', 'dangereux', 'relou') for *ip*, or an empty string."""
        with cls._lock:
            entry = cls._load().get(ip)
            return entry.get('tag', '') if entry else ''

    @classmethod
    def _update(cls, ip: str, names: list[str] | None, **fields: str) -> None:
        with cls._lock:
            notes = cls._load()
            entry = notes.get(ip, {'note': '', 'tag': '', 'names': '', 'updated': ''})
            entry.update(fields)
            if names:
                entry['names'] = ', '.join(names)
            entry['updated'] = datetime.now(tz=UTC).isoformat(timespec='seconds')
            if entry.get('note') or entry.get('tag'):
                notes[ip] = entry
            else:
                notes.pop(ip, None)
            cls._save()

    @classmethod
    def set(cls, ip: str, note: str, names: list[str] | None = None) -> None:
        """Save (or delete, when empty) the note for *ip*."""
        cls._update(ip, names, note=note.strip()[:MAX_NOTE_LENGTH])

    @classmethod
    def set_tag(cls, ip: str, tag: str, names: list[str] | None = None) -> None:
        """Set the tag for *ip* ('' removes it)."""
        cls._update(ip, names, tag=tag if tag in TAGS else '')

    @classmethod
    def search_text(cls, ip: str) -> str:
        """Return note + tag label, lowercase, for search matching."""
        with cls._lock:
            entry = cls._load().get(ip)
        if not entry:
            return ''
        tag = TAGS.get(entry.get('tag', ''), ('', '', ''))[0]
        return f"{entry.get('note', '')} {tag}".lower()

    @classmethod
    def search(cls, text: str) -> list[str]:
        """Return the IPs whose note or tag contains *text* (case-insensitive)."""
        text = text.lower()
        with cls._lock:
            ips = list(cls._load())
        return [ip for ip in ips if text in cls.search_text(ip)]


def tag_color(ip: str) -> str | None:
    """Return the colour of the player's tag, or None."""
    tag = PlayerNotes.get_tag(ip)
    return TAGS[tag][1] if tag in TAGS else None


def tag_badge(ip: str) -> str:
    """Return the badge text (e.g. '[Ami]') of the player's tag, or ''."""
    tag = PlayerNotes.get_tag(ip)
    return TAGS[tag][2] if tag in TAGS else ''


def add_tag_menu(menu: QMenu, ip: str, names: list[str] | None, on_changed: Callable[[], object] | None = None) -> QMenu:
    """Add an 'Étiquette' sub-menu (Ami / Dangereux / Relou / Aucune) to *menu*."""
    current = PlayerNotes.get_tag(ip)
    sub = menu.addMenu('Étiquette')
    sub.setToolTip('Classer ce joueur (couleur dans les tableaux, l\'historique et la mini-fenêtre)')

    def choose(tag: str) -> None:
        PlayerNotes.set_tag(ip, tag, names)
        if on_changed is not None:
            on_changed()

    for key, (label, color, _badge) in TAGS.items():
        pixmap = QPixmap(12, 12)
        pixmap.fill(QColor(color))
        action = sub.addAction(QIcon(pixmap), label)
        action.setCheckable(True)
        action.setChecked(current == key)
        action.triggered.connect(lambda _checked=False, k=key: choose(k))
    sub.addSeparator()
    none_action = sub.addAction('Aucune')
    none_action.setEnabled(bool(current))
    none_action.triggered.connect(lambda _checked=False: choose(''))
    return sub


def edit_player_note(parent: QWidget | None, ip: str, names: list[str] | None = None) -> bool:
    """Open a small dialog to add, edit or clear the note of a player. Returns True if saved."""
    who = ', '.join(names) if names else ip
    current = PlayerNotes.get(ip)
    text, accepted = QInputDialog.getMultiLineText(
        parent,
        'Note perso',
        f'Note pour {who} ({ip}) :\nLaisse vide pour supprimer la note.',
        current,
    )
    if not accepted:
        return False
    PlayerNotes.set(ip, text, names)
    return True
