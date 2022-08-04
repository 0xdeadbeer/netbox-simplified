from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers

from dcim.api.nested_serializers import NestedDeviceSerializer, NestedSiteSerializer
from ipam.choices import *
from ipam.constants import IPADDRESS_ASSIGNMENT_MODELS, VLANGROUP_SCOPE_TYPES
from ipam.models import *
from netbox.api import ChoiceField, ContentTypeField, SerializedPKRelatedField
from netbox.api.serializers import NetBoxModelSerializer
from netbox.constants import NESTED_SERIALIZER_PREFIX
from tenancy.api.nested_serializers import NestedTenantSerializer
from utilities.api import get_serializer_for_model
from virtualization.api.nested_serializers import NestedVirtualMachineSerializer
from .nested_serializers import *


#
# ASNs
#

class ASNSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:asn-detail')
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    site_count = serializers.IntegerField(read_only=True)
    provider_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ASN
        fields = [
            'id', 'url', 'display', 'asn', 'rir', 'tenant', 'description', 'site_count', 'provider_count', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]


#
# VRFs
#

class VRFSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:vrf-detail')
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    import_targets = SerializedPKRelatedField(
        queryset=RouteTarget.objects.all(),
        serializer=NestedRouteTargetSerializer,
        required=False,
        many=True
    )
    export_targets = SerializedPKRelatedField(
        queryset=RouteTarget.objects.all(),
        serializer=NestedRouteTargetSerializer,
        required=False,
        many=True
    )
    ipaddress_count = serializers.IntegerField(read_only=True)
    prefix_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VRF
        fields = [
            'id', 'url', 'display', 'name', 'rd', 'tenant', 'enforce_unique', 'description', 'import_targets',
            'export_targets', 'tags', 'custom_fields', 'created', 'last_updated', 'ipaddress_count', 'prefix_count',
        ]


#
# Route targets
#

class RouteTargetSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:routetarget-detail')
    tenant = NestedTenantSerializer(required=False, allow_null=True)

    class Meta:
        model = RouteTarget
        fields = [
            'id', 'url', 'display', 'name', 'tenant', 'description', 'tags', 'custom_fields', 'created', 'last_updated',
        ]


#
# RIRs/aggregates
#

class RIRSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:rir-detail')
    aggregate_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RIR
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'is_private', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'aggregate_count',
        ]


class AggregateSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:aggregate-detail')
    family = ChoiceField(choices=IPAddressFamilyChoices, read_only=True)
    rir = NestedRIRSerializer()
    tenant = NestedTenantSerializer(required=False, allow_null=True)

    class Meta:
        model = Aggregate
        fields = [
            'id', 'url', 'display', 'family', 'prefix', 'rir', 'tenant', 'date_added', 'description', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]
        read_only_fields = ['family']


#
# FHRP Groups
#

class FHRPGroupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:fhrpgroup-detail')
    ip_addresses = NestedIPAddressSerializer(many=True, read_only=True)

    class Meta:
        model = FHRPGroup
        fields = [
            'id', 'url', 'display', 'protocol', 'group_id', 'auth_type', 'auth_key', 'description', 'ip_addresses',
            'tags', 'custom_fields', 'created', 'last_updated',
        ]


class FHRPGroupAssignmentSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:fhrpgroupassignment-detail')
    group = NestedFHRPGroupSerializer()
    interface_type = ContentTypeField(
        queryset=ContentType.objects.all()
    )
    interface = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FHRPGroupAssignment
        fields = [
            'id', 'url', 'display', 'group', 'interface_type', 'interface_id', 'interface', 'priority', 'created',
            'last_updated',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_interface(self, obj):
        if obj.interface is None:
            return None
        serializer = get_serializer_for_model(obj.interface, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(obj.interface, context=context).data


#
# VLANs
#

class RoleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:role-detail')
    prefix_count = serializers.IntegerField(read_only=True)
    vlan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'weight', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'prefix_count', 'vlan_count',
        ]


class VLANGroupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:vlangroup-detail')
    scope_type = ContentTypeField(
        queryset=ContentType.objects.filter(
            model__in=VLANGROUP_SCOPE_TYPES
        ),
        required=False,
        default=None
    )
    scope_id = serializers.IntegerField(allow_null=True, required=False, default=None)
    scope = serializers.SerializerMethodField(read_only=True)
    vlan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VLANGroup
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'scope_type', 'scope_id', 'scope', 'min_vid', 'max_vid',
            'description', 'tags', 'custom_fields', 'created', 'last_updated', 'vlan_count',
        ]
        validators = []

    def get_scope(self, obj):
        if obj.scope_id is None:
            return None
        serializer = get_serializer_for_model(obj.scope, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}

        return serializer(obj.scope, context=context).data


class VLANSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:vlan-detail')
    site = NestedSiteSerializer(required=False, allow_null=True)
    group = NestedVLANGroupSerializer(required=False, allow_null=True, default=None)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=VLANStatusChoices, required=False)
    role = NestedRoleSerializer(required=False, allow_null=True)
    prefix_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VLAN
        fields = [
            'id', 'url', 'display', 'site', 'group', 'vid', 'name', 'tenant', 'status', 'role', 'description', 'tags',
            'custom_fields', 'created', 'last_updated', 'prefix_count',
        ]


class AvailableVLANSerializer(serializers.Serializer):
    """
    Representation of a VLAN which does not exist in the database.
    """
    vid = serializers.IntegerField(read_only=True)
    group = NestedVLANGroupSerializer(read_only=True)

    def to_representation(self, instance):
        return OrderedDict([
            ('vid', instance),
            ('group', NestedVLANGroupSerializer(
                self.context['group'],
                context={'request': self.context['request']}
            ).data),
        ])


class CreateAvailableVLANSerializer(NetBoxModelSerializer):
    site = NestedSiteSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=VLANStatusChoices, required=False)
    role = NestedRoleSerializer(required=False, allow_null=True)

    class Meta:
        model = VLAN
        fields = [
            'name', 'site', 'tenant', 'status', 'role', 'description', 'tags', 'custom_fields',
        ]

    def validate(self, data):
        # Bypass model validation since we don't have a VID yet
        return data


#
# Prefixes
#

class PrefixSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:prefix-detail')
    family = ChoiceField(choices=IPAddressFamilyChoices, read_only=True)
    site = NestedSiteSerializer(required=False, allow_null=True)
    vrf = NestedVRFSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    vlan = NestedVLANSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=PrefixStatusChoices, required=False)
    role = NestedRoleSerializer(required=False, allow_null=True)
    children = serializers.IntegerField(read_only=True)
    _depth = serializers.IntegerField(read_only=True)

    class Meta:
        model = Prefix
        fields = [
            'id', 'url', 'display', 'family', 'prefix', 'site', 'vrf', 'tenant', 'vlan', 'status', 'role', 'is_pool',
            'mark_utilized', 'description', 'tags', 'custom_fields', 'created', 'last_updated', 'children', '_depth',
        ]
        read_only_fields = ['family']


class PrefixLengthSerializer(serializers.Serializer):

    prefix_length = serializers.IntegerField()

    def to_internal_value(self, data):
        requested_prefix = data.get('prefix_length')
        if requested_prefix is None:
            raise serializers.ValidationError({
                'prefix_length': 'this field can not be missing'
            })
        if not isinstance(requested_prefix, int):
            raise serializers.ValidationError({
                'prefix_length': 'this field must be int type'
            })

        prefix = self.context.get('prefix')
        if prefix.family == 4 and requested_prefix > 32:
            raise serializers.ValidationError({
                'prefix_length': 'Invalid prefix length ({}) for IPv4'.format((requested_prefix))
            })
        elif prefix.family == 6 and requested_prefix > 128:
            raise serializers.ValidationError({
                'prefix_length': 'Invalid prefix length ({}) for IPv6'.format((requested_prefix))
            })
        return data


class AvailablePrefixSerializer(serializers.Serializer):
    """
    Representation of a prefix which does not exist in the database.
    """
    family = serializers.IntegerField(read_only=True)
    prefix = serializers.CharField(read_only=True)
    vrf = NestedVRFSerializer(read_only=True)

    def to_representation(self, instance):
        if self.context.get('vrf'):
            vrf = NestedVRFSerializer(self.context['vrf'], context={'request': self.context['request']}).data
        else:
            vrf = None
        return OrderedDict([
            ('family', instance.version),
            ('prefix', str(instance)),
            ('vrf', vrf),
        ])


