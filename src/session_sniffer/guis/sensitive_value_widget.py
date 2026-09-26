"""Sleek, polished container that renders sensitive data blurred until revealed."""

from typing import TYPE_CHECKING, Final, override

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsBlurEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from session_sniffer.constants.local import RESOURCES_DIR_PATH

if TYPE_CHECKING:
    from collections.abc import Callable

_SENSITIVE_BLUR_RADIUS: Final[float] = 10.0
_SENSITIVE_CONTAINER_WIDTH: Final[int] = 240

_REDACTED_PILL_STYLESHEET_BLURRED: Final[str] = (
    'QWidget#sensitive_container {'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '        stop:0 rgba(26, 13, 48, 0.85), stop:1 rgba(42, 15, 75, 0.85));'
    '    border: 1px solid rgba(165, 134, 255, 0.35);'
    '    border-radius: 6px;'
    '}'
    'QWidget#sensitive_container:hover {'
    '    border-color: rgba(192, 129, 255, 0.75);'
    '    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,'
    '        stop:0 rgba(35, 18, 66, 0.95), stop:1 rgba(58, 22, 102, 0.95));'
    '}'
)

_REDACTED_PILL_STYLESHEET_REVEALED: Final[str] = (
    'QWidget#sensitive_container {    background-color: rgba(20, 11, 37, 0.6);    border: 1px solid rgba(165, 134, 255, 0.25);    border-radius: 6px;}'
)

_SENSITIVE_ACTION_BUTTON_STYLESHEET: Final[str] = (
    'QPushButton {'
    '    background-color: rgba(122, 49, 246, 0.3);'
    '    border: 1px solid rgba(165, 134, 255, 0.45);'
    '    border-radius: 4px;'
    '    padding: 2px;'
    '}'
    'QPushButton:hover {'
    '    background-color: rgba(136, 84, 254, 0.55);'
    '    border-color: rgba(216, 179, 255, 0.8);'
    '}'
    'QPushButton:pressed {'
    '    background-color: #7a31f6;'
    '}'
)


class SensitiveValueWidget(QWidget):
    """A sleek, polished container that renders sensitive data blurred until revealed."""

    def __init__(
        self,
        text: str,
        *,
        on_toggled: Callable[[bool], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the sensitive value widget with blurred default state."""
        super().__init__(parent)
        self._text = text
        self._revealed = False
        self._on_toggled = on_toggled

        icons_directory = RESOURCES_DIR_PATH / 'icons'
        self._icon_copy = QIcon(str(icons_directory / 'copy.svg'))
        self._icon_check = QIcon(str(icons_directory / 'check.svg'))

        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(6)

        self._container = QWidget(self)
        self._container.setObjectName('sensitive_container')
        self._container.setFixedWidth(_SENSITIVE_CONTAINER_WIDTH)

        container_layout = QHBoxLayout(self._container)
        container_layout.setContentsMargins(10, 4, 8, 4)
        container_layout.setSpacing(8)

        self._label = QLabel(self._container)
        font = QFont('Consolas', 13)
        font.setBold(True)
        self._label.setFont(font)
        self._label.setStyleSheet('color: #f9effa; background: transparent; padding: 0 2px;')

        self._blur_effect = QGraphicsBlurEffect(self._label)
        self._blur_effect.setBlurRadius(_SENSITIVE_BLUR_RADIUS)
        self._label.setGraphicsEffect(self._blur_effect)

        self._copy_button = QPushButton(self._container)
        self._copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_button.setIcon(self._icon_copy)
        self._copy_button.setIconSize(QSize(16, 16))
        self._copy_button.setFixedSize(26, 26)
        self._copy_button.setStyleSheet(_SENSITIVE_ACTION_BUTTON_STYLESHEET)
        self._copy_button.setToolTip('Copier')
        self._copy_button.clicked.connect(self._copy_to_clipboard)

        container_layout.addWidget(self._label)
        container_layout.addWidget(self._copy_button)

        outer_layout.addWidget(self._container)
        self.setFixedWidth(_SENSITIVE_CONTAINER_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._container.installEventFilter(self)
        self._label.installEventFilter(self)

        self._apply_state()

    @override
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Clicking on the blurred container or label reveals the value."""
        target_widgets = (getattr(self, '_container', None), getattr(self, '_label', None))
        if not getattr(self, '_revealed', False) and watched in target_widgets:
            is_left_click = isinstance(event, QMouseEvent) and event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton
            if is_left_click:
                self.set_revealed(revealed=True)
                return True
        return super().eventFilter(watched, event)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Clicking on the widget when blurred reveals the value."""
        if not self._revealed and event.button() == Qt.MouseButton.LeftButton:
            self.set_revealed(revealed=True)
            event.accept()
            return
        super().mousePressEvent(event)

    def _copy_to_clipboard(self) -> None:
        """Copy the underlying text to clipboard and briefly acknowledge."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self._text)
        self._copy_button.setIcon(self._icon_check)
        self._copy_button.setToolTip('Copié !')
        QTimer.singleShot(1200, self, self._reset_copy_button)

    def _reset_copy_button(self) -> None:
        """Reset copy button icon and tooltip after acknowledgment timeout."""
        self._copy_button.setIcon(self._icon_copy)
        self._copy_button.setToolTip('Copier')

    @property
    def text(self) -> str:
        """The underlying sensitive text value."""
        return self._text

    def set_text(self, text: str) -> None:
        """Update the underlying sensitive text value."""
        self._text = text
        self._apply_state()

    @property
    def is_revealed(self) -> bool:
        """Whether the sensitive value is currently unblurred."""
        return self._revealed

    def set_revealed(self, *, revealed: bool) -> None:
        """Set revealed state explicitly."""
        if self._revealed != revealed:
            self._revealed = revealed
            self._apply_state()
            if self._on_toggled is not None:
                self._on_toggled(self._revealed)

    def toggle(self) -> None:
        """Toggle revealed state between blurred and clear."""
        self.set_revealed(revealed=not self._revealed)

    def _get_blurred_mask(self) -> str:
        """Compute the mask string dynamically to fill the container width."""
        layout = self._container.layout()
        if layout is not None:
            margins = layout.contentsMargins()
            non_label_width = margins.left() + margins.right() + layout.spacing() + self._copy_button.width()
            available_width = max(_SENSITIVE_CONTAINER_WIDTH - non_label_width, 0)
        else:
            available_width = max(_SENSITIVE_CONTAINER_WIDTH, 0)

        char_width = max(self._label.fontMetrics().horizontalAdvance('•'), 1)
        count = max(available_width // char_width, 1)
        return '•' * count

    def _apply_state(self) -> None:
        self._blur_effect.setEnabled(not self._revealed)
        if self._revealed:
            self._container.setStyleSheet(_REDACTED_PILL_STYLESHEET_REVEALED)
            self._container.setCursor(Qt.CursorShape.ArrowCursor)
            self._container.setToolTip('')
            self._label.setText(self._text)
            self._label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
            self._label.setCursor(Qt.CursorShape.IBeamCursor)
            self._label.setToolTip('Sélectionne le texte à copier, ou clique sur Copier')
        else:
            self._container.setStyleSheet(_REDACTED_PILL_STYLESHEET_BLURRED)
            self._container.setCursor(Qt.CursorShape.PointingHandCursor)
            self._container.setToolTip('Cliquer pour afficher')
            self._label.setText(self._get_blurred_mask() if self._text else '')
            self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            self._label.setCursor(Qt.CursorShape.PointingHandCursor)
            self._label.setToolTip('Cliquer pour afficher')
