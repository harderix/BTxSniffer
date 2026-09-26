"""Default setting values, metadata, and categories for Session Sniffer."""

# pylint: disable=too-many-lines

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TypedDict

from session_sniffer.constants.standalone import (
    CLASSICSTUN_PORT,
    DEFAULT_DETECTED_SERVER_COLOR,
    LLMNR_PORT,
    MAX_PORT,
    MIN_PORT,
    RAKNET_PORT,
    SSDPP_PORT,
    UAUDP_PORT,
    WEBSERVER_DEFAULT_HOST,
    WEBSERVER_DEFAULT_PORT,
)
from session_sniffer.networking.third_party_servers import ALL_THIRD_PARTY_SERVER_NAMES, ThirdPartyServers


class SettingType(Enum):
    """Enumeration of supported setting widget types."""

    BOOLEAN = auto()
    STRING = auto()
    INTEGER = auto()
    INTEGER_OR_ALL = auto()
    FLOAT = auto()
    ENUM = auto()
    BOOL_OR_ENUM = auto()
    IPV4 = auto()
    MAC_ADDRESS = auto()
    COLUMN_TUPLE = auto()
    IP_RANGE_TUPLE = auto()
    STRING_TUPLE = auto()
    THIRD_PARTY_SERVERS_TUPLE = auto()
    COLOR = auto()


@dataclass(frozen=True, slots=True)
class SettingMeta:
    """Metadata describing a single application setting for the Settings dialog."""

    category: str
    display_label: str
    setting_type: SettingType
    tooltip: str = ''
    requires_capture_restart: bool = False
    allowed_values: tuple[str, ...] = ()
    min_value: float | None = None
    max_value: float | None = None
    step: float | None = None
    column_source: tuple[str, ...] = field(default_factory=tuple)
    allowed_columns_attr: str | None = None
    display_labels: dict[str, str] | None = None
    group: str | None = None
    subgroup: str | None = None
    hidden: bool = False
    special_value_text: str = 'Tout'
    max_length: int | None = None
    min_length: int | None = None
    min_width: int | None = None
    max_width: int | None = None
    validator_pattern: str | None = None
    secret: bool = False


SETTING_CATEGORIES_ORDER: tuple[str, ...] = (
    'Launcher',
    'Capture',
    'Session',
    'Columns',
    'Discord',
    'Web Server',
    'GTA V',
)


