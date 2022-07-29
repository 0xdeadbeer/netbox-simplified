from django import forms
from django.contrib.contenttypes.models import ContentType

from dcim.models import Device, Interface, Location, Rack, Region, Site, SiteGroup
from extras.models import Tag
from ipam.choices import *
from ipam.constants import *
from ipam.formfields import IPNetworkFormField
from ipam.models import *
from ipam.models import ASN
from netbox.forms import NetBoxModelForm
from tenancy.forms import TenancyForm
from utilities.exceptions import PermissionsViolation
from utilities.forms import (
    add_blank_choice, BootstrapMixin, ContentTypeChoiceField, DatePicker, DynamicModelChoiceField,
    DynamicModelMultipleChoiceField, NumericArrayField, SlugField, StaticSelect, StaticSelectMultiple,
)
from virtualization.models import Cluster, ClusterGroup, VirtualMachine, VMInterface

__all__ = (
    'AggregateForm',
    'ASNForm',
    'FHRPGroupForm',
    'FHRPGroupAssignmentForm',
    'IPAddressAssignForm',
    'IPAddressBulkAddForm',
    'IPAddressForm',
    'IPRangeForm',
    'PrefixForm',
    'RIRForm',
    'RoleForm',
    'RouteTargetForm',
    'ServiceForm',
    'ServiceCreateForm',
    'ServiceTemplateForm',
    'VLANForm',
    'VLANGroupForm',
    'VRFForm',
)


