import django_tables2 as tables
from django.utils.safestring import mark_safe
from django_tables2.utils import Accessor

from ipam.models import *
from netbox.tables import NetBoxTable, columns
from tenancy.tables import TenancyColumnsMixin, TenantColumn

__all__ = (
    'AggregateTable',
    'ASNTable',
    'AssignedIPAddressesTable',
    'IPAddressAssignTable',
    'IPAddressTable',
    'IPRangeTable',
    'PrefixTable',
    'RIRTable',
    'RoleTable',
)

AVAILABLE_LABEL = mark_safe('<span class="badge bg-success">Available</span>')

PREFIX_LINK = """
{% load helpers %}
{% if record.depth %}
    <div class="record-depth">
        {% for i in record.depth|as_range %}
            <span>•</span>
        {% endfor %}
    </div>
{% endif %}
<a href="{% if record.pk %}{% url 'ipam:prefix' pk=record.pk %}{% else %}{% url 'ipam:prefix_add' %}?prefix={{ record }}{% if object.vrf %}&vrf={{ object.vrf.pk }}{% endif %}{% if object.site %}&site={{ object.site.pk }}{% endif %}{% if object.tenant %}&tenant_group={{ object.tenant.group.pk }}&tenant={{ object.tenant.pk }}{% endif %}{% endif %}">{{ record.prefix }}</a>
"""

PREFIXFLAT_LINK = """
{% load helpers %}
{% if record.pk %}
    <a href="{% url 'ipam:prefix' pk=record.pk %}">{{ record.prefix }}</a>
{% else %}
    {{ record.prefix }}
{% endif %}
"""

IPADDRESS_LINK = """
{% if record.pk %}
    <a href="{{ record.get_absolute_url }}">{{ record.address }}</a>
{% elif perms.ipam.add_ipaddress %}
    <a href="{% url 'ipam:ipaddress_add' %}?address={{ record.1 }}{% if object.vrf %}&vrf={{ object.vrf.pk }}{% endif %}{% if object.tenant %}&tenant={{ object.tenant.pk }}{% endif %}" class="btn btn-sm btn-success">{% if record.0 <= 65536 %}{{ record.0 }}{% else %}Many{% endif %} IP{{ record.0|pluralize }} available</a>
{% else %}
    {% if record.0 <= 65536 %}{{ record.0 }}{% else %}Many{% endif %} IP{{ record.0|pluralize }} available
{% endif %}
"""

IPADDRESS_ASSIGN_LINK = """
<a href="{% url 'ipam:ipaddress_edit' pk=record.pk %}?{% if request.GET.interface %}interface={{ request.GET.interface }}{% elif request.GET.vminterface %}vminterface={{ request.GET.vminterface }}{% endif %}&return_url={{ request.GET.return_url }}">{{ record }}</a>
"""

VRF_LINK = """
{% if record.vrf %}
    <a href="{{ record.vrf.get_absolute_url }}">{{ record.vrf }}</a>
{% elif object.vrf %}
    <a href="{{ object.vrf.get_absolute_url }}">{{ object.vrf }}</a>
{% else %}
    Global
{% endif %}
"""


#
# RIRs
#

class RIRTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    is_private = columns.BooleanColumn(
        verbose_name='Private'
    )
    aggregate_count = columns.LinkedCountColumn(
        viewname='ipam:aggregate_list',
        url_params={'rir_id': 'pk'},
        verbose_name='Aggregates'
    )
    tags = columns.TagColumn(
        url_name='ipam:rir_list'
    )

    class Meta(NetBoxTable.Meta):
        model = RIR
        fields = (
            'pk', 'id', 'name', 'slug', 'is_private', 'aggregate_count', 'description', 'tags', 'created',
            'last_updated', 'actions',
        )
        default_columns = ('pk', 'name', 'is_private', 'aggregate_count', 'description')


#
# ASNs
#

class ASNTable(TenancyColumnsMixin, NetBoxTable):
    asn = tables.Column(
        linkify=True
    )
    asn_asdot = tables.Column(
        accessor=tables.A('asn_asdot'),
        linkify=True,
        verbose_name='ASDOT'
    )
    site_count = columns.LinkedCountColumn(
        viewname='dcim:site_list',
        url_params={'asn_id': 'pk'},
        verbose_name='Site Count'
    )
    provider_count = columns.LinkedCountColumn(
        viewname='circuits:provider_list',
        url_params={'asn_id': 'pk'},
        verbose_name='Provider Count'
    )
    sites = columns.ManyToManyColumn(
        linkify_item=True,
        verbose_name='Sites'
    )
    tags = columns.TagColumn(
        url_name='ipam:asn_list'
    )

    class Meta(NetBoxTable.Meta):
        model = ASN
        fields = (
            'pk', 'asn', 'asn_asdot', 'rir', 'site_count', 'provider_count', 'tenant', 'tenant_group', 'description', 'sites', 'tags',
            'created', 'last_updated', 'actions',
        )
        default_columns = ('pk', 'asn', 'rir', 'site_count', 'provider_count', 'sites', 'description', 'tenant')


