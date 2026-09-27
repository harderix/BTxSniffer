"""BTXSniffer colour themes.

The BTX look is written everywhere in the code as neon-pink / violet / cyan colour literals.
To offer other themes without touching every file, this module installs an import hook
(only when a theme other than the default is chosen) that rewrites the colour literals of
the session_sniffer modules while they are loaded: pink/violet hues are moved to the theme's
main hue and cyan hues to its secondary hue. Status colours (green, red, yellow, orange...)
are left untouched, and so are colours chosen by the user in the settings.

The chosen theme is read once at start-up, so changing it requires a restart.
"""

import colorsys
import importlib.abc
import importlib.util
import json
import os
import re
import sys
import types
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from session_sniffer.constants.standalone import TITLE


@dataclass(frozen=True)
class Theme:
    """Hue targets of a theme (None = original BTX colours)."""

    label: str
    main_hue: float | None = None  # where neon pink / violet goes
    second_hue: float | None = None  # where neon cyan goes
    bg_hue: float | None = None  # hue of the tinted dark backgrounds and light text
    main_sat: float = 1.0
    second_sat: float = 1.0
    bg_sat: float = 1.0


DEFAULT_THEME = 'rose'
THEMES: dict[str, Theme] = {
    'rose': Theme('Néon rose (BTX)'),
    'bleu': Theme('Néon bleu', main_hue=208, second_hue=180, bg_hue=222),
    'vert': Theme('Néon vert', main_hue=142, second_hue=188, bg_hue=165, bg_sat=0.8),
    'violet': Theme('Néon violet', main_hue=268, second_hue=320, bg_hue=262),
    'sobre': Theme('Sombre sobre', main_hue=212, second_hue=200, bg_hue=220, main_sat=0.5, second_sat=0.45, bg_sat=0.16),
}

_PINK_REF = 311.0  # hue of #ff2bd6, the BTX accent
_CYAN_REF = 184.0  # hue of #3ff0ff


# ---------- choice persistence ----------