class VRFForm(TenancyForm, NetBoxModelForm):
    import_targets = DynamicModelMultipleChoiceField(
        queryset=RouteTarget.objects.all(),
        required=False
    )
    export_targets = DynamicModelMultipleChoiceField(
        queryset=RouteTarget.objects.all(),
        required=False
    )

    fieldsets = (
        ('VRF', ('name', 'rd', 'enforce_unique', 'description', 'tags')),
        ('Route Targets', ('import_targets', 'export_targets')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = VRF
        fields = [
            'name', 'rd', 'enforce_unique', 'description', 'import_targets', 'export_targets', 'tenant_group', 'tenant',
            'tags',
        ]
        labels = {
            'rd': "RD",
        }
        help_texts = {
            'rd': "Route distinguisher in any format",
        }


class RouteTargetForm(TenancyForm, NetBoxModelForm):
    fieldsets = (
        ('Route Target', ('name', 'description', 'tags')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = RouteTarget
        fields = [
            'name', 'description', 'tenant_group', 'tenant', 'tags',
        ]


class RIRForm(NetBoxModelForm):
    slug = SlugField()

    class Meta:
        model = RIR
        fields = [
            'name', 'slug', 'is_private', 'description', 'tags',
        ]


class AggregateForm(TenancyForm, NetBoxModelForm):
    rir = DynamicModelChoiceField(
        queryset=RIR.objects.all(),
        label='RIR'
    )

    fieldsets = (
        ('Aggregate', ('prefix', 'rir', 'date_added', 'description', 'tags')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = Aggregate
        fields = [
            'prefix', 'rir', 'date_added', 'description', 'tenant_group', 'tenant', 'tags',
        ]
        help_texts = {
            'prefix': "IPv4 or IPv6 network",
            'rir': "Regional Internet Registry responsible for this prefix",
        }
        widgets = {
            'date_added': DatePicker(),
        }


class ASNForm(TenancyForm, NetBoxModelForm):
    rir = DynamicModelChoiceField(
        queryset=RIR.objects.all(),
        label='RIR',
    )
    sites = DynamicModelMultipleChoiceField(
        queryset=Site.objects.all(),
        label='Sites',
        required=False
    )

    fieldsets = (
        ('ASN', ('asn', 'rir', 'sites', 'description', 'tags')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = ASN
        fields = [
            'asn', 'rir', 'sites', 'tenant_group', 'tenant', 'description', 'tags'
        ]
        help_texts = {
            'asn': "AS number",
            'rir': "Regional Internet Registry responsible for this prefix",
        }
        widgets = {
            'date_added': DatePicker(),
        }

    def __init__(self, data=None, instance=None, *args, **kwargs):
        super().__init__(data=data, instance=instance, *args, **kwargs)

        if self.instance and self.instance.pk is not None:
            self.fields['sites'].initial = self.instance.sites.all().values_list('id', flat=True)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.sites.set(self.cleaned_data['sites'])
        return instance


class RoleForm(NetBoxModelForm):
    slug = SlugField()

    class Meta:
        model = Role
        fields = [
            'name', 'slug', 'weight', 'description', 'tags',
        ]


class PrefixForm(TenancyForm, NetBoxModelForm):
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        }
    )
    site_group = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        }
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'region_id': '$region',
            'group_id': '$site_group',
        }
    )
    vlan_group = DynamicModelChoiceField(
        queryset=VLANGroup.objects.all(),
        required=False,
        label='VLAN group',
        null_option='None',
        query_params={
            'site': '$site'
        },
        initial_params={
            'vlans': '$vlan'
        }
    )
    vlan = DynamicModelChoiceField(
        queryset=VLAN.objects.all(),
        required=False,
        label='VLAN',
        query_params={
            'site_id': '$site',
            'group_id': '$vlan_group',
        }
    )
    role = DynamicModelChoiceField(
        queryset=Role.objects.all(),
        required=False
    )

    fieldsets = (
        ('Prefix', ('prefix', 'status', 'vrf', 'role', 'is_pool', 'mark_utilized', 'description', 'tags')),
        ('Site/VLAN Assignment', ('region', 'site_group', 'site', 'vlan_group', 'vlan')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = Prefix
        fields = [
            'prefix', 'vrf', 'site', 'vlan', 'status', 'role', 'is_pool', 'mark_utilized', 'description',
            'tenant_group', 'tenant', 'tags',
        ]
        widgets = {
            'status': StaticSelect(),
        }


class IPRangeForm(TenancyForm, NetBoxModelForm):
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    role = DynamicModelChoiceField(
        queryset=Role.objects.all(),
        required=False
    )

    fieldsets = (
        ('IP Range', ('vrf', 'start_address', 'end_address', 'role', 'status', 'description', 'tags')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = IPRange
        fields = [
            'vrf', 'start_address', 'end_address', 'status', 'role', 'description', 'tenant_group', 'tenant', 'tags',
        ]
        widgets = {
            'status': StaticSelect(),
        }


class IPAddressForm(TenancyForm, NetBoxModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        initial_params={
            'interfaces': '$interface'
        }
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=False,
        query_params={
            'device_id': '$device'
        }
    )
    virtual_machine = DynamicModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        initial_params={
            'interfaces': '$vminterface'
        }
    )
    vminterface = DynamicModelChoiceField(
        queryset=VMInterface.objects.all(),
        required=False,
        label='Interface',
        query_params={
            'virtual_machine_id': '$virtual_machine'
        }
    )
    fhrpgroup = DynamicModelChoiceField(
        queryset=FHRPGroup.objects.all(),
        required=False,
        label='FHRP Group'
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    nat_region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        label='Region',
        initial_params={
            'sites': '$nat_site'
        }
    )
    nat_site_group = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        label='Site group',
        initial_params={
            'sites': '$nat_site'
        }
    )
    nat_site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        label='Site',
        query_params={
            'region_id': '$nat_region',
            'group_id': '$nat_site_group',
        }
    )
    nat_rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        label='Rack',
        null_option='None',
        query_params={
            'site_id': '$site'
        }
    )
    nat_device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label='Device',
        query_params={
            'site_id': '$site',
            'rack_id': '$nat_rack',
        }
    )
    nat_cluster = DynamicModelChoiceField(
        queryset=Cluster.objects.all(),
        required=False,
        label='Cluster'
    )
    nat_virtual_machine = DynamicModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        label='Virtual Machine',
        query_params={
            'cluster_id': '$nat_cluster',
        }
    )
    nat_vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    nat_inside = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        label='IP Address',
        query_params={
            'device_id': '$nat_device',
            'virtual_machine_id': '$nat_virtual_machine',
            'vrf_id': '$nat_vrf',
        }
    )
    primary_for_parent = forms.BooleanField(
        required=False,
        label='Make this the primary IP for the device/VM'
    )

    class Meta:
        model = IPAddress
        fields = [
            'address', 'vrf', 'status', 'role', 'dns_name', 'description', 'primary_for_parent', 'nat_site', 'nat_rack',
            'nat_device', 'nat_cluster', 'nat_virtual_machine', 'nat_vrf', 'nat_inside', 'tenant_group', 'tenant',
            'tags',
        ]
        widgets = {
            'status': StaticSelect(),
            'role': StaticSelect(),
        }

    def __init__(self, *args, **kwargs):

        # Initialize helper selectors
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {}).copy()
        if instance:
            if type(instance.assigned_object) is Interface:
                initial['interface'] = instance.assigned_object
            elif type(instance.assigned_object) is VMInterface:
                initial['vminterface'] = instance.assigned_object
            elif type(instance.assigned_object) is FHRPGroup:
                initial['fhrpgroup'] = instance.assigned_object
            if instance.nat_inside:
                nat_inside_parent = instance.nat_inside.assigned_object
                if type(nat_inside_parent) is Interface:
                    initial['nat_site'] = nat_inside_parent.device.site.pk
                    if nat_inside_parent.device.rack:
                        initial['nat_rack'] = nat_inside_parent.device.rack.pk
                    initial['nat_device'] = nat_inside_parent.device.pk
                elif type(nat_inside_parent) is VMInterface:
                    initial['nat_cluster'] = nat_inside_parent.virtual_machine.cluster.pk
                    initial['nat_virtual_machine'] = nat_inside_parent.virtual_machine.pk
        kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

        # Initialize primary_for_parent if IP address is already assigned
        if self.instance.pk and self.instance.assigned_object:
            parent = getattr(self.instance.assigned_object, 'parent_object', None)
            if parent and (
                self.instance.address.version == 4 and parent.primary_ip4_id == self.instance.pk or
                self.instance.address.version == 6 and parent.primary_ip6_id == self.instance.pk
            ):
                self.initial['primary_for_parent'] = True

    def clean(self):
        super().clean()

        # Handle object assignment
        selected_objects = [
            field for field in ('interface', 'vminterface', 'fhrpgroup') if self.cleaned_data[field]
        ]
        if len(selected_objects) > 1:
            raise forms.ValidationError({
                selected_objects[1]: "An IP address can only be assigned to a single object."
            })
        elif selected_objects:
            self.instance.assigned_object = self.cleaned_data[selected_objects[0]]
        else:
            self.instance.assigned_object = None

        # Primary IP assignment is only available if an interface has been assigned.
        interface = self.cleaned_data.get('interface') or self.cleaned_data.get('vminterface')
        if self.cleaned_data.get('primary_for_parent') and not interface:
            self.add_error(
                'primary_for_parent', "Only IP addresses assigned to an interface can be designated as primary IPs."
            )

    def save(self, *args, **kwargs):
        ipaddress = super().save(*args, **kwargs)

        # Assign/clear this IPAddress as the primary for the associated Device/VirtualMachine.
        interface = self.instance.assigned_object
        if type(interface) in (Interface, VMInterface):
            parent = interface.parent_object
            if self.cleaned_data['primary_for_parent']:
                if ipaddress.address.version == 4:
                    parent.primary_ip4 = ipaddress
                else:
                    parent.primary_ip6 = ipaddress
                parent.save()
            elif ipaddress.address.version == 4 and parent.primary_ip4 == ipaddress:
                parent.primary_ip4 = None
                parent.save()
            elif ipaddress.address.version == 6 and parent.primary_ip6 == ipaddress:
                parent.primary_ip6 = None
                parent.save()

        return ipaddress


