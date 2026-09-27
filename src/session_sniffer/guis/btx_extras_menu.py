"""BTXSniffer menus: colour theme choice and backups of the notes / tags."""

import sys
from datetime import datetime

from PySide6.QtCore import QProcess, Qt, QUrl
from PySide6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from session_sniffer import btx_theme
from session_sniffer.constants.local import RESOURCES_DIR_PATH
from session_sniffer.constants.standalone import TITLE
from session_sniffer.guis.btx_notes import BACKUP_DIR, PlayerNotes, create_manual_backup, list_backups

# ---------- theme ----------


def _swatch(theme_key: str) -> QIcon:
    accent, second, background = btx_theme.preview_colors(theme_key)
    pixmap = QPixmap(30, 14)
    pixmap.fill(QColor(background))
    painter = QPainter(pixmap)
    painter.fillRect(2, 2, 12, 10, QColor(accent))
    painter.fillRect(16, 2, 12, 10, QColor(second))
    painter.end()
    return QIcon(pixmap)


def restart_app(window: QWidget) -> None:
    """Start a new BTXSniffer and close this one."""
    if getattr(sys, 'frozen', False):
        program, args = sys.executable, sys.argv[1:]
    else:
        program, args = sys.executable, list(sys.orig_argv[1:])
    started, _pid = QProcess.startDetached(program, args)
    if not started:
        QMessageBox.warning(window, TITLE, 'Impossible de redémarrer automatiquement. Ferme et relance BTXSniffer à la main.')
        return
    window.close()