#
# Aggregates
#

class AggregateTable(TenancyColumnsMixin, NetBoxTable):
    prefix = tables.Column(
        linkify=True,
        verbose_name='Aggregate'
    )
    date_added = tables.DateColumn(
        format="Y-m-d",
        verbose_name='Added'
    )
    child_count = tables.Column(
        verbose_name='Prefixes'
    )
    utilization = columns.UtilizationColumn(
        accessor='get_utilization',
        orderable=False
    )
    tags = columns.TagColumn(
        url_name='ipam:aggregate_list'
    )

    class Meta(NetBoxTable.Meta):
        model = Aggregate
        fields = (
            'pk', 'id', 'prefix', 'rir', 'tenant', 'tenant_group', 'child_count', 'utilization', 'date_added', 'description', 'tags',
            'created', 'last_updated',
        )
        default_columns = ('pk', 'prefix', 'rir', 'tenant', 'child_count', 'utilization', 'date_added', 'description')


#
# Roles
#

class RoleTable(NetBoxTable):
    name = tables.Column(
        linkify=True
    )
    prefix_count = columns.LinkedCountColumn(
        viewname='ipam:prefix_list',
        url_params={'role_id': 'pk'},
        verbose_name='Prefixes'
    )
    iprange_count = columns.LinkedCountColumn(
        viewname='ipam:iprange_list',
        url_params={'role_id': 'pk'},
        verbose_name='IP Ranges'
    )
    vlan_count = columns.LinkedCountColumn(
        viewname='ipam:vlan_list',
        url_params={'role_id': 'pk'},
        verbose_name='VLANs'
    )
    tags = columns.TagColumn(
        url_name='ipam:role_list'
    )

    class Meta(NetBoxTable.Meta):
        model = Role
        fields = (
            'pk', 'id', 'name', 'slug', 'prefix_count', 'iprange_count', 'vlan_count', 'description', 'weight', 'tags',
            'created', 'last_updated', 'actions',
        )
        default_columns = ('pk', 'name', 'prefix_count', 'iprange_count', 'vlan_count', 'description')


#
# Prefixes
#

class PrefixUtilizationColumn(columns.UtilizationColumn):
    """
    Extend UtilizationColumn to allow disabling the warning & danger thresholds for prefixes
    marked as fully utilized.
    """
    template_code = """
    {% load helpers %}
    {% if record.pk and record.mark_utilized %}
      {% utilization_graph value warning_threshold=0 danger_threshold=0 %}
    {% elif record.pk %}
      {% utilization_graph value %}
    {% endif %}
    """


class PrefixTable(TenancyColumnsMixin, NetBoxTable):
    prefix = columns.TemplateColumn(
        template_code=PREFIX_LINK,
        export_raw=True,
        attrs={'td': {'class': 'text-nowrap'}}
    )
    prefix_flat = tables.TemplateColumn(
        template_code=PREFIXFLAT_LINK,
        attrs={'td': {'class': 'text-nowrap'}},
        verbose_name='Prefix (Flat)',
    )
    depth = tables.Column(
        accessor=Accessor('_depth'),
        verbose_name='Depth'
    )
    children = columns.LinkedCountColumn(
        accessor=Accessor('_children'),
        viewname='ipam:prefix_list',
        url_params={
            'vrf_id': 'vrf_id',
            'within': 'prefix',
        },
        verbose_name='Children'
    )
    status = columns.ChoiceFieldColumn(
        default=AVAILABLE_LABEL
    )
    vrf = tables.TemplateColumn(
        template_code=VRF_LINK,
        verbose_name='VRF'
    )
    site = tables.Column(
        linkify=True
    )
    vlan_group = tables.Column(
        accessor='vlan__group',
        linkify=True,
        verbose_name='VLAN Group'
    )
    vlan = tables.Column(
        linkify=True,
        verbose_name='VLAN'
    )
    role = tables.Column(
        linkify=True
    )
    is_pool = columns.BooleanColumn(
        verbose_name='Pool'
    )
    mark_utilized = columns.BooleanColumn(
        verbose_name='Marked Utilized'
    )
    utilization = PrefixUtilizationColumn(
        accessor='get_utilization',
        orderable=False
    )
    tags = columns.TagColumn(
        url_name='ipam:prefix_list'
    )

    class Meta(NetBoxTable.Meta):
        model = Prefix
        fields = (
            'pk', 'id', 'prefix', 'prefix_flat', 'status', 'children', 'vrf', 'utilization', 'tenant', 'tenant_group', 'site',
            'vlan_group', 'vlan', 'role', 'is_pool', 'mark_utilized', 'description', 'tags', 'created', 'last_updated',
        )
        default_columns = (
            'pk', 'prefix', 'status', 'children', 'vrf', 'utilization', 'tenant', 'site', 'vlan', 'role', 'description',
        )
        row_attrs = {
            'class': lambda record: 'success' if not record.pk else '',
        }


