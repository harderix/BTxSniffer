"""Live packet latency graph window for the current capture session."""

from session_sniffer.guis.player_rate_graph import SingleRateGraphBase

_FLOOR_MS = 1.0


class PacketsLatencyGraphWindow(SingleRateGraphBase):
    """A standalone window displaying live per-packet latency over time."""

    WINDOW_TITLE = 'Graphique de latence des paquets'
    LEFT_LABEL = 'Latence (ms/s)'
    AXIS_PEN = '#ff9800'
    CURVE_PEN = '#ff9800'
    CURVE_BRUSH = (255, 152, 0, 60)
    AVG_PEN = '#e65100'
    Y_FLOOR = _FLOOR_MS

    # Public API —————————————————————————————————————————————————————————————

    def update_latency(self, latency_ms: float) -> None:
        """Append a new latency sample and refresh the graph."""
        self.update_graph(latency_ms)
