from django.urls import path

from netbox.views.generic import ObjectChangeLogView, ObjectJournalView

from . import views
from .base.models import UCKConsole, SyncLog
from .network.models import UnifiDevice
from .design.models import UnifiFloorplanMap

app_name = 'netbox_unifi_aio'

urlpatterns = [
    # UCKConsole
    path('consoles/', views.UCKConsoleListView.as_view(), name='uckconsole_list'),
    path('consoles/add/', views.UCKConsoleEditView.as_view(), name='uckconsole_add'),
    path('consoles/<int:pk>/', views.UCKConsoleView.as_view(), name='uckconsole'),
    path('consoles/<int:pk>/edit/', views.UCKConsoleEditView.as_view(), name='uckconsole_edit'),
    path('consoles/<int:pk>/delete/', views.UCKConsoleDeleteView.as_view(), name='uckconsole_delete'),
    path('consoles/<int:pk>/sync-network/', views.RunNetworkSyncView.as_view(), name='uckconsole_sync_network'),
    path('consoles/<int:pk>/sync-design/', views.RunDesignSyncView.as_view(), name='uckconsole_sync_design'),
    path('consoles/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='uckconsole_changelog', kwargs={'model': UCKConsole}),
    path('consoles/<int:pk>/journal/', ObjectJournalView.as_view(), name='uckconsole_journal', kwargs={'model': UCKConsole}),

    # UnifiDevice
    path('devices/', views.UnifiDeviceListView.as_view(), name='unifidevice_list'),
    path('devices/<int:pk>/', views.UnifiDeviceView.as_view(), name='unifidevice'),
    path('devices/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='unifidevice_changelog', kwargs={'model': UnifiDevice}),
    path('devices/<int:pk>/journal/', ObjectJournalView.as_view(), name='unifidevice_journal', kwargs={'model': UnifiDevice}),

    # UnifiFloorplanMap
    path('floorplan-maps/', views.UnifiFloorplanMapListView.as_view(), name='unififloorplanmap_list'),
    path('floorplan-maps/<int:pk>/', views.UnifiFloorplanMapView.as_view(), name='unififloorplanmap'),
    path('floorplan-maps/<int:pk>/push/', views.PushToFloorplanView.as_view(), name='unififloorplanmap_push'),
    path('floorplan-maps/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='unififloorplanmap_changelog', kwargs={'model': UnifiFloorplanMap}),
    path('floorplan-maps/<int:pk>/journal/', ObjectJournalView.as_view(), name='unififloorplanmap_journal', kwargs={'model': UnifiFloorplanMap}),

    # SyncLog
    path('sync-logs/', views.SyncLogListView.as_view(), name='synclog_list'),
    path('sync-logs/<int:pk>/', views.SyncLogView.as_view(), name='synclog'),
    path('sync-logs/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='synclog_changelog', kwargs={'model': SyncLog}),
    path('sync-logs/<int:pk>/journal/', ObjectJournalView.as_view(), name='synclog_journal', kwargs={'model': SyncLog}),
]
