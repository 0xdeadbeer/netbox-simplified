from collections import OrderedDict

import yaml
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, ProtectedError
from django.urls import reverse
from django.utils.safestring import mark_safe

from dcim.choices import *
from dcim.constants import *
from extras.models import ConfigContextModel
from extras.querysets import ConfigContextModelQuerySet
from netbox.config import ConfigItem
from netbox.models import OrganizationalModel, NetBoxModel
from utilities.choices import ColorChoices
from utilities.fields import ColorField, NaturalOrderingField
from .device_components import *


__all__ = (
    'Device',
    'DeviceRole',
    'DeviceType',
    'Manufacturer',
    'Module',
    'ModuleType',
    'Platform',
    'VirtualChassis',
)


#
# Device Types
#

class Manufacturer(OrganizationalModel):
    """
    A Manufacturer represents a company which produces hardware devices; for example, Juniper or Dell.
    """
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    description = models.CharField(
        max_length=200,
        blank=True
    )

    # Generic relations
    contacts = GenericRelation(
        to='tenancy.ContactAssignment'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:manufacturer', args=[self.pk])


class DeviceType(NetBoxModel):
    """
    A DeviceType represents a particular make (Manufacturer) and model of device. It specifies rack height and depth, as
    well as high-level functional role(s).

    Each DeviceType can have an arbitrary number of component templates assigned to it, which define console, power, and
    interface objects. For example, a Juniper EX4300-48T DeviceType would have:

      * 1 ConsolePortTemplate
      * 2 PowerPortTemplates
      * 48 InterfaceTemplates

    When a new Device of this type is created, the appropriate console, power, and interface objects (as defined by the
    DeviceType) are automatically created as well.
    """
    manufacturer = models.ForeignKey(
        to='dcim.Manufacturer',
        on_delete=models.PROTECT,
        related_name='device_types'
    )
    model = models.CharField(
        max_length=100
    )
    slug = models.SlugField(
        max_length=100
    )
    part_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Discrete part number (optional)'
    )
    u_height = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='Height (U)'
    )
    is_full_depth = models.BooleanField(
        default=True,
        verbose_name='Is full depth',
        help_text='Device consumes both front and rear rack faces'
    )
    subdevice_role = models.CharField(
        max_length=50,
        choices=SubdeviceRoleChoices,
        blank=True,
        verbose_name='Parent/child status',
        help_text='Parent devices house child devices in device bays. Leave blank '
                  'if this device type is neither a parent nor a child.'
    )
    airflow = models.CharField(
        max_length=50,
        choices=DeviceAirflowChoices,
        blank=True
    )
    front_image = models.ImageField(
        upload_to='devicetype-images',
        blank=True
    )
    rear_image = models.ImageField(
        upload_to='devicetype-images',
        blank=True
    )
    comments = models.TextField(
        blank=True
    )

    clone_fields = [
        'manufacturer', 'u_height', 'is_full_depth', 'subdevice_role', 'airflow',
    ]

    class Meta:
        ordering = ['manufacturer', 'model']
        unique_together = [
            ['manufacturer', 'model'],
            ['manufacturer', 'slug'],
        ]

    def __str__(self):
        return self.model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Save a copy of u_height for validation in clean()
        self._original_u_height = self.u_height

        # Save references to the original front/rear images
        self._original_front_image = self.front_image
        self._original_rear_image = self.rear_image

    def get_absolute_url(self):
        return reverse('dcim:devicetype', args=[self.pk])

    def to_yaml(self):
        data = OrderedDict((
            ('manufacturer', self.manufacturer.name),
            ('model', self.model),
            ('slug', self.slug),
            ('part_number', self.part_number),
            ('u_height', self.u_height),
            ('is_full_depth', self.is_full_depth),
            ('subdevice_role', self.subdevice_role),
            ('airflow', self.airflow),
            ('comments', self.comments),
        ))

        # Component templates
        if self.consoleporttemplates.exists():
            data['console-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.consoleporttemplates.all()
            ]
        if self.consoleserverporttemplates.exists():
            data['console-server-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.consoleserverporttemplates.all()
            ]
        if self.powerporttemplates.exists():
            data['power-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'maximum_draw': c.maximum_draw,
                    'allocated_draw': c.allocated_draw,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.powerporttemplates.all()
            ]
        if self.poweroutlettemplates.exists():
            data['power-outlets'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'power_port': c.power_port.name if c.power_port else None,
                    'feed_leg': c.feed_leg,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.poweroutlettemplates.all()
            ]
        if self.interfacetemplates.exists():
            data['interfaces'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'mgmt_only': c.mgmt_only,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.interfacetemplates.all()
            ]
        if self.frontporttemplates.exists():
            data['front-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'rear_port': c.rear_port.name,
                    'rear_port_position': c.rear_port_position,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.frontporttemplates.all()
            ]
        if self.rearporttemplates.exists():
            data['rear-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'positions': c.positions,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.rearporttemplates.all()
            ]
        if self.modulebaytemplates.exists():
            data['module-bays'] = [
                {
                    'name': c.name,
                    'label': c.label,
                    'position': c.position,
                    'description': c.description,
                }
                for c in self.modulebaytemplates.all()
            ]
        if self.devicebaytemplates.exists():
            data['device-bays'] = [
                {
                    'name': c.name,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.devicebaytemplates.all()
            ]

        return yaml.dump(dict(data), sort_keys=False)

    def clean(self):
        super().clean()

        # If editing an existing DeviceType to have a larger u_height, first validate that *all* instances of it have
        # room to expand within their racks. This validation will impose a very high performance penalty when there are
        # many instances to check, but increasing the u_height of a DeviceType should be a very rare occurrence.
        if self.pk and self.u_height > self._original_u_height:
            for d in Device.objects.filter(device_type=self, position__isnull=False):
                face_required = None if self.is_full_depth else d.face
                u_available = d.rack.get_available_units(
                    u_height=self.u_height,
                    rack_face=face_required,
                    exclude=[d.pk]
                )
                if d.position not in u_available:
                    raise ValidationError({
                        'u_height': "Device {} in rack {} does not have sufficient space to accommodate a height of "
                                    "{}U".format(d, d.rack, self.u_height)
                    })

        # If modifying the height of an existing DeviceType to 0U, check for any instances assigned to a rack position.
        elif self.pk and self._original_u_height > 0 and self.u_height == 0:
            racked_instance_count = Device.objects.filter(
                device_type=self,
                position__isnull=False
            ).count()
            if racked_instance_count:
                url = f"{reverse('dcim:device_list')}?manufactuer_id={self.manufacturer_id}&device_type_id={self.pk}"
                raise ValidationError({
                    'u_height': mark_safe(
                        f'Unable to set 0U height: Found <a href="{url}">{racked_instance_count} instances</a> already '
                        f'mounted within racks.'
                    )
                })

        if (
                self.subdevice_role != SubdeviceRoleChoices.ROLE_PARENT
        ) and self.devicebaytemplates.count():
            raise ValidationError({
                'subdevice_role': "Must delete all device bay templates associated with this device before "
                                  "declassifying it as a parent device."
            })

        if self.u_height and self.subdevice_role == SubdeviceRoleChoices.ROLE_CHILD:
            raise ValidationError({
                'u_height': "Child device types must be 0U."
            })

    def save(self, *args, **kwargs):
        ret = super().save(*args, **kwargs)

        # Delete any previously uploaded image files that are no longer in use
        if self.front_image != self._original_front_image:
            self._original_front_image.delete(save=False)
        if self.rear_image != self._original_rear_image:
            self._original_rear_image.delete(save=False)

        return ret

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        # Delete any uploaded image files
        if self.front_image:
            self.front_image.delete(save=False)
        if self.rear_image:
            self.rear_image.delete(save=False)

    @property
    def is_parent_device(self):
        return self.subdevice_role == SubdeviceRoleChoices.ROLE_PARENT

    @property
    def is_child_device(self):
        return self.subdevice_role == SubdeviceRoleChoices.ROLE_CHILD


class ModuleType(NetBoxModel):
    """
    A ModuleType represents a hardware element that can be installed within a device and which houses additional
    components; for example, a line card within a chassis-based switch such as the Cisco Catalyst 6500. Like a
    DeviceType, each ModuleType can have console, power, interface, and pass-through port templates assigned to it. It
    cannot, however house device bays or module bays.
    """
    manufacturer = models.ForeignKey(
        to='dcim.Manufacturer',
        on_delete=models.PROTECT,
        related_name='module_types'
    )
    model = models.CharField(
        max_length=100
    )
    part_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Discrete part number (optional)'
    )
    comments = models.TextField(
        blank=True
    )

    # Generic relations
    images = GenericRelation(
        to='extras.ImageAttachment'
    )

    clone_fields = ('manufacturer',)

    class Meta:
        ordering = ('manufacturer', 'model')
        unique_together = (
            ('manufacturer', 'model'),
        )

    def __str__(self):
        return self.model

    def get_absolute_url(self):
        return reverse('dcim:moduletype', args=[self.pk])

    def to_yaml(self):
        data = OrderedDict((
            ('manufacturer', self.manufacturer.name),
            ('model', self.model),
            ('part_number', self.part_number),
            ('comments', self.comments),
        ))

        # Component templates
        if self.consoleporttemplates.exists():
            data['console-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.consoleporttemplates.all()
            ]
        if self.consoleserverporttemplates.exists():
            data['console-server-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.consoleserverporttemplates.all()
            ]
        if self.powerporttemplates.exists():
            data['power-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'maximum_draw': c.maximum_draw,
                    'allocated_draw': c.allocated_draw,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.powerporttemplates.all()
            ]
        if self.poweroutlettemplates.exists():
            data['power-outlets'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'power_port': c.power_port.name if c.power_port else None,
                    'feed_leg': c.feed_leg,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.poweroutlettemplates.all()
            ]
        if self.interfacetemplates.exists():
            data['interfaces'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'mgmt_only': c.mgmt_only,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.interfacetemplates.all()
            ]
        if self.frontporttemplates.exists():
            data['front-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'rear_port': c.rear_port.name,
                    'rear_port_position': c.rear_port_position,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.frontporttemplates.all()
            ]
        if self.rearporttemplates.exists():
            data['rear-ports'] = [
                {
                    'name': c.name,
                    'type': c.type,
                    'positions': c.positions,
                    'label': c.label,
                    'description': c.description,
                }
                for c in self.rearporttemplates.all()
            ]

        return yaml.dump(dict(data), sort_keys=False)


