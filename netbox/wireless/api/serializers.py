from rest_framework import serializers

from dcim.choices import LinkStatusChoices
from dcim.api.serializers import NestedInterfaceSerializer
from ipam.api.serializers import NestedVLANSerializer
from netbox.api import ChoiceField
from netbox.api.serializers import NestedGroupModelSerializer, NetBoxModelSerializer
from wireless.choices import *
from wireless.models import *
from .nested_serializers import *

__all__ = (
    'WirelessLANGroupSerializer',
    'WirelessLANSerializer',
    'WirelessLinkSerializer',
)


class WirelessLANGroupSerializer(NestedGroupModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='wireless-api:wirelesslangroup-detail')
    parent = NestedWirelessLANGroupSerializer(required=False, allow_null=True, default=None)
    wirelesslan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = WirelessLANGroup
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'parent', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'wirelesslan_count', '_depth',
        ]


class WirelessLANSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='wireless-api:wirelesslan-detail')
    group = NestedWirelessLANGroupSerializer(required=False, allow_null=True)
    vlan = NestedVLANSerializer(required=False, allow_null=True)
    auth_type = ChoiceField(choices=WirelessAuthTypeChoices, required=False, allow_blank=True)
    auth_cipher = ChoiceField(choices=WirelessAuthCipherChoices, required=False, allow_blank=True)

    class Meta:
        model = WirelessLAN
        fields = [
            'id', 'url', 'display', 'ssid', 'description', 'group', 'vlan', 'auth_type', 'auth_cipher', 'auth_psk',
            'description', 'tags', 'custom_fields', 'created', 'last_updated',
        ]


class WirelessLinkSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='wireless-api:wirelesslink-detail')
    status = ChoiceField(choices=LinkStatusChoices, required=False)
    interface_a = NestedInterfaceSerializer()
    interface_b = NestedInterfaceSerializer()
    auth_type = ChoiceField(choices=WirelessAuthTypeChoices, required=False, allow_blank=True)
    auth_cipher = ChoiceField(choices=WirelessAuthCipherChoices, required=False, allow_blank=True)

    class Meta:
        model = WirelessLink
        fields = [
            'id', 'url', 'display', 'interface_a', 'interface_b', 'ssid', 'status', 'description', 'auth_type',
            'auth_cipher', 'auth_psk', 'description', 'tags', 'custom_fields', 'created', 'last_updated',
        ]
