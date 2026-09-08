from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from netbox.views import generic

from . import forms, tables
from .filtersets import (
    UCKConsoleFilterSet, UnifiDeviceFilterSet, UnifiFloorplanMapFilterSet, SyncLogFilterSet,
)
from .base.models import UCKConsole, SyncLog
from .network.models import UnifiDevice
from .network.sync import sync_network
from .design.models import UnifiFloorplanMap
from .design.sync import sync_design, push_to_floorplan


# --- UCKConsole: Standard-CRUD ---

class UCKConsoleListView(generic.ObjectListView):
    queryset = UCKConsole.objects.all()
    table = tables.UCKConsoleTable
    filterset = UCKConsoleFilterSet
    filterset_form = forms.UCKConsoleFilterForm


class UCKConsoleView(generic.ObjectView):
    queryset = UCKConsole.objects.all()

    def get_extra_context(self, request, instance):
        return {
            'devices': instance.devices.all()[:25],
            'floorplan_maps': instance.floorplan_maps.all(),
            'recent_logs': instance.sync_logs.all()[:10],
        }


class UCKConsoleEditView(generic.ObjectEditView):
    queryset = UCKConsole.objects.all()
    form = forms.UCKConsoleForm


class UCKConsoleDeleteView(generic.ObjectDeleteView):
    queryset = UCKConsole.objects.all()


# --- UnifiDevice: nur Ansicht, kein manuelles Anlegen (kommt aus dem Sync) ---

class UnifiDeviceListView(generic.ObjectListView):
    queryset = UnifiDevice.objects.all()
    table = tables.UnifiDeviceTable
    filterset = UnifiDeviceFilterSet
    filterset_form = forms.UnifiDeviceFilterForm


class UnifiDeviceView(generic.ObjectView):
    queryset = UnifiDevice.objects.all()


# --- UnifiFloorplanMap ---

class UnifiFloorplanMapListView(generic.ObjectListView):
    queryset = UnifiFloorplanMap.objects.all()
    table = tables.UnifiFloorplanMapTable
    filterset = UnifiFloorplanMapFilterSet
    filterset_form = forms.UnifiFloorplanMapFilterForm


class UnifiFloorplanMapView(generic.ObjectView):
    queryset = UnifiFloorplanMap.objects.all()


# --- SyncLog ---

class SyncLogListView(generic.ObjectListView):
    queryset = SyncLog.objects.all()
    table = tables.SyncLogTable
    filterset = SyncLogFilterSet
    filterset_form = forms.SyncLogFilterForm


class SyncLogView(generic.ObjectView):
    queryset = SyncLog.objects.all()


# --- Action-Views: kein Formular, nur POST -> Sync anstossen -> zurueck ---

class RunNetworkSyncView(View):
    def post(self, request, pk):
        console = get_object_or_404(UCKConsole, pk=pk)
        log = sync_network(console.pk)
        if log.status == SyncLog.STATUS_FAILED:
            messages.error(request, f'Network-Sync fehlgeschlagen: {log.summary}')
        else:
            messages.success(request, f'Network-Sync abgeschlossen: {log.summary}')
        return redirect(console.get_absolute_url())


class RunDesignSyncView(View):
    def post(self, request, pk):
        console = get_object_or_404(UCKConsole, pk=pk)
        log = sync_design(console.pk)
        if log.status == SyncLog.STATUS_FAILED:
            messages.error(request, f'Design-Sync fehlgeschlagen: {log.summary}')
        else:
            messages.success(request, f'Design-Sync abgeschlossen: {log.summary}')
        return redirect(console.get_absolute_url())


class PushToFloorplanView(View):
    def post(self, request, pk):
        map_obj = get_object_or_404(UnifiFloorplanMap, pk=pk)
        try:
            result = push_to_floorplan(map_obj, site=map_obj.console.site)
            messages.success(request, result)
        except RuntimeError as exc:
            messages.error(request, str(exc))
        return redirect(map_obj.get_absolute_url())