#
# Devices
#

class DeviceRole(OrganizationalModel):
    """
    Devices are organized by functional role; for example, "Core Switch" or "File Server". Each DeviceRole is assigned a
    color to be used when displaying rack elevations. The vm_role field determines whether the role is applicable to
    virtual machines as well.
    """
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    color = ColorField(
        default=ColorChoices.COLOR_GREY
    )
    vm_role = models.BooleanField(
        default=True,
        verbose_name='VM Role',
        help_text='Virtual machines may be assigned to this role'
    )
    description = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:devicerole', args=[self.pk])


class Platform(OrganizationalModel):
    """
    Platform refers to the software or firmware running on a Device. For example, "Cisco IOS-XR" or "Juniper Junos".
    NetBox uses Platforms to determine how to interact with devices when pulling inventory data or other information by
    specifying a NAPALM driver.
    """
    name = models.CharField(
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    manufacturer = models.ForeignKey(
        to='dcim.Manufacturer',
        on_delete=models.PROTECT,
        related_name='platforms',
        blank=True,
        null=True,
        help_text='Optionally limit this platform to devices of a certain manufacturer'
    )
    napalm_driver = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='NAPALM driver',
        help_text='The name of the NAPALM driver to use when interacting with devices'
    )
    napalm_args = models.JSONField(
        blank=True,
        null=True,
        verbose_name='NAPALM arguments',
        help_text='Additional arguments to pass when initiating the NAPALM driver (JSON format)'
    )
    description = models.CharField(
        max_length=200,
        blank=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:platform', args=[self.pk])


class Device(NetBoxModel, ConfigContextModel):
    """
    A Device represents a piece of physical hardware mounted within a Rack. Each Device is assigned a DeviceType,
    DeviceRole, and (optionally) a Platform. Device names are not required, however if one is set it must be unique.

    Each Device must be assigned to a site, and optionally to a rack within that site. Associating a device with a
    particular rack face or unit is optional (for example, vertically mounted PDUs do not consume rack units).

    When a new Device is created, console/power/interface/device bay components are created along with it as dictated
    by the component templates assigned to its DeviceType. Components can also be added, modified, or deleted after the
    creation of a Device.
    """
    name = models.CharField(
        max_length=64,
        blank=True,
        null=True
    )
    _name = NaturalOrderingField(
        target_field='name',
        max_length=100,
        blank=True,
        null=True
    )

    objects = ConfigContextModelQuerySet.as_manager()

    class Meta:
        ordering = ('_name', 'pk')  # Name may be null
        unique_together = (
            ('name'),  # See validate_unique below
        )

    def __str__(self):
        if self.name and self.asset_tag:
            return f'{self.name} ({self.asset_tag})'
        elif self.name:
            return self.name
        
        return super().__str__()

    def get_absolute_url(self):
        return reverse('dcim:device', args=[self.pk])

    def validate_unique(self, exclude=None):

        # Check for a duplicate name on a device assigned to the same Site and no Tenant. This is necessary
        # because Django does not consider two NULL fields to be equal, and thus will not trigger a violation
        # of the uniqueness constraint without manual intervention.
        if self.name:
            if Device.objects.exclude(pk=self.pk).filter(
                    name=self.name
            ):
                raise ValidationError({
                    'name': 'A device with this name already exists.'
                })

        super().validate_unique(exclude)

    def clean(self):
        super().clean()

    def save(self, *args, **kwargs):
        is_new = not bool(self.pk)

        # Inherit airflow attribute from DeviceType if not set
        if is_new and not self.airflow:
            self.airflow = self.device_type.airflow

        super().save(*args, **kwargs)

        # If this is a new Device, instantiate all of the related components per the DeviceType definition
        if is_new:
            # Avoid bulk_create to handle MPTT
            for x in self.device_type.inventoryitemtemplates.all():
                x.instantiate(device=self).save()

        # Update Site and Rack assignment for any child Devices
        devices = Device.objects.filter(parent_bay__device=self)
        for device in devices:
            device.site = self.site
            device.rack = self.rack
            device.save()

    @property
    def identifier(self):
        """
        Return the device name if set; otherwise return the Device's primary key as {pk}
        """
        if self.name is not None:
            return self.name
        return '{{{}}}'.format(self.pk)

    @property
    def primary_ip(self):
        if ConfigItem('PREFER_IPV4')() and self.primary_ip4:
            return self.primary_ip4
        elif self.primary_ip6:
            return self.primary_ip6
        elif self.primary_ip4:
            return self.primary_ip4
        else:
            return None

    @property
    def interfaces_count(self):
        return self.vc_interfaces().count()

    def get_vc_master(self):
        """
        If this Device is a VirtualChassis member, return the VC master. Otherwise, return None.
        """
        return self.virtual_chassis.master if self.virtual_chassis else None

    def vc_interfaces(self, if_master=True):
        """
        Return a QuerySet matching all Interfaces assigned to this Device or, if this Device is a VC master, to another
        Device belonging to the same VirtualChassis.

        :param if_master: If True, return VC member interfaces only if this Device is the VC master.
        """
        filter = Q(device=self)
        if self.virtual_chassis and (self.virtual_chassis.master == self or not if_master):
            filter |= Q(device__virtual_chassis=self.virtual_chassis, mgmt_only=False)
        return Interface.objects.filter(filter)

    def get_cables(self, pk_list=False):
        """
        Return a QuerySet or PK list matching all Cables connected to a component of this Device.
        """
        from .cables import Cable
        cable_pks = []
        for component_model in [
            ConsolePort, ConsoleServerPort, PowerPort, PowerOutlet, Interface, FrontPort, RearPort
        ]:
            cable_pks += component_model.objects.filter(
                device=self, cable__isnull=False
            ).values_list('cable', flat=True)
        if pk_list:
            return cable_pks
        return Cable.objects.filter(pk__in=cable_pks)

    def get_children(self):
        """
        Return the set of child Devices installed in DeviceBays within this Device.
        """
        return Device.objects.filter(parent_bay__device=self.pk)

    def get_status_color(self):
        return DeviceStatusChoices.colors.get(self.status)


class Module(NetBoxModel, ConfigContextModel):
    """
    A Module represents a field-installable component within a Device which may itself hold multiple device components
    (for example, a line card within a chassis switch). Modules are instantiated from ModuleTypes.
    """
    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.CASCADE,
        related_name='modules'
    )
    module_bay = models.OneToOneField(
        to='dcim.ModuleBay',
        on_delete=models.CASCADE,
        related_name='installed_module'
    )
    module_type = models.ForeignKey(
        to='dcim.ModuleType',
        on_delete=models.PROTECT,
        related_name='instances'
    )
    serial = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Serial number'
    )
    asset_tag = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Asset tag',
        help_text='A unique tag used to identify this device'
    )
    comments = models.TextField(
        blank=True
    )

    clone_fields = ('device', 'module_type')

    class Meta:
        ordering = ('module_bay',)

    def __str__(self):
        return f'{self.module_bay.name}: {self.module_type} ({self.pk})'

    def get_absolute_url(self):
        return reverse('dcim:module', args=[self.pk])

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        super().save(*args, **kwargs)

        adopt_components = getattr(self, '_adopt_components', False)
        disable_replication = getattr(self, '_disable_replication', False)

        # We skip adding components if the module is being edited or
        # both replication and component adoption is disabled
        if not is_new or (disable_replication and not adopt_components):
            return

        # Iterate all component types
        for templates, component_attribute, component_model in [
            ("consoleporttemplates", "consoleports", ConsolePort),
            ("consoleserverporttemplates", "consoleserverports", ConsoleServerPort),
            ("interfacetemplates", "interfaces", Interface),
            ("powerporttemplates", "powerports", PowerPort),
            ("poweroutlettemplates", "poweroutlets", PowerOutlet),
            ("rearporttemplates", "rearports", RearPort),
            ("frontporttemplates", "frontports", FrontPort)
        ]:
            create_instances = []
            update_instances = []

            # Prefetch installed components
            installed_components = {
                component.name: component for component in getattr(self.device, component_attribute).filter(module__isnull=True)
            }

            # Get the template for the module type.
            for template in getattr(self.module_type, templates).all():
                template_instance = template.instantiate(device=self.device, module=self)

                if adopt_components:
                    existing_item = installed_components.get(template_instance.name)

                    # Check if there's a component with the same name already
                    if existing_item:
                        # Assign it to the module
                        existing_item.module = self
                        update_instances.append(existing_item)
                        continue

                # Only create new components if replication is enabled
                if not disable_replication:
                    create_instances.append(template_instance)

            component_model.objects.bulk_create(create_instances)
            component_model.objects.bulk_update(update_instances, ['module'])


#
# Virtual chassis
#

class VirtualChassis(NetBoxModel):
    """
    A collection of Devices which operate with a shared control plane (e.g. a switch stack).
    """
    master = models.OneToOneField(
        to='Device',
        on_delete=models.PROTECT,
        related_name='vc_master_for',
        blank=True,
        null=True
    )
    name = models.CharField(
        max_length=64
    )
    domain = models.CharField(
        max_length=30,
        blank=True
    )

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'virtual chassis'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:virtualchassis', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Verify that the selected master device has been assigned to this VirtualChassis. (Skip when creating a new
        # VirtualChassis.)
        if self.pk and self.master and self.master not in self.members.all():
            raise ValidationError({
                'master': f"The selected master ({self.master}) is not assigned to this virtual chassis."
            })

    def delete(self, *args, **kwargs):

        # Check for LAG interfaces split across member chassis
        interfaces = Interface.objects.filter(
            device__in=self.members.all(),
            lag__isnull=False
        ).exclude(
            lag__device=F('device')
        )
        if interfaces:
            raise ProtectedError(
                f"Unable to delete virtual chassis {self}. There are member interfaces which form a cross-chassis LAG",
                interfaces
            )

        return super().delete(*args, **kwargs)
