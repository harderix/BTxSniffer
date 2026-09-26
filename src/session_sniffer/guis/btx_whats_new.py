"""BTXSniffer "Quoi de neuf" window.

Shows the description written in the GitHub releases of the BTXSniffer repository:
- automatically, once, the first time a new version is launched (after an update);
- on demand, from the menu Aide → Quoi de neuf.
"""

import json
import logging
import threading
import webbrowser
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime

import requests
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from session_sniffer.constants._build_info import RELEASE_TAG
from session_sniffer.constants.local import APP_DIR_ROAMING, RESOURCES_DIR_PATH
from session_sniffer.constants.standalone import BTX_UPDATES_CONFIGURED, GITHUB_RELEASES_URL, GITHUB_VERSIONS_URL, TITLE
from session_sniffer.networking.http_session import session

logger = logging.getLogger(__name__)

STATE_PATH = APP_DIR_ROAMING / 'btx_state.json'
_MONTHS = ('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre')


@dataclass
class ReleaseNote:
    """One published GitHub release."""

    tag: str
    name: str
    published: datetime | None
    body: str
    prerelease: bool


# ---------- state (last version whose notes were shown) ----------


def _load_state() -> dict[str, str]:
    with suppress(OSError, ValueError, TypeError):
        data = json.loads(STATE_PATH.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    return {}


def _save_state(**values: str) -> None:
    state = _load_state()
    state.update(values)
    with suppress(OSError):
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def current_tag() -> str | None:
    """Release tag baked into this build, or None when running from source."""
    tag = str(RELEASE_TAG).strip()
    return None if tag in {'', '-'} else tag


# ---------- GitHub ----------


def fetch_release_notes(limit: int = 15) -> list[ReleaseNote]:
    """Return the latest published releases (newest first). Raises on network errors."""
    response = session.get(
        GITHUB_VERSIONS_URL,
        params={'per_page': limit},
        headers={'Accept': 'application/vnd.github+json'},
        timeout=10,
    )
    if response.status_code == requests.codes.not_found:
        return []
    response.raise_for_status()
    notes: list[ReleaseNote] = []
    for release in response.json():
        if not isinstance(release, dict) or release.get('draft'):
            continue
        published = None
        with suppress(ValueError, TypeError):
            published = datetime.fromisoformat(str(release.get('published_at')).replace('Z', '+00:00'))
        notes.append(
            ReleaseNote(
                tag=str(release.get('tag_name') or ''),
                name=str(release.get('name') or release.get('tag_name') or ''),
                published=published,
                body=str(release.get('body') or '').strip(),
                prerelease=bool(release.get('prerelease')),
            ),
        )
    return notes


def _format_day(value: datetime | None) -> str:
    if value is None:
        return ''
    value = value.astimezone()
    return f'{value.day} {_MONTHS[value.month - 1]} {value.year}'


def _to_markdown(notes: list[ReleaseNote], highlight: str | None) -> str:
    parts: list[str] = []
    for note in notes:
        title = note.name or note.tag
        if note.tag and note.tag.removeprefix('v') not in title:
            title = f'{title} ({note.tag})'
        suffix = []
        if note.tag == highlight:
            suffix.append('**← ta version**')
        if note.prerelease:
            suffix.append('_version de test_')
        day = _format_day(note.published)
        header = f'## {title}'
        meta = ' · '.join(x for x in (day, *suffix) if x)
        body = note.body or '_Pas de description pour cette version._'
        parts.append(f'{header}\n\n{meta}\n\n{body}' if meta else f'{header}\n\n{body}')
    return '\n\n---\n\n'.join(parts)


# ---------- dialog ----------


class WhatsNewDialog(QDialog):
    """Window rendering release notes (GitHub markdown)."""

    def __init__(self, notes: list[ReleaseNote], *, highlight: str | None, heading: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, on=False)
        self.setWindowIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'lightbulb.svg')))
        self.setWindowTitle(f'Quoi de neuf — {TITLE}')
        self.resize(640, 560)

        layout = QVBoxLayout(self)
        title = QLabel(heading)
        title.setWordWrap(True)
        title.setStyleSheet('font-size: 18px; font-weight: 700; color: #ff2bd6;')
        layout.addWidget(title)

        browser = QTextBrowser(self)
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(_to_markdown(notes, highlight) if notes else "_Aucune version publiée pour l'instant._")
        layout.addWidget(browser, 1)

        buttons = QHBoxLayout()
        github = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'github.svg')), 'Voir sur GitHub')
        github.clicked.connect(lambda: webbrowser.open(GITHUB_RELEASES_URL))
        close = QPushButton('Fermer')
        close.setDefault(True)
        close.clicked.connect(self.close)
        buttons.addWidget(github)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)


class _Relay(QObject):
    done = Signal(object, object)  # (notes | None, error | None)


class WhatsNew(QObject):
    """Fetches release notes in the background and shows the window on the GUI thread."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._parent = parent
        self._relay = _Relay(self)
        self._relay.done.connect(self._on_done)
        self._busy = False
        self._manual = False

    def maybe_show_after_update(self) -> None:
        """Show the notes of this version once, the first time it is launched."""
        tag = current_tag()
        if not BTX_UPDATES_CONFIGURED or tag is None:
            return
        if _load_state().get('last_whats_new') == tag:
            return
        self._start(manual=False)

    def show_now(self) -> None:
        """Menu Aide → Quoi de neuf."""
        if not BTX_UPDATES_CONFIGURED:
            self._show_message('Les mises à jour ne sont pas encore configurées, il n’y a donc pas de notes de version à afficher.')
            return
        self._start(manual=True)

    def _start(self, *, manual: bool) -> None:
        if self._busy:
            return
        self._busy = True
        self._manual = manual
        relay = self._relay

        def work() -> None:
            try:
                notes: list[ReleaseNote] | None = fetch_release_notes()
                error = None
            except (requests.exceptions.RequestException, ValueError) as exc:
                notes, error = None, exc
            with suppress(RuntimeError):
                relay.done.emit(notes, error)

        threading.Thread(target=work, name='BTXWhatsNew', daemon=True).start()

    def _on_done(self, notes: object, error: object) -> None:
        self._busy = False
        tag = current_tag()
        if not isinstance(notes, list):
            logger.info('Could not fetch release notes: %s', error)
            if self._manual:
                self._show_message('Impossible de récupérer les nouveautés (pas de connexion à GitHub ?). Réessaie plus tard.')
            return

        if not self._manual:
            if tag is None:
                return
            _save_state(last_whats_new=tag)
            mine = next((n for n in notes if n.tag == tag), None)
            if mine is None or not mine.body:
                return  # nothing written for this version: don't bother the user
            heading = f'Nouveautés de {TITLE} {tag.removeprefix("v")}'
            dialog = WhatsNewDialog([mine], highlight=tag, heading=heading, parent=self._parent)
        else:
            heading = f'Nouveautés de {TITLE}'
            if tag is not None:
                heading += f' — tu as la version {tag.removeprefix("v")}'
            dialog = WhatsNewDialog(notes, highlight=tag, heading=heading, parent=self._parent)
        dialog.show()
        dialog.raise_()

    def _show_message(self, text: str) -> None:
        QMessageBox.information(self._parent, f'Quoi de neuf — {TITLE}', text)
