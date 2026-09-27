"""BTXSniffer personal notes on players.

Notes are stored per IP address in AppData/Roaming/<app>/btx_player_notes.json, so they are kept
between sessions and shown again every time the same player is met.
"""

import json
import logging
import os
import shutil
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import QInputDialog, QMenu, QWidget

from session_sniffer.constants.local import APP_DIR_ROAMING

NOTES_PATH = APP_DIR_ROAMING / 'btx_player_notes.json'
MAX_NOTE_LENGTH = 500

# Automatic backups of the notes / tags file
BACKUP_DIR = APP_DIR_ROAMING / 'Sauvegardes BTX'
DAILY_BACKUP_DIR = BACKUP_DIR / 'quotidiennes'
RECENT_BACKUP_DIR = BACKUP_DIR / 'avant-modification'
MANUAL_BACKUP_DIR = BACKUP_DIR / 'manuelles'
KEEP_DAILY_BACKUPS = 30
KEEP_RECENT_BACKUPS = 20
RECENT_BACKUP_MIN_INTERVAL = 120  # seconds between two "before change" backups

logger = logging.getLogger(__name__)

# Player tags: key -> (label, color, badge)
TAGS: dict[str, tuple[str, str, str]] = {
    'ami': ('Ami', '#39ff88', '[Ami]'),
    'dangereux': ('Dangereux', '#ff3860', '[Dangereux]'),
    'relou': ('Relou', '#ffd23f', '[Relou]'),
}


