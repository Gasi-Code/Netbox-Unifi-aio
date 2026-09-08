# netbox_unifi_aio — Grundgerüst (Phase 1: base + network + design)

Enthält NICHT: Protect, Access, Talk, eigenes UI-Theme. Das ist bewusst so
begrenzt (siehe die Architektur-Diskussion) — jede weitere App bekommt ihr
eigenes Submodul nach demselben Muster wie `network/`.

## Struktur

```
netbox_unifi_aio/
├── __init__.py          PluginConfig
├── models.py             Re-Export aller Modelle (Django braucht das hier)
├── forms.py, tables.py, views.py, filtersets.py, urls.py, navigation.py, signals.py
├── base/
│   ├── models.py          UCKConsole (ein Eintrag pro UDM/UCK), SyncLog
│   ├── client.py           UnifiIntegrationClient (offiziell) + UnifiDesignClient (inoffiziell)
│   └── crypto.py            Verschlüsselung für gespeicherte Zugangsdaten
├── network/
│   ├── models.py           UnifiDevice (Spiegel der UniFi-Geräte)
│   └── sync.py              sync_network() — Geräte-Abgleich per Integration-API
└── design/
    ├── models.py            UnifiFloorplanMap (Rohdaten aus UniFi Design)
    ├── mapping.py            Koordinaten-Transformation (NOCH ZU VERIFIZIEREN, siehe TODO dort)
    └── sync.py               sync_design() + push_to_floorplan()
```

## Installation auf deinem Stack

Analog zu `netbox-force`: als lokaler Ordner unter `/config/plugins/`,
da noch kein veröffentlichtes PyPI-Paket.

```bash
# Auf der NAS, im Ordner, den du für lokale Plugins nutzt:
cp -r netbox_unifi_aio /volume1/docker/netbox/config/plugins/netbox-unifi-aio
```

`docker-compose.yml` — `INSTALL_PIP_PACKAGES` erweitern:
```yaml
INSTALL_PIP_PACKAGES: "/config/plugins/netbox-force /config/plugins/netbox-unifi-aio netbox-floorplan-plugin netboxlabs-netbox-custom-objects"
```

`configuration.py` — `PLUGINS` erweitern:
```python
PLUGINS = ["netbox_floorplan", "netbox_custom_objects", "netbox_force", "netbox_unifi_aio"]

PLUGINS_CONFIG = {
    # ... bestehende Einträge ...
    "netbox_unifi_aio": {
        "sync_interval_minutes": 0,   # 0 = nur manueller Sync über den Button in der UI
        "default_verify_tls": False,
    },
}
```

## ⚠️ Kritischer erster Schritt: Migration erzeugen

Diese Modelle haben noch KEINE Migration — die muss einmalig gegen eine
laufende NetBox-Instanz erzeugt werden (das kann ich nicht offline für dich
vorwegnehmen, da sie von NetBox-Core-Modellversionen abhängt):

```bash
sudo docker exec -it Netbox python3 /app/netbox/netbox/manage.py makemigrations netbox_unifi_aio
```

Die erzeugte Datei landet im Container unter
`/config/plugins/netbox-unifi-aio/netbox_unifi_aio/migrations/000X_....py`
(weil `/config` bei dir ins Volume gemountet ist) — die bleibt danach dauerhaft
erhalten, du musst diesen Schritt also nur EINMAL machen, nicht bei jedem
Container-Neustart. Direkt danach:

```bash
sudo docker restart Netbox
```

## Nutzung

1. **Plugins → UCK Consoles → Console hinzufügen.** Name, zugehöriger
   NetBox-Site, `base_url` (z. B. `https://192.168.1.1`), optional
   Integration-API-Key (Network-Sync) und/oder Design-Zugangsdaten
   (Maps-Sync).
2. Auf der Console-Detailseite: **"Network synchronisieren"**-Button →
   holt Geräte über die offizielle API, legt sie als `UnifiDevice` an.
3. **"Design synchronisieren"**-Button → holt Karten+Wände über die
   inoffizielle v2-API. **Vor dem ersten Lauf unbedingt `design/mapping.py`
   und den Docstring in `base/client.py` lesen** — die Struktur der
   Antwort ist nicht verifiziert, das kann beim ersten Versuch fehlschlagen
   oder falsche Werte liefern.
4. Unter **Floorplan Maps** pro Karte **"Push zu netbox_floorplan"** —
   erzeugt ein echtes `Floorplan`+`FloorplanImage`-Objekt. Setzt voraus,
   dass `netbox_floorplan` installiert ist.

## Bekannte Lücken (bewusst, für Phase 1)

- Keine Gerätetyp-Zuordnung zu `dcim.Device` — `UnifiDevice` ist ein
  eigenständiges Spiegel-Modell. Beförderung zu einem echten NetBox-Gerät
  ist vorbereitet (`netbox_device`-Feld), aber noch kein automatisierter
  Schritt.
- Kein periodischer Hintergrund-Job — nur manueller Sync per Button. Für
  einen Scheduled Job müsste ein NetBox-`Job`/RQ-Wrapper um `sync_network`/
  `sync_design` gelegt werden.
- `design/mapping.py`s Koordinaten-Transformation ist ungetestet — siehe
  TODO-Kommentar dort.
- Kein eigenes CSS-Theme — nutzt aktuell NetBox' Standard-Look.
- Filtersets (`filtersets.py` + `*FilterForm` in `forms.py`) sind vorhanden,
  aber noch NIE gegen eine laufende NetBox-4.6.10-Instanz getestet — die
  verwendeten Imports (`utilities.forms.rendering.FieldSet`,
  `utilities.forms.choices.BOOLEAN_WITH_BLANK_CHOICES`) basieren auf der
  dokumentierten Plugin-API, nicht auf lokal verifiziertem Quellcode.

## Sicherheitshinweis

Zugangsdaten werden mit Fernet verschlüsselt, Schlüssel aus NetBox'
`SECRET_KEY` abgeleitet (`base/crypto.py`). Das schützt vor Klartext in
DB-Dumps, ist aber kein Ersatz für ein echtes Secrets-Management. Für den
Design-Sync unbedingt einen dedizierten Read-only-UniFi-Account anlegen,
nicht deinen Admin-Login.
