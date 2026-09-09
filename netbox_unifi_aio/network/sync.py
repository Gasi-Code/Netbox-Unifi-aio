import logging
from django.db import transaction
from django.utils import timezone

from ..base.client import UnifiIntegrationClient, UnifiAPIError
from ..base.models import UCKConsole, SyncLog
from .models import UnifiDevice

logger = logging.getLogger('netbox_unifi_aio.network')


def sync_network(console_id: int) -> SyncLog:
    """
    Fetches all devices for a UCKConsole via the official Integration API
    and reconciles them with the local UnifiDevice entries (upsert).
    Returns the created SyncLog object so the calling code/view can display
    the result.
    """
    console = UCKConsole.objects.get(pk=console_id)
    log = SyncLog.objects.create(
        console=console, module='network', status=SyncLog.STATUS_FAILED,
        started=timezone.now(),
    )

    if not console.has_integration_credentials:
        log.summary = 'Kein Integration-API-Key hinterlegt.'
        log.finished = timezone.now()
        log.save()
        return log

    try:
        client = UnifiIntegrationClient(
            base_url=console.base_url,
            api_key=console.integration_api_key,
            verify_tls=console.verify_tls,
        )
        site_id = console.unifi_site_id
        if not site_id:
            # The official Integration API v1 expects the site's UUID, not the
            # 'default' name used by the legacy/internal API - resolve it via
            # /sites when the console has no explicit unifi_site_id configured.
            sites = client.list_sites()
            if not sites:
                raise UnifiAPIError('Keine Sites ueber die Integration-API gefunden.')
            site_id = sites[0]['id']
        remote_devices = client.list_devices(site_id)
    except ValueError as exc:
        logger.exception('Network-Sync fehlgeschlagen fuer %s (Entschluesselung)', console)
        log.status = SyncLog.STATUS_FAILED
        log.summary = 'Zugangsdaten konnten nicht entschluesselt werden.'
        log.detail = str(exc)
        log.finished = timezone.now()
        log.save()
        return log
    except UnifiAPIError as exc:
        logger.exception('Network-Sync fehlgeschlagen fuer %s', console)
        log.status = SyncLog.STATUS_FAILED
        log.summary = 'API-Fehler beim Abruf der Geraeteliste.'
        log.detail = str(exc)
        log.finished = timezone.now()
        log.save()
        return log

    created, updated, errors = 0, 0, []

    # Outer atomic() makes the whole batch commit as one consistent snapshot
    # (a process crash mid-loop rolls back everything instead of leaving a
    # half-updated set of devices). Each device gets its own inner atomic()
    # savepoint so one broken record doesn't poison the outer transaction on
    # backends (Postgres) that abort the whole transaction after a DB error.
    with transaction.atomic():
        for remote in remote_devices:
            try:
                unifi_id = remote.get('id') or remote.get('_id')
                if not unifi_id:
                    continue
                with transaction.atomic():
                    obj, was_created = UnifiDevice.objects.update_or_create(
                        console=console,
                        unifi_id=unifi_id,
                        defaults={
                            'mac_address': remote.get('macAddress', remote.get('mac', '')),
                            'name': remote.get('name', ''),
                            'model': remote.get('model', ''),
                            'ip_address': remote.get('ipAddress') or None,
                            'state': remote.get('state', ''),
                            'adopted': remote.get('adopted', False),
                            'raw_data': remote,
                        },
                    )
                created += int(was_created)
                updated += int(not was_created)
            except Exception as exc:  # deliberately broad: ONE broken record must not
                # abort the whole sync - it gets logged and skipped instead.
                errors.append(f'{remote.get("id", "?")}: {exc}')

    log.finished = timezone.now()
    log.status = SyncLog.STATUS_SUCCESS if not errors else SyncLog.STATUS_PARTIAL
    log.summary = f'{created} neu, {updated} aktualisiert, {len(errors)} Fehler.'
    log.detail = '\n'.join(errors)
    log.save()
    return log