SETTING_METADATA: dict[str, SettingMeta] = {
    'capture_interface_name': SettingMeta(
        category='Capture',
        group='Interface',
        display_label="Nom de l'interface",
        setting_type=SettingType.STRING,
        tooltip="Nom de l'interface réseau utilisée pour la capture.",
        requires_capture_restart=True,
        hidden=True,
    ),
    'capture_ip_address': SettingMeta(
        category='Capture',
        group='Interface',
        display_label='Adresse IP',
        setting_type=SettingType.IPV4,
        tooltip='Adresse IP locale utilisée pour la capture.',
        requires_capture_restart=True,
        hidden=True,
    ),
    'capture_mac_address': SettingMeta(
        category='Capture',
        group='Interface',
        display_label='Adresse MAC',
        setting_type=SettingType.MAC_ADDRESS,
        tooltip='Adresse MAC locale à forcer pour la capture.',
        requires_capture_restart=True,
        hidden=True,
    ),
    'capture_arp_spoofing': SettingMeta(
        category='Capture',
        group='Interface',
        display_label='ARP Spoofing',
        setting_type=SettingType.BOOLEAN,
        tooltip="Activer l'ARP spoofing pour intercepter les paquets.",
        requires_capture_restart=True,
        hidden=True,
    ),
    'capture_feature_set': SettingMeta(
        category='Capture',
        group='General',
        display_label='Mode de fonctions',
        setting_type=SettingType.ENUM,
        tooltip='Débloque des outils et fonctions exclusives adaptés au logiciel/jeu choisi.',
        requires_capture_restart=True,
        allowed_values=(
            'None',
            'GTA V',
            'RDR2',
        ),
    ),
    'capture_filter_process_pid': SettingMeta(
        category='Capture',
        group='General',
        display_label='Processus cible',
        setting_type=SettingType.INTEGER_OR_ALL,
        special_value_text='Désactivé',
        min_value=0,
        max_value=4194304,
        step=1,
        tooltip=(
            "Quand l'app tourne sur ce PC, limite la capture au seul trafic réseau\ndu processus cible choisi (PID), en se basant sur ses ports UDP locaux actifs.\n\nTout le bruit de fond et les autres applications de ton PC (Discord,\nnavigateurs, Steam, etc.) seront complètement ignorés.\n\nDésactivé (0) : tout le trafic UDP est capturé sans filtre de processus.\n\nRemarque : ce réglage ne s'applique qu'aux captures sur ce PC. Quand tu scannes\nun appareil externe (console via ARP spoofing ou deuxième carte réseau), il est\nimpossible d'inspecter ses processus, donc cette limite est ignorée automatiquement."
        ),
        requires_capture_restart=False,
    ),
    'capture_overflow_timer': SettingMeta(
        category='Capture',
        group='General',
        display_label='Délai de débordement',
        setting_type=SettingType.INTEGER_OR_ALL,
        tooltip=(
            "Quand la capture prend du retard (ex. lors d'un pic soudain de paquets entrants),\nle moteur met les paquets en attente et les traite avec de plus en plus de retard —\ntu analyses alors du vieux trafic au lieu de la session en direct.\n\nCe seuil définit le retard maximum autorisé pour un paquet (en secondes).\nSi un paquet arrive avec plus de retard que ça, les paquets périmés sont supprimés\nautomatiquement pour rattraper le temps réel sans redémarrer la capture.\n\nConseillé : 3-5 secondes — assez bas pour récupérer vite sans réagir aux petits pics.\n\nDésactivé (0) : les paquets périmés ne sont jamais supprimés.\nSous gros trafic, le sniffer prendra de plus en plus de retard,\naffichera des données obsolètes et ratera des connexions jusqu'à ce que le trafic baisse."
        ),
        requires_capture_restart=False,
        min_value=0,
        step=1,
        special_value_text='Désactivé',
    ),
    'capture_ps3_name_resolver': SettingMeta(
        category='Capture',
        group='General',
        display_label='Résolveur de pseudos PS3',
        setting_type=SettingType.BOOLEAN,
        tooltip='Extraire les pseudos PlayStation directement des paquets de jeux PS3 et les afficher dans la colonne Usernames.',
        requires_capture_restart=True,
    ),
    'capture_block_third_party_servers': SettingMeta(
        category='Capture',
        group='IP Filters',
        display_label='Fournisseurs tiers',
        setting_type=SettingType.THIRD_PARTY_SERVERS_TUPLE,
        tooltip="Choisir les plages d'IP de serveurs tiers à exclure de la capture.",
        requires_capture_restart=True,
        allowed_columns_attr='ALL_THIRD_PARTY_SERVERS',
        display_labels={server.name: server.display_name for server in ThirdPartyServers},
    ),
    'capture_blocked_ips': SettingMeta(
        category='Capture',
        group='IP Filters',
        display_label='Liste de blocage perso (IP / plages)',
        setting_type=SettingType.IP_RANGE_TUPLE,
        tooltip='Adresses IP et plages bloquées dans la session. Ajoute des entrées ici ou via le clic droit sur un joueur.',
        requires_capture_restart=True,
    ),
    'capture_filtered_isps': SettingMeta(
        category='Capture',
        group='IP Filters',
        display_label='FAI / ASN filtrés',
        setting_type=SettingType.STRING_TUPLE,
        tooltip=(
            "Exclure les joueurs dont le FAI ou l'ASN correspond à une entrée de cette liste. Entre des noms de FAI ou d'ASN complets ou partiels (ex. Take-Two, Amazon, Hetzner, AS15169). Ajoute des entrées ici ou via le clic droit sur un joueur."
        ),
        requires_capture_restart=False,
    ),
    'capture_prepend_custom_capture_filter': SettingMeta(
        category='Capture',
        group='IP Filters',
        display_label='Filtre de capture perso',
        setting_type=SettingType.STRING,
        tooltip='Filtre BPF ajouté au début du filtre de capture.',
        requires_capture_restart=True,
    ),
    'capture_filter_block_rtcp': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Payload Filters',
        display_label='Bloquer RTCP',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            'Exclure les paquets RTCP (Real-Time Control Protocol) de la capture.\n\nLes paquets RTCP peuvent révéler les IP de services tiers comme les serveurs vocaux Discord.\nActive pour masquer ces IP ; désactive pour les voir dans le tableau.'
        ),
        requires_capture_restart=True,
    ),
    'capture_filter_block_ssdp': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Port Filters',
        display_label='Bloquer SSDP',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            f'Exclure les paquets SSDP (Simple Service Discovery Protocol) de la capture (port {SSDPP_PORT}). Ce sont des annonces de découverte d\'appareils du réseau local, sans rapport avec les sessions de jeu.'
        ),
        requires_capture_restart=True,
    ),
    'capture_filter_block_raknet': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Port Filters',
        display_label='Bloquer RakNet',
        setting_type=SettingType.BOOLEAN,
        tooltip=f'Exclure les paquets RakNet de la capture (port {RAKNET_PORT}). Utilisé par la découverte LAN de Minecraft Bedrock et des services similaires.',
        requires_capture_restart=True,
    ),
    'capture_filter_block_dtls': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Payload Filters',
        display_label='Bloquer DTLS',
        setting_type=SettingType.BOOLEAN,
        tooltip='Exclure les paquets DTLS (Datagram Transport Layer Security) de la capture. Identifiés par inspection du contenu.',
        requires_capture_restart=True,
    ),
    'capture_filter_block_uaudp': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Port Filters',
        display_label='Bloquer UAUDP',
        setting_type=SettingType.BOOLEAN,
        tooltip=f'Exclure les paquets UAUDP (audio Avaya/UA sur UDP) de la capture (port {UAUDP_PORT}).',
        requires_capture_restart=True,
    ),
    'capture_filter_block_classicstun': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Port Filters',
        display_label='Bloquer ClassicSTUN',
        setting_type=SettingType.BOOLEAN,
        tooltip=f'Exclure les paquets ClassicSTUN (Session Traversal Utilities for NAT) de la capture (port {CLASSICSTUN_PORT}).',
        requires_capture_restart=True,
    ),
    'capture_filter_block_llmnr': SettingMeta(
        category='Capture',
        group='IP Filters',
        subgroup='Port Filters',
        display_label='Bloquer LLMNR',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            f'Exclure les paquets LLMNR (Link-Local Multicast Name Resolution) de la capture (port {LLMNR_PORT}). Ce sont des annonces de résolution de noms du réseau local Windows, sans rapport avec les sessions de jeu.'
        ),
        requires_capture_restart=True,
    ),
    'gui_interface_selection_auto_connect': SettingMeta(
        category='Launcher',
        group='Interface Selection',
        display_label='Connexion auto',
        setting_type=SettingType.BOOLEAN,
        tooltip='Se connecter automatiquement à la dernière interface utilisée au démarrage.',
    ),
    'gui_interface_selection_hide_inactive': SettingMeta(
        category='Launcher',
        group='Interface Selection',
        display_label='Masquer les inactives',
        setting_type=SettingType.BOOLEAN,
        tooltip='Masquer les interfaces réseau sans trafic actif.',
    ),
    'gui_interface_selection_hide_neighbours': SettingMeta(
        category='Launcher',
        group='Interface Selection',
        display_label='Masquer les voisins',
        setting_type=SettingType.BOOLEAN,
        tooltip='Masquer les voisins (appareils découverts via ARP sur le réseau local).',
    ),
    'gui_sessions_logging': SettingMeta(
        category='Session',
        group='Sessions Logging',
        display_label='Logs de sessions',
        setting_type=SettingType.BOOLEAN,
        tooltip='Enregistrer les données de session dans le dossier Sessions Logging.',
    ),
    'gui_sessions_logging_delete_empty_files': SettingMeta(
        category='Session',
        group='Sessions Logging',
        display_label='Supprimer les fichiers vides',
        setting_type=SettingType.BOOLEAN,
        tooltip='Supprimer automatiquement les logs de session sans aucun joueur.',
    ),
    'gui_sessions_logging_delete_empty_folders': SettingMeta(
        category='Session',
        group='Sessions Logging',
        display_label='Supprimer les dossiers vides',
        setting_type=SettingType.BOOLEAN,
        tooltip='Supprimer automatiquement les dossiers de logs vides (année, mois ou jour).',
    ),
    'gui_reset_ports_on_rejoins': SettingMeta(
        category='Session',
        group='General',
        display_label='Réinitialiser les ports au retour',
        setting_type=SettingType.BOOLEAN,
        tooltip="Effacer les ports enregistrés d'un joueur quand il revient dans la session.",
    ),
    'gui_columns_connected_shown': SettingMeta(
        category='Columns',
        group='Column Visibility',
        display_label='Colonnes affichées (connectés)',
        setting_type=SettingType.COLUMN_TUPLE,
        tooltip='Colonnes affichées dans le tableau des joueurs connectés.',
        allowed_columns_attr='GUI_TOGGLEABLE_CONNECTED_COLUMNS',
    ),
    'gui_columns_disconnected_shown': SettingMeta(
        category='Columns',
        group='Column Visibility',
        display_label='Colonnes affichées (déconnectés)',
        setting_type=SettingType.COLUMN_TUPLE,
        tooltip='Colonnes affichées dans le tableau des joueurs déconnectés.',
        allowed_columns_attr='GUI_TOGGLEABLE_DISCONNECTED_COLUMNS',
    ),
    'gui_connected_table_sort_column': SettingMeta(
        category='Columns',
        group='Table Sorting',
        display_label='Colonne de tri (connectés)',
        setting_type=SettingType.ENUM,
        tooltip='Colonne utilisée par défaut pour trier le tableau des joueurs connectés.',
        allowed_columns_attr='GUI_ALL_CONNECTED_COLUMNS',
    ),
    'gui_connected_table_sort_order': SettingMeta(
        category='Columns',
        group='Table Sorting',
        display_label='Ordre de tri (connectés)',
        setting_type=SettingType.ENUM,
        tooltip='Ordre de tri par défaut (croissant ou décroissant) du tableau des joueurs connectés.',
        allowed_values=('Ascending', 'Descending'),
    ),
    'gui_disconnected_table_sort_column': SettingMeta(
        category='Columns',
        group='Table Sorting',
        display_label='Colonne de tri (déconnectés)',
        setting_type=SettingType.ENUM,
        tooltip='Colonne utilisée par défaut pour trier le tableau des joueurs déconnectés.',
        allowed_columns_attr='GUI_ALL_DISCONNECTED_COLUMNS',
    ),
    'gui_disconnected_table_sort_order': SettingMeta(
        category='Columns',
        group='Table Sorting',
        display_label='Ordre de tri (déconnectés)',
        setting_type=SettingType.ENUM,
        tooltip='Ordre de tri par défaut (croissant ou décroissant) du tableau des joueurs déconnectés.',
        allowed_values=('Ascending', 'Descending'),
    ),
    'gui_columns_datetime_show_date': SettingMeta(
        category='Columns',
        group='Date & Time Formatting',
        display_label='Afficher la date',
        setting_type=SettingType.BOOLEAN,
        tooltip='Afficher la date dans les colonnes date/heure.',
    ),
    'gui_columns_datetime_show_time': SettingMeta(
        category='Columns',
        group='Date & Time Formatting',
        display_label="Afficher l'heure",
        setting_type=SettingType.BOOLEAN,
        tooltip="Afficher l'heure dans les colonnes date/heure.",
    ),
    'gui_columns_datetime_show_elapsed_time': SettingMeta(
        category='Columns',
        group='Date & Time Formatting',
        display_label='Afficher le temps écoulé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Afficher le temps écoulé dans les colonnes date/heure.',
    ),
    'gui_columns_timezone_display': SettingMeta(
        category='Columns',
        group='Date & Time Formatting',
        display_label='Affichage du fuseau horaire',
        setting_type=SettingType.ENUM,
        tooltip=(
            "Choisit ce qui est affiché dans la colonne Fuseau horaire. « Fuseau horaire » affiche seulement le nom du fuseau, « Fuseau + heure locale » ajoute l'heure locale du joueur, « Heure locale » affiche seulement l'heure locale."
        ),
        allowed_values=(
            'Timezone',
            'Timezone + Local Time',
            'Local Time',
        ),
    ),
    'gui_columns_geo_country_append_alpha2': SettingMeta(
        category='Columns',
        group='Geolocation Data',
        display_label='Ajouter le code pays',
        setting_type=SettingType.BOOLEAN,
        tooltip='Ajouter le code ISO à deux lettres au nom du pays (ex. "France (FR)").',
    ),
    'gui_columns_geo_continent_append_alpha2': SettingMeta(
        category='Columns',
        group='Geolocation Data',
        display_label='Ajouter le code continent',
        setting_type=SettingType.BOOLEAN,
        tooltip='Ajouter le code ISO à deux lettres au nom du continent (ex. "Europe (EU)").',
    ),
    'gui_connected_table_rows_per_page': SettingMeta(
        category='Session',
        group='Table Pagination',
        display_label='Lignes par page (connectés)',
        setting_type=SettingType.INTEGER_OR_ALL,
        special_value_text='Tout',
        tooltip='Nombre maximum de lignes par page du tableau des joueurs connectés. 0 = tout afficher.',
        min_value=0,
        max_value=5000,
        step=10,
    ),
    'gui_disconnected_table_rows_per_page': SettingMeta(
        category='Session',
        group='Table Pagination',
        display_label='Lignes par page (déconnectés)',
        setting_type=SettingType.INTEGER_OR_ALL,
        special_value_text='Tout',
        tooltip='Nombre maximum de lignes par page du tableau des joueurs déconnectés. 0 = tout afficher.',
        min_value=0,
        max_value=5000,
        step=10,
    ),
    'gui_disconnected_players_enabled': SettingMeta(
        category='Session',
        group='Disconnected Players',
        display_label='Activé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Suivre et afficher les joueurs déconnectés dans un tableau séparé sous les joueurs connectés.',
    ),
    'gui_disconnected_players_timer': SettingMeta(
        category='Session',
        group='Disconnected Players',
        display_label='Délai de déconnexion',
        setting_type=SettingType.INTEGER,
        tooltip="Secondes d'inactivité avant qu'un joueur soit considéré comme déconnecté.",
        min_value=3,
        step=1,
    ),
    'pinger_local': SettingMeta(
        category='Session',
        group='Player Pinging',
        display_label='Ping direct (rapide)',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            "Choisir d'envoyer les pings directement depuis ton PC ou\nvia des serveurs web tiers.\n\nLe ping direct répond beaucoup plus vite, sans limite de requêtes,\nmais ton IP publique peut être visible par la cible.\nDésactivé, les pings passent par des serveurs externes pour aider à\ncacher ton IP, mais c'est plus lent et soumis à leurs limites ou pannes."
        ),
    ),
    'gui_always_on_top': SettingMeta(
        category='Session',
        group='Application Window',
        display_label='Toujours au premier plan',
        setting_type=SettingType.BOOLEAN,
        tooltip='Garder la fenêtre principale au-dessus de toutes les autres.',
    ),
    'gui_remember_window_layout': SettingMeta(
        category='Session',
        group='Application Window',
        display_label='Mémoriser la disposition',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            "Enregistrer et restaurer la disposition des tableaux de la fenêtre principale (séparation\nconnectés/déconnectés et largeur des colonnes) ainsi que la taille et la séparation\ndu gestionnaire UserIP d'un lancement à l'autre."
        ),
    ),
    'gui_servers_color_enabled': SettingMeta(
        category='Session',
        group='Detected Servers',
        display_label='Activé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Surligner les serveurs de jeu détectés avec une couleur de fond dans les tableaux de joueurs.',
    ),
    'gui_servers_color': SettingMeta(
        category='Session',
        group='Detected Servers',
        display_label='Couleur',
        setting_type=SettingType.COLOR,
        tooltip='Couleur de fond utilisée pour surligner les serveurs de jeu détectés dans les tableaux.',
    ),
    'voice_notifications_enabled': SettingMeta(
        category='Session',
        group='Voice Notifications',
        display_label='Activé',
        setting_type=SettingType.BOOLEAN,
        tooltip="Activer ou désactiver toutes les notifications vocales de l'application.",
    ),
    'gui_ignore_screen_resolution_warning': SettingMeta(
        category='Launcher',
        group='Application Popups',
        display_label="Ignorer l'alerte de résolution d'écran",
        setting_type=SettingType.BOOLEAN,
        tooltip="Ignorer l'alerte quand la résolution d'écran est inférieure à 1024x768.",
        hidden=True,
    ),
    # ------------------------------------------------------------------
    'discord_presence': SettingMeta(
        category='Discord',
        group='Rich Presence (RPC)',
        display_label='Activé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Activer le statut Discord Rich Presence (RPC).',
    ),
    'discord_presence_title': SettingMeta(
        category='Discord',
        group='Rich Presence (RPC)',
        display_label='Titre du statut',
        setting_type=SettingType.STRING,
        tooltip='Texte perso affiché dans ton statut Discord Rich Presence (laisse vide pour désactiver, ou au moins 2 caractères).',
    ),
    'show_discord_popup': SettingMeta(
        category='Launcher',
        group='Application Popups',
        display_label='Afficher la fenêtre Discord au démarrage',
        setting_type=SettingType.BOOLEAN,
        tooltip="Afficher la fenêtre d'invitation Discord au lancement de l'application.",
    ),
    'discord_webhook_enabled': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Activé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Copier en direct les tableaux des joueurs connectés/déconnectés dans un salon Discord via webhook.',
    ),
    'discord_webhook_url': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='URL du webhook',
        setting_type=SettingType.STRING,
        tooltip='URL du webhook du salon Discord (ex. https://discord.com/api/webhooks/<id>/<token>).',
        secret=True,
    ),
    'discord_webhook_refresh_interval': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Intervalle de mise à jour (s)',
        setting_type=SettingType.INTEGER,
        tooltip='Secondes entre deux mises à jour du webhook. Trop bas = risque de limite Discord (minimum 5).',
        min_value=5,
        max_value=300,
        step=1,
    ),
    'discord_webhook_include_connected': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Inclure le tableau des connectés',
        setting_type=SettingType.BOOLEAN,
        tooltip='Publier le tableau des joueurs connectés.',
    ),
    'discord_webhook_include_disconnected': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Inclure le tableau des déconnectés',
        setting_type=SettingType.BOOLEAN,
        tooltip='Publier le tableau des joueurs déconnectés.',
    ),
    'discord_webhook_max_rows_per_table': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Lignes max par tableau',
        setting_type=SettingType.INTEGER,
        tooltip='Nombre maximum de lignes par tableau (les autres sont résumées en "… et N de plus").',
        min_value=1,
        max_value=100,
        step=1,
    ),
    'discord_webhook_max_connected_players': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Joueurs connectés max',
        setting_type=SettingType.INTEGER_OR_ALL,
        tooltip='Nombre maximum de joueurs connectés envoyés au webhook. Mettre 0 pour tous les inclure.',
        min_value=0,
        max_value=100,
        step=1,
    ),
    'discord_webhook_max_disconnected_players': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Joueurs déconnectés max',
        setting_type=SettingType.INTEGER_OR_ALL,
        tooltip='Nombre maximum de joueurs déconnectés envoyés au webhook. Mettre 0 pour tous les inclure.',
        min_value=0,
        max_value=100,
        step=1,
    ),
    'discord_webhook_format': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label="Format d'affichage",
        setting_type=SettingType.ENUM,
        tooltip=(
            'Desktop : grand tableau encadré dans un bloc de code (idéal sur PC).\nMobile : un bloc markdown par joueur dans un embed Discord (lisible sur téléphone).'
        ),
        allowed_values=('Desktop', 'Mobile'),
    ),
    'discord_webhook_columns_connected': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Colonnes (connectés)',
        setting_type=SettingType.COLUMN_TUPLE,
        tooltip='Colonnes affichées dans le tableau webhook des joueurs connectés.',
        allowed_columns_attr='GUI_ALL_CONNECTED_COLUMNS',
    ),
    'discord_webhook_columns_disconnected': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='Colonnes (déconnectés)',
        setting_type=SettingType.COLUMN_TUPLE,
        tooltip='Colonnes affichées dans le tableau webhook des joueurs déconnectés.',
        allowed_columns_attr='GUI_ALL_DISCONNECTED_COLUMNS',
    ),
    'discord_webhook_message_ids': SettingMeta(
        category='Discord',
        group='Webhook',
        display_label='IDs des messages (interne)',
        setting_type=SettingType.STRING,
        tooltip='Stockage interne des IDs des messages du webhook (ne pas modifier).',
        hidden=True,
    ),
    'webserver_enabled': SettingMeta(
        category='Web Server',
        group='Connection',
        display_label='Activer le serveur web',
        setting_type=SettingType.BOOLEAN,
        tooltip='Activer un serveur web local pour voir la session en direct depuis un navigateur.',
    ),
    'webserver_host': SettingMeta(
        category='Web Server',
        group='Connection',
        display_label='Hôte',
        setting_type=SettingType.IPV4,
        tooltip="Adresse IP d'écoute du serveur web (0.0.0.0 = toutes les interfaces).",
    ),
    'webserver_port': SettingMeta(
        category='Web Server',
        group='Connection',
        display_label='Port',
        setting_type=SettingType.INTEGER,
        tooltip=f'Numéro de port du serveur web ({MIN_PORT}-{MAX_PORT}).',
        min_value=MIN_PORT,
        max_value=MAX_PORT,
        step=1,
    ),
    'webserver_username': SettingMeta(
        category='Web Server',
        group='Authentication',
        display_label="Nom d'utilisateur",
        setting_type=SettingType.STRING,
        tooltip="Nom d'utilisateur HTTP Basic Auth (optionnel). Laisse vide pour désactiver l'authentification.",
    ),
    'webserver_password': SettingMeta(
        category='Web Server',
        group='Authentication',
        display_label='Mot de passe',
        setting_type=SettingType.STRING,
        tooltip="Mot de passe HTTP Basic Auth (optionnel). L'authentification n'est active que si le nom d'utilisateur et le mot de passe sont remplis.",
        secret=True,
    ),
    'updater_channel': SettingMeta(
        category='Launcher',
        group='Updater',
        display_label='Canal de mise à jour',
        setting_type=SettingType.ENUM,
        tooltip='Canal de version pour les mises à jour.',
        allowed_values=('Stable', 'Pre-release'),
        hidden=True,
    ),
    'looky_enabled': SettingMeta(
        category='GTA V',
        group='Looky System',
        display_label='Activer Looky System',
        setting_type=SettingType.BOOLEAN,
        tooltip="Interrupteur général de toutes les fonctions Looky System. Le désactiver bloque tout appel à l'API Looky System.",
    ),
    'looky_exclusive_gta5_process': SettingMeta(
        category='GTA V',
        group='Looky System',
        display_label='Limiter au processus GTA5',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            "Ne lancer les recherches automatiques Looky System que si le processus GTA5 est détecté\nsur ce PC (Legacy GTA5.exe ou Enhanced GTA5_Enhanced.exe), et limiter les recherches\naux seules IP de joueurs qui communiquent avec le processus GTA5.\n\nRemarque : ce réglage ne s'applique qu'aux captures sur ce PC. Quand tu scannes\nun appareil externe (console via ARP spoofing), il est impossible d'inspecter\nses processus, donc cette limite est ignorée et les recherches portent sur\ntoutes les IP de joueurs capturées (hors serveurs tiers).\n\nDésactivé, les recherches tournent en continu quel que soit l'état de GTA5 et incluent\ntoutes les IP de joueurs capturées (hors serveurs tiers)."
        ),
    ),
    'looky_game_version': SettingMeta(
        category='GTA V',
        group='Looky System',
        display_label='Version du jeu',
        setting_type=SettingType.ENUM,
        tooltip=(
            "Filtre de version appliqué aux recherches Looky System (auto en arrière-plan et manuelles). Les demandes de crawler visent automatiquement l'édition du jeu lancée."
        ),
        allowed_values=('Both', 'Legacy', 'Enhanced'),
    ),
    'looky_api_key': SettingMeta(
        category='GTA V',
        group='Looky System',
        display_label='Clé API',
        setting_type=SettingType.STRING,
        tooltip='Ton jeton Bearer Looky System. Obligatoire pour toutes les fonctions Looky System — recherche auto, recherches manuelles et demandes de crawler.',
        validator_pattern=r'[A-Za-z0-9._\-]',
        secret=True,
        min_width=600,
        max_width=600,
    ),
    'gui_session_host_detection': SettingMeta(
        category='GTA V',
        group='Session Host',
        display_label="Détection de l'hôte de session",
        setting_type=SettingType.BOOLEAN,
        tooltip="Détecter et suivre l'hôte des sessions de jeu compatibles.",
    ),
    'gui_session_host_icon': SettingMeta(
        category='GTA V',
        group='Session Host',
        display_label="Icône de l'hôte dans le tableau",
        setting_type=SettingType.BOOLEAN,
        tooltip="Afficher l'icône couronne à côté de l'IP de l'hôte de session dans les tableaux.",
    ),
    'solo_session_duration': SettingMeta(
        category='GTA V',
        group='Solo Public Session',
        display_label='Durée de suspension pour session solo',
        setting_type=SettingType.INTEGER,
        tooltip='Durée en secondes de suspension du jeu pour obtenir une session publique solo.',
        min_value=6,
        max_value=60,
        step=1,
    ),
    'high_rate_monitor_icon': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Icône du moniteur de trafic élevé',
        setting_type=SettingType.BOOLEAN,
        tooltip="Afficher l'icône compteur de vitesse dans la colonne Adresse IP pour les joueurs qui dépassent les seuils.",
    ),
    'high_rate_monitor_run_in_background': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Moniteur de trafic élevé en arrière-plan',
        setting_type=SettingType.BOOLEAN,
        tooltip=(
            'Activé, le moniteur de trafic élevé suit en continu le débit des joueurs en arrière-plan même quand la fenêtre Trouver un joueur est fermée.\nDésactivé, le suivi ne fonctionne que quand la fenêtre Trouver un joueur est ouverte.'
        ),
    ),
    'high_rate_monitor_auto_select': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Sélection auto du moniteur de trafic élevé',
        setting_type=SettingType.BOOLEAN,
        tooltip='Sélectionner automatiquement les joueurs à trafic élevé dans le tableau des joueurs connectés.',
    ),
    'high_rate_monitor_pps_threshold': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Seuil PPS du moniteur de trafic élevé',
        setting_type=SettingType.INTEGER,
        tooltip='Nombre minimum de paquets par seconde pour signaler un joueur en trafic élevé.',
        min_value=20,
        max_value=50,
        step=1,
    ),
    'high_rate_monitor_bps_threshold': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Seuil BPS du moniteur de trafic élevé',
        setting_type=SettingType.INTEGER,
        tooltip='Bande passante minimum en kilo-octets par seconde (Ko/s) pour signaler un joueur en trafic élevé.',
        min_value=3,
        max_value=500,
        step=1,
    ),
    'high_rate_monitor_duration_threshold': SettingMeta(
        category='GTA V',
        group='High Rate Monitor',
        display_label='Durée du moniteur de trafic élevé',
        setting_type=SettingType.INTEGER,
        tooltip="Nombre de secondes d'affilée pendant lesquelles le trafic du joueur doit dépasser les seuils PPS et BPS.",
        min_value=1,
        max_value=10,
        step=1,
    ),
    'player_identifier_icon': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Icône du Trouveur de joueur',
        setting_type=SettingType.BOOLEAN,
        tooltip="Afficher l'icône de cible dans la colonne Adresse IP pour les joueurs identifiés par l'outil.",
    ),
    'player_identifier_spike_zscore': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Z-score de pic (Trouveur de joueur)',
        setting_type=SettingType.FLOAT,
        tooltip='Seuil de sensibilité statistique (z-score) pour détecter les pics de trafic.',
        min_value=1.0,
        max_value=20.0,
        step=0.5,
    ),
    'player_identifier_spike_seconds': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Durée de pic (Trouveur de joueur)',
        setting_type=SettingType.INTEGER,
        tooltip="Nombre de secondes d'affilée qu'un pic de trafic doit durer pour identifier un joueur.",
        min_value=1,
        max_value=30,
        step=1,
    ),
    'player_identifier_baseline_seconds': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Durée de référence (Trouveur de joueur)',
        setting_type=SettingType.INTEGER,
        tooltip="Durée en secondes d'enregistrement du trafic calme avant la recherche du joueur.",
        min_value=5,
        max_value=120,
        step=1,
    ),
    'player_identifier_contamination_zscore': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Z-score de perturbation (Trouveur de joueur)',
        setting_type=SettingType.FLOAT,
        tooltip='Seuil de z-score pour détecter une référence faussée. Annule la référence si une IP garde ce z-score.',
        min_value=3.0,
        max_value=50.0,
        step=0.5,
    ),
    'player_identifier_contamination_seconds': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Durée de perturbation (Trouveur de joueur)',
        setting_type=SettingType.INTEGER,
        tooltip="Secondes d'affilée pendant lesquelles une IP doit dépasser le z-score de perturbation pour annuler la référence.",
        min_value=1,
        max_value=30,
        step=1,
    ),
    'player_identifier_contamination_min_samples': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Délai de grâce (Trouveur de joueur)',
        setting_type=SettingType.INTEGER,
        tooltip="Nombre minimum de mesures avant d'activer la vérification de perturbation.",
        min_value=5,
        max_value=60,
        step=1,
    ),
    'player_identifier_baseline_timeout': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Délai max de référence (Trouveur de joueur)',
        setting_type=SettingType.INTEGER,
        tooltip='Temps maximum en secondes de la phase de référence avant de la verrouiller de force.',
        min_value=10,
        max_value=300,
        step=1,
    ),
    'player_identifier_session_drift_zscore': SettingMeta(
        category='GTA V',
        group='Player Identifier',
        display_label='Z-score de dérive de session (Trouveur de joueur)',
        setting_type=SettingType.FLOAT,
        tooltip='Seuil de z-score global sur toutes les IP suivies pour détecter une dérive du trafic de toute la session.',
        min_value=1.0,
        max_value=30.0,
        step=0.5,
    ),
}


