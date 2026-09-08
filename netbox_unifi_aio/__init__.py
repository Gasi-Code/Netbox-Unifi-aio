from netbox.plugins import PluginConfig


class NetboxUnifiAIOConfig(PluginConfig):
    name = 'netbox_unifi_aio'
    verbose_name = 'UniFi All-in-One'
    description = (
        'Integriert UniFi UCK Daten (Network, Design) in NetBox. '
        'Protect/Access folgen in spaeteren Phasen.'
    )
    version = '0.1.0'
    author = 'gascake'
    author_email = ''
    base_url = 'unifi-aio'
    min_version = '4.4.0'

    # Alles hier sind DEFAULTS. Echte Zugangsdaten gehoeren NICHT hierher,
    # sondern in die verschluesselten Felder des UCKConsole-Modells (siehe base/models.py).
    default_settings = {
        # Wie oft der periodische Sync-Job laufen soll (Minuten). 0 = nur manuell.
        'sync_interval_minutes': 0,
        # TLS-Verifikation für selbstsignierte UCK-Zertifikate standardmaessig aus,
        # da UDM/UCK-Geraete im Heimnetz i.d.R. kein vertrauenswuerdiges Zertifikat haben.
        # Kann pro Console ueberschrieben werden.
        'default_verify_tls': False,
    }

    def ready(self):
        super().ready()
        # Signal-Handler und periodische Jobs erst hier importieren,
        # NICHT auf Modulebene (sonst Gefahr von zirkulaeren Imports beim App-Loading).
        from . import signals  # noqa: F401


config = NetboxUnifiAIOConfig
