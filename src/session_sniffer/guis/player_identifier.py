"""Player Identifier — baseline PPS/BPS profiles then detect spikes to correlate IPs to players."""

from math import sqrt
from typing import TYPE_CHECKING, ClassVar, override

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from session_sniffer.guis._player_identifier_core import (
    BUTTON_WIDTH,
    CONVERGENCE_GREEN,
    CONVERGENCE_RECENT_WINDOW,
    CONVERGENCE_YELLOW,
    MIN_CONNECTED_PLAYERS,
    PROGRESS_BAR_WIDTH,
    UPDATE_INTERVAL_MS,
    IPBaseline,
    Phase,
    compute_aggregate_zscore,
)
from session_sniffer.guis.stylesheets import (
    PROGRESS_BAR_CHUNK_BLUE_STYLESHEET,
    PROGRESS_BAR_CHUNK_GREEN_STYLESHEET,
    PROGRESS_BAR_CHUNK_ORANGE_STYLESHEET,
    PROGRESS_BAR_CHUNK_RED_STYLESHEET,
    PROGRESS_BAR_IDLE_STYLESHEET,
)
from session_sniffer.models.player import PlayerBandwidth
from session_sniffer.networking.third_party_servers import is_third_party_server_ip
from session_sniffer.player.registry import PlayersRegistry
from session_sniffer.settings import Settings
from session_sniffer.text_utils import pluralize

if TYPE_CHECKING:
    from collections.abc import Callable

    from session_sniffer.models.player import Player


_PROGRESS_BAR_BLUE_GRADIENT: list[tuple[float, QColor]] = [
    (0.0, QColor('#e312ab')),
    (0.5, QColor('#f63bc4')),
    (1.0, QColor('#fa60d1')),
]
_PROGRESS_BAR_GREEN_GRADIENT: list[tuple[float, QColor]] = [
    (0.0, QColor('#059669')),
    (0.5, QColor('#10b981')),
    (1.0, QColor('#34d399')),
]
_PROGRESS_BAR_ORANGE_GRADIENT: list[tuple[float, QColor]] = [
    (0.0, QColor('#d97706')),
    (0.5, QColor('#f59e0b')),
    (1.0, QColor('#fbbf24')),
]
_PROGRESS_BAR_RED_GRADIENT: list[tuple[float, QColor]] = [
    (0.0, QColor('#b91c1c')),
    (0.5, QColor('#ef4444')),
    (1.0, QColor('#f87171')),
]