class SettingDefaults(TypedDict):
    """Strongly-typed structure for all application setting default values."""

    capture_interface_name: str | None
    capture_ip_address: str | None
    capture_mac_address: str | None
    capture_arp_spoofing: bool
    capture_block_third_party_servers: tuple[str, ...]
    capture_feature_set: str | None
    capture_filter_process_pid: int
    capture_overflow_timer: int
    capture_ps3_name_resolver: bool
    capture_prepend_custom_capture_filter: str | None
    capture_blocked_ips: tuple[str, ...]
    capture_filtered_isps: tuple[str, ...]
    capture_filter_block_rtcp: bool
    capture_filter_block_ssdp: bool
    capture_filter_block_raknet: bool
    capture_filter_block_dtls: bool
    capture_filter_block_uaudp: bool
    capture_filter_block_classicstun: bool
    capture_filter_block_llmnr: bool
    gui_always_on_top: bool
    gui_remember_window_layout: bool
    gui_servers_color_enabled: bool
    gui_servers_color: str
    gui_interface_selection_auto_connect: bool
    gui_interface_selection_hide_inactive: bool
    gui_interface_selection_hide_neighbours: bool
    gui_sessions_logging: bool
    gui_sessions_logging_delete_empty_files: bool
    gui_sessions_logging_delete_empty_folders: bool
    gui_reset_ports_on_rejoins: bool
    gui_session_host_detection: bool
    gui_session_host_icon: bool
    gui_columns_connected_shown: tuple[str, ...]
    gui_columns_disconnected_shown: tuple[str, ...]
    gui_columns_datetime_show_date: bool
    gui_columns_datetime_show_time: bool
    gui_columns_datetime_show_elapsed_time: bool
    gui_columns_timezone_display: str
    gui_columns_geo_country_append_alpha2: bool
    gui_columns_geo_continent_append_alpha2: bool
    gui_connected_table_rows_per_page: int
    gui_connected_table_sort_column: str
    gui_connected_table_sort_order: str
    gui_disconnected_players_enabled: bool
    gui_disconnected_table_rows_per_page: int
    gui_disconnected_table_sort_column: str
    gui_disconnected_table_sort_order: str
    gui_disconnected_players_timer: int
    gui_ignore_screen_resolution_warning: bool
    voice_notifications_enabled: bool
    pinger_local: bool
    discord_presence: bool
    discord_presence_title: str
    show_discord_popup: bool
    discord_webhook_enabled: bool
    discord_webhook_url: str | None
    discord_webhook_refresh_interval: int
    discord_webhook_include_connected: bool
    discord_webhook_include_disconnected: bool
    discord_webhook_max_rows_per_table: int
    discord_webhook_max_connected_players: int
    discord_webhook_max_disconnected_players: int
    discord_webhook_format: str
    discord_webhook_columns_connected: tuple[str, ...]
    discord_webhook_columns_disconnected: tuple[str, ...]
    discord_webhook_message_ids: str | None
    webserver_enabled: bool
    webserver_host: str
    webserver_port: int
    webserver_username: str | None
    webserver_password: str | None
    updater_channel: str | None
    looky_enabled: bool
    looky_exclusive_gta5_process: bool
    looky_game_version: str
    looky_api_key: str | None
    high_rate_monitor_icon: bool
    high_rate_monitor_run_in_background: bool
    high_rate_monitor_auto_select: bool
    solo_session_duration: int
    high_rate_monitor_pps_threshold: int
    high_rate_monitor_bps_threshold: int
    high_rate_monitor_duration_threshold: int
    player_identifier_icon: bool
    player_identifier_spike_zscore: float
    player_identifier_spike_seconds: int
    player_identifier_baseline_seconds: int
    player_identifier_contamination_zscore: float
    player_identifier_contamination_seconds: int
    player_identifier_contamination_min_samples: int
    player_identifier_baseline_timeout: int
    player_identifier_session_drift_zscore: float


