from django import forms

from dcim.choices import InterfaceModeChoices
from dcim.constants import INTERFACE_MTU_MAX, INTERFACE_MTU_MIN
from dcim.models import DeviceRole, Platform, Region, Site, SiteGroup
from ipam.models import VLAN, VLANGroup, VRF
from netbox.forms import NetBoxModelBulkEditForm
from tenancy.models import Tenant
from utilities.forms import (
    add_blank_choice, BulkEditNullBooleanSelect, BulkRenameForm, CommentField, DynamicModelChoiceField,
    DynamicModelMultipleChoiceField, SmallTextarea, StaticSelect
)
from virtualization.choices import *
from virtualization.models import *

__all__ = (
    'ClusterBulkEditForm',
    'ClusterGroupBulkEditForm',
    'ClusterTypeBulkEditForm',
    'VirtualMachineBulkEditForm',
    'VMInterfaceBulkEditForm',
    'VMInterfaceBulkRenameForm',
)


class ClusterTypeBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        max_length=200,
        required=False
    )

    model = ClusterType
    fieldsets = (
        (None, ('description',)),
    )
    nullable_fields = ('description',)


class ClusterGroupBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        max_length=200,
        required=False
    )

    model = ClusterGroup
    fieldsets = (
        (None, ('description',)),
    )
    nullable_fields = ('description',)


class ClusterBulkEditForm(NetBoxModelBulkEditForm):
    type = DynamicModelChoiceField(
        queryset=ClusterType.objects.all(),
        required=False
    )
    group = DynamicModelChoiceField(
        queryset=ClusterGroup.objects.all(),
        required=False
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    region = DynamicModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
    )
    site_group = DynamicModelChoiceField(
        queryset=SiteGroup.objects.all(),
        required=False,
    )
    site = DynamicModelChoiceField(
        queryset=Site.objects.all(),
        required=False,
        query_params={
            'region_id': '$region',
            'group_id': '$site_group',
        }
    )
    comments = CommentField(
        widget=SmallTextarea,
        label='Comments'
    )

    model = Cluster
    fieldsets = (
        (None, ('type', 'group', 'tenant',)),
        ('Site', ('region', 'site_group', 'site',)),
    )
    nullable_fields = (
        'group', 'site', 'comments', 'tenant',
    )


class VirtualMachineBulkEditForm(NetBoxModelBulkEditForm):
    status = forms.ChoiceField(
        choices=add_blank_choice(VirtualMachineStatusChoices),
        required=False,
        initial='',
        widget=StaticSelect(),
    )
    cluster = DynamicModelChoiceField(
        queryset=Cluster.objects.all(),
        required=False
    )
    role = DynamicModelChoiceField(
        queryset=DeviceRole.objects.filter(
            vm_role=True
        ),
        required=False,
        query_params={
            "vm_role": "True"
        }
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.all(),
        required=False
    )
    platform = DynamicModelChoiceField(
        queryset=Platform.objects.all(),
        required=False
    )
    vcpus = forms.IntegerField(
        required=False,
        label='vCPUs'
    )
    memory = forms.IntegerField(
        required=False,
        label='Memory (MB)'
    )
    disk = forms.IntegerField(
        required=False,
        label='Disk (GB)'
    )
    comments = CommentField(
        widget=SmallTextarea,
        label='Comments'
    )

    model = VirtualMachine
    fieldsets = (
        (None, ('cluster', 'status', 'role', 'tenant', 'platform')),
        ('Resources', ('vcpus', 'memory', 'disk'))
    )
    nullable_fields = (
        'role', 'tenant', 'platform', 'vcpus', 'memory', 'disk', 'comments',
    )


class VMInterfaceBulkEditForm(NetBoxModelBulkEditForm):
    virtual_machine = forms.ModelChoiceField(
        queryset=VirtualMachine.objects.all(),
        required=False,
        disabled=True,
        widget=forms.HiddenInput()
    )
    parent = DynamicModelChoiceField(
        queryset=VMInterface.objects.all(),
        required=False
    )
    bridge = DynamicModelChoiceField(
        queryset=VMInterface.objects.all(),
        required=False
    )
    enabled = forms.NullBooleanField(
        required=False,
        widget=BulkEditNullBooleanSelect()
    )
    mtu = forms.IntegerField(
        required=False,
        min_value=INTERFACE_MTU_MIN,
        max_value=INTERFACE_MTU_MAX,
        label='MTU'
    )
    description = forms.CharField(
        max_length=100,
        required=False
    )
    mode = forms.ChoiceField(
        choices=add_blank_choice(InterfaceModeChoices),
        required=False,
        widget=StaticSelect()
    )
    vlan_group = DynamicModelChoiceField(
        queryset=VLANGroup.objects.all(),
        required=False,
        label='VLAN group'
    )
    untagged_vlan = DynamicModelChoiceField(
        queryset=VLAN.objects.all(),
        required=False,
        query_params={
            'group_id': '$vlan_group',
        },
        label='Untagged VLAN'
    )
    tagged_vlans = DynamicModelMultipleChoiceField(
        queryset=VLAN.objects.all(),
        required=False,
        query_params={
            'group_id': '$vlan_group',
        },
        label='Tagged VLANs'
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label='VRF'
    )

    model = VMInterface
    fieldsets = (
        (None, ('mtu', 'enabled', 'vrf', 'description')),
        ('Related Interfaces', ('parent', 'bridge')),
        ('802.1Q Switching', ('mode', 'vlan_group', 'untagged_vlan', 'tagged_vlans')),
    )
    nullable_fields = (
        'parent', 'bridge', 'mtu', 'vrf', 'description',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'virtual_machine' in self.initial:
            vm_id = self.initial.get('virtual_machine')

            # Restrict parent/bridge interface assignment by VM
            self.fields['parent'].widget.add_query_param('virtual_machine_id', vm_id)
            self.fields['bridge'].widget.add_query_param('virtual_machine_id', vm_id)

            # Limit VLAN choices by virtual machine
            self.fields['untagged_vlan'].widget.add_query_param('available_on_virtualmachine', vm_id)
            self.fields['tagged_vlans'].widget.add_query_param('available_on_virtualmachine', vm_id)

        else:
            # See 5643
            if 'pk' in self.initial:
                site = None
                interfaces = VMInterface.objects.filter(pk__in=self.initial['pk']).prefetch_related(
                    'virtual_machine__cluster__site'
                )

                # Check interface sites.  First interface should set site, further interfaces will either continue the
                # loop or reset back to no site and break the loop.
                for interface in interfaces:
                    if site is None:
                        site = interface.virtual_machine.cluster.site
                    elif interface.virtual_machine.cluster.site is not site:
                        site = None
                        break

                if site is not None:
                    self.fields['untagged_vlan'].widget.add_query_param('site_id', site.pk)
                    self.fields['tagged_vlans'].widget.add_query_param('site_id', site.pk)

            self.fields['parent'].choices = ()
            self.fields['parent'].widget.attrs['disabled'] = True
            self.fields['bridge'].choices = ()
            self.fields['bridge'].widget.attrs['disabled'] = True


class VMInterfaceBulkRenameForm(BulkRenameForm):
    pk = forms.ModelMultipleChoiceField(
        queryset=VMInterface.objects.all(),
        widget=forms.MultipleHiddenInput()
    )
