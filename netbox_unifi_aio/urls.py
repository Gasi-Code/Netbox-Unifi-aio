from django.urls import path

from . import views

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

    # UnifiDevice
    path('devices/', views.UnifiDeviceListView.as_view(), name='unifidevice_list'),
    path('devices/<int:pk>/', views.UnifiDeviceView.as_view(), name='unifidevice'),

    # UnifiFloorplanMap
    path('floorplan-maps/', views.UnifiFloorplanMapListView.as_view(), name='unififloorplanmap_list'),
    path('floorplan-maps/<int:pk>/', views.UnifiFloorplanMapView.as_view(), name='unififloorplanmap'),
    path('floorplan-maps/<int:pk>/push/', views.PushToFloorplanView.as_view(), name='unififloorplanmap_push'),

    # SyncLog
    path('sync-logs/', views.SyncLogListView.as_view(), name='synclog_list'),
    path('sync-logs/<int:pk>/', views.SyncLogView.as_view(), name='synclog'),
]