class IPAddressBulkAddForm(TenancyForm, NetBoxModelForm):
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )

    class Meta:
        model = IPAddress
        fields = [
            'address', 'vrf', 'status', 'role', 'dns_name', 'description', 'tenant_group', 'tenant', 'tags',
        ]
        widgets = {
            'status': StaticSelect(),
            'role': StaticSelect(),
        }


class IPAddressAssignForm(BootstrapMixin, forms.Form):
    vrf_id = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    q = forms.CharField(
        required=False,
        label='Search',
    )


class FHRPGroupForm(NetBoxModelForm):

    # Optionally create a new IPAddress along with the FHRPGroup
    ip_vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )
    ip_address = IPNetworkFormField(
        required=False,
        label='Address'
    )
    ip_status = forms.ChoiceField(
        choices=add_blank_choice(IPAddressStatusChoices),
        required=False,
        label='Status'
    )

    fieldsets = (
        ('FHRP Group', ('protocol', 'group_id', 'description', 'tags')),
        ('Authentication', ('auth_type', 'auth_key')),
        ('Virtual IP Address', ('ip_vrf', 'ip_address', 'ip_status'))
    )

    class Meta:
        model = FHRPGroup
        fields = (
            'protocol', 'group_id', 'auth_type', 'auth_key', 'description', 'ip_vrf', 'ip_address', 'ip_status', 'tags',
        )

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        # Check if we need to create a new IPAddress for the group
        if self.cleaned_data.get('ip_address'):
            ipaddress = IPAddress(
                vrf=self.cleaned_data['ip_vrf'],
                address=self.cleaned_data['ip_address'],
                status=self.cleaned_data['ip_status'],
                role=FHRP_PROTOCOL_ROLE_MAPPINGS.get(self.cleaned_data['protocol'], IPAddressRoleChoices.ROLE_VIP),
                assigned_object=instance
            )
            ipaddress.save()

            # Check that the new IPAddress conforms with any assigned object-level permissions
            if not IPAddress.objects.filter(pk=ipaddress.pk).first():
                raise PermissionsViolation()

        return instance

    def clean(self):
        super().clean()

        ip_vrf = self.cleaned_data.get('ip_vrf')
        ip_address = self.cleaned_data.get('ip_address')
        ip_status = self.cleaned_data.get('ip_status')

        if ip_address:
            ip_form = IPAddressForm({
                'address': ip_address,
                'vrf': ip_vrf,
                'status': ip_status,
            })
            if not ip_form.is_valid():
                self.errors.update({
                    f'ip_{field}': error for field, error in ip_form.errors.items()
                })


