"""BTXSniffer in-game mini window (overlay) with a configurable global hotkey.

- A small frameless, always-on-top window showing the current session: connected count,
  latest players, and a search bar over every player met this session.
- A global keyboard shortcut (works while the game has focus, on Windows) toggles it.
- Settings (hotkey, position, opacity) are stored in AppData/Roaming/<app>/btx_overlay.json.
"""

import ctypes
import json
import sys
import time
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from typing import Any

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QGuiApplication, QKeySequence, QMouseEvent, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from session_sniffer.constants.local import APP_DIR_ROAMING
from session_sniffer.guis.btx_notes import PlayerNotes, add_tag_menu, edit_player_note, tag_badge, tag_color
from session_sniffer.guis.btx_player_card import open_player_card
from session_sniffer.player.registry import PlayersRegistry

if sys.platform == 'win32':
    import ctypes.wintypes

CONFIG_PATH = APP_DIR_ROAMING / 'btx_overlay.json'
DEFAULT_CONFIG: dict[str, Any] = {'hotkey': 'F8', 'x': 40, 'y': 40, 'opacity': 90}
MAX_RECENT_PLAYERS = 64  # the window grows with the number of players (up to the screen height)
MAX_SEARCH_RESULTS = 30

_OVERLAY_STYLESHEET = """
QFrame#btxOverlayCard {
    background-color: rgba(16, 10, 22, 235);
    border: 2px solid #ff2bd6;
    border-radius: 12px;
}
QLabel { background: transparent; color: #efd7f3; }
QLabel#btxOverlayTitle { color: #ff2bd6; font-weight: bold; font-size: 11pt; }
QLabel#btxOverlayCount { color: #3ff0ff; font-weight: bold; font-size: 11pt; }
QLabel#btxOverlaySection { color: #ffab2e; font-weight: bold; font-size: 8pt; }
QLineEdit {
    background-color: #1b1024; color: #efd7f3; border: 1px solid #5de8fb;
    border-radius: 6px; padding: 4px 6px;
}
QListWidget {
    background: transparent; border: none; color: #efd7f3; font-size: 9pt;
}
QListWidget::item { padding: 2px 2px; border-bottom: 1px solid rgba(255, 43, 214, 40); }
QListWidget::item:selected { background-color: rgba(255, 43, 214, 90); }
QPushButton {
    background-color: #2a1938; color: #efd7f3; border: 1px solid #ff2bd6;
    border-radius: 6px; padding: 3px 8px; font-size: 8pt;
}
QPushButton:hover { background-color: #ff2bd6; color: #ffffff; }
QPushButton#btxOverlayClose { border: none; background: transparent; color: #a293ad; font-size: 11pt; padding: 0 4px; }
QPushButton#btxOverlayClose:hover { color: #ff3860; }
"""


# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
def load_overlay_config() -> dict[str, Any]:
    """Load the overlay config, falling back to defaults for anything missing or invalid."""
    config = dict(DEFAULT_CONFIG)
    with suppress(OSError, ValueError, TypeError):
        data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            config.update({key: value for key, value in data.items() if key in DEFAULT_CONFIG})
    return config


def save_overlay_config(config: dict[str, Any]) -> None:
    """Persist the overlay config (errors are ignored: the overlay still works without it)."""
    with suppress(OSError):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')


# ----------------------------------------------------------------------------
# Global hotkey
# ----------------------------------------------------------------------------
_WM_HOTKEY = 0x0312
_MOD_ALT, _MOD_CONTROL, _MOD_SHIFT, _MOD_WIN, _MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
_HOTKEY_ID = 0xB7C1

_SPECIAL_VK: dict[int, int] = {
    Qt.Key.Key_Insert.value: 0x2D, Qt.Key.Key_Delete.value: 0x2E, Qt.Key.Key_Home.value: 0x24,
    Qt.Key.Key_End.value: 0x23, Qt.Key.Key_PageUp.value: 0x21, Qt.Key.Key_PageDown.value: 0x22,
    Qt.Key.Key_Pause.value: 0x13, Qt.Key.Key_ScrollLock.value: 0x91, Qt.Key.Key_Space.value: 0x20,
    Qt.Key.Key_Tab.value: 0x09, Qt.Key.Key_Backspace.value: 0x08, Qt.Key.Key_Return.value: 0x0D,
    Qt.Key.Key_Enter.value: 0x0D, Qt.Key.Key_Up.value: 0x26, Qt.Key.Key_Down.value: 0x28,
    Qt.Key.Key_Left.value: 0x25, Qt.Key.Key_Right.value: 0x27, Qt.Key.Key_Minus.value: 0xBD,
    Qt.Key.Key_Plus.value: 0xBB, Qt.Key.Key_Equal.value: 0xBB, Qt.Key.Key_Comma.value: 0xBC,
    Qt.Key.Key_Period.value: 0xBE, Qt.Key.Key_Slash.value: 0xBF, Qt.Key.Key_Asterisk.value: 0x6A,
}