class PlayerIdentifierProgressBar(QProgressBar):
    """Capsule progress bar with anti-aliased clipping to prevent chunk overflow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the custom capsule progress bar."""
        super().__init__(parent)
        self.setRange(0, 100)
        self.setFixedHeight(24)
        self.setFixedWidth(PROGRESS_BAR_WIDTH)
        self.setTextVisible(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chunk_gradient: list[tuple[float, QColor]] | None = None
        self._background_color = QColor('#150d1a')
        self._border_color = QColor('#372144')

    @override
    def setStyleSheet(self, styleSheet: str) -> None:
        super().setStyleSheet(styleSheet)
        if '#e312ab' in styleSheet:
            self._chunk_gradient = _PROGRESS_BAR_BLUE_GRADIENT
        elif '#059669' in styleSheet:
            self._chunk_gradient = _PROGRESS_BAR_GREEN_GRADIENT
        elif '#d97706' in styleSheet:
            self._chunk_gradient = _PROGRESS_BAR_ORANGE_GRADIENT
        elif '#b91c1c' in styleSheet:
            self._chunk_gradient = _PROGRESS_BAR_RED_GRADIENT
        else:
            self._chunk_gradient = None
        self.update()

    @override
    def paintEvent(self, a0: QPaintEvent | None) -> None:  # pylint: disable=unused-argument
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            bounding_rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            capsule_radius = bounding_rect.height() / 2.0

            outer_path = QPainterPath()
            outer_path.addRoundedRect(bounding_rect, capsule_radius, capsule_radius)
            painter.fillPath(outer_path, self._background_color)
            painter.setPen(QPen(self._border_color, 1.0))
            painter.drawPath(outer_path)

            current_value = self.value()
            if current_value > 0 and self._chunk_gradient is not None:
                inner_rect = bounding_rect.adjusted(2.0, 2.0, -2.0, -2.0)
                inner_radius = max(0.0, inner_rect.height() / 2.0)
                clip_path = QPainterPath()
                clip_path.addRoundedRect(inner_rect, inner_radius, inner_radius)

                value_range = self.maximum() - self.minimum()
                progress_ratio = (current_value - self.minimum()) / value_range if value_range > 0 else 0.0
                chunk_width = inner_rect.width() * progress_ratio
                chunk_rect = QRectF(inner_rect.x(), inner_rect.y(), chunk_width, inner_rect.height())

                painter.save()
                painter.setClipPath(clip_path)
                linear_gradient = QLinearGradient(inner_rect.left(), 0.0, inner_rect.right(), 0.0)
                for stop_point, stop_color in self._chunk_gradient:
                    linear_gradient.setColorAt(stop_point, stop_color)
                painter.fillRect(chunk_rect, linear_gradient)
                painter.restore()

            displayed_text = self.text()
            if displayed_text and self.isTextVisible():
                painter.setPen(QColor('#ffffff'))
                text_font = self.font()
                text_font.setPointSize(9)
                text_font.setBold(True)
                painter.setFont(text_font)
                painter.drawText(bounding_rect, Qt.AlignmentFlag.AlignCenter, displayed_text)
        finally:
            painter.end()


class PlayerIdentifierTracker:
    """Global tracker for IPs currently identified by the Player Identifier tool."""

    identified_ips: ClassVar[set[str]] = set()

    @classmethod
    def is_identified(cls, ip: str) -> bool:
        """Return whether the given IP is currently identified."""
        return ip in cls.identified_ips

    @classmethod
    def set_identified_ips(cls, ips: set[str]) -> None:
        """Update the set of identified IPs."""
        cls.identified_ips = ips


class PlayerIdentifierWidget(QWidget):
    """Baseline PPS/BPS then detect spikes to identify which IP belongs to a target player."""

    def __init__(
        self,
        select_ips_callback: Callable[[list[str]], None] | None = None,
        deselect_ips_callback: Callable[[list[str] | None], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the Player Identifier widget."""
        super().__init__(parent)

        self._select_ips = select_ips_callback
        self._deselect_ips = deselect_ips_callback
        self._phase = Phase.IDLE
        self._baseline_ips: set[str] = set()
        self._baselines: dict[str, IPBaseline] = {}
        self._sample_count = 0
        self._spike_streak: dict[str, int] = {}
        self._total_spike_duration: dict[str, int] = {}
        self._contamination_streak: dict[str, int] = {}
        self._identified_ips: set[str] = set()
        self._currently_selected_ips: set[str] = set()
        self._auto_select: bool = True
        PlayerIdentifierTracker.set_identified_ips(set())

        # Widget update caches — skip redundant repaints when values haven't changed
        self._prev_stability_pct: int | None = None
        self._prev_stability_format: str | None = None
        self._prev_stability_style: str | None = None
        self._prev_stability_text: str | None = None
        self._prev_sample_text: str | None = None
        self._prev_result_text: str | None = None

        layout = QVBoxLayout(self)

        # Instructions
        self._instructions = QLabel()
        self._instructions.setWordWrap(True)
        self._instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_idle_instructions()
        layout.addWidget(self._instructions)

        # Stability indicator
        self._stability_label = QLabel('Stabilité : —')
        self._stability_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stability_label.setToolTip(
            "Indique si les mesures de trafic se sont stabilisées.\n\nVERT = Le trafic est stable. Tu peux arrêter la référence.\nJAUNE = Le trafic change encore. Continue d'attendre.\nORANGE = Collecte des premières données. Pas encore assez d'échantillons.\nROUGE = Le trafic est très instable. Ne bouge pas et attends.",
        )
        self._stability_label.setVisible(False)
        layout.addWidget(self._stability_label)

        self._stability_bar = PlayerIdentifierProgressBar()
        self._stability_bar.setRange(0, 100)
        self._stability_bar.setValue(0)
        self._stability_bar.setTextVisible(True)
        self._stability_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stability_bar.setFormat('En attente...')
        self._stability_bar.setFixedWidth(PROGRESS_BAR_WIDTH)
        self._stability_bar.setStyleSheet(PROGRESS_BAR_IDLE_STYLESHEET)
        self._stability_bar.setToolTip(
            'Progression vers une référence stable.\n\nPendant la référence : se remplit à mesure que le trafic se stabilise. À 100 % et en vert, les données sont fiables.\n\nPendant la recherche : se remplit quand une IP candidate garde un pic de trafic. Atteint 100 % quand une correspondance est confirmée.',
        )
        self._stability_bar.setVisible(False)
        layout.addWidget(self._stability_bar, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Sample count label
        self._sample_label = QLabel('')
        self._sample_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sample_label.setToolTip(
            "Nombre d'IP suivies et nombre de mesures d'une seconde enregistrées.\nPlus de mesures = référence plus précise.",
        )
        self._sample_label.setVisible(False)
        layout.addWidget(self._sample_label)

        # Result label
        self._result_label = QLabel('')
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        # Buttons row
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._baseline_button = QPushButton('Lancer la référence')
        self._baseline_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._baseline_button.setMinimumWidth(BUTTON_WIDTH)
        self._baseline_button.clicked.connect(self._on_baseline_button_clicked)
        button_layout.addWidget(self._baseline_button)

        self._resolve_button = QPushButton('Trouver')
        self._resolve_button.setToolTip(
            f'Étape 2 : commence à surveiller les pics de trafic.\n\nAprès avoir cliqué, observe le joueur que tu veux identifier avec le canon orbital, une caméra de surveillance, ou en t\'approchant de lui.\nQuand ton jeu charge ce joueur, il échange plus de données avec son IP, ce qui crée un pic par rapport à la référence.\n\nUne IP doit avoir un pic pendant {self._spike_sustained_seconds} secondes d\'affilée pour être confirmée.\n\nAstuce : la détection marche mieux quand le joueur cible bouge — un joueur en mouvement génère beaucoup plus de trafic qu\'un joueur immobile.',
        )
        self._resolve_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._resolve_button.setMinimumWidth(BUTTON_WIDTH)
        self._resolve_button.clicked.connect(self._on_resolve)
        self._resolve_button.setEnabled(False)
        button_layout.addWidget(self._resolve_button)

        self._reset_button = QPushButton("Réinitialiser l'analyse")
        self._reset_button.setToolTip(
            "Efface les candidats et les joueurs identifiés de l'analyse en cours, en gardant la référence pour pouvoir chercher un autre joueur tout de suite.",
        )
        self._reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_button.setMinimumWidth(BUTTON_WIDTH)
        self._reset_button.clicked.connect(self._on_reset_scan)
        self._reset_button.setEnabled(False)
        button_layout.addWidget(self._reset_button)

        self._update_baseline_button_state()

        layout.addLayout(button_layout)

        # Table selection controls
        table_selection_layout = QHBoxLayout()
        table_selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._select_button = QPushButton('Sélectionner dans le tableau')
        self._select_button.setToolTip('Sélectionner et afficher tous les joueurs identifiés dans le tableau des joueurs connectés.')
        self._select_button.setMinimumWidth(BUTTON_WIDTH)
        self._select_button.setEnabled(False)
        self._select_button.clicked.connect(self._select_resolved)
        table_selection_layout.addWidget(self._select_button)

        self._deselect_button = QPushButton('Désélectionner dans le tableau')
        self._deselect_button.setToolTip('Désélectionner tous les joueurs identifiés dans le tableau des joueurs connectés.')
        self._deselect_button.setMinimumWidth(BUTTON_WIDTH)
        self._deselect_button.setEnabled(False)
        self._deselect_button.clicked.connect(self._deselect_resolved)
        table_selection_layout.addWidget(self._deselect_button)

        self._auto_select_checkbox = QCheckBox('Sélection auto dans le tableau')
        self._auto_select_checkbox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._auto_select_checkbox.toggled.connect(self._on_auto_select_toggled)
        self._auto_select_checkbox.setToolTip(
            'Garder automatiquement les joueurs identifiés sélectionnés dans le tableau des joueurs connectés.\n\nMise à jour à chaque analyse. Désactive pour sélectionner toi-même.',
        )
        self._auto_select_checkbox.setChecked(True)
        table_selection_layout.addWidget(self._auto_select_checkbox)

        layout.addLayout(table_selection_layout)
        layout.addStretch()

        # Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    # -- Phase transitions ----------------------------------------------------

    def _update_baseline_button_state(self) -> None:
        if self._phase == Phase.IDLE:
            self._baseline_button.setText('Lancer la référence')
            self._baseline_button.setToolTip(
                f'Étape 1 : enregistre le trafic normal (PPS/BPS) de chaque IP présente dans la session.\n\nIMPORTANT : sois SEUL et immobile (ex. dans un bunker, une base, ou loin des autres joueurs) avant de cliquer.\n\nSeules les IP connectées MAINTENANT seront suivies. Ceux qui arrivent après sont ignorés.\n\nLa référence tourne jusqu\'à ce que le trafic soit stable ou que {self._baseline_max_seconds}s soient passées, puis se verrouille automatiquement.',
            )
            self._baseline_button.setEnabled(True)
        elif self._phase == Phase.BASELINE:
            self._baseline_button.setText('Annuler la référence')
            self._baseline_button.setToolTip("Annuler l'enregistrement de la référence et revenir à l'état initial.")
            self._baseline_button.setEnabled(True)
        else:
            self._baseline_button.setText('Réinitialiser la référence')
            self._baseline_button.setToolTip('Supprimer les données de référence enregistrées et recommencer à zéro.')
            self._baseline_button.setEnabled(True)

    def _on_baseline_button_clicked(self) -> None:
        if self._phase == Phase.IDLE:
            self._on_start_baseline()
        else:
            self.reset()

    def _set_idle_instructions(self) -> None:
        self._instructions.setText(
            f'<b>Comment utiliser le Trouveur de joueur :</b><br><br><b>1.</b> Va quelque part seul en jeu, sans aucun joueur près de toi (ex. un bunker, une base ou une zone vide).<br><b>2.</b> Clique sur <b>Lancer la référence</b> pour enregistrer le trafic normal de chaque IP de la session. Reste immobile et n\'interagis avec personne.<br><b>3.</b> La référence se verrouille toute seule quand le trafic est stable (ou après {self._baseline_max_seconds}s).<br><b>4.</b> Clique sur <b>Trouver</b>, puis observe le joueur que tu veux identifier (ex. canon orbital, caméra de surveillance, ou en t\'approchant).<br>L\'outil détecte quelle IP voit son trafic augmenter quand ton jeu charge ce joueur.<br><br><small>Seules les IP présentes au lancement de la référence sont suivies. Ceux qui arrivent après sont ignorés.<br>Astuce : la détection marche mieux quand le joueur cible <b>bouge</b> — un joueur en mouvement génère beaucoup plus de trafic qu\'un joueur immobile.</small>',
        )

    def _on_start_baseline(self) -> None:
        players = [player for player in PlayersRegistry.get_connected_players() if not is_third_party_server_ip(player.ip)]
        if len(players) < MIN_CONNECTED_PLAYERS:
            QMessageBox.warning(
                self,
                'Pas assez de joueurs',
                f'Il faut au moins {MIN_CONNECTED_PLAYERS} joueurs connectés pour utiliser le Trouveur de joueur.\n\nAvec 0 ou 1 joueur, il n\'y a rien à chercher.',
            )
            return

        self._phase = Phase.BASELINE
        self._baselines.clear()
        self._sample_count = 0
        self._spike_streak.clear()
        self._total_spike_duration.clear()
        self._contamination_streak.clear()
        self._identified_ips.clear()
        PlayerIdentifierTracker.set_identified_ips(set())
        self._prev_stability_pct = None
        self._prev_stability_format = None
        self._prev_stability_style = None
        self._prev_stability_text = None
        self._prev_sample_text = None
        self._prev_result_text = None
        self._result_label.setText('')
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(False)

        self._baseline_ips = {player.ip for player in players}
        for ip in self._baseline_ips:
            self._baselines[ip] = IPBaseline()

        num_ips = len(self._baseline_ips)
        self._instructions.setText(
            f'Enregistrement de la référence pour <b>{num_ips}</b> IP{pluralize(num_ips)}…<br><br>Reste immobile pendant l\'enregistrement. Elle se verrouille toute seule quand le trafic est stable (ou après {self._baseline_max_seconds}s).<br>Ne <b>bouge PAS</b> et n\'interagis avec personne pendant l\'enregistrement.',
        )
        self._stability_bar.setFormat('Collecte…')
        self._stability_bar.setValue(0)
        self._stability_bar.setStyleSheet(PROGRESS_BAR_IDLE_STYLESHEET)
        self._prev_stability_pct = 0
        self._prev_stability_format = 'Collecting…'
        self._prev_stability_style = PROGRESS_BAR_IDLE_STYLESHEET
        self._prev_stability_text = None
        self._stability_label.setVisible(True)
        self._stability_bar.setVisible(True)
        self._sample_label.setVisible(True)
        self._sample_label.setText('')
        self._timer.start(UPDATE_INTERVAL_MS)

    def _auto_stop_baseline(self, reason: str) -> None:
        """Finalize baselines and transition to READY (timer keeps running for contamination monitoring)."""
        for bl in self._baselines.values():
            bl.finalize()
        self._phase = Phase.READY
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(True)
        self._reset_button.setEnabled(False)
        num_ips = len(self._baselines)
        self._instructions.setText(
            f'Référence verrouillée ({reason}) avec <b>{num_ips}</b> IP{pluralize(num_ips)} sur <b>{self._sample_count}</b> mesure{pluralize(self._sample_count)}.<br><br>Clique sur <b>Trouver</b>, puis observe le joueur cible (canon orbital, caméra, ou approche-toi).<br>L\'outil va détecter quelle IP a un pic de trafic quand ton jeu charge ce joueur.<br><small>Astuce : la détection marche mieux quand le joueur cible <b>bouge</b>.</small>',
        )
        self._stability_bar.setFormat('Verrouillée')
        self._stability_bar.setValue(100)
        self._stability_bar.setStyleSheet(PROGRESS_BAR_CHUNK_GREEN_STYLESHEET)
        self._stability_label.setText('Stabilité : <span style="color:green;">Verrouillée</span>')
        self._contamination_streak.clear()

    def _on_resolve(self) -> None:
        self._phase = Phase.RESOLVING
        self._spike_streak.clear()
        self._total_spike_duration.clear()
        self._identified_ips.clear()
        PlayerIdentifierTracker.set_identified_ips(set())
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(True)
        self._select_button.setEnabled(not self._auto_select)
        self._deselect_button.setEnabled(not self._auto_select)
        self._instructions.setText(
            f'Observe le joueur que tu veux identifier (canon orbital, caméra, ou approche-toi).<br><br>L\'outil compare le trafic en direct avec la référence.<br>Si une IP a un pic de trafic pendant <b>{self._spike_sustained_seconds}</b> secondes d\'affilée, elle sera signalée comme correspondance.<br><small>Astuce : la détection marche mieux quand le joueur cible <b>bouge</b>.</small>',
        )
        self._result_label.setText('')
        self._stability_bar.setFormat('Recherche…')
        self._stability_bar.setValue(0)
        self._stability_bar.setStyleSheet(PROGRESS_BAR_CHUNK_BLUE_STYLESHEET)

    def _on_reset_scan(self) -> None:
        """Reset the resolution scan results while keeping the baseline intact."""
        if self._currently_selected_ips and self._deselect_ips is not None:
            self._deselect_ips(list(self._currently_selected_ips))
        self._currently_selected_ips.clear()
        self._spike_streak.clear()
        self._total_spike_duration.clear()
        self._identified_ips.clear()
        PlayerIdentifierTracker.set_identified_ips(set())

        self._phase = Phase.READY
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(True)
        self._reset_button.setEnabled(False)
        self._select_button.setEnabled(False)
        self._deselect_button.setEnabled(False)

        num_ips = len(self._baselines)
        self._instructions.setText(
            f'Référence verrouillée avec <b>{num_ips}</b> IP{pluralize(num_ips)} sur <b>{self._sample_count}</b> mesure{pluralize(self._sample_count)}.<br><br>Clique sur <b>Trouver</b>, puis observe le joueur cible (canon orbital, caméra, ou approche-toi).<br>L\'outil va détecter quelle IP a un pic de trafic quand ton jeu charge ce joueur.<br><small>Astuce : la détection marche mieux quand le joueur cible <b>bouge</b>.</small>',
        )
        self._update_stability(100, PROGRESS_BAR_CHUNK_GREEN_STYLESHEET, 'Stability: <span style="color:green;">Locked</span>', bar_format='Locked')
        self._update_sample_label(f'{num_ips} IP{pluralize(num_ips)} · {self._sample_count} sample{pluralize(self._sample_count)}')
        self._update_result_label('')
        self._contamination_streak.clear()

    def _on_auto_select_toggled(self, checked: bool) -> None:  # noqa: FBT001
        self._auto_select = checked
        is_active = self._phase == Phase.RESOLVING
        self._select_button.setEnabled(not checked and is_active)
        self._deselect_button.setEnabled(not checked and is_active)
        if checked:
            if self._identified_ips and self._select_ips is not None:
                self._select_ips(list(self._identified_ips))
                self._currently_selected_ips = set(self._identified_ips)
        elif self._currently_selected_ips and self._deselect_ips is not None:
            self._deselect_ips(list(self._currently_selected_ips))
            self._currently_selected_ips.clear()

    def _select_resolved(self) -> None:
        if self._select_ips is not None:
            target_ips = list(self._identified_ips or self._spike_streak.keys())
            if target_ips:
                self._select_ips(target_ips)
                self._currently_selected_ips = set(target_ips)

    def _deselect_resolved(self) -> None:
        if self._deselect_ips is not None:
            target_ips = set(self._identified_ips) | set(self._spike_streak.keys())
            ips_to_deselect = list(self._currently_selected_ips | target_ips)
            self._deselect_ips(ips_to_deselect or None)
            self._currently_selected_ips.clear()

    def reset(self) -> None:
        """Discard all data and return the widget to its initial idle state."""
        self._timer.stop()
        self._phase = Phase.IDLE
        if self._currently_selected_ips and self._deselect_ips is not None:
            self._deselect_ips(list(self._currently_selected_ips))
        self._currently_selected_ips.clear()
        self._baseline_ips.clear()
        self._baselines.clear()
        self._sample_count = 0
        self._spike_streak.clear()
        self._total_spike_duration.clear()
        self._contamination_streak.clear()
        self._identified_ips.clear()
        PlayerIdentifierTracker.set_identified_ips(set())
        self._prev_stability_pct = None
        self._prev_stability_format = None
        self._prev_stability_style = None
        self._prev_stability_text = None
        self._prev_sample_text = None
        self._prev_result_text = None
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(False)
        self._select_button.setEnabled(False)
        self._deselect_button.setEnabled(False)
        self._set_idle_instructions()
        self._stability_label.setText('Stabilité : —')
        self._stability_label.setVisible(False)
        self._stability_bar.setValue(0)
        self._stability_bar.setFormat('En attente...')
        self._stability_bar.setStyleSheet(PROGRESS_BAR_IDLE_STYLESHEET)
        self._stability_bar.setVisible(False)
        self._sample_label.setText('')
        self._sample_label.setVisible(False)
        self._result_label.setText('')

    def _abort_insufficient_players(self) -> None:
        """Stop the current phase because too many players disconnected."""
        self._timer.stop()
        self._phase = Phase.IDLE
        PlayerIdentifierTracker.set_identified_ips(set())
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(False)
        self._select_button.setEnabled(False)
        self._deselect_button.setEnabled(False)
        self._stability_bar.setValue(0)
        self._stability_bar.setFormat('Annulé')
        self._stability_bar.setStyleSheet(PROGRESS_BAR_CHUNK_RED_STYLESHEET)
        self._stability_label.setText(
            'Stabilité : <span style="color:red;">Annulé — plus assez de joueurs</span>',
        )
        self._instructions.setText(
            f'<b style="color:#e74c3c;">Annulé :</b> il reste moins de {MIN_CONNECTED_PLAYERS} joueurs suivis dans la session.<br><br>Des joueurs se sont déconnectés pendant l\'analyse. Clique sur <b>Lancer la référence</b> pour réessayer…',
        )

    def _abort_contaminated(self, ip: str, zscore: float) -> None:
        """Stop the baseline because a dramatic traffic spike was detected (contamination)."""
        self._timer.stop()
        self._phase = Phase.IDLE
        PlayerIdentifierTracker.set_identified_ips(set())
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(False)
        self._select_button.setEnabled(False)
        self._deselect_button.setEnabled(False)
        self._stability_bar.setValue(0)
        self._stability_bar.setFormat('Faussée')
        self._stability_bar.setStyleSheet(PROGRESS_BAR_CHUNK_RED_STYLESHEET)
        self._stability_label.setText(
            'Stabilité : <span style="color:red;">Annulé — référence faussée</span>',
        )
        self._instructions.setText(
            f'<b style="color:#e74c3c;">Référence faussée !</b> L\'IP <b>{ip}</b> a eu un énorme pic de trafic (z-score : {zscore:.1f}) pendant l\'enregistrement.<br><br>En général, ça veut dire que tu as bougé, observé quelqu\'un, ou qu\'un joueur s\'est approché. Les données de référence ne sont plus fiables.<br><br>Clique sur <b>Lancer la référence</b> pour recommencer. Reste complètement immobile et isolé.',
        )

    def _abort_session_changed(self) -> None:
        """Stop the current phase because overall session traffic drifted too far from the baseline."""
        self._timer.stop()
        self._phase = Phase.IDLE
        PlayerIdentifierTracker.set_identified_ips(set())
        self._update_baseline_button_state()
        self._resolve_button.setEnabled(False)
        self._reset_button.setEnabled(False)
        self._select_button.setEnabled(False)
        self._deselect_button.setEnabled(False)
        self._stability_bar.setValue(0)
        self._stability_bar.setFormat('Annulé')
        self._stability_bar.setStyleSheet(PROGRESS_BAR_CHUNK_RED_STYLESHEET)
        self._stability_label.setText(
            'Stabilité : <span style="color:red;">Annulé — la session a changé</span>',
        )
        self._instructions.setText(
            '<b style="color:#e74c3c;">Référence invalide :</b> le trafic global de la session a trop changé par rapport à la référence.<br><br>La session est peut-être terminée, ou un événement du jeu a fait monter ou chuter tout le trafic en même temps. Les données de référence ne sont plus fiables.<br><br>Clique sur <b>Lancer la référence</b> pour recommencer.',
        )

    # -- Periodic tick --------------------------------------------------------

    def _tick(self) -> None:
        players = [player for player in PlayersRegistry.get_connected_players() if not is_third_party_server_ip(player.ip)]
        if self._phase == Phase.BASELINE:
            self._tick_baseline(players)
        elif self._phase == Phase.READY:
            self._tick_ready(players)
        elif self._phase == Phase.RESOLVING:
            self._tick_resolving(players)

    def _tick_baseline(self, players: list[Player]) -> None:
        self._sample_count += 1
        sampled_ips: set[str] = set()
        player_by_ip: dict[str, Player] = {}
        for player in players:
            if player.ip in self._baseline_ips:
                sampled_ips.add(player.ip)
                player_by_ip[player.ip] = player
                self._baselines[player.ip].add_sample(
                    player.packets.pps.calculated_rate,
                    player.bandwidth.bps.calculated_rate,
                )
        disconnected = self._baseline_ips - sampled_ips
        if disconnected:
            self._baseline_ips -= disconnected
            for ip in disconnected:
                self._baselines.pop(ip, None)

        if len(self._baselines) < MIN_CONNECTED_PLAYERS:
            self._abort_insufficient_players()
            return

        if self._sample_count >= self._contamination_min_samples:
            for ip, bl in self._baselines.items():
                matched_player = player_by_ip.get(ip)
                if matched_player is None:
                    continue
                zscore = bl.live_zscore(matched_player.packets.pps.calculated_rate, matched_player.bandwidth.bps.calculated_rate)
                if zscore >= self._contamination_zscore:
                    streak = self._contamination_streak[ip] = self._contamination_streak.get(ip, 0) + 1
                    if streak >= self._contamination_seconds:
                        self._abort_contaminated(ip, zscore)
                        return
                else:
                    self._contamination_streak.pop(ip, None)

        if self._sample_count >= CONVERGENCE_RECENT_WINDOW:
            shifts: list[float] = [bl.mean_shift(CONVERGENCE_RECENT_WINDOW) for bl in self._baselines.values()]
            avg_shift = sum(shifts) / len(shifts)
            confidence_factor = sqrt(min(self._sample_count / CONVERGENCE_RECENT_WINDOW, 4.0))
            effective_green = CONVERGENCE_GREEN * confidence_factor
            effective_yellow = CONVERGENCE_YELLOW * confidence_factor
            converged = avg_shift <= effective_green and self._sample_count >= self._baseline_min_samples
        else:
            avg_shift = None
            effective_green = CONVERGENCE_GREEN
            effective_yellow = CONVERGENCE_YELLOW
            converged = False

        if avg_shift is None:
            remaining = CONVERGENCE_RECENT_WINDOW - self._sample_count
            pct = int(self._sample_count / CONVERGENCE_RECENT_WINDOW * 50)
            style = PROGRESS_BAR_CHUNK_ORANGE_STYLESHEET
            label = f'Stabilité : <span style="color:orange;">Collecte des données (encore {remaining}s)</span>'
        elif self._sample_count < self._baseline_min_samples:
            remaining = self._baseline_min_samples - self._sample_count
            shift_ok = avg_shift <= effective_green
            pct = int(self._sample_count / self._baseline_min_samples * 60)
            if shift_ok:
                style = PROGRESS_BAR_CHUNK_ORANGE_STYLESHEET
                label = f'Stabilité : <span style="color:orange;">Semble stable, encore {remaining}s de données</span>'
            else:
                style = PROGRESS_BAR_CHUNK_RED_STYLESHEET
                label = 'Stabilité : <span style="color:red;">Instable — ne bouge pas</span>'
        elif converged:
            pct = 100
            style = PROGRESS_BAR_CHUNK_GREEN_STYLESHEET
            label = 'Stabilité : <span style="color:green;">Stable — tu peux arrêter</span>'
        elif avg_shift <= effective_yellow:
            ratio = (effective_yellow - avg_shift) / (effective_yellow - effective_green)
            pct = int(60 + ratio * 39)
            style = PROGRESS_BAR_CHUNK_ORANGE_STYLESHEET
            label = 'Stabilité : <span style="color:yellow;">Presque stable… continue d\'attendre</span>'
        else:
            pct = max(int((1.0 - min(avg_shift, 1.0)) * 60), 5)
            style = PROGRESS_BAR_CHUNK_RED_STYLESHEET
            label = 'Stabilité : <span style="color:red;">Instable — ne bouge pas</span>'

        self._update_stability(pct, style, label)
        num_ips = len(self._baselines)
        self._update_sample_label(f'{num_ips} IP{pluralize(num_ips)} · {self._sample_count} sample{pluralize(self._sample_count)}')

        if converged:
            self._auto_stop_baseline('converged')
        elif self._sample_count >= self._baseline_max_seconds:
            self._auto_stop_baseline(f'{self._baseline_max_seconds}s timeout')

    def _tick_ready(self, players: list[Player]) -> None:
        """Monitor while the baseline is locked and the user hasn't clicked Resolve yet."""
        aggregate_z = compute_aggregate_zscore(self._baselines, players)
        if aggregate_z is not None and abs(aggregate_z) >= self._session_drift_threshold:
            self._abort_session_changed()
            return

        connected_baselined = sum(1 for player in players if player.ip in self._baselines)
        if connected_baselined < MIN_CONNECTED_PLAYERS:
            self._abort_insufficient_players()
            return

    def _tick_resolving(self, players: list[Player]) -> None:
        connected_baselined = sum(1 for player in players if player.ip in self._baselines)
        if connected_baselined < MIN_CONNECTED_PLAYERS:
            self._abort_insufficient_players()
            return

        aggregate_z = compute_aggregate_zscore(self._baselines, players)
        if aggregate_z is not None and aggregate_z <= -self._session_drift_threshold:
            self._abort_session_changed()
            return

        max_streak = 0

        for player in players:
            baseline = self._baselines.get(player.ip)
            if baseline is None:
                continue
            score = baseline.spike_score(
                player.packets.pps.calculated_rate,
                player.bandwidth.bps.calculated_rate,
            )
            if score > self._spike_min_zscore:
                streak = self._spike_streak[player.ip] = self._spike_streak.get(player.ip, 0) + 1
                self._total_spike_duration[player.ip] = self._total_spike_duration.get(player.ip, 0) + 1
                if streak >= self._spike_sustained_seconds:
                    self._identified_ips.add(player.ip)
                max_streak = max(max_streak, streak)
            else:
                self._spike_streak.pop(player.ip, None)

        PlayerIdentifierTracker.set_identified_ips(self._identified_ips)

        if self._auto_select and self._identified_ips != self._currently_selected_ips:
            if self._identified_ips:
                if self._select_ips is not None:
                    self._select_ips(list(self._identified_ips))
            elif self._currently_selected_ips and self._deselect_ips is not None:
                self._deselect_ips(list(self._currently_selected_ips))
            self._currently_selected_ips = set(self._identified_ips)

        self._update_resolving_display(players, max_streak)

    def _update_resolving_display(self, players: list[Player], max_streak: int) -> None:
        player_by_ip = {player.ip: player for player in players}
        identified_players = [player_by_ip[ip] for ip in self._identified_ips if ip in player_by_ip]
        candidate_players = [player_by_ip[ip] for ip in self._spike_streak if ip in player_by_ip and ip not in self._identified_ips]

        if not identified_players and not candidate_players:
            num_ips = len(self._baselines)
            self._update_result_label(
                f'<b>Aucun joueur en pic détecté.</b><br><small>Surveillance de {num_ips} IP{pluralize(num_ips)} de référence.</small>',
            )
            self._update_stability(0, PROGRESS_BAR_IDLE_STYLESHEET, 'Stability: <span style="color:green;">Locked</span>', bar_format='Resolving…')
            return

        lines: list[str] = []
        if identified_players:
            num_identified = len(identified_players)
            lines.append(f'<b style="color:#27ae60;">{num_identified} joueur{pluralize(num_identified)} identifié{pluralize(num_identified)} :</b>')
            for player in identified_players:
                name_part = f' ({", ".join(player.usernames)})' if player.usernames else ''
                formatted_bps = PlayerBandwidth.format_bytes(player.bandwidth.bps.calculated_rate)
                streak = self._spike_streak.get(player.ip, 0)
                total_duration = self._total_spike_duration.get(player.ip, 0)
                streak_text = f'série : {streak}s (total : {total_duration}s)' if streak > 0 else f'pic total : {total_duration}s'
                lines.append(f'• <b>{player.ip}</b>{name_part} — {player.packets.pps.calculated_rate} PPS · {formatted_bps} · {streak_text}')

        if candidate_players:
            num_candidates = len(candidate_players)
            lines.append(f'<b style="color:#f39c12;">{num_candidates} candidat{pluralize(num_candidates)} en pic :</b>')
            for player in candidate_players:
                name_part = f' ({", ".join(player.usernames)})' if player.usernames else ''
                formatted_bps = PlayerBandwidth.format_bytes(player.bandwidth.bps.calculated_rate)
                streak = self._spike_streak.get(player.ip, 0)
                total_duration = self._total_spike_duration.get(player.ip, 0)
                streak_text = f'série : {streak}/{self._spike_sustained_seconds}s (total : {total_duration}s)'
                lines.append(f'• <b>{player.ip}</b>{name_part} — {player.packets.pps.calculated_rate} PPS · {formatted_bps} · {streak_text}')

        if identified_players:
            lines.append('<small>Les joueurs identifiés ont une icône de cible dans le tableau des joueurs connectés.</small>')
        else:
            lines.append(f'<small>Il faut {self._spike_sustained_seconds} secondes d\'affilée de trafic élevé pour confirmer.</small>')

        self._update_result_label('<br>'.join(lines))

        if identified_players:
            self._update_stability(100, PROGRESS_BAR_CHUNK_GREEN_STYLESHEET, 'Stability: <span style="color:green;">Resolved</span>', bar_format='Resolved')
        elif candidate_players:
            pct = min(int(max_streak / self._spike_sustained_seconds * 100), 99)
            self._update_stability(
                pct,
                PROGRESS_BAR_CHUNK_ORANGE_STYLESHEET,
                'Stabilité : <span style="color:orange;">Pic détecté</span>',
                bar_format=f'{pct}%',
            )

    # -- Widget update helpers (skip redundant repaints) ----------------------

    def _update_stability(self, pct: int, style: str, label_text: str, bar_format: str | None = None) -> None:
        """Update stability bar and label only when values actually change."""
        resolved_format = bar_format if bar_format is not None else f'{pct}%'
        if pct != self._prev_stability_pct or resolved_format != self._prev_stability_format:
            self._stability_bar.setValue(pct)
            self._stability_bar.setFormat(resolved_format)
            self._prev_stability_pct = pct
            self._prev_stability_format = resolved_format
        if style != self._prev_stability_style:
            self._stability_bar.setStyleSheet(style)
            self._prev_stability_style = style
        if label_text != self._prev_stability_text:
            self._stability_label.setText(label_text)
            self._prev_stability_text = label_text

    def _update_sample_label(self, text: str) -> None:
        """Update sample label only when text actually changes."""
        if text != self._prev_sample_text:
            self._sample_label.setText(text)
            self._prev_sample_text = text

    def _update_result_label(self, text: str) -> None:
        """Update result label only when text actually changes."""
        if text != self._prev_result_text:
            self._result_label.setText(text)
            self._prev_result_text = text

    @property
    def _spike_min_zscore(self) -> float:
        return Settings.player_identifier_spike_zscore

    @property
    def _spike_sustained_seconds(self) -> int:
        return Settings.player_identifier_spike_seconds

    @property
    def _contamination_zscore(self) -> float:
        return Settings.player_identifier_contamination_zscore

    @property
    def _contamination_seconds(self) -> int:
        return Settings.player_identifier_contamination_seconds

    @property
    def _contamination_min_samples(self) -> int:
        return Settings.player_identifier_contamination_min_samples

    @property
    def _baseline_min_samples(self) -> int:
        return Settings.player_identifier_baseline_seconds

    @property
    def _baseline_max_seconds(self) -> int:
        return Settings.player_identifier_baseline_timeout

    @property
    def _session_drift_threshold(self) -> float:
        return Settings.player_identifier_session_drift_zscore

    def apply_settings(self) -> None:
        """Apply updated detection parameters from `Settings`."""
        self._update_baseline_button_state()
        self._resolve_button.setToolTip(
            f'Étape 2 : commence à bouger, sauter ou générer du trafic pendant que les autres joueurs restent immobiles.\n\nL\'outil compare chaque IP à sa référence pour trouver celle dont le trafic monte fortement.\n\nUne IP doit avoir un pic pendant {self._spike_sustained_seconds} secondes d\'affilée pour être confirmée.\n\nAstuce : la détection marche mieux quand le joueur cible bouge — un joueur en mouvement génère beaucoup plus de trafic qu\'un joueur immobile.',
        )