#
# IP ranges
#

class IPRangeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:iprange-detail')
    family = ChoiceField(choices=IPAddressFamilyChoices, read_only=True)
    vrf = NestedVRFSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=IPRangeStatusChoices, required=False)
    role = NestedRoleSerializer(required=False, allow_null=True)
    children = serializers.IntegerField(read_only=True)

    class Meta:
        model = IPRange
        fields = [
            'id', 'url', 'display', 'family', 'start_address', 'end_address', 'size', 'vrf', 'tenant', 'status', 'role',
            'description', 'tags', 'custom_fields', 'created', 'last_updated', 'children',
        ]
        read_only_fields = ['family']


#
# IP addresses
#

class IPAddressSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:ipaddress-detail')
    family = ChoiceField(choices=IPAddressFamilyChoices, read_only=True)
    vrf = NestedVRFSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=IPAddressStatusChoices, required=False)
    role = ChoiceField(choices=IPAddressRoleChoices, allow_blank=True, required=False)
    assigned_object_type = ContentTypeField(
        queryset=ContentType.objects.filter(IPADDRESS_ASSIGNMENT_MODELS),
        required=False,
        allow_null=True
    )
    assigned_object = serializers.SerializerMethodField(read_only=True)
    nat_inside = NestedIPAddressSerializer(required=False, allow_null=True)
    nat_outside = NestedIPAddressSerializer(required=False, read_only=True)

    class Meta:
        model = IPAddress
        fields = [
            'id', 'url', 'display', 'family', 'address', 'vrf', 'tenant', 'status', 'role', 'assigned_object_type',
            'assigned_object_id', 'assigned_object', 'nat_inside', 'nat_outside', 'dns_name', 'description', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]
        read_only_fields = ['family', 'nat_outside']

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_assigned_object(self, obj):
        if obj.assigned_object is None:
            return None
        serializer = get_serializer_for_model(obj.assigned_object, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(obj.assigned_object, context=context).data


class AvailableIPSerializer(serializers.Serializer):
    """
    Representation of an IP address which does not exist in the database.
    """
    family = serializers.IntegerField(read_only=True)
    address = serializers.CharField(read_only=True)
    vrf = NestedVRFSerializer(read_only=True)

    def to_representation(self, instance):
        if self.context.get('vrf'):
            vrf = NestedVRFSerializer(self.context['vrf'], context={'request': self.context['request']}).data
        else:
            vrf = None
        return OrderedDict([
            ('family', self.context['parent'].family),
            ('address', f"{instance}/{self.context['parent'].mask_length}"),
            ('vrf', vrf),
        ])


#
# Services
#

class ServiceTemplateSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:servicetemplate-detail')
    protocol = ChoiceField(choices=ServiceProtocolChoices, required=False)

    class Meta:
        model = ServiceTemplate
        fields = [
            'id', 'url', 'display', 'name', 'ports', 'protocol', 'description', 'tags', 'custom_fields', 'created',
            'last_updated',
        ]


class ServiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='ipam-api:service-detail')
    device = NestedDeviceSerializer(required=False, allow_null=True)
    virtual_machine = NestedVirtualMachineSerializer(required=False, allow_null=True)
    protocol = ChoiceField(choices=ServiceProtocolChoices, required=False)
    ipaddresses = SerializedPKRelatedField(
        queryset=IPAddress.objects.all(),
        serializer=NestedIPAddressSerializer,
        required=False,
        many=True
    )

    class Meta:
        model = Service
        fields = [
            'id', 'url', 'display', 'device', 'virtual_machine', 'name', 'ports', 'protocol', 'ipaddresses',
            'description', 'tags', 'custom_fields', 'created', 'last_updated',
        ]


class ConnectionSerializer(NetBoxModelSerializer):

    class Meta:
        model = Connection
        fields = [
            'id', 'name', 'protocol', 'port', 'device_from', 'device_to', 'comments'
        ]