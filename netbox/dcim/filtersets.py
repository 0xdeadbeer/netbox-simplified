import django_filters
from django.contrib.auth.models import User

from extras.filtersets import LocalConfigContextFilterSet
from netbox.filtersets import (
    BaseFilterSet, ChangeLoggedModelFilterSet, OrganizationalModelFilterSet, NetBoxModelFilterSet,
)
from tenancy.filtersets import TenancyFilterSet, ContactModelFilterSet
from tenancy.models import *
from utilities.choices import ColorChoices
from utilities.filters import (
    ContentTypeFilter, MultiValueCharFilter, MultiValueMACAddressFilter, MultiValueNumberFilter, MultiValueWWNFilter,
    TreeNodeMultipleChoiceFilter,
)
from virtualization.models import Cluster
from .choices import *
from .constants import *
from .models import *

__all__ = (
    'DeviceFilterSet',
)


class DeviceFilterSet(NetBoxModelFilterSet, TenancyFilterSet, ContactModelFilterSet, LocalConfigContextFilterSet):
    class Meta:
        fields = ['id', 'name', 'asset_tag', 'face', 'position', 'airflow', 'vc_position', 'vc_priority']

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(serial__icontains=value.strip()) |
            Q(inventoryitems__serial__icontains=value.strip()) |
            Q(asset_tag__icontains=value.strip()) |
            Q(comments__icontains=value)
        ).distinct()

    def _has_primary_ip(self, queryset, name, value):
        params = Q(primary_ip4__isnull=False) | Q(primary_ip6__isnull=False)
        if value:
            return queryset.filter(params)
        return queryset.exclude(params)

    def _virtual_chassis_member(self, queryset, name, value):
        return queryset.exclude(virtual_chassis__isnull=value)

    def _console_ports(self, queryset, name, value):
        return queryset.exclude(consoleports__isnull=value)

    def _console_server_ports(self, queryset, name, value):
        return queryset.exclude(consoleserverports__isnull=value)

    def _power_ports(self, queryset, name, value):
        return queryset.exclude(powerports__isnull=value)

    def _power_outlets(self, queryset, name, value):
        return queryset.exclude(poweroutlets__isnull=value)

    def _interfaces(self, queryset, name, value):
        return queryset.exclude(interfaces__isnull=value)

    def _pass_through_ports(self, queryset, name, value):
        return queryset.exclude(
            frontports__isnull=value,
            rearports__isnull=value
        )

    def _module_bays(self, queryset, name, value):
        return queryset.exclude(modulebays__isnull=value)

    def _device_bays(self, queryset, name, value):
        return queryset.exclude(devicebays__isnull=value)