def add_theme_menu(menu: QMenu, window: QWidget) -> QMenu:
    """Add a 'Thème' sub-menu (one radio entry per theme)."""
    sub = menu.addMenu(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'eye.svg')), 'Thème')
    sub.setToolTipsVisible(True)
    group = QActionGroup(sub)
    group.setExclusive(True)
    saved = btx_theme.saved_theme()
    actions: dict[str, QAction] = {}

    def label(key: str, chosen: str) -> str:
        return f'{btx_theme.THEMES[key].label}   ✓' if key == chosen else btx_theme.THEMES[key].label

    def choose(key: str) -> None:
        if key == btx_theme.saved_theme():
            return
        btx_theme.save_theme(key)
        for other, other_action in actions.items():
            other_action.setText(label(other, key))
        if key == btx_theme.ACTIVE_THEME:
            return  # back to the theme already on screen
        answer = QMessageBox.question(
            window,
            TITLE,
            f'Le thème « {btx_theme.THEMES[key].label} » sera appliqué au redémarrage de BTXSniffer.\n\nRedémarrer maintenant ?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            restart_app(window)

    for key in btx_theme.THEMES:
        action = QAction(_swatch(key), label(key, saved), sub)
        actions[key] = action
        action.setCheckable(True)
        action.setChecked(key == saved)
        action.setToolTip('Couleurs actuelles' if key == btx_theme.ACTIVE_THEME else 'Appliqué au prochain démarrage')
        action.triggered.connect(lambda _checked=False, k=key: choose(k))
        group.addAction(action)
        sub.addAction(action)
    return sub


# ---------- backups ----------


def _refresh_everything() -> None:
    for widget in QApplication.topLevelWidgets():
        widget.update()


class BackupsDialog(QDialog):
    """List of the automatic / manual backups of the notes and tags, with restore."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, on=False)
        self.setWindowTitle('Sauvegardes des notes et étiquettes')
        self.setWindowIcon(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'save.svg')))
        self.resize(620, 480)

        layout = QVBoxLayout(self)
        info = QLabel(
            'BTXSniffer sauvegarde tout seul tes notes et étiquettes :\n'
            '• une copie par jour (gardée 30 jours)\n'
            '• une copie avant chaque modification (les 20 dernières)\n'
            'Choisis une sauvegarde puis clique sur « Restaurer » pour revenir en arrière.',
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self._current = QLabel()
        self._current.setStyleSheet('color: #3ff0ff; font-weight: 600;')
        layout.addWidget(self._current)

        self._table = QTableWidget(0, 3, self)
        self._table.setHorizontalHeaderLabels(['Date', 'Type', 'Joueurs'])
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.doubleClicked.connect(lambda _index: self._restore())
        v_header = self._table.verticalHeader()
        if v_header:
            v_header.setVisible(False)
        h_header = self._table.horizontalHeader()
        if h_header:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            h_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self._table, 1)

        row1 = QHBoxLayout()
        restore = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'reset.svg')), 'Restaurer')
        restore.clicked.connect(self._restore)
        now = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'save.svg')), 'Sauvegarder maintenant')
        now.clicked.connect(self._backup_now)
        folder = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier')
        folder.clicked.connect(open_backup_folder)
        row1.addWidget(restore)
        row1.addWidget(now)
        row1.addWidget(folder)
        row1.addStretch(1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        export = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'export.svg')), 'Exporter…')
        export.setToolTip('Enregistrer tes notes et étiquettes dans un fichier (pour un autre PC ou pour un pote)')
        export.clicked.connect(lambda: export_notes(self))
        import_btn = QPushButton(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'import.svg')), 'Importer…')
        import_btn.setToolTip("Ajouter les notes et étiquettes d'un fichier exporté (les tiennes sont gardées)")
        import_btn.clicked.connect(lambda: (import_notes(self), self._fill()))
        close = QPushButton('Fermer')
        close.clicked.connect(self.close)
        row2.addWidget(export)
        row2.addWidget(import_btn)
        row2.addStretch(1)
        row2.addWidget(close)
        layout.addLayout(row2)

        self._backups = []
        self._fill()

    def _fill(self) -> None:
        self._current.setText(f'Actuellement : {PlayerNotes.count()} joueur(s) avec une note ou une étiquette.')
        self._backups = list_backups()
        self._table.setRowCount(0)
        for backup in self._backups:
            row = self._table.rowCount()
            self._table.insertRow(row)
            date_item = QTableWidgetItem(backup.mtime.strftime('%d/%m/%Y  %H:%M'))
            count = backup.count()
            count_item = QTableWidgetItem('illisible' if count < 0 else str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, date_item)
            self._table.setItem(row, 1, QTableWidgetItem(backup.kind))
            self._table.setItem(row, 2, count_item)
        if not self._backups:
            self._table.insertRow(0)
            self._table.setItem(0, 0, QTableWidgetItem("Pas encore de sauvegarde (elles se créent dès que tu as une note ou une étiquette)."))
            self._table.setSpan(0, 0, 1, 3)

    def _restore(self) -> None:
        row = self._table.currentRow()
        if not 0 <= row < len(self._backups):
            QMessageBox.information(self, TITLE, 'Choisis une sauvegarde dans la liste.')
            return
        backup = self._backups[row]
        answer = QMessageBox.question(
            self,
            TITLE,
            f'Revenir à la sauvegarde du {backup.mtime:%d/%m/%Y à %H:%M} ({backup.count()} joueurs) ?\n\n'
            "Tes notes actuelles seront d'abord sauvegardées, tu pourras donc annuler.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        if PlayerNotes.restore(backup.path):
            _refresh_everything()
            QMessageBox.information(self, TITLE, 'Sauvegarde restaurée.')
        else:
            QMessageBox.warning(self, TITLE, 'Cette sauvegarde est illisible.')
        self._fill()

    def _backup_now(self) -> None:
        if create_manual_backup():
            QMessageBox.information(self, TITLE, 'Sauvegarde créée.')
        else:
            QMessageBox.information(self, TITLE, "Rien à sauvegarder pour l'instant.")
        self._fill()


def open_backups_dialog(parent: QWidget | None) -> None:
    BackupsDialog(parent).show()


def open_backup_folder() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(BACKUP_DIR)))


def export_notes(parent: QWidget | None) -> None:
    default = str(BACKUP_DIR.parent / f'BTX_notes_{datetime.now().astimezone():%Y-%m-%d}.json')
    path, _filter = QFileDialog.getSaveFileName(parent, 'Exporter mes notes et étiquettes', default, 'Notes BTX (*.json)')
    if not path:
        return
    if PlayerNotes.export_to(path):
        QMessageBox.information(parent, TITLE, f'{PlayerNotes.count()} joueur(s) exporté(s).')
    else:
        QMessageBox.warning(parent, TITLE, "Impossible d'écrire ce fichier.")


def import_notes(parent: QWidget | None) -> None:
    path, _filter = QFileDialog.getOpenFileName(parent, 'Importer des notes et étiquettes', str(BACKUP_DIR.parent), 'Notes BTX (*.json)')
    if not path:
        return
    result = PlayerNotes.import_merge(path)
    if result is None:
        QMessageBox.warning(parent, TITLE, "Ce fichier n'est pas un export de notes BTXSniffer.")
        return
    added, completed = result
    _refresh_everything()
    QMessageBox.information(parent, TITLE, f'Import terminé : {added} nouveau(x) joueur(s), {completed} complété(s).\nTes notes existantes ont été gardées.')


def add_backup_menu(menu: QMenu, window: QWidget) -> QMenu:
    """Add the 'Notes et étiquettes' sub-menu (backups, export, import)."""
    sub = menu.addMenu(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'save.svg')), 'Notes et étiquettes')
    sub.setToolTipsVisible(True)
    sub.addAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'history.svg')), 'Sauvegardes et restauration…', lambda: open_backups_dialog(window))
    sub.addSeparator()
    sub.addAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'export.svg')), 'Exporter mes notes…', lambda: export_notes(window))
    sub.addAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'import.svg')), 'Importer des notes…', lambda: import_notes(window))
    sub.addSeparator()
    sub.addAction(QIcon(str(RESOURCES_DIR_PATH / 'icons' / 'folder.svg')), 'Ouvrir le dossier des sauvegardes', open_backup_folder)
    return sub
