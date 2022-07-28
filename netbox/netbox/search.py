import dcim.filtersets
import dcim.tables
import tenancy.filtersets
import tenancy.tables
import virtualization.filtersets
import virtualization.tables
from tenancy.models import Contact, Tenant, ContactAssignment
from utilities.utils import count_related
from virtualization.models import Cluster, VirtualMachine

DCIM_TYPES = {
}

TENANCY_TYPES = {
    'tenant': {
        'queryset': Tenant.objects.prefetch_related('group'),
        'filterset': tenancy.filtersets.TenantFilterSet,
        'table': tenancy.tables.TenantTable,
        'url': 'tenancy:tenant_list',
    },
    'contact': {
        'queryset': Contact.objects.prefetch_related('group', 'assignments').annotate(
            assignment_count=count_related(ContactAssignment, 'contact')),
        'filterset': tenancy.filtersets.ContactFilterSet,
        'table': tenancy.tables.ContactTable,
        'url': 'tenancy:contact_list',
    },
}

VIRTUALIZATION_TYPES = {
    'virtualmachine': {
        'queryset': VirtualMachine.objects.prefetch_related(
            'cluster', 'tenant', 'tenant__group', 'platform', 'primary_ip4', 'primary_ip6',
        ),
        'filterset': virtualization.filtersets.VirtualMachineFilterSet,
        'table': virtualization.tables.VirtualMachineTable,
        'url': 'virtualization:virtualmachine_list',
    },
}

SEARCH_TYPE_HIERARCHY = {
    'DCIM': DCIM_TYPES,
    'Tenancy': TENANCY_TYPES,
    'Virtualization': VIRTUALIZATION_TYPES,
}


def build_search_types():
    result = dict()

    for app_types in SEARCH_TYPE_HIERARCHY.values():
        for name, items in app_types.items():
            result[name] = items

    return result


SEARCH_TYPES = build_search_types()
