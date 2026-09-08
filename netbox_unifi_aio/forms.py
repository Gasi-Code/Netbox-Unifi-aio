from django import forms

from dcim.models import Site
from netbox.forms import NetBoxModelForm, NetBoxModelFilterSetForm
from utilities.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.fields import CommentField, DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from .base.models import UCKConsole, SyncLog
from .network.models import UnifiDevice
from .design.models import UnifiFloorplanMap


class UCKConsoleForm(NetBoxModelForm):
    """
    Zeigt die verschluesselten Felder als normale Passwort-/Text-Eingaben an.
    Die eigentliche Ver-/Entschluesselung passiert transparent ueber die
    Property-Setter auf dem Modell (siehe base/models.py) - hier im Formular
    muss dafuer nichts Besonderes gemacht werden, ausser save() zu ueberschreiben.
    """
    integration_api_key = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=True),
        help_text='X-API-Key aus UniFi Controller -> Einstellungen -> Integrationen.',
    )
    design_username = forms.CharField(
        required=False,
        help_text='Nur fuer den Design/Maps-Import (inoffizielle API). Read-only-Account empfohlen.',
    )
    design_password = forms.CharField(
        required=False, widget=forms.PasswordInput(render_value=True),
    )
    comments = CommentField()

    class Meta:
        model = UCKConsole
        fields = [
            'name', 'site', 'base_url', 'verify_tls', 'unifi_site_id',
            'integration_api_key', 'design_username', 'design_password',
            'comments', 'tags',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Beim Bearbeiten NICHT den entschluesselten Klartext ins Feld
            # vorbefuellen (der wuerde sonst im HTML landen) - Platzhalter
            # signalisiert stattdessen "ist bereits gesetzt".
            if self.instance.has_integration_credentials:
                self.fields['integration_api_key'].widget.attrs['placeholder'] = '•••••••• (gesetzt, zum Aendern ueberschreiben)'
            if self.instance.has_design_credentials:
                self.fields['design_username'].initial = self.instance.design_username
                self.fields['design_password'].widget.attrs['placeholder'] = '•••••••• (gesetzt, zum Aendern ueberschreiben)'

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Nur ueberschreiben, wenn tatsaechlich etwas eingegeben wurde -
        # leeres Feld beim Bearbeiten soll bestehende Credentials nicht loeschen.
        if self.cleaned_data.get('integration_api_key'):
            obj.integration_api_key = self.cleaned_data['integration_api_key']
        if self.cleaned_data.get('design_username'):
            obj.design_username = self.cleaned_data['design_username']
        if self.cleaned_data.get('design_password'):
            obj.design_password = self.cleaned_data['design_password']
        if commit:
            obj.save()
        return obj


class UCKConsoleFilterForm(NetBoxModelFilterSetForm):
    model = UCKConsole
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('site_id', 'has_integration_credentials', 'has_design_credentials', name='UniFi AIO'),
    )
    tag = TagFilterField(UCKConsole)
    site_id = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(), required=False, label='Site',
    )
    has_integration_credentials = forms.NullBooleanField(
        required=False, label='Hat Integration-API-Key',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )
    has_design_credentials = forms.NullBooleanField(
        required=False, label='Hat Design-Zugangsdaten',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )


class UnifiDeviceFilterForm(NetBoxModelFilterSetForm):
    model = UnifiDevice
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('console_id', 'state', 'adopted', name='UniFi'),
    )
    tag = TagFilterField(UnifiDevice)
    console_id = DynamicModelMultipleChoiceField(
        queryset=UCKConsole.objects.all(), required=False, label='UCK Console',
    )
    state = forms.CharField(required=False)
    adopted = forms.NullBooleanField(
        required=False, widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )


class UnifiFloorplanMapFilterForm(NetBoxModelFilterSetForm):
    model = UnifiFloorplanMap
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('console_id', 'is_pushed', name='UniFi Design'),
    )
    tag = TagFilterField(UnifiFloorplanMap)
    console_id = DynamicModelMultipleChoiceField(
        queryset=UCKConsole.objects.all(), required=False, label='UCK Console',
    )
    is_pushed = forms.NullBooleanField(
        required=False, label='Bereits gepusht',
        widget=forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
    )


class SyncLogFilterForm(NetBoxModelFilterSetForm):
    model = SyncLog
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet('console_id', 'module', 'status', 'started_after', 'started_before', name='Sync'),
    )
    tag = TagFilterField(SyncLog)
    console_id = DynamicModelMultipleChoiceField(
        queryset=UCKConsole.objects.all(), required=False, label='UCK Console',
    )
    module = forms.MultipleChoiceField(
        choices=(('network', 'network'), ('design', 'design')), required=False,
    )
    status = forms.MultipleChoiceField(choices=SyncLog.STATUS_CHOICES, required=False)
    started_after = forms.DateTimeField(required=False, label='Gestartet nach')
    started_before = forms.DateTimeField(required=False, label='Gestartet vor')