SETTING_DEFAULTS: SettingDefaults = {
    'capture_interface_name': None,
    'capture_ip_address': None,
    'capture_mac_address': None,
    'capture_arp_spoofing': False,
    'capture_block_third_party_servers': ALL_THIRD_PARTY_SERVER_NAMES,
    'capture_feature_set': None,
    'capture_filter_process_pid': 0,
    'capture_overflow_timer': 3,
    'capture_ps3_name_resolver': False,
    'capture_prepend_custom_capture_filter': None,
    'capture_blocked_ips': (),
    'capture_filtered_isps': (),
    'capture_filter_block_rtcp': True,
    'capture_filter_block_ssdp': True,
    'capture_filter_block_raknet': True,
    'capture_filter_block_dtls': True,
    'capture_filter_block_uaudp': True,
    'capture_filter_block_classicstun': True,
    'capture_filter_block_llmnr': True,
    'gui_always_on_top': False,
    'gui_remember_window_layout': False,
    'gui_servers_color_enabled': True,
    'gui_servers_color': DEFAULT_DETECTED_SERVER_COLOR,
    'gui_interface_selection_auto_connect': False,
    'gui_interface_selection_hide_inactive': True,
    'gui_interface_selection_hide_neighbours': False,
    'gui_sessions_logging': True,
    'gui_sessions_logging_delete_empty_files': False,
    'gui_sessions_logging_delete_empty_folders': False,
    'gui_reset_ports_on_rejoins': True,
    'gui_session_host_detection': True,
    'gui_session_host_icon': True,
    'gui_columns_connected_shown': (
        'Packets',
        'PPS',
        'Bandwidth',
        'BPS',
        'Hostname',
        'Ports',
        'Country',
        'Region',
        'ASN / ISP',
        'Mobile',
        'VPN',
        'Hosting',
        'Pinging',
    ),
    'gui_columns_disconnected_shown': (
        'T. Session Time',
        'Session Time',
        'Packets',
        'Bandwidth',
        'Hostname',
        'Ports',
        'Country',
        'Region',
        'ASN / ISP',
        'Mobile',
        'VPN',
        'Hosting',
        'Pinging',
    ),
    'gui_columns_datetime_show_date': False,
    'gui_columns_datetime_show_time': False,
    'gui_columns_datetime_show_elapsed_time': True,
    'gui_columns_timezone_display': 'Timezone',
    'gui_columns_geo_country_append_alpha2': True,
    'gui_columns_geo_continent_append_alpha2': True,
    'gui_connected_table_rows_per_page': 0,
    'gui_connected_table_sort_column': 'Last Rejoin',
    'gui_connected_table_sort_order': 'Descending',
    'gui_disconnected_players_enabled': True,
    'gui_disconnected_table_rows_per_page': 0,
    'gui_disconnected_table_sort_column': 'Last Seen',
    'gui_disconnected_table_sort_order': 'Ascending',
    'gui_disconnected_players_timer': 10,
    'gui_ignore_screen_resolution_warning': False,
    'voice_notifications_enabled': True,
    'pinger_local': True,
    'discord_presence': False,
    'discord_presence_title': 'Sniffing session traffic',
    'show_discord_popup': True,
    'discord_webhook_enabled': False,
    'discord_webhook_url': None,
    'discord_webhook_refresh_interval': 15,
    'discord_webhook_include_connected': True,
    'discord_webhook_include_disconnected': True,
    'discord_webhook_max_rows_per_table': 25,
    'discord_webhook_max_connected_players': 0,
    'discord_webhook_max_disconnected_players': 0,
    'discord_webhook_format': 'Desktop',
    'discord_webhook_columns_connected': (
        'Usernames',
        'IP Address',
        'Country',
        'Ports',
        'Packets',
        'Session Time',
        'Last Rejoin',
    ),
    'discord_webhook_columns_disconnected': (
        'Usernames',
        'IP Address',
        'Country',
        'Ports',
        'Packets',
        'Session Time',
        'Last Seen',
    ),
    'discord_webhook_message_ids': None,
    'webserver_enabled': False,
    'webserver_host': WEBSERVER_DEFAULT_HOST,
    'webserver_port': WEBSERVER_DEFAULT_PORT,
    'webserver_username': None,
    'webserver_password': None,
    'updater_channel': 'Stable',
    'looky_enabled': True,
    'looky_exclusive_gta5_process': True,
    'looky_game_version': 'Both',
    'looky_api_key': None,
    'high_rate_monitor_icon': True,
    'high_rate_monitor_run_in_background': True,
    'high_rate_monitor_auto_select': True,
    'solo_session_duration': 6,
    'high_rate_monitor_pps_threshold': 30,
    'high_rate_monitor_bps_threshold': 5,
    'high_rate_monitor_duration_threshold': 3,
    'player_identifier_icon': True,
    'player_identifier_spike_zscore': 3.0,
    'player_identifier_spike_seconds': 3,
    'player_identifier_baseline_seconds': 10,
    'player_identifier_contamination_zscore': 10.0,
    'player_identifier_contamination_seconds': 5,
    'player_identifier_contamination_min_samples': 15,
    'player_identifier_baseline_timeout': 30,
    'player_identifier_session_drift_zscore': 6.0,
}
