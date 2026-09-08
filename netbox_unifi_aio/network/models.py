from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel


class UnifiDevice(NetBoxModel):
    """
    Deliberately a SEPARATE, lightweight model instead of populating
    dcim.Device directly. Reason: dcim.Device requires Manufacturer/
    DeviceType/Role, which would need proper mapping (different models,
    form factors) - that's phase 2. Here in phase 1 we sync the UniFi state
    1:1, and you can later decide (manually or via a management command)
    which UnifiDevice entries get promoted to a real dcim.Device.
    """
    console = models.ForeignKey(
        to='netbox_unifi_aio.UCKConsole',
        on_delete=models.CASCADE,
        related_name='devices',
    )
    unifi_id = models.CharField(max_length=100, help_text='Interne UniFi-Geraete-ID')
    mac_address = models.CharField(max_length=17, db_index=True)
    name = models.CharField(max_length=100, blank=True, default='')
    model = models.CharField(max_length=100, blank=True, default='')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    state = models.CharField(max_length=50, blank=True, default='')
    adopted = models.BooleanField(default=False)

    # Link to a "real" NetBox device, if promoted.
    netbox_device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='unifi_source',
    )

    raw_data = models.JSONField(
        default=dict, blank=True,
        help_text='Vollstaendige API-Antwort fuer dieses Geraet, fuer Debugging/spaetere Felder.',
    )
    last_synced = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'netbox_unifi_aio'
        ordering = ('name', 'mac_address')
        unique_together = [('console', 'unifi_id')]
        verbose_name = 'UniFi Device'
        verbose_name_plural = 'UniFi Devices'

    def __str__(self):
        return self.name or self.mac_address

    def get_absolute_url(self):
        return reverse('plugins:netbox_unifi_aio:unifidevice', args=[self.pk])