# BTX: mouse buttons can be used as the overlay key (handy when a mod menu grabs the F keys)
MOUSE_BUTTONS: dict[str, tuple[int, str]] = {
    'Souris4': (0x05, 'Bouton latéral arrière de la souris (bouton 4)'),
    'Souris5': (0x06, 'Bouton latéral avant de la souris (bouton 5)'),
    'SourisMilieu': (0x04, 'Clic molette'),
}

_VK_NAMES: dict[int, str] = {
    0x01: 'Clic gauche', 0x02: 'Clic droit', 0x04: 'Clic molette', 0x05: 'Souris 4', 0x06: 'Souris 5',
    0x08: 'Retour arrière', 0x09: 'Tab', 0x0D: 'Entrée', 0x10: 'Maj', 0x11: 'Ctrl', 0x12: 'Alt', 0x13: 'Pause',
    0x14: 'Verr. Maj', 0x1B: 'Échap', 0x20: 'Espace', 0x21: 'Page préc.', 0x22: 'Page suiv.', 0x23: 'Fin',
    0x24: 'Début', 0x25: 'Gauche', 0x26: 'Haut', 0x27: 'Droite', 0x28: 'Bas', 0x2C: 'Impr. écran', 0x2D: 'Inser',
    0x2E: 'Suppr', 0x5B: 'Windows', 0x5C: 'Windows', 0x5D: 'Menu', 0x90: 'Verr. Num', 0x91: 'Arrêt défil',
}
_VK_IGNORED = {0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5}  # left/right variants of Shift/Ctrl/Alt (generic ones are shown)


def vk_name(vk: int) -> str:
    """Human-readable name of a Windows virtual key."""
    if vk in _VK_NAMES:
        return _VK_NAMES[vk]
    if 0x70 <= vk <= 0x87:
        return f'F{vk - 0x6F}'
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x60 <= vk <= 0x69:
        return f'Pavé num. {vk - 0x60}'
    if 0xAD <= vk <= 0xB7:
        return 'Touche multimédia (son/lecture)'
    return f'Touche 0x{vk:02X}'


def display_hotkey(sequence_text: str) -> str:
    """Text shown to the user for a saved hotkey."""
    if sequence_text in MOUSE_BUTTONS:
        return MOUSE_BUTTONS[sequence_text][1]
    return QKeySequence(sequence_text).toString(QKeySequence.SequenceFormat.NativeText) or sequence_text


def _sequence_to_win32(sequence_text: str) -> tuple[int, int] | None:
    """Convert a Qt key sequence string (e.g. 'Ctrl+F8') to Win32 (modifiers, virtual key)."""
    if sequence_text in MOUSE_BUTTONS:
        return _MOD_NOREPEAT, MOUSE_BUTTONS[sequence_text][0]
    sequence = QKeySequence(sequence_text)
    if sequence.isEmpty():
        return None
    combo = sequence[0]
    key = combo.key().value
    mods = combo.keyboardModifiers()
    win_mods = _MOD_NOREPEAT
    if mods & Qt.KeyboardModifier.ControlModifier:
        win_mods |= _MOD_CONTROL
    if mods & Qt.KeyboardModifier.AltModifier:
        win_mods |= _MOD_ALT
    if mods & Qt.KeyboardModifier.ShiftModifier:
        win_mods |= _MOD_SHIFT
    if mods & Qt.KeyboardModifier.MetaModifier:
        win_mods |= _MOD_WIN
    if Qt.Key.Key_F1.value <= key <= Qt.Key.Key_F24.value:
        return win_mods, 0x70 + (key - Qt.Key.Key_F1.value)
    if Qt.Key.Key_A.value <= key <= Qt.Key.Key_Z.value or Qt.Key.Key_0.value <= key <= Qt.Key.Key_9.value:
        return win_mods, key
    vk = _SPECIAL_VK.get(key)
    return (win_mods, vk) if vk is not None else None


_GAME_EXES = {'gta5.exe', 'gta5_enhanced.exe', 'playgtav.exe'}


def is_running_as_admin() -> bool:
    """True when BTXSniffer runs elevated (always True outside Windows)."""
    if sys.platform != 'win32':
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
    except (OSError, AttributeError):
        return True


