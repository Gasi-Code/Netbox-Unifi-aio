import django_tables2 as tables

from netbox.tables import NetBoxTable, columns

from .base.models import UCKConsole, SyncLog
from .network.models import UnifiDevice
from .design.models import UnifiFloorplanMap


class UCKConsoleTable(NetBoxTable):
    name = tables.Column(linkify=True)
    site = tables.Column(linkify=True)
    has_integration_credentials = columns.BooleanColumn(verbose_name='Network-API')
    has_design_credentials = columns.BooleanColumn(verbose_name='Design-API')

    class Meta(NetBoxTable.Meta):
        model = UCKConsole
        fields = (
            'pk', 'name', 'site', 'base_url', 'has_integration_credentials',
            'has_design_credentials', 'tags',
        )
        default_columns = (
            'name', 'site', 'base_url', 'has_integration_credentials',
            'has_design_credentials',
        )


class UnifiDeviceTable(NetBoxTable):
    name = tables.Column(linkify=True)
    console = tables.Column(linkify=True)
    netbox_device = tables.Column(linkify=True, verbose_name='NetBox-Geraet')
    # No unifidevice_edit/_delete views exist - devices are managed exclusively via sync.
    actions = columns.ActionsColumn(actions=('changelog',))

    class Meta(NetBoxTable.Meta):
        model = UnifiDevice
        fields = (
            'pk', 'name', 'console', 'mac_address', 'model', 'ip_address',
            'state', 'adopted', 'netbox_device', 'last_synced',
        )
        default_columns = (
            'name', 'console', 'mac_address', 'model', 'ip_address', 'state', 'netbox_device',
        )


class UnifiFloorplanMapTable(NetBoxTable):
    name = tables.Column(linkify=True)
    console = tables.Column(linkify=True)
    is_pushed = columns.BooleanColumn(verbose_name='In netbox_floorplan')
    # No unififloorplanmap_edit/_delete views exist - maps are managed exclusively via sync/push.
    actions = columns.ActionsColumn(actions=('changelog',))

    class Meta(NetBoxTable.Meta):
        model = UnifiFloorplanMap
        fields = ('pk', 'name', 'console', 'width_px', 'height_px', 'is_pushed', 'last_synced')
        default_columns = ('name', 'console', 'is_pushed', 'last_synced')


class SyncLogTable(NetBoxTable):
    console = tables.Column(linkify=True)
    status = columns.ChoiceFieldColumn()
    # No synclog_edit/_delete views exist - logs are written exclusively by sync jobs.
    actions = columns.ActionsColumn(actions=('changelog',))

    class Meta(NetBoxTable.Meta):
        model = SyncLog
        fields = ('pk', 'console', 'module', 'status', 'started', 'finished', 'summary')
        default_columns = ('console', 'module', 'status', 'started', 'summary')
