import logging

import requests
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from ..base.client import UnifiDesignClient, UnifiAPIError
from ..base.models import UCKConsole, SyncLog
from .models import UnifiFloorplanMap

logger = logging.getLogger('netbox_unifi_aio.design')


def sync_design(console_id: int) -> SyncLog:
    """
    Fetches maps + walls via the unofficial v2 API and stores them as
    UnifiFloorplanMap. Deliberately does NOT create netbox_floorplan objects
    yet - that only happens in the separate push_to_floorplan() step, so
    the result can be reviewed first.
    """
    console = UCKConsole.objects.get(pk=console_id)
    log = SyncLog.objects.create(
        console=console, module='design', status=SyncLog.STATUS_FAILED,
        started=timezone.now(),
    )

    if not console.has_design_credentials:
        log.summary = 'Keine Design-Zugangsdaten (Benutzername/Passwort) hinterlegt.'
        log.finished = timezone.now()
        log.save()
        return log

    try:
        client = UnifiDesignClient(
            base_url=console.base_url,
            username=console.design_username,
            password=console.design_password,
            verify_tls=console.verify_tls,
        )
        site_id = console.unifi_site_id or 'default'
        maps = client.get_maps(site_id)
        walls = client.get_walls(site_id)
    except ValueError as exc:
        logger.exception('Design-Sync fehlgeschlagen fuer %s (Entschluesselung)', console)
        log.status = SyncLog.STATUS_FAILED
        log.summary = 'Zugangsdaten konnten nicht entschluesselt werden.'
        log.detail = str(exc)
        log.finished = timezone.now()
        log.save()
        return log
    except UnifiAPIError as exc:
        logger.exception('Design-Sync fehlgeschlagen fuer %s', console)
        log.status = SyncLog.STATUS_FAILED
        log.summary = 'API-Fehler - moeglicherweise hat sich die inoffizielle v2-API geaendert.'
        log.detail = str(exc)
        log.finished = timezone.now()
        log.save()
        return log

    created, updated, errors = 0, 0, []

    for remote_map in maps:
        try:
            map_id = remote_map.get('id')
            if not map_id:
                continue

            obj, was_created = UnifiFloorplanMap.objects.update_or_create(
                console=console,
                unifi_map_id=map_id,
                defaults={
                    'name': remote_map.get('name', ''),
                    'width_px': remote_map.get('width'),
                    'height_px': remote_map.get('height'),
                    'raw_devices': remote_map.get('devices', []),
                    'raw_walls': [w for w in walls if w.get('mapId') == map_id],
                },
            )

            image_url = remote_map.get('imageUrl')
            if image_url:
                image_error = _download_map_image(client, obj, image_url)
                if image_error:
                    errors.append(f'{map_id}: Kartenbild-Download fehlgeschlagen ({image_error})')

            created += int(was_created)
            updated += int(not was_created)
        except Exception as exc:
            errors.append(f'{remote_map.get("id", "?")}: {exc}')

    log.finished = timezone.now()
    log.status = SyncLog.STATUS_SUCCESS if not errors else SyncLog.STATUS_PARTIAL
    log.summary = f'{created} neu, {updated} aktualisiert, {len(errors)} Fehler.'
    log.detail = '\n'.join(errors)
    log.save()
    return log


def _download_map_image(client: UnifiDesignClient, obj: UnifiFloorplanMap, image_url: str) -> str | None:
    """Downloads the map image and attaches it to the UnifiFloorplanMap object.

    Returns an error message on failure (None on success) so the caller can
    record it instead of silently reporting a successful sync.
    """
    try:
        resp = client.session.get(image_url, timeout=client.timeout, verify=client.verify_tls)
        resp.raise_for_status()
        filename = f'{obj.unifi_map_id}.png'
        obj.image.save(filename, ContentFile(resp.content), save=True)
        return None
    except requests.RequestException as exc:
        logger.warning('Map image download failed for %s: %s', obj, exc)
        return str(exc)


def push_to_floorplan(map_obj: UnifiFloorplanMap, site) -> str:
    """
    Creates a real netbox_floorplan FloorplanImage + Floorplan object from a
    UnifiFloorplanMap. Deliberately imports netbox_floorplan HERE (not at
    module level) so design/ still works without netbox_floorplan installed
    (sync works then, just not the push).

    Returns a short status message.
    """
    try:
        from netbox_floorplan.models import Floorplan, FloorplanImage
    except ImportError:
        raise RuntimeError(
            'netbox_floorplan ist nicht installiert/aktiviert - Push nicht moeglich.'
        )

    if map_obj.is_pushed:
        return f'Bereits gepusht (Floorplan-PK {map_obj.floorplan_object_id}).'

    if not map_obj.image:
        raise RuntimeError('Kein Kartenbild vorhanden - erst sync_design() erneut laufen lassen.')

    with transaction.atomic():
        fp_image = FloorplanImage.objects.create(
            name=f'UniFi Import: {map_obj.name}',
            image=map_obj.image,
        )
        floorplan = Floorplan.objects.create(
            name=map_obj.name or f'UniFi Map {map_obj.unifi_map_id}',
            site=site,
            image=fp_image,
        )

        map_obj.floorplan_object_id = floorplan.pk
        map_obj.save()

    # Writing device positions from raw_devices into floorplan.canvas or
    # similar is deliberately NOT done here - it depends on the final
    # coordinate system (see TODO in mapping.py) and should only be added
    # after verifying the real API response.

    return f'Floorplan "{floorplan.name}" (PK {floorplan.pk}) erstellt.'
