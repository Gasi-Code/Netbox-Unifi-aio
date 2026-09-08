from netbox.api.viewsets import NetBoxModelViewSet

from ..base.models import UCKConsole, SyncLog
from ..network.models import UnifiDevice
from ..design.models import UnifiFloorplanMap
from .serializers import (
    UCKConsoleSerializer, SyncLogSerializer, UnifiDeviceSerializer, UnifiFloorplanMapSerializer,
)


class UCKConsoleViewSet(NetBoxModelViewSet):
    queryset = UCKConsole.objects.all()
    serializer_class = UCKConsoleSerializer


class SyncLogViewSet(NetBoxModelViewSet):
    queryset = SyncLog.objects.all()
    serializer_class = SyncLogSerializer


class UnifiDeviceViewSet(NetBoxModelViewSet):
    queryset = UnifiDevice.objects.all()
    serializer_class = UnifiDeviceSerializer


class UnifiFloorplanMapViewSet(NetBoxModelViewSet):
    queryset = UnifiFloorplanMap.objects.all()
    serializer_class = UnifiFloorplanMapSerializer
