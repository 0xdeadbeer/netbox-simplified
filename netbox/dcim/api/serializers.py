from django.contrib.contenttypes.models import ContentType
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from timezone_field.rest_framework import TimeZoneSerializerField

from dcim.choices import *
from dcim.constants import *
from dcim.models import *
from ipam.api.nested_serializers import (
    NestedASNSerializer, NestedIPAddressSerializer, NestedVLANSerializer, NestedVRFSerializer,
)
from ipam.models import ASN, VLAN
from netbox.api import ChoiceField, ContentTypeField, SerializedPKRelatedField
from netbox.api.serializers import (
    NestedGroupModelSerializer, NetBoxModelSerializer, ValidatedModelSerializer, WritableNestedSerializer,
)
from netbox.config import ConfigItem
from netbox.constants import NESTED_SERIALIZER_PREFIX
from tenancy.api.nested_serializers import NestedTenantSerializer
from users.api.nested_serializers import NestedUserSerializer
from utilities.api import get_serializer_for_model
from virtualization.api.nested_serializers import NestedClusterSerializer
from wireless.api.nested_serializers import NestedWirelessLANSerializer, NestedWirelessLinkSerializer
from wireless.choices import *
from wireless.models import WirelessLAN
from .nested_serializers import *


class LinkTerminationSerializer(serializers.ModelSerializer):
    link_peer_type = serializers.SerializerMethodField(read_only=True)
    link_peer = serializers.SerializerMethodField(read_only=True)
    _occupied = serializers.SerializerMethodField(read_only=True)

    def get_link_peer_type(self, obj):
        if obj._link_peer is not None:
            return f'{obj._link_peer._meta.app_label}.{obj._link_peer._meta.model_name}'
        return None

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_link_peer(self, obj):
        """
        Return the appropriate serializer for the link termination model.
        """
        if obj._link_peer is not None:
            serializer = get_serializer_for_model(obj._link_peer, prefix=NESTED_SERIALIZER_PREFIX)
            context = {'request': self.context['request']}
            return serializer(obj._link_peer, context=context).data
        return None

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get__occupied(self, obj):
        return obj._occupied


class ConnectedEndpointSerializer(serializers.ModelSerializer):
    connected_endpoint_type = serializers.SerializerMethodField(read_only=True)
    connected_endpoint = serializers.SerializerMethodField(read_only=True)
    connected_endpoint_reachable = serializers.SerializerMethodField(read_only=True)

    def get_connected_endpoint_type(self, obj):
        if obj._path is not None and obj._path.destination is not None:
            return f'{obj._path.destination._meta.app_label}.{obj._path.destination._meta.model_name}'
        return None

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_connected_endpoint(self, obj):
        """
        Return the appropriate serializer for the type of connected object.
        """
        if obj._path is not None and obj._path.destination is not None:
            serializer = get_serializer_for_model(obj._path.destination, prefix=NESTED_SERIALIZER_PREFIX)
            context = {'request': self.context['request']}
            return serializer(obj._path.destination, context=context).data
        return None

    @swagger_serializer_method(serializer_or_field=serializers.BooleanField)
    def get_connected_endpoint_reachable(self, obj):
        if obj._path is not None:
            return obj._path.is_active
        return None


#
# Regions/sites
#

class RegionSerializer(NestedGroupModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:region-detail')
    parent = NestedRegionSerializer(required=False, allow_null=True, default=None)
    site_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Region
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'parent', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'site_count', '_depth',
        ]


class SiteGroupSerializer(NestedGroupModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:sitegroup-detail')
    parent = NestedSiteGroupSerializer(required=False, allow_null=True, default=None)
    site_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SiteGroup
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'parent', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'site_count', '_depth',
        ]


class SiteSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:site-detail')
    status = ChoiceField(choices=SiteStatusChoices, required=False)
    region = NestedRegionSerializer(required=False, allow_null=True)
    group = NestedSiteGroupSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    time_zone = TimeZoneSerializerField(required=False)
    asns = SerializedPKRelatedField(
        queryset=ASN.objects.all(),
        serializer=NestedASNSerializer,
        required=False,
        many=True
    )

    # Related object counts
    circuit_count = serializers.IntegerField(read_only=True)
    device_count = serializers.IntegerField(read_only=True)
    prefix_count = serializers.IntegerField(read_only=True)
    rack_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)
    vlan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Site
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'status', 'region', 'group', 'tenant', 'facility', 'time_zone',
            'description', 'physical_address', 'shipping_address', 'latitude', 'longitude', 'comments', 'asns', 'tags',
            'custom_fields', 'created', 'last_updated', 'circuit_count', 'device_count', 'prefix_count', 'rack_count',
            'virtualmachine_count', 'vlan_count',
        ]


#
# Racks
#

class LocationSerializer(NestedGroupModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:location-detail')
    site = NestedSiteSerializer()
    parent = NestedLocationSerializer(required=False, allow_null=True)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    rack_count = serializers.IntegerField(read_only=True)
    device_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Location
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'site', 'parent', 'tenant', 'description', 'tags', 'custom_fields',
            'created', 'last_updated', 'rack_count', 'device_count', '_depth',
        ]


class RackRoleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rackrole-detail')
    rack_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = RackRole
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'color', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'rack_count',
        ]


class RackSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rack-detail')
    site = NestedSiteSerializer()
    location = NestedLocationSerializer(required=False, allow_null=True, default=None)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    status = ChoiceField(choices=RackStatusChoices, required=False)
    role = NestedRackRoleSerializer(required=False, allow_null=True)
    type = ChoiceField(choices=RackTypeChoices, allow_blank=True, required=False)
    facility_id = serializers.CharField(max_length=50, allow_blank=True, allow_null=True, label='Facility ID',
                                        default=None)
    width = ChoiceField(choices=RackWidthChoices, required=False)
    outer_unit = ChoiceField(choices=RackDimensionUnitChoices, allow_blank=True, required=False)
    device_count = serializers.IntegerField(read_only=True)
    powerfeed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Rack
        fields = [
            'id', 'url', 'display', 'name', 'facility_id', 'site', 'location', 'tenant', 'status', 'role', 'serial',
            'asset_tag', 'type', 'width', 'u_height', 'desc_units', 'outer_width', 'outer_depth', 'outer_unit',
            'comments', 'tags', 'custom_fields', 'created', 'last_updated', 'device_count', 'powerfeed_count',
        ]


