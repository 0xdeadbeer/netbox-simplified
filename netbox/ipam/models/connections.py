from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from ipam.choices import *
from ipam.constants import *
from netbox.models import NetBoxModel
from utilities.utils import array_to_string
from extras.models import ConfigContextModel
from extras.querysets import ConfigContextModelQuerySet
from utilities.fields import ColorField, NaturalOrderingField


__all__ = (
    'Connection',
)

class Connection(NetBoxModel, ConfigContextModel):
    """
    """
    name = models.CharField(
        max_length=100
    )
    _name = NaturalOrderingField(
        target_field='name',
        max_length=100,
        blank=True,
        null=True
    )
    protocol = models.CharField (
        max_length=255,
        null=True,
        blank=True, 
        verbose_name='Protocol'
    )
    port = models.CharField (
        max_length=255,
        null=True,
        blank=True, 
        verbose_name='Port'
    )
    device_from = models.ManyToManyField (
        to='dcim.Device',
        related_name='from_services',
        verbose_name='from_device',
        blank=True
    )
    device_to = models.ManyToManyField(
        to='dcim.Device',
        related_name='to_services',
        verbose_name='to_device',
        blank=True
    )
    comments = models.CharField ( 
        max_length=255,
        null=True, 
        blank=True, 
        verbose_name='Comments'
    )

    objects = ConfigContextModelQuerySet.as_manager()

    clone_fields = [
        'protocol', 'port', 'device_from', 'device_to', 'comments'
    ]
    class Meta:
        ordering = ('_name', 'pk',)  # (protocol, port) may be non-unique
        unique_together = (
            ('name'),
        )

    def get_absolute_url(self):
        return reverse('ipam:connection', args=[self.pk])

    def validate_unique(self, exclude=None):

        # Check for a duplicate name on a device assigned to the same Site and no Tenant. This is necessary
        # because Django does not consider two NULL fields to be equal, and thus will not trigger a violation
        # of the uniqueness constraint without manual intervention.
        if self.name:
            if Connection.objects.exclude(pk=self.pk).filter(
                    name=self.name,
            ):
                raise ValidationError({
                    'name': 'A connection with this name already exists.'
                })

    def clean(self):
        super().clean()

        # # A Service must belong to a Device *or* to a VirtualMachine
        # if not (self.device_from and self.device_to):
        #     raise ValidationError("Both from and to devices are required for a connection")
    
    @property
    def identifier(self):
        """
        Return the connection name if set; otherwise return the connections's primary key as {pk}
        """
        if self.name is not None:
            return self.name
        return '{{{}}}'.format(self.pk)