def elevated_game_in_foreground() -> bool:
    """True when the foreground window is GTA V running with higher rights than BTXSniffer.

    Windows then hides the keyboard from non-elevated programs (UIPI), so the overlay key cannot work.
    """
    if sys.platform != 'win32':
        return False
    try:
        from ctypes import wintypes  # noqa: PLC0415

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        advapi32 = ctypes.windll.advapi32  # type: ignore[attr-defined]
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        kernel32.OpenProcess.restype = wintypes.HANDLE
        handle = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            size = wintypes.DWORD(1024)
            buffer = ctypes.create_unicode_buffer(1024)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return False
            if buffer.value.replace('/', '\\').rsplit('\\', 1)[-1].lower() not in _GAME_EXES:
                return False
            token = wintypes.HANDLE()
            if not advapi32.OpenProcessToken(handle, 0x0008, ctypes.byref(token)):  # TOKEN_QUERY
                return True  # access denied -> the game runs with higher rights than us
            try:
                elevation = wintypes.DWORD()
                returned = wintypes.DWORD()
                ok = advapi32.GetTokenInformation(token, 20, ctypes.byref(elevation), 4, ctypes.byref(returned))  # TokenElevation
                return bool(ok and elevation.value)
            finally:
                kernel32.CloseHandle(token)
        finally:
            kernel32.CloseHandle(handle)
    except (OSError, AttributeError, ValueError):
        return False


def relaunch_as_admin(window: QWidget) -> bool:
    """Start BTXSniffer again with administrator rights and close this instance."""
    if sys.platform != 'win32':
        return False
    if getattr(sys, 'frozen', False):
        program, params = sys.executable, ' '.join(f'"{a}"' for a in sys.argv[1:])
    else:
        program, params = sys.executable, ' '.join(f'"{a}"' for a in sys.orig_argv[1:])
    try:
        result = ctypes.windll.shell32.ShellExecuteW(None, 'runas', program, params, None, 1)  # type: ignore[attr-defined]
    except (OSError, AttributeError):
        return False
    if result <= 32:  # noqa: PLR2004 - ShellExecute error codes (user refused the admin prompt, ...)
        return False
    window.close()
    return True


class GlobalHotkey(QWidget):
    """System-wide hotkey.

    BTX: on Windows two detectors run together (a press is counted once):
    - RegisterHotKey (Windows hotkey), which works even when the game runs with higher rights;
    - polling of the keyboard state (GetAsyncKeyState), which works even when another program
      (mod menu, Discord, NVIDIA/AMD overlay, OBS...) already registered the same key.
    Other platforms use an in-app shortcut.
    """

    activated = Signal()
    _POLL_MS = 25

    def __init__(self, fallback_parent: QWidget) -> None:
        """Create the (never shown) helper widget."""
        super().__init__(None)
        self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)  # noqa: FBT003
        self._fallback_parent = fallback_parent
        self._fallback_shortcut: QShortcut | None = None
        self._vk: int | None = None
        self._mods = 0
        self._was_down = False
        self._paused = False
        self._timer = QTimer(self)
        self._timer.setInterval(self._POLL_MS)
        self._timer.timeout.connect(self._poll)
        self._registered = False
        self._last_fire = 0.0
        if sys.platform == 'win32':
            self.winId()  # native window that receives WM_HOTKEY

    def set_sequence(self, sequence_text: str) -> bool:
        """(Re)bind the hotkey. Returns False if the key cannot be used."""
        self.unregister()
        if not sequence_text:
            return True
        if sys.platform == 'win32':
            converted = _sequence_to_win32(sequence_text)
            if converted is None:
                return False
            self._mods, self._vk = converted[0] & ~_MOD_NOREPEAT, converted[1]
            self._was_down = self._is_down()  # ignore a key already held when (re)binding
            self._timer.start()
            if sequence_text not in MOUSE_BUTTONS:  # RegisterHotKey only handles keyboard keys
                with suppress(OSError, AttributeError):
                    self._registered = bool(
                        ctypes.windll.user32.RegisterHotKey(int(self.winId()), _HOTKEY_ID, converted[0], converted[1]),  # type: ignore[attr-defined]
                    )
            return True
        self._fallback_shortcut = QShortcut(QKeySequence(sequence_text), self._fallback_parent)
        self._fallback_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._fallback_shortcut.activated.connect(self.activated.emit)
        return True

    def set_paused(self, paused: bool) -> None:  # noqa: FBT001
        """Temporarily ignore the key (e.g. while choosing a new one)."""
        self._paused = paused
        self._was_down = True  # require a fresh press after resuming

    def unregister(self) -> None:
        """Release the current hotkey, if any."""
        self._timer.stop()
        self._vk = None
        if self._registered:
            with suppress(OSError, AttributeError):
                ctypes.windll.user32.UnregisterHotKey(int(self.winId()), _HOTKEY_ID)  # type: ignore[attr-defined]
            self._registered = False
        if self._fallback_shortcut is not None:
            self._fallback_shortcut.setEnabled(False)
            self._fallback_shortcut.deleteLater()
            self._fallback_shortcut = None

    @staticmethod
    def _key_down(vk: int) -> bool:
        return bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)  # type: ignore[attr-defined]

    def _mods_match(self) -> bool:
        wanted = {
            _MOD_CONTROL: (0x11,),  # VK_CONTROL
            _MOD_ALT: (0x12,),  # VK_MENU
            _MOD_SHIFT: (0x10,),  # VK_SHIFT
            _MOD_WIN: (0x5B, 0x5C),  # VK_LWIN / VK_RWIN
        }
        for flag, keys in wanted.items():
            down = any(self._key_down(k) for k in keys)
            if down != bool(self._mods & flag):
                return False
        return True

    def _is_down(self) -> bool:
        return self._vk is not None and self._key_down(self._vk)

    def _poll(self) -> None:
        try:
            down = self._is_down()
        except (OSError, AttributeError):
            return
        if down and not self._was_down and self._mods_match():
            self._fire()
        self._was_down = down

    def _fire(self) -> None:
        """Emit once per key press, whichever detector saw it first."""
        if self._paused:
            return
        now = time.monotonic()
        if now - self._last_fire < 0.35:  # noqa: PLR2004
            return
        self._last_fire = now
        self.activated.emit()

    def nativeEvent(self, event_type: Any, message: Any) -> tuple[bool, int]:  # noqa: ANN401, N802  # pylint: disable=invalid-name
        """Catch WM_HOTKEY (Windows hotkey detector)."""
        if sys.platform == 'win32' and event_type == b'windows_generic_MSG':
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == _WM_HOTKEY and msg.wParam == _HOTKEY_ID:
                self._fire()
                return True, 0
        return super().nativeEvent(event_type, message)