class FHRPGroupAssignmentForm(BootstrapMixin, forms.ModelForm):
    group = DynamicModelChoiceField(
        queryset=FHRPGroup.objects.all()
    )

    class Meta:
        model = FHRPGroupAssignment
        fields = ('group', 'priority')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ipaddresses = self.instance.interface.ip_addresses.all()
        for ipaddress in ipaddresses:
            self.fields['group'].widget.add_query_param('related_ip', ipaddress.pk)


class VLANGroupForm(NetBoxModelForm):
    scope_type = ContentTypeChoiceField(
        queryset=ContentType.objects.filter(model__in=VLANGROUP_SCOPE_TYPES),
        required=False
    )
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        }
    )
    sitegroup = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        },
        label='Site group'
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        initial_params={
            'locations': '$location'
        },
        query_params={
            'region_id': '$region',
            'group_id': '$sitegroup',
        }
    )
    location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        initial_params={
            'racks': '$rack'
        },
        query_params={
            'site_id': '$site',
        }
    )
    rack = DynamicModelChoiceField(
        queryset=Rack.objects.all(),
        required=False,
        query_params={
            'site_id': '$site',
            'location_id': '$location',
        }
    )
    clustergroup = DynamicModelChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False,
        initial_params={
            'clusters': '$cluster'
        },
        label='Cluster group'
    )
    cluster = DynamicModelChoiceField(
        queryset=Cluster.objects.all(),
        required=False,
        query_params={
            'group_id': '$clustergroup',
        }
    )
    slug = SlugField()

    fieldsets = (
        ('VLAN Group', ('name', 'slug', 'description', 'tags')),
        ('Child VLANs', ('min_vid', 'max_vid')),
        ('Scope', ('scope_type', 'region', 'sitegroup', 'site', 'location', 'rack', 'clustergroup', 'cluster')),
    )

    class Meta:
        model = VLANGroup
        fields = [
            'name', 'slug', 'description', 'scope_type', 'region', 'sitegroup', 'site', 'location', 'rack',
            'clustergroup', 'cluster', 'min_vid', 'max_vid', 'tags',
        ]
        widgets = {
            'scope_type': StaticSelect,
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {})

        if instance is not None and instance.scope:
            initial[instance.scope_type.model] = instance.scope

            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        # Assign scope based on scope_type
        if self.cleaned_data.get('scope_type'):
            scope_field = self.cleaned_data['scope_type'].model
            self.instance.scope = self.cleaned_data.get(scope_field)
        else:
            self.instance.scope_id = None