#
# IP ranges
#
class IPRangeTable(TenancyColumnsMixin, NetBoxTable):
    start_address = tables.Column(
        linkify=True
    )
    vrf = tables.TemplateColumn(
        template_code=VRF_LINK,
        verbose_name='VRF'
    )
    status = columns.ChoiceFieldColumn(
        default=AVAILABLE_LABEL
    )
    role = tables.Column(
        linkify=True
    )
    utilization = columns.UtilizationColumn(
        accessor='utilization',
        orderable=False
    )
    tags = columns.TagColumn(
        url_name='ipam:iprange_list'
    )

    class Meta(NetBoxTable.Meta):
        model = IPRange
        fields = (
            'pk', 'id', 'start_address', 'end_address', 'size', 'vrf', 'status', 'role', 'tenant', 'tenant_group', 'description',
            'utilization', 'tags', 'created', 'last_updated',
        )
        default_columns = (
            'pk', 'start_address', 'end_address', 'size', 'vrf', 'status', 'role', 'tenant', 'description',
        )
        row_attrs = {
            'class': lambda record: 'success' if not record.pk else '',
        }


#
# IPAddresses
#

class IPAddressTable(TenancyColumnsMixin, NetBoxTable):
    address = tables.TemplateColumn(
        template_code=IPADDRESS_LINK,
        verbose_name='IP Address'
    )
    vrf = tables.TemplateColumn(
        template_code=VRF_LINK,
        verbose_name='VRF'
    )
    status = columns.ChoiceFieldColumn(
        default=AVAILABLE_LABEL
    )
    role = columns.ChoiceFieldColumn()
    assigned_object = tables.Column(
        linkify=True,
        orderable=False,
        verbose_name='Interface'
    )
    assigned_object_parent = tables.Column(
        accessor='assigned_object__parent_object',
        linkify=True,
        orderable=False,
        verbose_name='Device/VM'
    )
    nat_inside = tables.Column(
        linkify=True,
        orderable=False,
        verbose_name='NAT (Inside)'
    )
    assigned = columns.BooleanColumn(
        accessor='assigned_object_id',
        linkify=True,
        verbose_name='Assigned'
    )
    tags = columns.TagColumn(
        url_name='ipam:ipaddress_list'
    )

    class Meta(NetBoxTable.Meta):
        model = IPAddress
        fields = (
            'pk', 'id', 'address', 'vrf', 'status', 'role', 'tenant', 'tenant_group', 'nat_inside', 'assigned', 'dns_name', 'description',
            'tags', 'created', 'last_updated',
        )
        default_columns = (
            'pk', 'address', 'vrf', 'status', 'role', 'tenant', 'assigned', 'dns_name', 'description',
        )
        row_attrs = {
            'class': lambda record: 'success' if not isinstance(record, IPAddress) else '',
        }


class IPAddressAssignTable(NetBoxTable):
    address = tables.TemplateColumn(
        template_code=IPADDRESS_ASSIGN_LINK,
        verbose_name='IP Address'
    )
    status = columns.ChoiceFieldColumn()
    assigned_object = tables.Column(
        orderable=False
    )

    class Meta(NetBoxTable.Meta):
        model = IPAddress
        fields = ('address', 'dns_name', 'vrf', 'status', 'role', 'tenant', 'assigned_object', 'description')
        exclude = ('id', )
        orderable = False


class AssignedIPAddressesTable(NetBoxTable):
    """
    List IP addresses assigned to an object.
    """
    address = tables.Column(
        linkify=True,
        verbose_name='IP Address'
    )
    vrf = tables.TemplateColumn(
        template_code=VRF_LINK,
        verbose_name='VRF'
    )
    status = columns.ChoiceFieldColumn()
    tenant = TenantColumn()

    class Meta(NetBoxTable.Meta):
        model = IPAddress
        fields = ('address', 'vrf', 'status', 'role', 'tenant', 'description')
        exclude = ('id', )