# ----------------------------------------------------------------------------
# Overlay window
# ----------------------------------------------------------------------------
def _player_label(player: Any) -> str:  # noqa: ANN401
    """Return 'Username (Country)' or 'IP (Country)' for a player."""
    names = ', '.join(player.usernames) if player.usernames else player.ip
    badge = tag_badge(player.ip)
    if badge:
        names = f'{badge} {names}'
    country = player.iplookup.geolite2.country
    return f'{names}  ·  {country}' if country and country != '...' else names


def _matches(player: Any, text: str) -> bool:  # noqa: ANN401
    """Case-insensitive match on usernames, IP, country and ISP."""
    haystack = ' '.join(
        [
            *player.usernames,
            player.ip,
            str(player.iplookup.geolite2.country),
            str(player.iplookup.geolite2.asn),
            PlayerNotes.search_text(player.ip),
        ],
    ).lower()
    return text in haystack


class BTXOverlay(QWidget):
    """Small always-on-top window to keep an eye on the session while playing."""

    def __init__(self, open_history_search: Callable[[str], None]) -> None:
        """Build the overlay (hidden until toggled)."""
        super().__init__(None)
        self._open_history_search = open_history_search
        self._config = load_overlay_config()
        self._drag_offset: QPoint | None = None

        self.setWindowTitle('BTXSniffer - Mini-fenêtre')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)  # noqa: FBT003
        self.setStyleSheet(_OVERLAY_STYLESHEET)
        self.setFixedWidth(340)
        self.setWindowOpacity(max(30, min(100, int(self._config['opacity']))) / 100)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName('btxOverlayCard')
        outer.addWidget(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        title = QLabel('⚡ BTX')
        title.setObjectName('btxOverlayTitle')
        header.addWidget(title)
        header.addStretch()
        self._count_label = QLabel('0 connecté')
        self._count_label.setObjectName('btxOverlayCount')
        header.addWidget(self._count_label)
        close_button = QPushButton('✕')
        close_button.setObjectName('btxOverlayClose')
        close_button.setToolTip('Masquer (ou appuie sur ton raccourci)')
        close_button.clicked.connect(self.toggle)
        header.addWidget(close_button)
        layout.addLayout(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText('Chercher un joueur (pseudo, IP, pays, note)…')
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self.refresh)
        self._search.returnPressed.connect(self._search_in_history)
        layout.addWidget(self._search)

        self._section_label = QLabel('DERNIERS ARRIVÉS')
        self._section_label.setObjectName('btxOverlaySection')
        layout.addWidget(self._section_label)

        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_player_menu)
        self._list.setToolTip('Clic droit sur un joueur pour copier son IP, son port ou son pseudo')
        layout.addWidget(self._list)
        self._previous_foreground: int | None = None

        footer = QHBoxLayout()
        history_button = QPushButton('🔎 Chercher dans l\'historique')
        history_button.setToolTip("Chercher ce texte dans l'onglet Historique des joueurs (tous les joueurs déjà croisés)")
        history_button.clicked.connect(self._search_in_history)
        footer.addWidget(history_button)
        footer.addStretch()
        self._hint = QLabel('')
        self._hint.setStyleSheet('color: #a293ad; font-size: 7pt;')
        footer.addWidget(self._hint)
        layout.addLayout(footer)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)

        self.move(int(self._config['x']), int(self._config['y']))

    # --- public API -------------------------------------------------------
    def set_hotkey_hint(self, sequence_text: str) -> None:
        """Show the current shortcut in the footer."""
        self._hint.setText(f'Raccourci : {sequence_text}' if sequence_text else '')

    def set_opacity_percent(self, percent: int) -> None:
        """Change and remember the overlay opacity."""
        self._config['opacity'] = percent
        self.setWindowOpacity(percent / 100)
        save_overlay_config(self._config)

    def toggle(self) -> None:
        """Show or hide the overlay. Showing it takes the focus so the mouse cursor appears over the game."""
        if self.isVisible():
            self.hide()
            self._give_focus_back()
        else:
            self._remember_foreground()
            self.refresh()
            self.show()
            self.raise_()
            self.activateWindow()
            self._force_foreground()
            self._search.setFocus()

    def _remember_foreground(self) -> None:
        """Remember the game window so the focus can be given back when the overlay is hidden."""
        if sys.platform == 'win32':
            self._previous_foreground = ctypes.windll.user32.GetForegroundWindow() or None  # type: ignore[attr-defined]

    def _force_foreground(self) -> None:
        """Bring the overlay to the foreground (this releases the game's hidden cursor)."""
        if sys.platform == 'win32':
            ctypes.windll.user32.SetForegroundWindow(int(self.winId()))  # type: ignore[attr-defined]

    def _give_focus_back(self) -> None:
        """Return the focus to the game so it captures the mouse again."""
        if sys.platform == 'win32' and self._previous_foreground:
            ctypes.windll.user32.SetForegroundWindow(self._previous_foreground)  # type: ignore[attr-defined]
        self._previous_foreground = None

    # --- behaviour --------------------------------------------------------
    def showEvent(self, event: Any) -> None:  # noqa: ANN401, N802  # pylint: disable=invalid-name
        """Start live refresh while visible."""
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event: Any) -> None:  # noqa: ANN401, N802  # pylint: disable=invalid-name
        """Stop refreshing while hidden."""
        super().hideEvent(event)
        self._timer.stop()

    def refresh(self) -> None:
        """Rebuild the list from the live players registry."""
        connected = PlayersRegistry.get_connected_players()
        count = len(connected)
        self._count_label.setText(f'{count} connecté{"s" if count > 1 else ""}')

        text = self._search.text().strip().lower()
        self._list.clear()
        if text:
            self._section_label.setText('RÉSULTATS (CETTE SESSION)')
            players = [player for player in PlayersRegistry.get_all_players() if _matches(player, text)]
            players.sort(key=lambda player: player.datetime.last_seen, reverse=True)
            players = players[:MAX_SEARCH_RESULTS]
            if not players:
                self._add_item('Aucun joueur trouvé dans cette session — Entrée pour chercher dans l\'historique', '#a293ad')
        else:
            self._section_label.setText('DERNIERS ARRIVÉS')
            players = sorted(connected, key=lambda player: player.datetime.last_rejoin, reverse=True)[:MAX_RECENT_PLAYERS]
            if not players:
                self._add_item('Aucun joueur connecté pour l\'instant', '#a293ad')

        for player in players:
            is_connected = PlayersRegistry.is_player_connected(player)
            dot = '🟢' if is_connected else '🔴'
            since = _format_since(player.datetime.last_rejoin if is_connected else player.datetime.last_seen)
            port = getattr(getattr(player, 'ports', None), 'last', None)
            note = PlayerNotes.get(player.ip)
            tooltip = f'IP : {player.ip}' + (f'  ·  Port : {port}' if port else '') + (f'\n📝 {note}' if note else '')
            text = f'{dot} {_player_label(player)}   {since}'
            if note:
                short_note = note if len(note) <= 40 else f'{note[:39]}…'  # noqa: PLR2004
                text += f'\n      📝 {short_note}'
            item = self._add_item(text, tag_color(player.ip) or '#efd7f3', tooltip=tooltip)
            item.setData(Qt.ItemDataRole.UserRole, {'ip': player.ip, 'port': port, 'names': list(player.usernames)})

        self._fit_height()

    def _fit_height(self) -> None:
        """Grow or shrink the window with the number of rows (capped to the screen height)."""
        count = self._list.count()
        rows_height = sum(max(self._list.sizeHintForRow(i), 18) for i in range(count)) if count else 22
        wanted = rows_height + 2 * self._list.frameWidth() + 4
        screen = self.screen() or QGuiApplication.primaryScreen()
        max_list_height = max(120, (screen.availableGeometry().height() if screen else 900) - 220)
        self._list.setFixedHeight(min(wanted, max_list_height))
        self._list.updateGeometry()
        for widget in (self._list.parentWidget(), self):
            layout = widget.layout() if widget is not None else None
            if layout is not None:
                layout.invalidate()
                layout.activate()
        self.setFixedHeight(self.layout().totalSizeHint().height())

    def _show_player_menu(self, pos: QPoint) -> None:
        """Right-click menu: copy IP, port, IP:port or username."""
        item = self._list.itemAt(pos)
        data = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if not isinstance(data, dict):
            return
        clipboard = QGuiApplication.clipboard()
        ip, port, names = data['ip'], data['port'], data['names']
        menu = QMenu(self)
        menu.addAction(f"Copier l'IP  ({ip})", lambda: clipboard.setText(ip))
        if port:
            menu.addAction(f'Copier le port  ({port})', lambda: clipboard.setText(str(port)))
            menu.addAction(f'Copier IP:port  ({ip}:{port})', lambda: clipboard.setText(f'{ip}:{port}'))
        if names:
            menu.addAction(f'Copier le pseudo  ({", ".join(names)})', lambda: clipboard.setText(', '.join(names)))
        menu.addSeparator()
        menu.addAction('Fiche joueur…', lambda: open_player_card(None, ip, names, self.refresh))
        menu.addAction('Modifier la note…' if PlayerNotes.get(ip) else 'Ajouter une note…', lambda: edit_player_note(self, ip, names) and self.refresh())
        add_tag_menu(menu, ip, names, self.refresh)
        menu.addAction("Chercher dans l'historique", lambda: self._open_history_search(names[0] if names else ip))
        self._timer.stop()  # keep the list stable while the menu is open
        menu.exec(self._list.viewport().mapToGlobal(pos))
        if self.isVisible():
            self._timer.start()

    def _add_item(self, text: str, color: str, *, tooltip: str | None = None) -> QListWidgetItem:
        item = QListWidgetItem(text)
        item.setForeground(QColor('#ffffff') if color == '#efd7f3' else QColor(color))
        if tooltip:
            item.setToolTip(tooltip)
        self._list.addItem(item)
        return item

    def _search_in_history(self) -> None:
        self._open_history_search(self._search.text().strip())

    # --- drag to move -----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Start dragging the overlay."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Move the overlay with the mouse."""
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Remember where the overlay was dropped."""
        if self._drag_offset is not None:
            self._drag_offset = None
            self._config['x'], self._config['y'] = self.x(), self.y()
            save_overlay_config(self._config)
        super().mouseReleaseEvent(event)


def _format_since(moment: datetime) -> str:
    """Return a short 'il y a …' string."""
    seconds = max(0, int((datetime.now(tz=moment.tzinfo) - moment).total_seconds()))
    if seconds < 60:  # noqa: PLR2004
        return f'{seconds}s'
    if seconds < 3600:  # noqa: PLR2004
        return f'{seconds // 60} min'
    return f'{seconds // 3600} h'


# ----------------------------------------------------------------------------
# Settings dialog
# ----------------------------------------------------------------------------
class OverlaySettingsDialog(QDialog):
    """Let the user choose the overlay hotkey and opacity."""

    def __init__(self, parent: QWidget | None, current_hotkey: str, current_opacity: int) -> None:
        """Build the dialog."""
        super().__init__(parent)
        self.setWindowTitle('Mini-fenêtre en jeu - Réglages')
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        info = QLabel(
            'Clique dans le champ puis appuie sur la touche (ou la combinaison) de ton choix.\n'
            'Exemples : F8, Ctrl+F9, Alt+B, Inser.\n'
            'Tu peux aussi utiliser un bouton de souris (pratique si ton mod menu bloque les touches F).\n\n'
            "Astuce : mets ton jeu en « Plein écran fenêtré » (borderless) pour que la mini-fenêtre s'affiche par-dessus.",
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        row.addWidget(QLabel('Raccourci :'))
        self._editor = QKeySequenceEdit(QKeySequence('' if current_hotkey in MOUSE_BUTTONS else current_hotkey))
        self._editor.setMaximumSequenceLength(1)
        row.addWidget(self._editor, 1)
        clear_button = QPushButton('Effacer')
        clear_button.clicked.connect(self._editor.clear)
        row.addWidget(clear_button)
        layout.addLayout(row)

        mouse_row = QHBoxLayout()
        mouse_row.addWidget(QLabel('Ou souris :'))
        self._mouse = QComboBox()
        self._mouse.addItem('Aucun (utiliser la touche ci-dessus)', '')
        for key, (_vk, label) in MOUSE_BUTTONS.items():
            self._mouse.addItem(label, key)
        if current_hotkey in MOUSE_BUTTONS:
            self._mouse.setCurrentIndex(self._mouse.findData(current_hotkey))
        mouse_row.addWidget(self._mouse, 1)
        layout.addLayout(mouse_row)
        self._editor.keySequenceChanged.connect(lambda seq: (not seq.isEmpty()) and self._mouse.setCurrentIndex(0))
        self._mouse.currentIndexChanged.connect(lambda i: i > 0 and self._editor.clear())

        # Live key tester: shows what Windows really receives from the keyboard / mouse
        self._tester = QLabel()
        self._tester.setWordWrap(True)
        self._tester.setMinimumHeight(52)
        self._tester.setStyleSheet('padding: 8px; border: 1px dashed rgba(63, 240, 255, 0.5); border-radius: 6px;')
        layout.addWidget(QLabel('<b>Test :</b> appuie sur ta touche, elle doit apparaître ici.'))
        layout.addWidget(self._tester)
        if sys.platform == 'win32' and not is_running_as_admin():
            admin_row = QHBoxLayout()
            admin_info = QLabel('Ça marche partout sauf en jeu ? Si GTA est lancé en administrateur, BTXSniffer doit l\'être aussi.')
            admin_info.setWordWrap(True)
            admin_button = QPushButton('Relancer en administrateur')
            admin_button.clicked.connect(lambda: relaunch_as_admin(self.parentWidget() or self))
            admin_row.addWidget(admin_info, 1)
            admin_row.addWidget(admin_button)
            layout.addLayout(admin_row)
        self._seen_keys: list[str] = []
        self._shortcut_seen = False
        self._test_timer = QTimer(self)
        self._test_timer.setInterval(40)
        self._test_timer.timeout.connect(self._poll_test)
        if sys.platform == 'win32':
            self._tester.setText('En attente… (appuie sur une touche)')
            self._test_timer.start()
        else:
            self._tester.setText('Le test des touches est disponible sous Windows.')

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel('Opacité :'))
        self._opacity = QSlider(Qt.Orientation.Horizontal)
        self._opacity.setRange(30, 100)
        self._opacity.setValue(current_opacity)
        self._opacity_value = QLabel(f'{current_opacity} %')
        self._opacity.valueChanged.connect(lambda value: self._opacity_value.setText(f'{value} %'))
        opacity_row.addWidget(self._opacity, 1)
        opacity_row.addWidget(self._opacity_value)
        layout.addLayout(opacity_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Enregistrer')
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Annuler')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setMinimumWidth(520)
        self.setMinimumHeight(layout.heightForWidth(520) if layout.hasHeightForWidth() else 0)
        self.adjustSize()

    def hotkey(self) -> str:
        """Return the chosen shortcut as portable text (e.g. 'Ctrl+F8' or 'Souris4')."""
        mouse = self._mouse.currentData()
        if mouse:
            return str(mouse)
        return self._editor.keySequence().toString(QKeySequence.SequenceFormat.PortableText)

    def _poll_test(self) -> None:
        """Show which keys Windows currently sees as pressed, and whether the chosen shortcut matches."""
        try:
            get_state = ctypes.windll.user32.GetAsyncKeyState  # type: ignore[attr-defined]
            down = [vk for vk in range(1, 255) if vk not in _VK_IGNORED and get_state(vk) & 0x8000]
        except (OSError, AttributeError):
            return
        names = [vk_name(vk) for vk in down if vk not in (0x01,)]  # left click is used to click in this window
        if names:
            combo = ' + '.join(names)
            if not self._seen_keys or self._seen_keys[-1] != combo:
                self._seen_keys = [*self._seen_keys[-3:], combo]
            converted = _sequence_to_win32(self.hotkey())
            if converted is not None and converted[1] in down:
                self._shortcut_seen = True
        lines = [f'Dernières touches reçues par Windows : {" | ".join(self._seen_keys)}' if self._seen_keys else 'En attente… (appuie sur une touche)']
        if self._shortcut_seen:
            lines.append(f'✅ Ton raccourci ({display_hotkey(self.hotkey())}) est bien détecté.')
        elif self._seen_keys:
            lines.append(
                "Si ta touche n'apparaît pas : essaie avec Fn (PC portable), ou choisis une autre touche / un bouton de souris.",
            )
        self._tester.setText('\n'.join(lines))

    def opacity(self) -> int:
        """Return the chosen opacity percentage."""
        return self._opacity.value()


class OverlayController:
    """Glue between the main window, the overlay, the hotkey and its settings."""

    def __init__(self, main_window: QWidget, open_history_search: Callable[[str], None]) -> None:
        """Create the overlay and bind the saved hotkey."""
        self._main_window = main_window
        self.overlay = BTXOverlay(open_history_search)
        self._hotkey = GlobalHotkey(main_window)
        self._hotkey.activated.connect(self.overlay.toggle)
        self._apply_hotkey(load_overlay_config()['hotkey'])
        # BTX: warn (once) when GTA runs as administrator but BTXSniffer does not -> keys are invisible to us
        self._admin_warned = False
        self._admin_timer = QTimer(main_window)
        self._admin_timer.setInterval(3000)
        self._admin_timer.timeout.connect(self._check_game_rights)
        if sys.platform == 'win32' and not is_running_as_admin():
            self._admin_timer.start()

    def _check_game_rights(self) -> None:
        if self._admin_warned or not elevated_game_in_foreground():
            return
        self._admin_warned = True
        self._admin_timer.stop()
        QTimer.singleShot(0, self._warn_game_is_admin)

    def _warn_game_is_admin(self) -> None:
        from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

        box = QMessageBox(self._main_window)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle('Mini-fenêtre en jeu')
        box.setText(
            'GTA est lancé en administrateur, mais pas BTXSniffer.\n\n'
            'Windows empêche alors BTXSniffer de voir tes touches pendant que tu joues : '
            'le raccourci de la mini-fenêtre ne peut pas marcher.\n\n'
            'Solution : relancer BTXSniffer en administrateur.',
        )
        relaunch = box.addButton('Relancer en administrateur', QMessageBox.ButtonRole.AcceptRole)
        box.addButton('Plus tard', QMessageBox.ButtonRole.RejectRole)
        box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on=True)
        box.exec()
        if box.clickedButton() is relaunch and not relaunch_as_admin(self._main_window):
            QMessageBox.warning(self._main_window, 'Mini-fenêtre en jeu', "Le relancement en administrateur a été annulé ou a échoué.")

    def _apply_hotkey(self, sequence_text: str) -> bool:
        ok = self._hotkey.set_sequence(sequence_text)
        short = {'Souris4': 'Souris 4', 'Souris5': 'Souris 5', 'SourisMilieu': 'Clic molette'}
        self.overlay.set_hotkey_hint(short.get(sequence_text) or display_hotkey(sequence_text) if ok and sequence_text else '')
        return ok

    def toggle(self) -> None:
        """Show/hide the overlay from the menu."""
        self.overlay.toggle()

    def open_settings(self) -> None:
        """Open the hotkey/opacity dialog and apply the result."""
        config = load_overlay_config()
        dialog = OverlaySettingsDialog(self._main_window, str(config['hotkey']), int(config['opacity']))
        self._hotkey.set_paused(True)
        try:
            accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally:
            self._hotkey.set_paused(False)
        if not accepted:
            return
        new_hotkey = dialog.hotkey()
        if not self._apply_hotkey(new_hotkey):
            from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

            QMessageBox.warning(
                self._main_window,
                'Raccourci indisponible',
                f'Impossible d\'utiliser « {new_hotkey} ».\n\n'
                'Cette touche n\'est pas prise en charge. Choisis une touche F1-F12, une lettre, un chiffre ou une combinaison (ex. F8, Ctrl+F9).',
            )
            self._apply_hotkey(str(config['hotkey']))
            return
        config = load_overlay_config()
        config['hotkey'] = new_hotkey
        save_overlay_config(config)
        self.overlay.set_opacity_percent(dialog.opacity())

    def shutdown(self) -> None:
        """Release the hotkey and close the overlay."""
        self._admin_timer.stop()
        self._hotkey.unregister()
        self.overlay.close()
        self._hotkey.close()
