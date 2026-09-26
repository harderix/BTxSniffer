"""BTXSniffer French display translations.

Internal names (column names, settings categories/groups, combo values) stay in English because
the code and the Settings.ini file rely on them. This module only translates them at display time.
"""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtCore import QModelIndex, QPersistentModelIndex
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStyleOptionHeader,
    QStyleOptionViewItem,
    QStylePainter,
    QTreeView,
    QWidget,
)

FR: dict[str, str] = {
    # --- Column names ---
    'Usernames': 'Pseudos',
    'First Seen': 'Première vue',
    'Last Rejoin': 'Dernier retour',
    'Last Seen': 'Dernière vue',
    'T. Session Time': 'Temps total',
    'Session Time': 'Temps de session',
    'Rejoins': 'Retours',
    'T. Packets': 'Paquets tot.',
    'Packets': 'Paquets',
    'T. Packets Received': 'Paquets reçus tot.',
    'Packets Received': 'Paquets reçus',
    'T. Packets Sent': 'Paquets envoyés tot.',
    'Packets Sent': 'Paquets envoyés',
    'T. Min Packet Length': 'Taille min tot.',
    'Min Packet Length': 'Taille min',
    'T. Avg Packet Length': 'Taille moy. tot.',
    'Avg Packet Length': 'Taille moy.',
    'T. Max Packet Length': 'Taille max tot.',
    'Max Packet Length': 'Taille max',
    'T. Bandwidth': 'Bande passante tot.',
    'Bandwidth': 'Bande passante',
    'T. Download': 'Reçu tot.',
    'Download': 'Reçu',
    'T. Upload': 'Envoyé tot.',
    'Upload': 'Envoyé',
    'IP Address': 'Adresse IP',
    'Hostname': "Nom d'hôte",
    'Last Port': 'Dernier port',
    'Middle Ports': 'Ports intermédiaires',
    'First Port': 'Premier port',
    'Country': 'Pays',
    'Region': 'Région',
    'R. Code': 'Code région',
    'City': 'Ville',
    'District': 'Quartier',
    'ZIP Code': 'Code postal',
    'Time Zone': 'Fuseau horaire',
    'Offset': 'Décalage',
    'Currency': 'Devise',
    'Organization': 'Organisation',
    'ISP': 'FAI',
    'ASN / ISP': 'ASN / FAI',
    'Hosting': 'Hébergeur',
    'Pinging': 'Ping',
    'Range': 'Plage',
    'Database': 'Base',
    'Name': 'Nom',
    'Type': 'Type',
    'Gateway IP': 'IP passerelle',
    'MAC Address': 'Adresse MAC',
    'Vendor Name': 'Fabricant',
    'Duration': 'Durée',
    'Players': 'Joueurs',
    'Player': 'Joueur',
    'Total Time': 'Temps total',
    'Status': 'État',
    'Count': 'Nombre',
    '% of Total': '% du total',
    'Application / Process Name': 'Application / processus',
    'Executable Path': "Chemin de l'exécutable",
    'Time': 'Heure',
    'Port': 'Port',
    'State': 'État',
    'Service': 'Service',
    'Banner': 'Bannière',
    'Protocol': 'Protocole',
    'Seen': 'Vu',
    'Rank': 'Rang',
    # --- Combo box values (kept in English internally) ---
    'Top 20 Common': 'Top 20 courants',
    'Top 100 Common': 'Top 100 courants',
    'Top 1024 (Standard)': 'Top 1024 (standard)',
    'Gaming & Consoles': 'Jeux & consoles',
    'Web & Proxies': 'Web & proxys',
    'All Ports (1-65535)': 'Tous les ports (1-65535)',
    'Custom': 'Personnalisé',
    'Disabled': 'Désactivé',
    'Male': 'Voix homme',
    'Female': 'Voix femme',
    'Manual': 'Manuel',
    'Auto': 'Auto',
    'Yes': 'Oui',
    'No': 'Non',
    'None': 'Aucun',
    'Ascending': 'Croissant',
    'Descending': 'Décroissant',
    'Desktop': 'PC',
    'Both': 'Les deux',
    'Timezone': 'Fuseau horaire',
    'Timezone + Local Time': 'Fuseau + heure locale',
    'Local Time': 'Heure locale',
    'Stable': 'Stable',
    'Pre-release': 'Pré-version',
    'Continent': 'Continent',
    'GeoLite2 ASN / ISP': 'ASN / FAI (GeoLite2)',
    'AS Name': "Nom de l'AS",
    'AS Number': "Numéro d'AS",
    'Modder': 'Moddeur',
    'Legacy': 'Legacy',
    'Enhanced': 'Enhanced',
    'Event': 'Événement',
    'Lat': 'Latitude',
    'Lon': 'Longitude',
    'All Columns': 'Toutes les colonnes',
    'Sessions': 'Sessions',
    'Days': 'Jours',
    'Unique Days': 'Jours différents',
    'Period': 'Période',
    'Description': 'Description',
    'Username / IP': 'Pseudo / IP',
    'Detection': 'Détection',
    'Date': 'Date',
    'Device / Hostname': 'Appareil / nom',
    'IPv4 Address': 'Adresse IPv4',
    'Manufacturer / Vendor': 'Fabricant',
    'Latency (ms)': 'Latence (ms)',
    'Banner / Details': 'Bannière / détails',
    'Network': 'Réseau',
    'Location': 'Localisation',
    'Other': 'Autres',
    # --- Settings categories ---
    'Launcher': 'Démarrage',
    'Capture': 'Capture',
    'Session': 'Session',
    'Columns': 'Colonnes',
    'Discord': 'Discord',
    'Web Server': 'Serveur web',
    'GTA V': 'GTA V',
    # --- Settings groups / subgroups ---
    'Application Popups': "Fenêtres de l'application",
    'Application Window': "Fenêtre de l'application",
    'Authentication': 'Authentification',
    'Column Visibility': 'Colonnes visibles',
    'Connection': 'Connexion',
    'Date & Time Formatting': 'Format de la date et heure',
    'Detected Servers': 'Serveurs détectés',
    'Disconnected Players': 'Joueurs déconnectés',
    'General': 'Général',
    'Geolocation Data': 'Géolocalisation',
    'High Rate Monitor': 'Moniteur de trafic élevé',
    'IP Filters': "Filtres d'IP",
    'Interface Selection': "Choix de l'interface",
    'Interface': 'Interface',
    'Looky System': 'Looky System',
    'Player Identifier': 'Trouveur de joueur',
    'Player Pinging': 'Ping des joueurs',
    'Rich Presence (RPC)': 'Statut Discord (RPC)',
    'Session Host': 'Hôte de session',
    'Sessions Logging': 'Logs de sessions',
    'Solo Public Session': 'Session publique solo',
    'Table Pagination': 'Pagination des tableaux',
    'Table Sorting': 'Tri des tableaux',
    'Updater': 'Mises à jour',
    'Voice Notifications': 'Notifications vocales',
    'Webhook': 'Webhook',
    'Payload Filters': 'Filtres de contenu',
    'Port Filters': 'Filtres de ports',
    'Server Webhook': 'Webhook du serveur',
}