class PlayerNotes:
    """Thread-safe, file-backed store of notes keyed by IP address."""

    _lock = threading.RLock()
    _notes: dict[str, dict[str, str]] | None = None
    _last_recent_backup: float = 0.0

    @classmethod
    def _load(cls) -> dict[str, dict[str, str]]:
        if cls._notes is None:
            cls._notes = {}
            if NOTES_PATH.exists():
                parsed = parse_notes_file(NOTES_PATH)
                if parsed is None:
                    # damaged file: keep it aside and recover from the newest good backup
                    with suppress(OSError):
                        shutil.copy2(NOTES_PATH, NOTES_PATH.with_name(f'btx_player_notes.abime-{time.strftime("%Y%m%d-%H%M%S")}.json'))
                    for backup in list_backups():
                        parsed = parse_notes_file(backup.path)
                        if parsed is not None:
                            logger.warning('Notes file was damaged, restored from backup %s', backup.path)
                            cls._notes = parsed
                            cls._write()
                            break
                else:
                    cls._notes = parsed
            _daily_backup()
        return cls._notes

    @classmethod
    def _write(cls) -> None:
        """Atomic write (a crash in the middle never leaves a half-written file)."""
        with suppress(OSError):
            NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = NOTES_PATH.with_suffix('.tmp')
            tmp.write_text(json.dumps(cls._notes or {}, ensure_ascii=False, indent=2), encoding='utf-8')
            os.replace(tmp, NOTES_PATH)

    @classmethod
    def _save(cls) -> None:
        cls._load()
        now = time.monotonic()
        if now - cls._last_recent_backup >= RECENT_BACKUP_MIN_INTERVAL or not cls._last_recent_backup:
            cls._last_recent_backup = now
            _copy_backup(RECENT_BACKUP_DIR, time.strftime('notes_%Y-%m-%d_%H-%M-%S.json'), KEEP_RECENT_BACKUPS)
        _daily_backup()
        cls._write()

    @classmethod
    def reload(cls) -> None:
        """Forget the in-memory copy and read the file again."""
        with cls._lock:
            cls._notes = None
            cls._load()

    @classmethod
    def count(cls) -> int:
        with cls._lock:
            return len(cls._load())

    @classmethod
    def restore(cls, path: 'os.PathLike[str] | str') -> bool:
        """Replace every note / tag with the content of a backup (the current state is backed up first)."""
        from pathlib import Path  # noqa: PLC0415

        parsed = parse_notes_file(Path(path))
        if parsed is None:
            return False
        with cls._lock:
            cls._load()
            _copy_backup(RECENT_BACKUP_DIR, time.strftime('notes_%Y-%m-%d_%H-%M-%S_avant-restauration.json'), KEEP_RECENT_BACKUPS)
            cls._notes = parsed
            cls._write()
        return True

    @classmethod
    def import_merge(cls, path: 'os.PathLike[str] | str') -> tuple[int, int] | None:
        """Add the notes / tags of another file. Existing notes are kept; returns (added, completed)."""
        from pathlib import Path  # noqa: PLC0415

        parsed = parse_notes_file(Path(path))
        if parsed is None:
            return None
        added = completed = 0
        with cls._lock:
            notes = cls._load()
            _copy_backup(RECENT_BACKUP_DIR, time.strftime('notes_%Y-%m-%d_%H-%M-%S_avant-import.json'), KEEP_RECENT_BACKUPS)
            for ip, entry in parsed.items():
                mine = notes.get(ip)
                if mine is None:
                    notes[ip] = entry
                    added += 1
                    continue
                changed = False
                if not mine.get('tag') and entry.get('tag'):
                    mine['tag'] = entry['tag']
                    changed = True
                if entry.get('note') and entry['note'] not in mine.get('note', ''):
                    mine['note'] = (f"{mine['note']}\n{entry['note']}" if mine.get('note') else entry['note'])[:MAX_NOTE_LENGTH]
                    changed = True
                if changed:
                    completed += 1
            cls._write()
        return added, completed

    @classmethod
    def export_to(cls, path: 'os.PathLike[str] | str') -> bool:
        with cls._lock, suppress(OSError):
            from pathlib import Path  # noqa: PLC0415

            Path(path).write_text(json.dumps(cls._load(), ensure_ascii=False, indent=2), encoding='utf-8')
            return True
        return False

    @classmethod
    def _key(cls, ip: str) -> str:
        """IP under which the note of *ip* is stored (linked IPs share one note / tag)."""
        members = PlayerLinks.group_of(ip)
        if len(members) == 1:
            return ip
        notes = cls._load()
        return next((member for member in members if member in notes), members[0])

    @classmethod
    def get(cls, ip: str) -> str:
        """Return the note for *ip*, or an empty string."""
        with cls._lock:
            entry = cls._load().get(cls._key(ip))
            return entry['note'] if entry else ''

    @classmethod
    def get_tag(cls, ip: str) -> str:
        """Return the tag key ('ami', 'dangereux', 'relou') for *ip*, or an empty string."""
        with cls._lock:
            entry = cls._load().get(cls._key(ip))
            return entry.get('tag', '') if entry else ''

    @classmethod
    def merge_group(cls, members: list[str]) -> None:
        """Linked IPs: keep a single note / tag for the whole group."""
        with cls._lock:
            notes = cls._load()
            entries = [(ip, notes[ip]) for ip in members if ip in notes]
            if len(entries) < 2:  # noqa: PLR2004
                return
            primary_ip, primary = entries[0]
            texts = [primary.get('note', '')]
            names = [n for n in primary.get('names', '').split(', ') if n]
            for ip, entry in entries[1:]:
                if entry.get('note') and entry['note'] not in texts:
                    texts.append(entry['note'])
                if not primary.get('tag') and entry.get('tag'):
                    primary['tag'] = entry['tag']
                names += [n for n in entry.get('names', '').split(', ') if n and n not in names]
                notes.pop(ip, None)
            primary['note'] = '\n'.join(t for t in texts if t)[:MAX_NOTE_LENGTH]
            primary['names'] = ', '.join(names)
            notes[primary_ip] = primary
            cls._save()

    @classmethod
    def move_entry(cls, from_ip: str, to_ip: str) -> None:
        with cls._lock:
            notes = cls._load()
            if from_ip in notes and to_ip not in notes:
                notes[to_ip] = notes.pop(from_ip)
                cls._save()

    @classmethod
    def _update(cls, ip: str, names: list[str] | None, **fields: str) -> None:
        with cls._lock:
            notes = cls._load()
            ip = cls._key(ip)
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
            entry = cls._load().get(cls._key(ip))
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


LINKS_PATH = APP_DIR_ROAMING / 'btx_player_links.json'


class PlayerLinks:
    """Groups of IP addresses that belong to the same player (new box, VPN...)."""

    _lock = threading.RLock()
    _groups: list[list[str]] | None = None

    @classmethod
    def _load(cls) -> list[list[str]]:
        if cls._groups is None:
            cls._groups = []
            with suppress(OSError, ValueError, TypeError):
                data = json.loads(LINKS_PATH.read_text(encoding='utf-8'))
                groups = data.get('groups', []) if isinstance(data, dict) else []
                seen: set[str] = set()
                for group in groups:
                    if isinstance(group, list):
                        clean = [str(ip) for ip in group if str(ip) not in seen]
                        seen.update(clean)
                        if len(clean) > 1:
                            cls._groups.append(clean)
        return cls._groups

    @classmethod
    def _save(cls) -> None:
        with suppress(OSError):
            LINKS_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = LINKS_PATH.with_suffix('.tmp')
            tmp.write_text(json.dumps({'groups': cls._load()}, ensure_ascii=False, indent=2), encoding='utf-8')
            os.replace(tmp, LINKS_PATH)

    @classmethod
    def group_of(cls, ip: str) -> list[str]:
        """All IPs of the player that owns *ip* (just [ip] when not linked)."""
        with cls._lock:
            for group in cls._load():
                if ip in group:
                    return list(group)
        return [ip]

    @classmethod
    def link(cls, ip_a: str, ip_b: str) -> list[str]:
        """Declare that *ip_a* and *ip_b* are the same player. Returns the resulting group."""
        with cls._lock:
            groups = cls._load()
            group_a = next((g for g in groups if ip_a in g), None)
            group_b = next((g for g in groups if ip_b in g), None)
            if group_a is not None and group_a is group_b:
                return list(group_a)
            merged = list(group_a or [ip_a])
            merged += [ip for ip in (group_b or [ip_b]) if ip not in merged]
            cls._groups = [g for g in groups if g is not group_a and g is not group_b] + [merged]
            cls._save()
        PlayerNotes.merge_group(merged)
        return list(merged)

    @classmethod
    def unlink(cls, ip: str) -> None:
        """Remove *ip* from its group (its note / tag stays with the rest of the group)."""
        with cls._lock:
            groups = cls._load()
            group = next((g for g in groups if ip in g), None)
            if group is None:
                return
            remaining = [member for member in group if member != ip]
            cls._groups = [g for g in groups if g is not group] + ([remaining] if len(remaining) > 1 else [])
            cls._save()
        if remaining:
            PlayerNotes.move_entry(ip, remaining[0])


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


