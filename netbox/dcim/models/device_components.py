from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

from dcim.choices import *
from dcim.constants import *
from dcim.fields import MACAddressField, WWNField
from dcim.svg import CableTraceSVG
from netbox.models import OrganizationalModel, NetBoxModel
from utilities.choices import ColorChoices
from utilities.fields import ColorField, NaturalOrderingField
from utilities.mptt import TreeManager
from utilities.ordering import naturalize_interface
from utilities.query_functions import CollateAsChar
from wireless.choices import *
from wireless.utils import get_channel_attr


__all__ = (
    'BaseInterface',
    'LinkTermination',
    'ConsolePort',
    'ConsoleServerPort',
    'DeviceBay',
    'FrontPort',
    'Interface',
    'InventoryItem',
    'InventoryItemRole',
    'ModuleBay',
    'PathEndpoint',
    'PowerOutlet',
    'PowerPort',
    'RearPort',
)


class ComponentModel(NetBoxModel):
    """
    An abstract model inherited by any model which has a parent Device.
    """
    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    name = models.CharField(
        max_length=64
    )
    _name = NaturalOrderingField(
        target_field='name',
        max_length=100,
        blank=True
    )
    label = models.CharField(
        max_length=64,
        blank=True,
        help_text="Physical label"
    )
    description = models.CharField(
        max_length=200,
        blank=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        if self.label:
            return f"{self.name} ({self.label})"
        return self.name

    def to_objectchange(self, action):
        objectchange = super().to_objectchange(action)
        objectchange.related_object = self.device
        return objectchange

    @property
    def parent_object(self):
        return self.device


class ModularComponentModel(ComponentModel):
    module = models.ForeignKey(
        to='dcim.Module',
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        blank=True,
        null=True
    )
    inventory_items = GenericRelation(
        to='dcim.InventoryItem',
        content_type_field='component_type',
        object_id_field='component_id'
    )

    class Meta:
        abstract = True


class LinkTermination(models.Model):
    """
    An abstract model inherited by all models to which a Cable, WirelessLink, or other such link can terminate. Examples
    include most device components, CircuitTerminations, and PowerFeeds. The `cable` and `wireless_link` fields
    reference the attached Cable or WirelessLink instance, respectively.

    `_link_peer` is a GenericForeignKey used to cache the far-end LinkTermination on the local instance; this is a
    shortcut to referencing `instance.link.termination_b`, for example.
    """
    cable = models.ForeignKey(
        to='dcim.Cable',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True
    )
    _link_peer_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True
    )
    _link_peer_id = models.PositiveBigIntegerField(
        blank=True,
        null=True
    )
    _link_peer = GenericForeignKey(
        ct_field='_link_peer_type',
        fk_field='_link_peer_id'
    )
    mark_connected = models.BooleanField(
        default=False,
        help_text="Treat as if a cable is connected"
    )

    # Generic relations to Cable. These ensure that an attached Cable is deleted if the terminated object is deleted.
    _cabled_as_a = GenericRelation(
        to='dcim.Cable',
        content_type_field='termination_a_type',
        object_id_field='termination_a_id'
    )
    _cabled_as_b = GenericRelation(
        to='dcim.Cable',
        content_type_field='termination_b_type',
        object_id_field='termination_b_id'
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()

        if self.mark_connected and self.cable_id:
            raise ValidationError({
                "mark_connected": "Cannot mark as connected with a cable attached."
            })

    def get_link_peer(self):
        return self._link_peer

    @property
    def _occupied(self):
        return bool(self.mark_connected or self.cable_id)

    @property
    def parent_object(self):
        raise NotImplementedError("CableTermination models must implement parent_object()")

    @property
    def link(self):
        """
        Generic wrapper for a Cable, WirelessLink, or some other relation to a connected termination.
        """
        return self.cable


class PathEndpoint(models.Model):
    """
    An abstract model inherited by any CableTermination subclass which represents the end of a CablePath; specifically,
    these include ConsolePort, ConsoleServerPort, PowerPort, PowerOutlet, Interface, and PowerFeed.

    `_path` references the CablePath originating from this instance, if any. It is set or cleared by the receivers in
    dcim.signals in response to changes in the cable path, and complements the `origin` GenericForeignKey field on the
    CablePath model. `_path` should not be accessed directly; rather, use the `path` property.

    `connected_endpoint()` is a convenience method for returning the destination of the associated CablePath, if any.
    """
    _path = models.ForeignKey(
        to='dcim.CablePath',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    def trace(self):
        origin = self
        path = []

        # Construct the complete path
        while origin is not None:

            if origin._path is None:
                break

            path.extend([origin, *origin._path.get_path()])
            while (len(path) + 1) % 3:
                # Pad to ensure we have complete three-tuples (e.g. for paths that end at a non-connected FrontPort)
                path.append(None)
            path.append(origin._path.destination)

            # Check for bridge interface to continue the trace
            origin = getattr(origin._path.destination, 'bridge', None)

        # Return the path as a list of three-tuples (A termination, cable, B termination)
        return list(zip(*[iter(path)] * 3))

    def get_trace_svg(self, base_url=None, width=None):
        if width is not None:
            trace = CableTraceSVG(self, base_url=base_url, width=width)
        else:
            trace = CableTraceSVG(self, base_url=base_url)
        return trace.render()

    @property
    def path(self):
        return self._path

    @property
    def connected_endpoint(self):
        """
        Caching accessor for the attached CablePath's destination (if any)
        """
        if not hasattr(self, '_connected_endpoint'):
            self._connected_endpoint = self._path.destination if self._path else None
        return self._connected_endpoint


#
# Console components
#

class ConsolePort(ModularComponentModel, LinkTermination, PathEndpoint):
    """
    A physical console port within a Device. ConsolePorts connect to ConsoleServerPorts.
    """
    type = models.CharField(
        max_length=50,
        choices=ConsolePortTypeChoices,
        blank=True,
        help_text='Physical port type'
    )
    speed = models.PositiveIntegerField(
        choices=ConsolePortSpeedChoices,
        blank=True,
        null=True,
        help_text='Port speed in bits per second'
    )

    clone_fields = ['device', 'type', 'speed']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:consoleport', kwargs={'pk': self.pk})


class ConsoleServerPort(ModularComponentModel, LinkTermination, PathEndpoint):
    """
    A physical port within a Device (typically a designated console server) which provides access to ConsolePorts.
    """
    type = models.CharField(
        max_length=50,
        choices=ConsolePortTypeChoices,
        blank=True,
        help_text='Physical port type'
    )
    speed = models.PositiveIntegerField(
        choices=ConsolePortSpeedChoices,
        blank=True,
        null=True,
        help_text='Port speed in bits per second'
    )

    clone_fields = ['device', 'type', 'speed']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:consoleserverport', kwargs={'pk': self.pk})


#
# Power components
#

class PowerPort(ModularComponentModel, LinkTermination, PathEndpoint):
    """
    A physical power supply (intake) port within a Device. PowerPorts connect to PowerOutlets.
    """
    type = models.CharField(
        max_length=50,
        choices=PowerPortTypeChoices,
        blank=True,
        help_text='Physical port type'
    )
    maximum_draw = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum power draw (watts)"
    )
    allocated_draw = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Allocated power draw (watts)"
    )

    clone_fields = ['device', 'maximum_draw', 'allocated_draw']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:powerport', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        if self.maximum_draw is not None and self.allocated_draw is not None:
            if self.allocated_draw > self.maximum_draw:
                raise ValidationError({
                    'allocated_draw': f"Allocated draw cannot exceed the maximum draw ({self.maximum_draw}W)."
                })

    def get_power_draw(self):
        """
        Return the allocated and maximum power draw (in VA) and child PowerOutlet count for this PowerPort.
        """
        # Calculate aggregate draw of all child power outlets if no numbers have been defined manually
        if self.allocated_draw is None and self.maximum_draw is None:
            poweroutlet_ct = ContentType.objects.get_for_model(PowerOutlet)
            outlet_ids = PowerOutlet.objects.filter(power_port=self).values_list('pk', flat=True)
            utilization = PowerPort.objects.filter(
                _link_peer_type=poweroutlet_ct,
                _link_peer_id__in=outlet_ids
            ).aggregate(
                maximum_draw_total=Sum('maximum_draw'),
                allocated_draw_total=Sum('allocated_draw'),
            )
            ret = {
                'allocated': utilization['allocated_draw_total'] or 0,
                'maximum': utilization['maximum_draw_total'] or 0,
                'outlet_count': len(outlet_ids),
                'legs': [],
            }

            # Calculate per-leg aggregates for three-phase feeds
            if getattr(self._link_peer, 'phase', None) == PowerFeedPhaseChoices.PHASE_3PHASE:
                for leg, leg_name in PowerOutletFeedLegChoices:
                    outlet_ids = PowerOutlet.objects.filter(power_port=self, feed_leg=leg).values_list('pk', flat=True)
                    utilization = PowerPort.objects.filter(
                        _link_peer_type=poweroutlet_ct,
                        _link_peer_id__in=outlet_ids
                    ).aggregate(
                        maximum_draw_total=Sum('maximum_draw'),
                        allocated_draw_total=Sum('allocated_draw'),
                    )
                    ret['legs'].append({
                        'name': leg_name,
                        'allocated': utilization['allocated_draw_total'] or 0,
                        'maximum': utilization['maximum_draw_total'] or 0,
                        'outlet_count': len(outlet_ids),
                    })

            return ret

        # Default to administratively defined values
        return {
            'allocated': self.allocated_draw or 0,
            'maximum': self.maximum_draw or 0,
            'outlet_count': PowerOutlet.objects.filter(power_port=self).count(),
            'legs': [],
        }