COLUMN_TOOLTIPS_FR: dict[str, str] = {
    'Usernames': (
        'Affiche les pseudos des joueurs depuis tes bases UserIP.\n\n'
        'Sur GTA V PC, avec le plugin de mod menu Session Sniffer,\n'
        'les pseudos sont trouvés automatiquement pendant que le plugin tourne,\n'
        'ou affichés pour les joueurs déjà vus par le plugin.'
    ),
    'First Seen': 'La toute première fois que le joueur a été vu, toutes sessions confondues.',
    'Last Rejoin': 'La dernière fois que le joueur est revenu dans ta session.',
    'Last Seen': 'La dernière fois que le joueur a été actif dans ta session.',
    'T. Session Time': 'Le temps total de jeu du joueur, toutes sessions confondues.',
    'Session Time': 'Le temps de jeu du joueur dans sa dernière session avant déconnexion.',
    'Rejoins': 'Le nombre de fois où le joueur a quitté puis rejoint ta session, toutes sessions confondues.',
    'T. Packets': 'Le nombre total de paquets échangés avec le joueur, toutes sessions confondues.',
    'Packets': 'Le nombre de paquets échangés (reçus + envoyés) avec le joueur pendant la session actuelle.',
    'T. Packets Received': 'Le nombre total de paquets reçus du joueur, toutes sessions confondues.',
    'Packets Received': 'Le nombre de paquets reçus du joueur pendant la session actuelle.',
    'T. Packets Sent': 'Le nombre total de paquets envoyés au joueur, toutes sessions confondues.',
    'Packets Sent': 'Le nombre de paquets envoyés au joueur pendant la session actuelle.',
    'T. Min Packet Length': 'La taille minimum des paquets (en octets) échangés avec le joueur, toutes sessions confondues.',
    'Min Packet Length': 'La taille minimum des paquets (en octets) échangés avec le joueur pendant la session actuelle.',
    'T. Avg Packet Length': 'La taille moyenne des paquets (en octets) échangés avec le joueur, toutes sessions confondues.',
    'Avg Packet Length': 'La taille moyenne des paquets (en octets) échangés avec le joueur pendant la session actuelle.',
    'T. Max Packet Length': 'La taille maximum des paquets (en octets) échangés avec le joueur, toutes sessions confondues.',
    'Max Packet Length': 'La taille maximum des paquets (en octets) échangés avec le joueur pendant la session actuelle.',
    'PPS': 'Le nombre de paquets échangés (reçus + envoyés) avec le joueur par seconde pendant la session actuelle.',
    'PPM': 'Le nombre de paquets échangés (reçus + envoyés) avec le joueur par minute pendant la session actuelle.',
    'T. Bandwidth': "La quantité totale d'octets transférés (reçus + envoyés) avec le joueur, toutes sessions confondues.",
    'Bandwidth': "La quantité d'octets transférés (reçus + envoyés) avec le joueur pendant la session actuelle.",
    'T. Download': "La quantité totale d'octets reçus du joueur, toutes sessions confondues.",
    'Download': "La quantité d'octets reçus du joueur pendant la session actuelle.",
    'T. Upload': "La quantité totale d'octets envoyés au joueur, toutes sessions confondues.",
    'Upload': "La quantité d'octets envoyés au joueur pendant la session actuelle.",
    'BPS': "Le nombre d'octets transférés (reçus + envoyés) avec le joueur par seconde pendant la session actuelle.",
    'BPM': "Le nombre d'octets transférés (reçus + envoyés) avec le joueur par minute pendant la session actuelle.",
    'IP Address': "L'adresse IP du joueur.",
    'Hostname': "Le nom de domaine associé à l'IP du joueur, trouvé par une recherche DNS inverse.",
    'Ports': 'Tous les ports utilisés par le joueur, du premier au dernier découvert (de gauche à droite).',
    'Last Port': 'Le port du dernier paquet capturé du joueur.',
    'Middle Ports': 'Les ports utilisés par le joueur entre le premier et le dernier paquet capturé.',
    'First Port': 'Le port du premier paquet capturé du joueur.',
    'Continent': "Le continent de la localisation de l'IP du joueur.",
    'Country': "Le pays de la localisation de l'IP du joueur.",
    'Region': "La région de la localisation de l'IP du joueur.",
    'R. Code': "Le code de région de la localisation de l'IP du joueur.",
    'City': "La ville associée à l'IP du joueur (souvent celle du FAI ou d'un point intermédiaire, pas celle du domicile du joueur).",
    'District': "Le quartier de la localisation de l'IP du joueur.",
    'ZIP Code': "Le code postal de la localisation de l'IP du joueur.",
    'Lat': "La latitude de la localisation de l'IP du joueur.",
    'Lon': "La longitude de la localisation de l'IP du joueur.",
    'Time Zone': "Le fuseau horaire de la localisation de l'IP du joueur.",
    'Offset': "Le décalage horaire de la localisation de l'IP du joueur.",
    'Currency': "La devise associée à la localisation de l'IP du joueur.",
    'Organization': "L'organisation associée à l'IP du joueur.",
    'ISP': "Le fournisseur d'accès internet (FAI) de l'IP du joueur.",
    'ASN / ISP': "Le numéro de système autonome (ASN) ou le fournisseur d'accès du joueur.",
    'AS': "Le code du système autonome de l'IP du joueur.",
    'ASN': "Le nom du système autonome (ASN) associé à l'IP du joueur.",
    'Mobile': 'Indique si le joueur utilise un réseau mobile (partage de connexion ou données mobiles).',
    'VPN': 'Indique si le joueur utilise un VPN, un proxy ou un relais Tor.',
    'Hosting': 'Indique si le joueur passe par un hébergeur (comme un VPN).',
    'Pinging': 'Indique si le joueur est en train d\'être pingé.',
}


