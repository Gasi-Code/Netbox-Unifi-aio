from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.register('consoles', views.UCKConsoleViewSet)
router.register('sync-logs', views.SyncLogViewSet)
router.register('devices', views.UnifiDeviceViewSet)
router.register('floorplan-maps', views.UnifiFloorplanMapViewSet)

urlpatterns = router.urls
