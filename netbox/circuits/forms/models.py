from django import forms
from django.utils.translation import gettext as _

from circuits.models import *
from dcim.models import Region, Site, SiteGroup
from ipam.models import ASN
from netbox.forms import NetBoxModelForm
from tenancy.forms import TenancyForm
from utilities.forms import (
    BootstrapMixin, CommentField, DatePicker, DynamicModelChoiceField, DynamicModelMultipleChoiceField,
    SelectSpeedWidget, SmallTextarea, SlugField, StaticSelect,
)

__all__ = (
    'CircuitForm',
    'CircuitTerminationForm',
    'CircuitTypeForm',
    'ProviderForm',
    'ProviderNetworkForm',
)


class ProviderForm(NetBoxModelForm):
    slug = SlugField()
    asns = DynamicModelMultipleChoiceField(
        queryset=ASN.objects.all(),
        label=_('ASNs'),
        required=False
    )
    comments = CommentField()

    fieldsets = (
        ('Provider', ('name', 'slug', 'asn', 'asns', 'tags')),
        ('Support Info', ('account', 'portal_url', 'noc_contact', 'admin_contact')),
    )

    class Meta:
        model = Provider
        fields = [
            'name', 'slug', 'asn', 'account', 'portal_url', 'noc_contact', 'admin_contact', 'asns', 'comments', 'tags',
        ]
        widgets = {
            'noc_contact': SmallTextarea(
                attrs={'rows': 5}
            ),
            'admin_contact': SmallTextarea(
                attrs={'rows': 5}
            ),
        }
        help_texts = {
            'name': "Full name of the provider",
            'asn': "BGP autonomous system number (if applicable)",
            'portal_url': "URL of the provider's customer support portal",
            'noc_contact': "NOC email address and phone number",
            'admin_contact': "Administrative contact email address and phone number",
        }


class ProviderNetworkForm(NetBoxModelForm):
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all()
    )
    comments = CommentField()

    fieldsets = (
        ('Provider Network', ('provider', 'name', 'service_id', 'description', 'tags')),
    )

    class Meta:
        model = ProviderNetwork
        fields = [
            'provider', 'name', 'service_id', 'description', 'comments', 'tags',
        ]


class CircuitTypeForm(NetBoxModelForm):
    slug = SlugField()

    class Meta:
        model = CircuitType
        fields = [
            'name', 'slug', 'description', 'tags',
        ]


class CircuitForm(TenancyForm, NetBoxModelForm):
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all()
    )
    type = DynamicModelChoiceField(
        queryset=CircuitType.objects.all()
    )
    comments = CommentField()

    fieldsets = (
        ('Circuit', ('provider', 'cid', 'type', 'status', 'install_date', 'commit_rate', 'description', 'tags')),
        ('Tenancy', ('tenant_group', 'tenant')),
    )

    class Meta:
        model = Circuit
        fields = [
            'cid', 'type', 'provider', 'status', 'install_date', 'commit_rate', 'description', 'tenant_group', 'tenant',
            'comments', 'tags',
        ]
        help_texts = {
            'cid': "Unique circuit ID",
            'commit_rate': "Committed rate",
        }
        widgets = {
            'status': StaticSelect(),
            'install_date': DatePicker(),
            'commit_rate': SelectSpeedWidget(),
        }


class CircuitTerminationForm(BootstrapMixin, forms.ModelForm):
    provider = DynamicModelChoiceField(
        queryset=Provider.objects.all(),
        required=False,
        initial_params={
            'circuits': '$circuit'
        }
    )
    circuit = DynamicModelChoiceField(
        queryset=Circuit.objects.all(),
        query_params={
            'provider_id': '$provider',
        },
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
        query_params={
            'region_id': '$region',
            'group_id': '$site_group',
        },
        required=False
    )
    provider_network = DynamicModelChoiceField(
        queryset=ProviderNetwork.objects.all(),
        required=False
    )

    class Meta:
        model = CircuitTermination
        fields = [
            'provider', 'circuit', 'term_side', 'region', 'site_group', 'site', 'provider_network', 'mark_connected',
            'port_speed', 'upstream_speed', 'xconnect_id', 'pp_info', 'description',
        ]
        help_texts = {
            'port_speed': "Physical circuit speed",
            'xconnect_id': "ID of the local cross-connect",
            'pp_info': "Patch panel ID and port number(s)"
        }
        widgets = {
            'term_side': StaticSelect(),
            'port_speed': SelectSpeedWidget(),
            'upstream_speed': SelectSpeedWidget(),
        }