def tr(text: str) -> str:
    """Return the French display text for an internal English name (or the text itself)."""
    return FR.get(text, text)


class TranslatedHeaderView(QHeaderView):
    """Header view that paints translated section titles while the model keeps English names."""

    def sectionSizeFromContents(self, logical_index: int) -> QSize:  # noqa: N802  # pylint: disable=invalid-name
        """Size sections using the translated title so French headers are not truncated."""
        size = super().sectionSizeFromContents(logical_index)
        model = self.model()
        if model is None:
            return size
        text = model.headerData(logical_index, self.orientation(), Qt.ItemDataRole.DisplayRole)
        if isinstance(text, str) and text:
            metrics = self.fontMetrics()
            extra = metrics.horizontalAdvance(tr(text)) - metrics.horizontalAdvance(text)
            if extra > 0:
                size.setWidth(size.width() + extra)
        return size

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Paint a header section with its translated text."""
        if not rect.isValid():
            return
        option = QStyleOptionHeader()
        self.initStyleOptionForIndex(option, logical_index)
        option.rect = rect
        option.text = tr(option.text)
        painter.save()
        self.style().drawControl(QStyle.ControlElement.CE_Header, option, painter, self)
        painter.restore()


def install_translated_header(view: QWidget) -> None:
    """Replace the horizontal header of a table/tree view with a translating one."""
    is_tree = isinstance(view, QTreeView)
    old = view.header() if is_tree else view.horizontalHeader()  # type: ignore[attr-defined]
    new = TranslatedHeaderView(Qt.Orientation.Horizontal, view)
    new.setSectionsClickable(old.sectionsClickable())
    new.setSectionsMovable(old.sectionsMovable())
    new.setHighlightSections(old.highlightSections())
    new.setStretchLastSection(old.stretchLastSection())
    new.setDefaultAlignment(old.defaultAlignment())
    new.setSortIndicatorShown(old.isSortIndicatorShown())
    if is_tree:
        view.setHeader(new)  # type: ignore[attr-defined]
    else:
        view.setHorizontalHeader(new)  # type: ignore[attr-defined]


class _TranslatingDelegate(QStyledItemDelegate):
    """Item delegate that shows translated text in a combo box popup."""

    def initStyleOption(self, option: QStyleOptionViewItem, index: QModelIndex | QPersistentModelIndex) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Translate the item text before painting."""
        super().initStyleOption(option, index)
        option.text = tr(option.text)