class RackUnitSerializer(serializers.Serializer):
    """
    A rack unit is an abstraction formed by the set (rack, position, face); it does not exist as a row in the database.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    face = ChoiceField(choices=DeviceFaceChoices, read_only=True)
    device = NestedDeviceSerializer(read_only=True)
    occupied = serializers.BooleanField(read_only=True)
    display = serializers.SerializerMethodField(read_only=True)

    def get_display(self, obj):
        return obj['name']


class RackReservationSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rackreservation-detail')
    rack = NestedRackSerializer()
    user = NestedUserSerializer()
    tenant = NestedTenantSerializer(required=False, allow_null=True)

    class Meta:
        model = RackReservation
        fields = [
            'id', 'url', 'display', 'rack', 'units', 'created', 'last_updated', 'user', 'tenant', 'description', 'tags',
            'custom_fields',
        ]


class RackElevationDetailFilterSerializer(serializers.Serializer):
    q = serializers.CharField(
        required=False,
        default=None
    )
    face = serializers.ChoiceField(
        choices=DeviceFaceChoices,
        default=DeviceFaceChoices.FACE_FRONT
    )
    render = serializers.ChoiceField(
        choices=RackElevationDetailRenderChoices,
        default=RackElevationDetailRenderChoices.RENDER_JSON
    )
    unit_width = serializers.IntegerField(
        default=ConfigItem('RACK_ELEVATION_DEFAULT_UNIT_WIDTH')
    )
    unit_height = serializers.IntegerField(
        default=ConfigItem('RACK_ELEVATION_DEFAULT_UNIT_HEIGHT')
    )
    legend_width = serializers.IntegerField(
        default=RACK_ELEVATION_LEGEND_WIDTH_DEFAULT
    )
    exclude = serializers.IntegerField(
        required=False,
        default=None
    )
    expand_devices = serializers.BooleanField(
        required=False,
        default=True
    )
    include_images = serializers.BooleanField(
        required=False,
        default=True
    )


#
# Device/module types
#

class ManufacturerSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:manufacturer-detail')
    devicetype_count = serializers.IntegerField(read_only=True)
    inventoryitem_count = serializers.IntegerField(read_only=True)
    platform_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Manufacturer
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'description', 'tags', 'custom_fields', 'created', 'last_updated',
            'devicetype_count', 'inventoryitem_count', 'platform_count',
        ]


class DeviceTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:devicetype-detail')
    manufacturer = NestedManufacturerSerializer()
    subdevice_role = ChoiceField(choices=SubdeviceRoleChoices, allow_blank=True, required=False)
    airflow = ChoiceField(choices=DeviceAirflowChoices, allow_blank=True, required=False)
    device_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceType
        fields = [
            'id', 'url', 'display', 'manufacturer', 'model', 'slug', 'part_number', 'u_height', 'is_full_depth',
            'subdevice_role', 'airflow', 'front_image', 'rear_image', 'comments', 'tags', 'custom_fields', 'created',
            'last_updated', 'device_count',
        ]


class ModuleTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:moduletype-detail')
    manufacturer = NestedManufacturerSerializer()
    # module_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ModuleType
        fields = [
            'id', 'url', 'display', 'manufacturer', 'model', 'part_number', 'comments', 'tags', 'custom_fields',
            'created', 'last_updated',
        ]


#
# Component templates
#

class ConsolePortTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:consoleporttemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = ConsolePortTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'description', 'created',
            'last_updated',
        ]


class ConsoleServerPortTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:consoleserverporttemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = ConsoleServerPortTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'description', 'created',
            'last_updated',
        ]


class PowerPortTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:powerporttemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=PowerPortTypeChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = PowerPortTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'maximum_draw',
            'allocated_draw', 'description', 'created', 'last_updated',
        ]


class PowerOutletTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:poweroutlettemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=PowerOutletTypeChoices,
        allow_blank=True,
        required=False
    )
    power_port = NestedPowerPortTemplateSerializer(
        required=False,
        allow_null=True
    )
    feed_leg = ChoiceField(
        choices=PowerOutletFeedLegChoices,
        allow_blank=True,
        required=False
    )

    class Meta:
        model = PowerOutletTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'power_port', 'feed_leg',
            'description', 'created', 'last_updated',
        ]


class InterfaceTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:interfacetemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(choices=InterfaceTypeChoices)

    class Meta:
        model = InterfaceTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'mgmt_only', 'description',
            'created', 'last_updated',
        ]


class RearPortTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rearporttemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(choices=PortTypeChoices)

    class Meta:
        model = RearPortTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'color', 'positions',
            'description', 'created', 'last_updated',
        ]


class FrontPortTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:frontporttemplate-detail')
    device_type = NestedDeviceTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    module_type = NestedModuleTypeSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(choices=PortTypeChoices)
    rear_port = NestedRearPortTemplateSerializer()

    class Meta:
        model = FrontPortTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'module_type', 'name', 'label', 'type', 'color', 'rear_port',
            'rear_port_position', 'description', 'created', 'last_updated',
        ]


class ModuleBayTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:modulebaytemplate-detail')
    device_type = NestedDeviceTypeSerializer()

    class Meta:
        model = ModuleBayTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'name', 'label', 'position', 'description', 'created',
            'last_updated',
        ]


class DeviceBayTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:devicebaytemplate-detail')
    device_type = NestedDeviceTypeSerializer()

    class Meta:
        model = DeviceBayTemplate
        fields = ['id', 'url', 'display', 'device_type', 'name', 'label', 'description', 'created', 'last_updated']


class InventoryItemTemplateSerializer(ValidatedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:inventoryitemtemplate-detail')
    device_type = NestedDeviceTypeSerializer()
    parent = serializers.PrimaryKeyRelatedField(
        queryset=InventoryItemTemplate.objects.all(),
        allow_null=True,
        default=None
    )
    role = NestedInventoryItemRoleSerializer(required=False, allow_null=True)
    manufacturer = NestedManufacturerSerializer(required=False, allow_null=True, default=None)
    component_type = ContentTypeField(
        queryset=ContentType.objects.filter(MODULAR_COMPONENT_TEMPLATE_MODELS),
        required=False,
        allow_null=True
    )
    component = serializers.SerializerMethodField(read_only=True)
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = InventoryItemTemplate
        fields = [
            'id', 'url', 'display', 'device_type', 'parent', 'name', 'label', 'role', 'manufacturer', 'part_id',
            'description', 'component_type', 'component_id', 'component', 'created', 'last_updated', '_depth',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_component(self, obj):
        if obj.component is None:
            return None
        serializer = get_serializer_for_model(obj.component, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(obj.component, context=context).data


#
# Devices
#

class DeviceRoleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:devicerole-detail')
    device_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeviceRole
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'color', 'vm_role', 'description', 'tags', 'custom_fields',
            'created', 'last_updated', 'device_count', 'virtualmachine_count',
        ]


class PlatformSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:platform-detail')
    manufacturer = NestedManufacturerSerializer(required=False, allow_null=True)
    device_count = serializers.IntegerField(read_only=True)
    virtualmachine_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Platform
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'manufacturer', 'napalm_driver', 'napalm_args', 'description',
            'tags', 'custom_fields', 'created', 'last_updated', 'device_count', 'virtualmachine_count',
        ]


class DeviceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:device-detail')
    device_type = NestedDeviceTypeSerializer()
    device_role = NestedDeviceRoleSerializer()
    tenant = NestedTenantSerializer(required=False, allow_null=True, default=None)
    platform = NestedPlatformSerializer(required=False, allow_null=True)
    site = NestedSiteSerializer()
    location = NestedLocationSerializer(required=False, allow_null=True, default=None)
    rack = NestedRackSerializer(required=False, allow_null=True, default=None)
    face = ChoiceField(choices=DeviceFaceChoices, allow_blank=True, default='')
    position = serializers.IntegerField(allow_null=True, label='Position (U)', min_value=1, default=None)
    status = ChoiceField(choices=DeviceStatusChoices, required=False)
    airflow = ChoiceField(choices=DeviceAirflowChoices, allow_blank=True, required=False)
    primary_ip = NestedIPAddressSerializer(read_only=True)
    primary_ip4 = NestedIPAddressSerializer(required=False, allow_null=True)
    primary_ip6 = NestedIPAddressSerializer(required=False, allow_null=True)
    parent_device = serializers.SerializerMethodField()
    cluster = NestedClusterSerializer(required=False, allow_null=True)
    virtual_chassis = NestedVirtualChassisSerializer(required=False, allow_null=True, default=None)
    vc_position = serializers.IntegerField(allow_null=True, max_value=255, min_value=0, default=None)

    class Meta:
        model = Device
        fields = [
            'id', 'url', 'display', 'name', 'device_type', 'device_role', 'tenant', 'platform', 'serial', 'asset_tag',
            'site', 'location', 'rack', 'position', 'face', 'parent_device', 'status', 'airflow', 'primary_ip',
            'primary_ip4', 'primary_ip6', 'cluster', 'virtual_chassis', 'vc_position', 'vc_priority', 'comments',
            'local_context_data', 'tags', 'custom_fields', 'created', 'last_updated',
        ]

    @swagger_serializer_method(serializer_or_field=NestedDeviceSerializer)
    def get_parent_device(self, obj):
        try:
            device_bay = obj.parent_bay
        except DeviceBay.DoesNotExist:
            return None
        context = {'request': self.context['request']}
        data = NestedDeviceSerializer(instance=device_bay.device, context=context).data
        data['device_bay'] = NestedDeviceBaySerializer(instance=device_bay, context=context).data
        return data


class ModuleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:module-detail')
    device = NestedDeviceSerializer()
    module_bay = NestedModuleBaySerializer()
    module_type = NestedModuleTypeSerializer()

    class Meta:
        model = Module
        fields = [
            'id', 'url', 'display', 'device', 'module_bay', 'module_type', 'serial', 'asset_tag', 'comments', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]


class DeviceWithConfigContextSerializer(DeviceSerializer):
    config_context = serializers.SerializerMethodField()

    class Meta(DeviceSerializer.Meta):
        fields = [
            'id', 'url', 'display', 'name', 'device_type', 'device_role', 'tenant', 'platform', 'serial', 'asset_tag',
            'site', 'location', 'rack', 'position', 'face', 'parent_device', 'status', 'airflow', 'primary_ip',
            'primary_ip4', 'primary_ip6', 'cluster', 'virtual_chassis', 'vc_position', 'vc_priority', 'comments',
            'local_context_data', 'tags', 'custom_fields', 'config_context', 'created', 'last_updated',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_config_context(self, obj):
        return obj.get_config_context()


class DeviceNAPALMSerializer(serializers.Serializer):
    method = serializers.DictField()


#
# Device components
#

class ConsoleServerPortSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:consoleserverport-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )
    speed = ChoiceField(
        choices=ConsolePortSpeedChoices,
        allow_null=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = ConsoleServerPort
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'speed', 'description',
            'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'connected_endpoint', 'connected_endpoint_type',
            'connected_endpoint_reachable', 'tags', 'custom_fields', 'created', 'last_updated', '_occupied',
        ]


class ConsolePortSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:consoleport-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(
        choices=ConsolePortTypeChoices,
        allow_blank=True,
        required=False
    )
    speed = ChoiceField(
        choices=ConsolePortSpeedChoices,
        allow_null=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = ConsolePort
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'speed', 'description',
            'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'connected_endpoint', 'connected_endpoint_type',
            'connected_endpoint_reachable', 'tags', 'custom_fields', 'created', 'last_updated', '_occupied',
        ]


class PowerOutletSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:poweroutlet-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(
        choices=PowerOutletTypeChoices,
        allow_blank=True,
        required=False
    )
    power_port = NestedPowerPortSerializer(
        required=False,
        allow_null=True
    )
    feed_leg = ChoiceField(
        choices=PowerOutletFeedLegChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(
        read_only=True
    )

    class Meta:
        model = PowerOutlet
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'power_port', 'feed_leg',
            'description', 'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'connected_endpoint',
            'connected_endpoint_type', 'connected_endpoint_reachable', 'tags', 'custom_fields', 'created',
            'last_updated', '_occupied',
        ]


class PowerPortSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:powerport-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(
        choices=PowerPortTypeChoices,
        allow_blank=True,
        required=False
    )
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = PowerPort
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'maximum_draw', 'allocated_draw',
            'description', 'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'connected_endpoint',
            'connected_endpoint_type', 'connected_endpoint_reachable', 'tags', 'custom_fields', 'created',
            'last_updated', '_occupied',
        ]


class InterfaceSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:interface-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(choices=InterfaceTypeChoices)
    parent = NestedInterfaceSerializer(required=False, allow_null=True)
    bridge = NestedInterfaceSerializer(required=False, allow_null=True)
    lag = NestedInterfaceSerializer(required=False, allow_null=True)
    mode = ChoiceField(choices=InterfaceModeChoices, required=False, allow_blank=True)
    duplex = ChoiceField(choices=InterfaceDuplexChoices, required=False, allow_blank=True)
    rf_role = ChoiceField(choices=WirelessRoleChoices, required=False, allow_blank=True)
    rf_channel = ChoiceField(choices=WirelessChannelChoices, required=False, allow_blank=True)
    untagged_vlan = NestedVLANSerializer(required=False, allow_null=True)
    tagged_vlans = SerializedPKRelatedField(
        queryset=VLAN.objects.all(),
        serializer=NestedVLANSerializer,
        required=False,
        many=True
    )
    vrf = NestedVRFSerializer(required=False, allow_null=True)
    cable = NestedCableSerializer(read_only=True)
    wireless_link = NestedWirelessLinkSerializer(read_only=True)
    wireless_lans = SerializedPKRelatedField(
        queryset=WirelessLAN.objects.all(),
        serializer=NestedWirelessLANSerializer,
        required=False,
        many=True
    )
    count_ipaddresses = serializers.IntegerField(read_only=True)
    count_fhrp_groups = serializers.IntegerField(read_only=True)

    class Meta:
        model = Interface
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'enabled', 'parent', 'bridge', 'lag',
            'mtu', 'mac_address', 'speed', 'duplex', 'wwn', 'mgmt_only', 'description', 'mode', 'rf_role', 'rf_channel',
            'rf_channel_frequency', 'rf_channel_width', 'tx_power', 'untagged_vlan', 'tagged_vlans', 'mark_connected',
            'cable', 'wireless_link', 'link_peer', 'link_peer_type', 'wireless_lans', 'vrf', 'connected_endpoint',
            'connected_endpoint_type', 'connected_endpoint_reachable', 'tags', 'custom_fields', 'created',
            'last_updated', 'count_ipaddresses', 'count_fhrp_groups', '_occupied',
        ]

    def validate(self, data):

        # Validate many-to-many VLAN assignments
        device = self.instance.device if self.instance else data.get('device')
        for vlan in data.get('tagged_vlans', []):
            if vlan.site not in [device.site, None]:
                raise serializers.ValidationError({
                    'tagged_vlans': f"VLAN {vlan} must belong to the same site as the interface's parent device, or "
                                    f"it must be global."
                })

        return super().validate(data)


class RearPortSerializer(NetBoxModelSerializer, LinkTerminationSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rearport-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(choices=PortTypeChoices)
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = RearPort
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'color', 'positions', 'description',
            'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'tags', 'custom_fields', 'created',
            'last_updated', '_occupied',
        ]


class FrontPortRearPortSerializer(WritableNestedSerializer):
    """
    NestedRearPortSerializer but with parent device omitted (since front and rear ports must belong to same device)
    """
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:rearport-detail')

    class Meta:
        model = RearPort
        fields = ['id', 'url', 'display', 'name', 'label']


class FrontPortSerializer(NetBoxModelSerializer, LinkTerminationSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:frontport-detail')
    device = NestedDeviceSerializer()
    module = ComponentNestedModuleSerializer(
        required=False,
        allow_null=True
    )
    type = ChoiceField(choices=PortTypeChoices)
    rear_port = FrontPortRearPortSerializer()
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = FrontPort
        fields = [
            'id', 'url', 'display', 'device', 'module', 'name', 'label', 'type', 'color', 'rear_port',
            'rear_port_position', 'description', 'mark_connected', 'cable', 'link_peer', 'link_peer_type', 'tags',
            'custom_fields', 'created', 'last_updated', '_occupied',
        ]


class ModuleBaySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:modulebay-detail')
    device = NestedDeviceSerializer()
    installed_module = ModuleBayNestedModuleSerializer(required=False, allow_null=True)

    class Meta:
        model = ModuleBay
        fields = [
            'id', 'url', 'display', 'device', 'name', 'installed_module', 'label', 'position', 'description', 'tags', 'custom_fields',
            'created', 'last_updated',
        ]


class DeviceBaySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:devicebay-detail')
    device = NestedDeviceSerializer()
    installed_device = NestedDeviceSerializer(required=False, allow_null=True)

    class Meta:
        model = DeviceBay
        fields = [
            'id', 'url', 'display', 'device', 'name', 'label', 'description', 'installed_device', 'tags',
            'custom_fields', 'created', 'last_updated',
        ]


class InventoryItemSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:inventoryitem-detail')
    device = NestedDeviceSerializer()
    parent = serializers.PrimaryKeyRelatedField(queryset=InventoryItem.objects.all(), allow_null=True, default=None)
    role = NestedInventoryItemRoleSerializer(required=False, allow_null=True)
    manufacturer = NestedManufacturerSerializer(required=False, allow_null=True, default=None)
    component_type = ContentTypeField(
        queryset=ContentType.objects.filter(MODULAR_COMPONENT_MODELS),
        required=False,
        allow_null=True
    )
    component = serializers.SerializerMethodField(read_only=True)
    _depth = serializers.IntegerField(source='level', read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            'id', 'url', 'display', 'device', 'parent', 'name', 'label', 'role', 'manufacturer', 'part_id', 'serial',
            'asset_tag', 'discovered', 'description', 'component_type', 'component_id', 'component', 'tags',
            'custom_fields', 'created', 'last_updated', '_depth',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_component(self, obj):
        if obj.component is None:
            return None
        serializer = get_serializer_for_model(obj.component, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(obj.component, context=context).data


#
# Device component roles
#

class InventoryItemRoleSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:inventoryitemrole-detail')
    inventoryitem_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = InventoryItemRole
        fields = [
            'id', 'url', 'display', 'name', 'slug', 'color', 'description', 'tags', 'custom_fields', 'created',
            'last_updated', 'inventoryitem_count',
        ]


#
# Cables
#

class CableSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:cable-detail')
    termination_a_type = ContentTypeField(
        queryset=ContentType.objects.filter(CABLE_TERMINATION_MODELS)
    )
    termination_b_type = ContentTypeField(
        queryset=ContentType.objects.filter(CABLE_TERMINATION_MODELS)
    )
    termination_a = serializers.SerializerMethodField(read_only=True)
    termination_b = serializers.SerializerMethodField(read_only=True)
    status = ChoiceField(choices=LinkStatusChoices, required=False)
    tenant = NestedTenantSerializer(required=False, allow_null=True)
    length_unit = ChoiceField(choices=CableLengthUnitChoices, allow_blank=True, required=False)

    class Meta:
        model = Cable
        fields = [
            'id', 'url', 'display', 'termination_a_type', 'termination_a_id', 'termination_a', 'termination_b_type',
            'termination_b_id', 'termination_b', 'type', 'status', 'tenant', 'label', 'color', 'length', 'length_unit',
            'tags', 'custom_fields', 'created', 'last_updated',
        ]

    def _get_termination(self, obj, side):
        """
        Serialize a nested representation of a termination.
        """
        if side.lower() not in ['a', 'b']:
            raise ValueError("Termination side must be either A or B.")
        termination = getattr(obj, 'termination_{}'.format(side.lower()))
        if termination is None:
            return None
        serializer = get_serializer_for_model(termination, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        data = serializer(termination, context=context).data

        return data

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_termination_a(self, obj):
        return self._get_termination(obj, 'a')

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_termination_b(self, obj):
        return self._get_termination(obj, 'b')


class TracedCableSerializer(serializers.ModelSerializer):
    """
    Used only while tracing a cable path.
    """
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:cable-detail')

    class Meta:
        model = Cable
        fields = [
            'id', 'url', 'type', 'status', 'label', 'color', 'length', 'length_unit',
        ]


class CablePathSerializer(serializers.ModelSerializer):
    origin_type = ContentTypeField(read_only=True)
    origin = serializers.SerializerMethodField(read_only=True)
    destination_type = ContentTypeField(read_only=True)
    destination = serializers.SerializerMethodField(read_only=True)
    path = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CablePath
        fields = [
            'id', 'origin_type', 'origin', 'destination_type', 'destination', 'path', 'is_active', 'is_split',
        ]

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_origin(self, obj):
        """
        Return the appropriate serializer for the origin.
        """
        serializer = get_serializer_for_model(obj.origin, prefix=NESTED_SERIALIZER_PREFIX)
        context = {'request': self.context['request']}
        return serializer(obj.origin, context=context).data

    @swagger_serializer_method(serializer_or_field=serializers.DictField)
    def get_destination(self, obj):
        """
        Return the appropriate serializer for the destination, if any.
        """
        if obj.destination_id is not None:
            serializer = get_serializer_for_model(obj.destination, prefix=NESTED_SERIALIZER_PREFIX)
            context = {'request': self.context['request']}
            return serializer(obj.destination, context=context).data
        return None

    @swagger_serializer_method(serializer_or_field=serializers.ListField)
    def get_path(self, obj):
        ret = []
        for node in obj.get_path():
            serializer = get_serializer_for_model(node, prefix=NESTED_SERIALIZER_PREFIX)
            context = {'request': self.context['request']}
            ret.append(serializer(node, context=context).data)
        return ret


#
# Virtual chassis
#

class VirtualChassisSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:virtualchassis-detail')
    master = NestedDeviceSerializer(required=False)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = VirtualChassis
        fields = [
            'id', 'url', 'display', 'name', 'domain', 'master', 'tags', 'custom_fields', 'member_count',
            'created', 'last_updated',
        ]


#
# Power panels
#

class PowerPanelSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:powerpanel-detail')
    site = NestedSiteSerializer()
    location = NestedLocationSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    powerfeed_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = PowerPanel
        fields = [
            'id', 'url', 'display', 'site', 'location', 'name', 'tags', 'custom_fields', 'powerfeed_count',
            'created', 'last_updated',
        ]


class PowerFeedSerializer(NetBoxModelSerializer, LinkTerminationSerializer, ConnectedEndpointSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='dcim-api:powerfeed-detail')
    power_panel = NestedPowerPanelSerializer()
    rack = NestedRackSerializer(
        required=False,
        allow_null=True,
        default=None
    )
    type = ChoiceField(
        choices=PowerFeedTypeChoices,
        default=PowerFeedTypeChoices.TYPE_PRIMARY
    )
    status = ChoiceField(
        choices=PowerFeedStatusChoices,
        default=PowerFeedStatusChoices.STATUS_ACTIVE
    )
    supply = ChoiceField(
        choices=PowerFeedSupplyChoices,
        default=PowerFeedSupplyChoices.SUPPLY_AC
    )
    phase = ChoiceField(
        choices=PowerFeedPhaseChoices,
        default=PowerFeedPhaseChoices.PHASE_SINGLE
    )
    cable = NestedCableSerializer(read_only=True)

    class Meta:
        model = PowerFeed
        fields = [
            'id', 'url', 'display', 'power_panel', 'rack', 'name', 'status', 'type', 'supply', 'phase', 'voltage',
            'amperage', 'max_utilization', 'comments', 'mark_connected', 'cable', 'link_peer', 'link_peer_type',
            'connected_endpoint', 'connected_endpoint_type', 'connected_endpoint_reachable', 'tags', 'custom_fields',
            'created', 'last_updated', '_occupied',
        ]