class PowerOutlet(ModularComponentModel, LinkTermination, PathEndpoint):
    """
    A physical power outlet (output) within a Device which provides power to a PowerPort.
    """
    type = models.CharField(
        max_length=50,
        choices=PowerOutletTypeChoices,
        blank=True,
        help_text='Physical port type'
    )
    power_port = models.ForeignKey(
        to='dcim.PowerPort',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='poweroutlets'
    )
    feed_leg = models.CharField(
        max_length=50,
        choices=PowerOutletFeedLegChoices,
        blank=True,
        help_text="Phase (for three-phase feeds)"
    )

    clone_fields = ['device', 'type', 'power_port', 'feed_leg']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:poweroutlet', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Validate power port assignment
        if self.power_port and self.power_port.device != self.device:
            raise ValidationError(
                "Parent power port ({}) must belong to the same device".format(self.power_port)
            )


#
# Interfaces
#

class BaseInterface(models.Model):
    """
    Abstract base class for fields shared by dcim.Interface and virtualization.VMInterface.
    """
    enabled = models.BooleanField(
        default=True
    )
    mac_address = MACAddressField(
        null=True,
        blank=True,
        verbose_name='MAC Address'
    )
    mtu = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(INTERFACE_MTU_MIN),
            MaxValueValidator(INTERFACE_MTU_MAX)
        ],
        verbose_name='MTU'
    )
    mode = models.CharField(
        max_length=50,
        choices=InterfaceModeChoices,
        blank=True
    )
    parent = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        related_name='child_interfaces',
        null=True,
        blank=True,
        verbose_name='Parent interface'
    )
    bridge = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        related_name='bridge_interfaces',
        null=True,
        blank=True,
        verbose_name='Bridge interface'
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):

        # Remove untagged VLAN assignment for non-802.1Q interfaces
        if not self.mode:
            self.untagged_vlan = None

        # Only "tagged" interfaces may have tagged VLANs assigned. ("tagged all" implies all VLANs are assigned.)
        if self.pk and self.mode != InterfaceModeChoices.MODE_TAGGED:
            self.tagged_vlans.clear()

        return super().save(*args, **kwargs)

    @property
    def count_ipaddresses(self):
        return self.ip_addresses.count()

    @property
    def count_fhrp_groups(self):
        return self.fhrp_group_assignments.count()