class TrComboBox(QComboBox):
    """Non-editable combo box that *displays* French labels while currentText() stays English.

    The code compares combo values with English words ('Disabled', 'Male', ...) and saves them to
    the settings files, so only the painting is translated.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the combo box with a translating popup delegate."""
        super().__init__(parent)
        self.setItemDelegate(_TranslatingDelegate(self))

    def _extra_width(self) -> int:
        metrics = self.fontMetrics()
        extra = 0
        for i in range(self.count()):
            text = self.itemText(i)
            extra = max(extra, metrics.horizontalAdvance(tr(text)) - metrics.horizontalAdvance(text))
        return extra

    def sizeHint(self) -> QSize:  # noqa: N802  # pylint: disable=invalid-name
        """Make room for the (sometimes longer) French labels."""
        size = super().sizeHint()
        size.setWidth(size.width() + self._extra_width())
        return size

    def minimumSizeHint(self) -> QSize:  # noqa: N802  # pylint: disable=invalid-name
        """Make room for the (sometimes longer) French labels."""
        size = super().minimumSizeHint()
        size.setWidth(size.width() + self._extra_width())
        return size

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002, N802  # pylint: disable=invalid-name,unused-argument
        """Paint the closed combo box with the translated current text."""
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = tr(option.currentText)
        painter.drawComplexControl(QStyle.ComplexControl.CC_ComboBox, option)
        painter.drawControl(QStyle.ControlElement.CE_ComboBoxLabel, option)
