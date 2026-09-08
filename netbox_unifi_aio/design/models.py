from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel


class UnifiFloorplanMap(NetBoxModel):
    """
    Raw data of a UniFi Design map (image + wall/device geometry).

    Deliberately kept separate from netbox_floorplan.Floorplan: this way
    the plugin still works even if netbox_floorplan is not (yet) installed,
    and the "push" step to netbox_floorplan can be triggered manually
    instead of happening automatically on every sync - important because
    the underlying UniFi API is unofficial and the geometry structure has
    not yet been verified against real data (see client.py docstring).
    """
    console = models.ForeignKey(
        to='netbox_unifi_aio.UCKConsole',
        on_delete=models.CASCADE,
        related_name='floorplan_maps',
    )
    unifi_map_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100, blank=True, default='')

    image = models.ImageField(
        upload_to='netbox_unifi_aio/design/',
        null=True, blank=True,
        help_text='Heruntergeladenes Kartenbild aus UniFi Design.',
    )
    width_px = models.PositiveIntegerField(null=True, blank=True)
    height_px = models.PositiveIntegerField(null=True, blank=True)

    raw_walls = models.JSONField(
        default=list, blank=True,
        help_text='Rohe Wand-Geometrie aus /v2/api/site/{site}/walls.',
    )
    raw_devices = models.JSONField(
        default=list, blank=True,
        help_text='Rohe Geraete-Positionen aus der Karten-Antwort.',
    )

    # Set after the manual "push" - prevents creating duplicates.
    floorplan_object_id = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='PK des erzeugten netbox_floorplan.Floorplan-Objekts, falls schon gepusht.',
    )

    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'netbox_unifi_aio'
        ordering = ('name',)
        unique_together = [('console', 'unifi_map_id')]
        verbose_name = 'UniFi Floorplan Map'
        verbose_name_plural = 'UniFi Floorplan Maps'

    def __str__(self):
        return self.name or self.unifi_map_id

    def get_absolute_url(self):
        return reverse('plugins:netbox_unifi_aio:unififloorplanmap', args=[self.pk])

    @property
    def is_pushed(self) -> bool:
        return self.floorplan_object_id is not None