def _config_path() -> Path:
    if sys.platform == 'win32':
        base = Path(os.getenv('APPDATA', str(Path.home() / 'AppData' / 'Roaming')))
    else:
        base = Path(os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    return base / TITLE / 'btx_ui.json'


def _read_config() -> dict:
    with suppress(OSError, ValueError, TypeError):
        data = json.loads(_config_path().read_text(encoding='utf-8'))
        if isinstance(data, dict):
            return data
    return {}


def saved_theme() -> str:
    """Theme chosen by the user (applies at the next start)."""
    theme = str(_read_config().get('theme', DEFAULT_THEME))
    return theme if theme in THEMES else DEFAULT_THEME


def save_theme(theme: str) -> None:
    """Remember *theme* for the next start."""
    if theme not in THEMES:
        return
    data = _read_config()
    data['theme'] = theme
    with suppress(OSError):
        path = _config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


ACTIVE_THEME: str = DEFAULT_THEME  # theme really applied in this run


# ---------- colour remapping ----------


def _shift(r: int, g: int, b: int, theme: Theme) -> tuple[int, int, int]:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hue = h * 360
    if s < 0.08:  # greys, black, white
        return r, g, b
    if 250 <= hue <= 345:  # neon pink / magenta / violet family
        vivid = s >= 0.45 and 0.25 <= l <= 0.85
        target = theme.main_hue if vivid or theme.bg_hue is None else theme.bg_hue
        if target is None:
            return r, g, b
        hue = (target + (hue - _PINK_REF) * 0.6) % 360
        s = min(1.0, s * (theme.main_sat if vivid else theme.bg_sat))
    elif 165 <= hue <= 205:  # neon cyan family
        if theme.second_hue is None:
            return r, g, b
        hue = (theme.second_hue + (hue - _CYAN_REF)) % 360
        s = min(1.0, s * theme.second_sat)
    else:
        return r, g, b
    nr, ng, nb = colorsys.hls_to_rgb(hue / 360, l, s)
    return round(nr * 255), round(ng * 255), round(nb * 255)


_HEX_RE = re.compile(r'#([0-9a-fA-F]{6})\b')
_RGB_RE = re.compile(r'(rgba?\(\s*)(\d{1,3})(\s*,\s*)(\d{1,3})(\s*,\s*)(\d{1,3})')
_cache: dict[str, str] = {}


def remap_text(text: str, theme: Theme | None = None) -> str:
    """Return *text* with every BTX colour replaced by its equivalent in *theme*."""
    theme = theme or THEMES[ACTIVE_THEME]
    if theme.main_hue is None or ('#' not in text and 'rgb' not in text):
        return text
    key = text if theme is THEMES[ACTIVE_THEME] else ''
    if key and key in _cache:
        return _cache[key]

    def hex_sub(match: re.Match[str]) -> str:
        value = match.group(1)
        r, g, b = int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
        nr, ng, nb = _shift(r, g, b, theme)
        if (nr, ng, nb) == (r, g, b):
            return match.group(0)
        out = f'{nr:02x}{ng:02x}{nb:02x}'
        return '#' + (out.upper() if value.isupper() else out)

    def rgb_sub(match: re.Match[str]) -> str:
        r, g, b = (min(255, int(match.group(i))) for i in (2, 4, 6))
        nr, ng, nb = _shift(r, g, b, theme)
        return f'{match.group(1)}{nr}{match.group(3)}{ng}{match.group(5)}{nb}'

    result = _RGB_RE.sub(rgb_sub, _HEX_RE.sub(hex_sub, text))
    if key and len(_cache) < 20_000:
        _cache[key] = result
    return result


# ---------- import hook ----------


def _transform_const(value: object) -> object:
    if isinstance(value, str):
        return remap_text(value)
    if isinstance(value, types.CodeType):
        return _transform_code(value)
    if isinstance(value, tuple):
        new = tuple(_transform_const(v) for v in value)
        return new if any(a is not b for a, b in zip(new, value, strict=True)) else value
    if isinstance(value, frozenset):
        new_set = frozenset(_transform_const(v) for v in value)
        return new_set if new_set != value else value
    return value


def _transform_code(code: types.CodeType) -> types.CodeType:
    consts = tuple(_transform_const(c) for c in code.co_consts)
    if all(a is b for a, b in zip(consts, code.co_consts, strict=True)):
        return code
    return code.replace(co_consts=consts)


class _ThemedLoader(importlib.abc.Loader):
    def __init__(self, inner: importlib.abc.Loader) -> None:
        self._inner = inner

    def create_module(self, spec):  # noqa: ANN001, ANN201
        return self._inner.create_module(spec)

    def exec_module(self, module: types.ModuleType) -> None:
        try:
            code = self._inner.get_code(module.__name__)  # type: ignore[attr-defined]
            themed = _transform_code(code) if code is not None else None
        except Exception:  # noqa: BLE001 - if anything goes wrong, load the module normally
            themed = None
        if themed is None:
            self._inner.exec_module(module)
            return
        exec(themed, module.__dict__)  # noqa: S102

    def __getattr__(self, name: str) -> object:  # get_resource_reader, is_package, get_source...
        return getattr(self._inner, name)


class _ThemedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path, target=None):  # noqa: ANN001, ANN201, ARG002
        if not fullname.startswith('session_sniffer.') or fullname == __name__:
            return None
        for finder in sys.meta_path:
            if finder is self or not hasattr(finder, 'find_spec'):
                continue
            try:
                spec = finder.find_spec(fullname, path, target)
            except (ImportError, AttributeError, ValueError):
                continue
            if spec is None:
                continue
            loader = spec.loader
            if loader is not None and hasattr(loader, 'get_code') and hasattr(loader, 'exec_module'):
                spec.loader = _ThemedLoader(loader)
            return spec
        return None


def install() -> None:
    """Apply the saved theme for this run (called very early, from session_sniffer/__init__)."""
    global ACTIVE_THEME  # noqa: PLW0603
    theme = saved_theme()
    ACTIVE_THEME = theme
    if THEMES[theme].main_hue is None:
        return  # default BTX colours: nothing to do
    if not any(isinstance(f, _ThemedFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, _ThemedFinder())


def preview_colors(theme_key: str) -> tuple[str, str, str]:
    """(accent, secondary, background) of a theme, for the menu swatches."""
    theme = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    if theme.main_hue is None:
        return '#ff2bd6', '#3ff0ff', '#1b1024'
    return tuple(remap_text(c, theme) for c in ('#ff2bd6', '#3ff0ff', '#1b1024'))  # type: ignore[return-value]