class VLANForm(TenancyForm, NetBoxModelForm):
    # VLANGroup assignment fields
    scope_type = forms.ChoiceField(
        choices=(
            ('', ''),
            ('dcim.region', 'Region'),
            ('dcim.sitegroup', 'Site group'),
            ('dcim.site', 'Site'),
            ('dcim.location', 'Location'),
            ('dcim.rack', 'Rack'),
            ('virtualization.clustergroup', 'Cluster group'),
            ('virtualization.cluster', 'Cluster'),
        ),
        required=False,
        widget=StaticSelect,
        label='Group scope'
    )
    group = DynamicModelChoiceField(
        queryset=VLANGroup.objects.all(),
        required=False,
        query_params={
            'scope_type': '$scope_type',
        },
        label='VLAN Group'
    )

    # Site assignment fields
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        },
        label='Region'
    )
    sitegroup = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
        initial_params={
            'sites': '$site'
        },
        label='Site group'
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        null_option='None',
        query_params={
            'region_id': '$region',
            'group_id': '$sitegroup',
        }
    )

    # Other fields
    role = DynamicModelChoiceField(
        queryset=Role.objects.all(),
        required=False
    )

    class Meta:
        model = VLAN
        fields = [
            'site', 'group', 'vid', 'name', 'status', 'role', 'description', 'tenant_group', 'tenant', 'tags',
        ]
        help_texts = {
            'site': "Leave blank if this VLAN spans multiple sites",
            'group': "VLAN group (optional)",
            'vid': "Configured VLAN ID",
            'name': "Configured VLAN name",
            'status': "Operational status of this VLAN",
            'role': "The primary function of this VLAN",
        }
        widgets = {
            'status': StaticSelect(),
        }


class ServiceTemplateForm(NetBoxModelForm):
    ports = NumericArrayField(
        base_field=forms.IntegerField(
            min_value=SERVICE_PORT_MIN,
            max_value=SERVICE_PORT_MAX
        ),
        help_text="Comma-separated list of one or more port numbers. A range may be specified using a hyphen."
    )

    class Meta:
        model = ServiceTemplate
        fields = ('name', 'protocol', 'ports', 'description', 'tags')
        widgets = {
            'protocol': StaticSelect(),
        }


class ServiceForm(NetBoxModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False
    )
    virtual_machine = DynamicModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False
    )
    ports = NumericArrayField(
        base_field=forms.IntegerField(
            min_value=SERVICE_PORT_MIN,
            max_value=SERVICE_PORT_MAX
        ),
        help_text="Comma-separated list of one or more port numbers. A range may be specified using a hyphen."
    )
    ipaddresses = DynamicModelMultipleChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        label='IP Addresses',
        query_params={
            'device_id': '$device',
            'virtual_machine_id': '$virtual_machine',
        }
    )

    class Meta:
        model = Service
        fields = [
            'device', 'virtual_machine', 'name', 'protocol', 'ports', 'ipaddresses', 'description', 'tags',
        ]
        help_texts = {
            'ipaddresses': "IP address assignment is optional. If no IPs are selected, the service is assumed to be "
                           "reachable via all IPs assigned to the device.",
        }
        widgets = {
            'protocol': StaticSelect(),
            'ipaddresses': StaticSelectMultiple(),
        }


class ServiceCreateForm(ServiceForm):
    service_template = DynamicModelChoiceField(
        queryset=ServiceTemplate.objects.all(),
        required=False
    )

    class Meta(ServiceForm.Meta):
        fields = [
            'device', 'virtual_machine', 'service_template', 'name', 'protocol', 'ports', 'ipaddresses', 'description',
            'tags',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fields which may be populated from a ServiceTemplate are not required
        for field in ('name', 'protocol', 'ports'):
            self.fields[field].required = False
            del(self.fields[field].widget.attrs['required'])

    def clean(self):
        if self.cleaned_data['service_template']:
            # Create a new Service from the specified template
            service_template = self.cleaned_data['service_template']
            self.cleaned_data['name'] = service_template.name
            self.cleaned_data['protocol'] = service_template.protocol
            self.cleaned_data['ports'] = service_template.ports
            if not self.cleaned_data['description']:
                self.cleaned_data['description'] = service_template.description
        elif not all(self.cleaned_data[f] for f in ('name', 'protocol', 'ports')):
            raise forms.ValidationError("Must specify name, protocol, and port(s) if not using a service template.")
