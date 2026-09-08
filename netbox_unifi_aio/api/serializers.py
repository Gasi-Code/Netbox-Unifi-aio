from netbox.api.serializers import NetBoxModelSerializer

from ..base.models import UCKConsole, SyncLog
from ..network.models import UnifiDevice
from ..design.models import UnifiFloorplanMap


class UCKConsoleSerializer(NetBoxModelSerializer):
    class Meta:
        model = UCKConsole
        # integration_api_key_encrypted / design_username_encrypted / design_password_encrypted
        # and their decrypted properties are deliberately excluded - never expose credentials via the API.
        fields = (
            'id', 'url', 'display', 'name', 'site', 'base_url', 'verify_tls', 'unifi_site_id',
            'has_integration_credentials', 'has_design_credentials', 'comments', 'tags', 'custom_fields',
            'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name')


class SyncLogSerializer(NetBoxModelSerializer):
    class Meta:
        model = SyncLog
        fields = (
            'id', 'url', 'display', 'console', 'module', 'status', 'started', 'finished', 'summary', 'detail',
            'tags', 'custom_fields', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'module', 'status')


class UnifiDeviceSerializer(NetBoxModelSerializer):
    class Meta:
        model = UnifiDevice
        fields = (
            'id', 'url', 'display', 'console', 'unifi_id', 'mac_address', 'name', 'model', 'ip_address', 'state',
            'adopted', 'netbox_device', 'raw_data', 'last_synced', 'tags', 'custom_fields', 'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name', 'mac_address')


class UnifiFloorplanMapSerializer(NetBoxModelSerializer):
    class Meta:
        model = UnifiFloorplanMap
        fields = (
            'id', 'url', 'display', 'console', 'unifi_map_id', 'name', 'image', 'width_px', 'height_px',
            'raw_walls', 'raw_devices', 'floorplan_object_id', 'last_synced', 'tags', 'custom_fields',
            'created', 'last_updated',
        )
        brief_fields = ('id', 'url', 'display', 'name')