class Interface(ModularComponentModel, BaseInterface, LinkTermination, PathEndpoint):
    """
    A network interface within a Device. A physical Interface can connect to exactly one other Interface.
    """
    # Override ComponentModel._name to specify naturalize_interface function
    _name = NaturalOrderingField(
        target_field='name',
        naturalize_function=naturalize_interface,
        max_length=100,
        blank=True
    )
    lag = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        related_name='member_interfaces',
        null=True,
        blank=True,
        verbose_name='Parent LAG'
    )
    type = models.CharField(
        max_length=50,
        choices=InterfaceTypeChoices
    )
    mgmt_only = models.BooleanField(
        default=False,
        verbose_name='Management only',
        help_text='This interface is used only for out-of-band management'
    )
    speed = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Speed (Kbps)'
    )
    duplex = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=InterfaceDuplexChoices
    )
    wwn = WWNField(
        null=True,
        blank=True,
        verbose_name='WWN',
        help_text='64-bit World Wide Name'
    )
    rf_role = models.CharField(
        max_length=30,
        choices=WirelessRoleChoices,
        blank=True,
        verbose_name='Wireless role'
    )
    rf_channel = models.CharField(
        max_length=50,
        choices=WirelessChannelChoices,
        blank=True,
        verbose_name='Wireless channel'
    )
    rf_channel_frequency = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Channel frequency (MHz)'
    )
    rf_channel_width = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        blank=True,
        null=True,
        verbose_name='Channel width (MHz)'
    )
    tx_power = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(MaxValueValidator(127),),
        verbose_name='Transmit power (dBm)'
    )
    wireless_link = models.ForeignKey(
        to='wireless.WirelessLink',
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True
    )
    wireless_lans = models.ManyToManyField(
        to='wireless.WirelessLAN',
        related_name='interfaces',
        blank=True,
        verbose_name='Wireless LANs'
    )
    untagged_vlan = models.ForeignKey(
        to='ipam.VLAN',
        on_delete=models.SET_NULL,
        related_name='interfaces_as_untagged',
        null=True,
        blank=True,
        verbose_name='Untagged VLAN'
    )
    tagged_vlans = models.ManyToManyField(
        to='ipam.VLAN',
        related_name='interfaces_as_tagged',
        blank=True,
        verbose_name='Tagged VLANs'
    )
    vrf = models.ForeignKey(
        to='ipam.VRF',
        on_delete=models.SET_NULL,
        related_name='interfaces',
        null=True,
        blank=True,
        verbose_name='VRF'
    )
    ip_addresses = GenericRelation(
        to='ipam.IPAddress',
        content_type_field='assigned_object_type',
        object_id_field='assigned_object_id',
        related_query_name='interface'
    )
    fhrp_group_assignments = GenericRelation(
        to='ipam.FHRPGroupAssignment',
        content_type_field='interface_type',
        object_id_field='interface_id',
        related_query_name='+'
    )

    clone_fields = ['device', 'parent', 'bridge', 'lag', 'type', 'mgmt_only']

    class Meta:
        ordering = ('device', CollateAsChar('_name'))
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:interface', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Virtual Interfaces cannot have a Cable attached
        if self.is_virtual and self.cable:
            raise ValidationError({
                'type': f"{self.get_type_display()} interfaces cannot have a cable attached."
            })

        # Virtual Interfaces cannot be marked as connected
        if self.is_virtual and self.mark_connected:
            raise ValidationError({
                'mark_connected': f"{self.get_type_display()} interfaces cannot be marked as connected."
            })

        # Parent validation

        # An interface cannot be its own parent
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({'parent': "An interface cannot be its own parent."})

        # A physical interface cannot have a parent interface
        if self.type != InterfaceTypeChoices.TYPE_VIRTUAL and self.parent is not None:
            raise ValidationError({'parent': "Only virtual interfaces may be assigned to a parent interface."})

        # An interface's parent must belong to the same device or virtual chassis
        if self.parent and self.parent.device != self.device:
            if self.device.virtual_chassis is None:
                raise ValidationError({
                    'parent': f"The selected parent interface ({self.parent}) belongs to a different device "
                              f"({self.parent.device})."
                })
            elif self.parent.device.virtual_chassis != self.parent.virtual_chassis:
                raise ValidationError({
                    'parent': f"The selected parent interface ({self.parent}) belongs to {self.parent.device}, which "
                              f"is not part of virtual chassis {self.device.virtual_chassis}."
                })

        # Bridge validation

        # An interface cannot be bridged to itself
        if self.pk and self.bridge_id == self.pk:
            raise ValidationError({'bridge': "An interface cannot be bridged to itself."})

        # A bridged interface belong to the same device or virtual chassis
        if self.bridge and self.bridge.device != self.device:
            if self.device.virtual_chassis is None:
                raise ValidationError({
                    'bridge': f"The selected bridge interface ({self.bridge}) belongs to a different device "
                              f"({self.bridge.device})."
                })
            elif self.bridge.device.virtual_chassis != self.device.virtual_chassis:
                raise ValidationError({
                    'bridge': f"The selected bridge interface ({self.bridge}) belongs to {self.bridge.device}, which "
                              f"is not part of virtual chassis {self.device.virtual_chassis}."
                })

        # LAG validation

        # A virtual interface cannot have a parent LAG
        if self.type == InterfaceTypeChoices.TYPE_VIRTUAL and self.lag is not None:
            raise ValidationError({'lag': "Virtual interfaces cannot have a parent LAG interface."})

        # A LAG interface cannot be its own parent
        if self.pk and self.lag_id == self.pk:
            raise ValidationError({'lag': "A LAG interface cannot be its own parent."})

        # An interface's LAG must belong to the same device or virtual chassis
        if self.lag and self.lag.device != self.device:
            if self.device.virtual_chassis is None:
                raise ValidationError({
                    'lag': f"The selected LAG interface ({self.lag}) belongs to a different device ({self.lag.device})."
                })
            elif self.lag.device.virtual_chassis != self.device.virtual_chassis:
                raise ValidationError({
                    'lag': f"The selected LAG interface ({self.lag}) belongs to {self.lag.device}, which is not part "
                           f"of virtual chassis {self.device.virtual_chassis}."
                })

        # Wireless validation

        # RF role & channel may only be set for wireless interfaces
        if self.rf_role and not self.is_wireless:
            raise ValidationError({'rf_role': "Wireless role may be set only on wireless interfaces."})
        if self.rf_channel and not self.is_wireless:
            raise ValidationError({'rf_channel': "Channel may be set only on wireless interfaces."})

        # Validate channel frequency against interface type and selected channel (if any)
        if self.rf_channel_frequency:
            if not self.is_wireless:
                raise ValidationError({
                    'rf_channel_frequency': "Channel frequency may be set only on wireless interfaces.",
                })
            if self.rf_channel and self.rf_channel_frequency != get_channel_attr(self.rf_channel, 'frequency'):
                raise ValidationError({
                    'rf_channel_frequency': "Cannot specify custom frequency with channel selected.",
                })
        elif self.rf_channel:
            self.rf_channel_frequency = get_channel_attr(self.rf_channel, 'frequency')

        # Validate channel width against interface type and selected channel (if any)
        if self.rf_channel_width:
            if not self.is_wireless:
                raise ValidationError({'rf_channel_width': "Channel width may be set only on wireless interfaces."})
            if self.rf_channel and self.rf_channel_width != get_channel_attr(self.rf_channel, 'width'):
                raise ValidationError({'rf_channel_width': "Cannot specify custom width with channel selected."})
        elif self.rf_channel:
            self.rf_channel_width = get_channel_attr(self.rf_channel, 'width')

        # VLAN validation

        # Validate untagged VLAN
        if self.untagged_vlan and self.untagged_vlan.site not in [self.device.site, None]:
            raise ValidationError({
                'untagged_vlan': f"The untagged VLAN ({self.untagged_vlan}) must belong to the same site as the "
                                 f"interface's parent device, or it must be global."
            })

    @property
    def _occupied(self):
        return super()._occupied or bool(self.wireless_link_id)

    @property
    def is_wired(self):
        return not self.is_virtual and not self.is_wireless

    @property
    def is_virtual(self):
        return self.type in VIRTUAL_IFACE_TYPES

    @property
    def is_wireless(self):
        return self.type in WIRELESS_IFACE_TYPES

    @property
    def is_lag(self):
        return self.type == InterfaceTypeChoices.TYPE_LAG

    @property
    def is_bridge(self):
        return self.type == InterfaceTypeChoices.TYPE_BRIDGE

    @property
    def link(self):
        return self.cable or self.wireless_link


