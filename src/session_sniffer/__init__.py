"""The package contains all the modules for the project."""

# BTX: apply the colour theme chosen by the user (must run before any GUI module is imported).
try:
    from session_sniffer import btx_theme as _btx_theme

    _btx_theme.install()
except Exception:  # noqa: BLE001, S110 - a theme problem must never prevent the app from starting
    pass
