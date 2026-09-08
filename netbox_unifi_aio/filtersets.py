import django_filters
from django.db.models import Q

from dcim.models import Site
from netbox.filtersets import NetBoxModelFilterSet

from .base.models import UCKConsole, SyncLog
from .network.models import UnifiDevice
from .design.models import UnifiFloorplanMap


class UCKConsoleFilterSet(NetBoxModelFilterSet):
    site_id = django_filters.ModelMultipleChoiceFilter(
        field_name='site',
        queryset=Site.objects.all(),
        label='Site (ID)',
    )
    has_integration_credentials = django_filters.BooleanFilter(
        method='filter_has_integration_credentials',
        label='Hat Integration-API-Key',
    )
    has_design_credentials = django_filters.BooleanFilter(
        method='filter_has_design_credentials',
        label='Hat Design-Zugangsdaten',
    )

    class Meta:
        model = UCKConsole
        fields = ('id', 'name', 'base_url', 'unifi_site_id', 'verify_tls')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(base_url__icontains=value) | Q(comments__icontains=value)
        )

    def filter_has_integration_credentials(self, queryset, name, value):
        if value is None:
            return queryset
        condition = Q(integration_api_key_encrypted='')
        return queryset.exclude(condition) if value else queryset.filter(condition)

    def filter_has_design_credentials(self, queryset, name, value):
        if value is None:
            return queryset
        condition = Q(design_username_encrypted='') | Q(design_password_encrypted='')
        return queryset.exclude(condition) if value else queryset.filter(condition)


class UnifiDeviceFilterSet(NetBoxModelFilterSet):
    console_id = django_filters.ModelMultipleChoiceFilter(
        queryset=UCKConsole.objects.all(),
        label='UCK Console (ID)',
    )
    adopted = django_filters.BooleanFilter()

    class Meta:
        model = UnifiDevice
        fields = ('id', 'name', 'mac_address', 'model', 'ip_address', 'state', 'unifi_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(mac_address__icontains=value)
            | Q(model__icontains=value)
            | Q(ip_address__icontains=value)
            | Q(unifi_id__icontains=value)
        )


class UnifiFloorplanMapFilterSet(NetBoxModelFilterSet):
    console_id = django_filters.ModelMultipleChoiceFilter(
        queryset=UCKConsole.objects.all(),
        label='UCK Console (ID)',
    )
    is_pushed = django_filters.BooleanFilter(
        method='filter_is_pushed',
        label='Bereits gepusht',
    )

    class Meta:
        model = UnifiFloorplanMap
        fields = ('id', 'name', 'unifi_map_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(unifi_map_id__icontains=value))

    def filter_is_pushed(self, queryset, name, value):
        if value is None:
            return queryset
        condition = Q(floorplan_object_id__isnull=False)
        return queryset.filter(condition) if value else queryset.exclude(condition)


class SyncLogFilterSet(NetBoxModelFilterSet):
    console_id = django_filters.ModelMultipleChoiceFilter(
        queryset=UCKConsole.objects.all(),
        label='UCK Console (ID)',
    )
    module = django_filters.MultipleChoiceFilter(
        choices=(('network', 'network'), ('design', 'design')),
    )
    status = django_filters.MultipleChoiceFilter(choices=SyncLog.STATUS_CHOICES)
    started_after = django_filters.DateTimeFilter(field_name='started', lookup_expr='gte')
    started_before = django_filters.DateTimeFilter(field_name='started', lookup_expr='lte')

    class Meta:
        model = SyncLog
        fields = ('id', 'module', 'status')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(summary__icontains=value) | Q(detail__icontains=value))