# ---------- backups ----------


def parse_notes_file(path: 'os.PathLike[str]') -> dict[str, dict[str, str]] | None:
    """Read a notes file (or backup). Returns None if it is unreadable or not a notes file."""
    from pathlib import Path  # noqa: PLC0415

    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    result: dict[str, dict[str, str]] = {}
    for ip, entry in data.items():
        if not isinstance(entry, dict):
            continue
        note = str(entry.get('note', ''))[:MAX_NOTE_LENGTH]
        tag = str(entry.get('tag', '')) if entry.get('tag') in TAGS else ''
        if note or tag:
            result[str(ip)] = {'note': note, 'tag': tag, 'names': str(entry.get('names', '')), 'updated': str(entry.get('updated', ''))}
    return result


def _prune(directory: 'os.PathLike[str]', keep: int) -> None:
    from pathlib import Path  # noqa: PLC0415

    files = sorted(Path(directory).glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in files[keep:]:
        with suppress(OSError):
            old.unlink()


def _copy_backup(directory: 'os.PathLike[str]', name: str, keep: int) -> None:
    from pathlib import Path  # noqa: PLC0415

    if not NOTES_PATH.exists() or NOTES_PATH.stat().st_size == 0:
        return
    with suppress(OSError):
        Path(directory).mkdir(parents=True, exist_ok=True)
        shutil.copy2(NOTES_PATH, Path(directory) / name)
        _prune(directory, keep)


def _daily_backup() -> None:
    target = DAILY_BACKUP_DIR / time.strftime('notes_%Y-%m-%d.json')
    if not target.exists():
        _copy_backup(DAILY_BACKUP_DIR, target.name, KEEP_DAILY_BACKUPS)


def create_manual_backup() -> bool:
    """Save a copy right now (kept until deleted by the user)."""
    with PlayerNotes._lock:  # noqa: SLF001
        PlayerNotes._load()  # noqa: SLF001
        if not NOTES_PATH.exists():
            PlayerNotes._write()  # noqa: SLF001
        before = len(list(MANUAL_BACKUP_DIR.glob('*.json'))) if MANUAL_BACKUP_DIR.exists() else 0
        _copy_backup(MANUAL_BACKUP_DIR, time.strftime('notes_%Y-%m-%d_%H-%M-%S.json'), 1000)
        return MANUAL_BACKUP_DIR.exists() and len(list(MANUAL_BACKUP_DIR.glob('*.json'))) > before


class BackupInfo:
    """A backup file on disk."""

    KINDS = {'quotidiennes': 'Quotidienne (auto)', 'avant-modification': 'Avant modification (auto)', 'manuelles': 'Manuelle'}

    def __init__(self, path: 'os.PathLike[str]') -> None:
        from pathlib import Path  # noqa: PLC0415

        self.path = Path(path)
        self.kind = self.KINDS.get(self.path.parent.name, self.path.parent.name)
        self.mtime = datetime.fromtimestamp(self.path.stat().st_mtime).astimezone()

    def count(self) -> int:
        parsed = parse_notes_file(self.path)
        return -1 if parsed is None else len(parsed)


def list_backups() -> list[BackupInfo]:
    """Every backup, newest first."""
    backups: list[BackupInfo] = []
    for directory in (RECENT_BACKUP_DIR, DAILY_BACKUP_DIR, MANUAL_BACKUP_DIR):
        if directory.exists():
            for path in directory.glob('*.json'):
                with suppress(OSError):
                    backups.append(BackupInfo(path))
    backups.sort(key=lambda b: b.mtime, reverse=True)
    return backups
