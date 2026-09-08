from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel

from .crypto import encrypt_value, decrypt_value


class UCKConsole(NetBoxModel):
    """
    A UniFi controller (Dream Machine, Cloud Key, or Network Application
    container). All app-specific sync jobs (network/, design/, later
    protect/, access/) hang off this model.
    """
    name = models.CharField(max_length=100, unique=True)
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='unifi_consoles',
        help_text='Welchem NetBox-Standort dieser Controller zugeordnet ist.',
    )
    base_url = models.CharField(
        max_length=200,
        help_text='z.B. https://192.168.1.1 (ohne Pfad, ohne trailing slash)',
    )
    verify_tls = models.BooleanField(
        default=False,
        help_text='TLS-Zertifikat pruefen. Bei selbstsigniertem UCK-Zertifikat i.d.R. aus.',
    )

    # --- Integration API v1 (official, API key) - for the network/ module ---
    integration_api_key_encrypted = models.CharField(
        max_length=500, blank=True, default='',
        help_text='X-API-Key fuer /integration/v1/*. Wird verschluesselt gespeichert.',
    )
    unifi_site_id = models.CharField(
        max_length=100, blank=True, default='',
        help_text='UniFi-interne Site-ID (nicht der NetBox-Site-Name). Leer = "default".',
    )

    # --- Session login (unofficial, v2 API) - for the design/ module ---
    design_username_encrypted = models.CharField(max_length=500, blank=True, default='')
    design_password_encrypted = models.CharField(max_length=500, blank=True, default='')

    comments = models.TextField(blank=True)

    class Meta:
        app_label = 'netbox_unifi_aio'
        ordering = ('name',)
        verbose_name = 'UCK Console'
        verbose_name_plural = 'UCK Consoles'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_unifi_aio:uckconsole', args=[self.pk])

    # --- Encrypted fields: convenient property access instead of ---
    # --- calling encrypt_value()/decrypt_value() manually everywhere. ---

    @property
    def integration_api_key(self) -> str:
        return decrypt_value(self.integration_api_key_encrypted)

    @integration_api_key.setter
    def integration_api_key(self, value: str):
        self.integration_api_key_encrypted = encrypt_value(value)

    @property
    def design_username(self) -> str:
        return decrypt_value(self.design_username_encrypted)

    @design_username.setter
    def design_username(self, value: str):
        self.design_username_encrypted = encrypt_value(value)

    @property
    def design_password(self) -> str:
        return decrypt_value(self.design_password_encrypted)

    @design_password.setter
    def design_password(self, value: str):
        self.design_password_encrypted = encrypt_value(value)

    @property
    def has_integration_credentials(self) -> bool:
        return bool(self.integration_api_key_encrypted)

    @property
    def has_design_credentials(self) -> bool:
        return bool(self.design_username_encrypted and self.design_password_encrypted)


class SyncLog(NetBoxModel):
    """
    Log of every sync run (network/ or design/), so the UI can show when
    the last sync happened and what went wrong - important given the
    inherently fragile v2 API.
    """
    STATUS_SUCCESS = 'success'
    STATUS_PARTIAL = 'partial'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Erfolgreich'),
        (STATUS_PARTIAL, 'Teilweise erfolgreich'),
        (STATUS_FAILED, 'Fehlgeschlagen'),
    ]

    console = models.ForeignKey(
        to=UCKConsole, on_delete=models.CASCADE, related_name='sync_logs',
    )
    module = models.CharField(
        max_length=20,
        help_text='Welches Sub-Modul den Sync ausgefuehrt hat, z.B. "network" oder "design".',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    started = models.DateTimeField()
    finished = models.DateTimeField(null=True, blank=True)
    summary = models.CharField(max_length=500, blank=True, default='')
    detail = models.TextField(
        blank=True, default='',
        help_text='Tracebacks/Rohfehler bei fehlgeschlagenen Syncs.',
    )

    class Meta:
        app_label = 'netbox_unifi_aio'
        ordering = ('-started',)
        verbose_name = 'UniFi Sync-Log'
        verbose_name_plural = 'UniFi Sync-Logs'

    def __str__(self):
        return f'{self.console} / {self.module} @ {self.started:%Y-%m-%d %H:%M}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_unifi_aio:synclog', args=[self.pk])