#
# Pass-through ports
#

class FrontPort(ModularComponentModel, LinkTermination):
    """
    A pass-through port on the front of a Device.
    """
    type = models.CharField(
        max_length=50,
        choices=PortTypeChoices
    )
    color = ColorField(
        blank=True
    )
    rear_port = models.ForeignKey(
        to='dcim.RearPort',
        on_delete=models.CASCADE,
        related_name='frontports'
    )
    rear_port_position = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(REARPORT_POSITIONS_MIN),
            MaxValueValidator(REARPORT_POSITIONS_MAX)
        ]
    )

    clone_fields = ['device', 'type']

    class Meta:
        ordering = ('device', '_name')
        unique_together = (
            ('device', 'name'),
            ('rear_port', 'rear_port_position'),
        )

    def get_absolute_url(self):
        return reverse('dcim:frontport', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Validate rear port assignment
        if self.rear_port.device != self.device:
            raise ValidationError({
                "rear_port": f"Rear port ({self.rear_port}) must belong to the same device"
            })

        # Validate rear port position assignment
        if self.rear_port_position > self.rear_port.positions:
            raise ValidationError({
                "rear_port_position": f"Invalid rear port position ({self.rear_port_position}): Rear port "
                                      f"{self.rear_port.name} has only {self.rear_port.positions} positions"
            })


class RearPort(ModularComponentModel, LinkTermination):
    """
    A pass-through port on the rear of a Device.
    """
    type = models.CharField(
        max_length=50,
        choices=PortTypeChoices
    )
    color = ColorField(
        blank=True
    )
    positions = models.PositiveSmallIntegerField(
        default=1,
        validators=[
            MinValueValidator(REARPORT_POSITIONS_MIN),
            MaxValueValidator(REARPORT_POSITIONS_MAX)
        ]
    )
    clone_fields = ['device', 'type', 'positions']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:rearport', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Check that positions count is greater than or equal to the number of associated FrontPorts
        frontport_count = self.frontports.count()
        if self.positions < frontport_count:
            raise ValidationError({
                "positions": f"The number of positions cannot be less than the number of mapped front ports "
                             f"({frontport_count})"
            })


#
# Bays
#

class ModuleBay(ComponentModel):
    """
    An empty space within a Device which can house a child device
    """
    position = models.CharField(
        max_length=30,
        blank=True,
        help_text='Identifier to reference when renaming installed components'
    )

    clone_fields = ['device']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:modulebay', kwargs={'pk': self.pk})


class DeviceBay(ComponentModel):
    """
    An empty space within a Device which can house a child device
    """
    installed_device = models.OneToOneField(
        to='dcim.Device',
        on_delete=models.SET_NULL,
        related_name='parent_bay',
        blank=True,
        null=True
    )

    clone_fields = ['device']

    class Meta:
        ordering = ('device', '_name')
        unique_together = ('device', 'name')

    def get_absolute_url(self):
        return reverse('dcim:devicebay', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # Validate that the parent Device can have DeviceBays
        if not self.device.device_type.is_parent_device:
            raise ValidationError("This type of device ({}) does not support device bays.".format(
                self.device.device_type
            ))

        # Cannot install a device into itself, obviously
        if self.device == self.installed_device:
            raise ValidationError("Cannot install a device into itself.")

        # Check that the installed device is not already installed elsewhere
        if self.installed_device:
            current_bay = DeviceBay.objects.filter(installed_device=self.installed_device).first()
            if current_bay and current_bay != self:
                raise ValidationError({
                    'installed_device': "Cannot install the specified device; device is already installed in {}".format(
                        current_bay
                    )
                })


#
# Inventory items
#


class InventoryItemRole(OrganizationalModel):
    """
    Inventory items may optionally be assigned a functional role.
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
    description = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('dcim:inventoryitemrole', args=[self.pk])


class InventoryItem(MPTTModel, ComponentModel):
    """
    An InventoryItem represents a serialized piece of hardware within a Device, such as a line card or power supply.
    InventoryItems are used only for inventory purposes.
    """
    parent = TreeForeignKey(
        to='self',
        on_delete=models.CASCADE,
        related_name='child_items',
        blank=True,
        null=True,
        db_index=True
    )
    component_type = models.ForeignKey(
        to=ContentType,
        limit_choices_to=MODULAR_COMPONENT_MODELS,
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True
    )
    component_id = models.PositiveBigIntegerField(
        blank=True,
        null=True
    )
    component = GenericForeignKey(
        ct_field='component_type',
        fk_field='component_id'
    )
    role = models.ForeignKey(
        to='dcim.InventoryItemRole',
        on_delete=models.PROTECT,
        related_name='inventory_items',
        blank=True,
        null=True
    )
    manufacturer = models.ForeignKey(
        to='dcim.Manufacturer',
        on_delete=models.PROTECT,
        related_name='inventory_items',
        blank=True,
        null=True
    )
    part_id = models.CharField(
        max_length=50,
        verbose_name='Part ID',
        blank=True,
        help_text='Manufacturer-assigned part identifier'
    )
    serial = models.CharField(
        max_length=50,
        verbose_name='Serial number',
        blank=True
    )
    asset_tag = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Asset tag',
        help_text='A unique tag used to identify this item'
    )
    discovered = models.BooleanField(
        default=False,
        help_text='This item was automatically discovered'
    )

    objects = TreeManager()

    clone_fields = ['device', 'parent', 'role', 'manufacturer', 'part_id']

    class Meta:
        ordering = ('device__id', 'parent__id', '_name')
        unique_together = ('device', 'parent', 'name')

    def get_absolute_url(self):
        return reverse('dcim:inventoryitem', kwargs={'pk': self.pk})

    def clean(self):
        super().clean()

        # An InventoryItem cannot be its own parent
        if self.pk and self.parent_id == self.pk:
            raise ValidationError({
                "parent": "Cannot assign self as parent."
            })
